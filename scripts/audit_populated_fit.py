#!/usr/bin/env python3
"""Check native-position component envelopes against the enclosure and carrier.

Use the geometry venv. Manufacturer height maxima and explicit assembly allowances
are kept separate from unapproved harness/antenna/battery reservations. The report
never implies complete mechanical, electrical, RF or ingress qualification.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rounded_rect(w, h, r):
    return box(-w / 2 + r, -h / 2 + r, w / 2 - r, h / 2 - r).buffer(r, quad_segs=128)


def carrier_solids(parameters, reliefs):
    p = parameters['pcb']
    floor = parameters['body']['floor']
    ring = rounded_rect(41.6, 33.6, 1.8).difference(rounded_rect(39.2, 31.2, .6))
    levels = sorted({0, 1.5} | {min(1.5, r.get('depth_mm', 1.5)) for r in reliefs})
    solids = []
    for low, high in zip(levels, levels[1:]):
        section = ring
        for r in reliefs:
            if r.get('depth_mm', 1.5) > low:
                section = section.difference(box(*r['bounds_mm']))
        solids.append(('carrier ledge', section, p['bottom_z'] - 1.5 + low, p['bottom_z'] - 1.5 + high))
    for s in (-1, 1):
        for y in (-12, 12):
            solids.extend([
                ('carrier guide', box(s * 20.4 - .3, y - 1, s * 20.4 + .3, y + 1),
                 p['bottom_z'] - 1.5, p['bottom_z'] + 1.2),
                ('carrier leg', box(s * 19.8 - .5, y - 1, s * 19.8 + .5, y + 1),
                 floor, p['bottom_z'] - 1.5),
            ])
    return solids


def solid_distance(a, b):
    """Euclidean distance between two prismatic conservative envelopes."""
    pa, alo, ahi = a
    pb, blo, bhi = b
    return math.hypot(pa.distance(pb), max(alo - bhi, blo - ahi, 0))


def evaluate(native, profile, parameters, reliefs=None):
    indexed = {r['ref']: r for r in profile['parts']}
    assert len(indexed) == len(profile['parts']), 'Duplicate fit profile reference'
    assert set(indexed) == {r['ref'] for r in native['parts']}, 'Incomplete fit profile'
    assert native['board_size_mm'] == parameters['pcb']['size']
    pcb, body = parameters['pcb'], parameters['body']
    xy = profile['xy_allowance_mm']
    z_allowance = profile['solder_allowance_mm'] + profile['board_warp_allowance_mm']
    gap = profile['minimum_mechanical_gap_mm']
    assert xy >= 0 and z_allowance >= 0 and gap > 0
    cavity = rounded_rect(*body['cavity'], body['cavity_radius'])
    reliefs = profile['carrier_reliefs'] if reliefs is None else reliefs
    obstacles = carrier_solids(parameters, reliefs)
    battery = parameters['battery_reservation']
    obstacles.append(('battery reservation', box(-battery['size'][0] / 2, -battery['size'][1] / 2,
                                                battery['size'][0] / 2, battery['size'][1] / 2),
                      battery['bottom_z'], battery['bottom_z'] + battery['size'][2]))
    for a in parameters['antenna_reservations']:
        cx, cy, cz = a['center']
        w, d, h = a['size']
        obstacles.append((a['label'], box(cx - w / 2, cy - d / 2, cx + w / 2, cy + d / 2), cz - h / 2, cz + h / 2))
    c, retention = parameters['contacts'], profile['contact_retention']
    assert c['thread_major'] == retention['thread_major_mm']
    assert retention['all_orientation_diameter_mm'] >= retention['nut_across_flats_max_mm'] * 2 / math.sqrt(3)
    stack = retention['nut_thickness_max_mm'] + retention['washer_and_lug_stack_max_mm']
    radius = retention['all_orientation_diameter_mm'] / 2
    inner_x = body['cavity'][0] / 2
    hardware = [('contact backing stack', box(inner_x - stack, y - radius, inner_x, y + radius),
                 c['center_z'] - radius, c['center_z'] + radius) for y in c['centers_y']]
    hardware_checks = []
    for name, shape, lo, hi in hardware:
        # The contact intentionally bears on the cavity wall; inspect floor,
        # board and other contents instead of requiring wall separation.
        distances = [('floor', lo - body['floor']),
                     ('board underside', pcb['bottom_z'] - profile['board_warp_allowance_mm'] - hi)]
        distances += [(n, solid_distance((shape, lo, hi), (s, l, h))) for n, s, l, h in obstacles
                      if n not in [a['label'] for a in parameters['antenna_reservations']]]
        hardware_checks.extend(dict(item=name, obstacle=n, clearance_mm=round(d, 6), pass_=d >= gap - 1e-8)
                               for n, d in distances)
    hardware_checks.append(dict(item='contact thread', obstacle='engagement stack',
                                clearance_mm=c['thread_length'] - stack,
                                pass_=c['thread_length'] - stack >= retention['minimum_exposed_thread_mm'] - 1e-8))
    original_r = retention['original_M4_envelope']['across_flats_mm'] / math.sqrt(3)
    original_hardware = dict(
        nut_all_rotation_radius_mm=original_r,
        floor_gap_mm=retention['original_M4_envelope']['center_z_mm'] - original_r - body['floor'],
        board_gap_mm=pcb['bottom_z'] - profile['board_warp_allowance_mm'] - retention['original_M4_envelope']['center_z_mm'] - original_r,
        scope='Conservative all-rotation M4 hex-nut envelope from the r01 requirement; not a measured assembled collision.')
    obstacles += hardware
    parts = []
    violations = []
    for actual in native['parts']:
        ref = actual['ref']
        definition = indexed[ref]
        assert actual['dnp'] == (definition['status'] == 'dnp'), ref + ': DNP mismatch'
        if actual['dnp']:
            continue
        assert definition['height_max_mm'] > 0
        footprint = box(*actual['body_and_land_bounds_mm'])
        if 'mated_sweep_radius_mm' in definition:
            x, y = actual['position_mm']
            r = definition['mated_sweep_radius_mm']
            # A square encloses all plug rotations and matches the exported CAD.
            footprint = footprint.union(box(x - r, y - r, x + r, y + r))
        envelope = box(*footprint.bounds).buffer(xy, join_style='mitre')
        h = definition['height_max_mm'] + z_allowance
        if actual['side'] == 'top':
            lo, hi = pcb['bottom_z'] + pcb['size'][2], pcb['bottom_z'] + pcb['size'][2] + h
        else:
            lo, hi = pcb['bottom_z'] - h, pcb['bottom_z']
        wall_gap = envelope.distance(cavity.boundary) if cavity.covers(envelope) else -envelope.difference(cavity).area
        clearances = [('cavity wall', wall_gap), ('floor', lo - body['floor']), ('lid underside', body['size'][2] - hi)]
        for name, shape, zlo, zhi in obstacles:
            clearances.append((name, solid_distance((envelope, lo, hi), (shape, zlo, zhi))))
        for name, distance in clearances:
            if distance < gap - 1e-8:
                violations.append(dict(ref=ref, obstacle=name, clearance_mm=round(distance, 6), required_mm=gap))
        minimum = min(clearances, key=lambda r: r[1])
        parts.append(dict(ref=ref, side=actual['side'], mpn=definition['mpn'], status=definition['status'],
                          height_max_mm=definition['height_max_mm'], applied_z_allowance_mm=z_allowance,
                          nominal_xy_bounds_mm=actual['body_and_land_bounds_mm'],
                          envelope_xy_bounds_mm=list(envelope.bounds), envelope_z_mm=[lo, hi],
                          minimum_gap_mm=round(minimum[1], 6), limiting_obstacle=minimum[0]))
    return dict(parts=parts, violations=violations, checked=len(parts),
                hardware_checks=hardware_checks, original_M4_hardware=original_hardware,
                checked_geometry_pass=not violations and all(r['pass_'] for r in hardware_checks),
                production_assembly_complete=False,
                board_side_height_mm={side: max(r['height_max_mm'] + r['applied_z_allowance_mm'] for r in parts if r['side'] == side)
                                      for side in ('top', 'bottom')},
                minimum_required_gap_mm=gap, open_items=profile['open_items'],
                scope='Conservative native body/land boxes plus assembly XY allowance and sourced maximum heights plus solder/warp allowance. Tests carrier ledge/legs/guides, cavity, floor/lid, contact backing stack, and existing battery/antenna reservations. Does not test cable routing, carrier retention, actual pack/antennas, full hardware interference, physical tolerance capability or RF/IP qualification.')


def write_scad(out, report, profile):
    rows = []
    for r in report['parts']:
        a, b, c, d = r['envelope_xy_bounds_mm']
        lo, hi = r['envelope_z_mm']
        rows.append([r['ref'], [a, b, lo], [c - a, d - b, hi - lo], r['status']])
    text = '// Generated by scripts/audit_populated_fit.py. Conservative fit envelopes, not detailed part models.\n'
    text += 'fit_boxes = ' + json.dumps(rows) + ';\n'
    text += 'carrier_reliefs = ' + json.dumps([r['bounds_mm'] + [r.get('depth_mm', 1.5)] for r in profile['carrier_reliefs']]) + ';\n'
    retention = profile['contact_retention']
    text += 'retention_d = ' + str(retention['all_orientation_diameter_mm']) + ';\n'
    text += 'retention_stack = ' + str(retention['nut_thickness_max_mm'] + retention['washer_and_lug_stack_max_mm']) + ';\n'
    (out / 'populated.scad').write_text(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT / 'mechanical/swim-r02-fit')
    args = parser.parse_args()
    out = args.directory.resolve()
    assert ROOT in out.parents
    paths = {n: out / n for n in ('components.native.json', 'fit-profile.json', 'parameters.json')}
    native, profile, parameters = [json.loads(paths[n].read_text()) for n in paths]
    assert sha(ROOT / native['source']) == native['source_sha256'], 'PCB changed; re-export actual geometry'
    assert sha(ROOT / 'scripts/export_populated_geometry.py') == native['exporter_sha256'], 'Exporter changed; re-export'
    result = evaluate(native, profile, parameters)
    previous = evaluate(native, profile, parameters, reliefs=profile['carrier_reliefs'][:1])
    result.update(input_sha256={n: sha(p) for n, p in paths.items()}, checker_sha256=sha(Path(__file__)),
                  pcb_sha256=native['source_sha256'], original_carrier_violations=previous['violations'],
                  original_carrier_hardware_violations=[r for r in previous['hardware_checks'] if not r['pass_']])
    (out / 'populated-fit.json').write_text(json.dumps(result, indent=2) + '\n')
    write_scad(out, result, profile)
    print(json.dumps({k: result[k] for k in ('checked', 'checked_geometry_pass', 'violations', 'original_carrier_violations', 'board_side_height_mm')}))
    raise SystemExit(not result['checked_geometry_pass'])


if __name__ == '__main__':
    main()
