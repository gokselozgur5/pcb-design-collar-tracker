#!/usr/bin/env python3
"""Screen bounded staking volumes at r18 poses; adhesion is a physical test."""
import hashlib
import json
from pathlib import Path

import numpy as np
from shapely.geometry import box

from check_charge_thermal_clearance import retention_envelopes, parts, p, r
from check_internal_harness import point_box_distance
from internal_harness_geometry import evaluate, physical_radii

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assembly/internal-charge-r03'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def box_gap(a, b, c, d):
    return float(np.linalg.norm(np.maximum(0, np.maximum(c - b, a - d))))


def validate(spec):
    if spec['adhesion_to_PTFE_relied_on'] or spec['material_candidate'] != 'DOWSIL 3145 RTV MIL-A-46146 Gray':
        raise ValueError('This prototype has no qualified PTFE bond or substitute material')
    if spec['minimum_clearance_mm'] != .2 or spec['minimum_bare_conductor_cover_mm'] != .05:
        raise ValueError('Do not weaken the declared clearance or cover')
    if [(p['id'],p['anchor'],p['wires']) for p in spec['patches']] != [
        ('pcb-pair','pcb',[0,1]),('red-terminal','body',[0]),('black-terminal','body',[1])]:
        raise ValueError('Missing or changed conductor ownership')
    for patch in spec['patches']:
        a,b=np.asarray(patch['low_mm']),np.asarray(patch['high_mm'])
        if a.shape!=(3,) or b.shape!=(3,) or not np.isfinite([a,b]).all() or not (b>a).all():
            raise ValueError('Invalid staking volume')
    for key in ['holding_force_qualified','continuous_motion_accepted','physical_qualification','manufacturing_release']:
        if spec[key]:
            raise ValueError('Physical qualification is not supplied by CAD')


def envelopes(spec, row):
    shift = np.asarray(row['pcb_pose_mm']) - [0, 0, 11.24088]
    error = spec['nominal_envelope_position_allowance_mm']
    result = []
    for patch in spec['patches']:
        delta = shift if patch['anchor'] == 'pcb' else np.zeros(3)
        a, b = np.asarray(patch['low_mm']) + delta, np.asarray(patch['high_mm']) + delta
        low, high = a - error, b + error
        if patch['anchor'] == 'pcb':
            # The substrate face defines the bottom; dispensing cannot go below it.
            low[2] = a[2]
        result.append((patch, a, b, low, high))
    return result


def check_pose(spec, row, model, wire_spec, reliefs):
    shift = np.asarray(row['pcb_pose_mm']) - [0, 0, 11.24088]
    thermal = np.array([.15, .15, .08])
    solids = retention_envelopes(reliefs)
    rf = [evaluate(c['control_points_mm'], 4001) for c in row['cables']]
    wires = [evaluate(c, 16001) for c in row['charge_controls']]
    boxes = envelopes(spec, row)
    checks = []

    def add(name, value, minimum=spec['minimum_clearance_mm'], **extra):
        checks.append(dict(name=name, value=float(value), minimum=minimum,
                           pass_=bool(value >= minimum-1e-8), **extra))

    for patch, a, b, low, high in boxes:
        label = patch['id']
        gaps = []
        for part in parts:
            if part['ref'] == 'J3':
                continue  # Native J3 solder-pad ownership is checked by r18.
            x, y, u, v = part['envelope_xy_bounds_mm']
            z0, z1 = part['envelope_z_mm']
            lo = np.array([x, y, z0]) + shift - thermal
            hi = np.array([u, v, z1]) + shift + thermal
            if part['side'] == 'bottom':
                lo[2] -= .91 - .84088
            gaps.append((box_gap(low, high, lo, hi), part['ref']))
        value, limiting = min(gaps)
        add(label + ' expanded components', value, obstacle=limiting)
        values = [(float(np.hypot(box(*low[:2], *high[:2]).distance(s),
                                  max(0, z0-high[2], low[2]-z1))), name)
                  for name, s, z0, z1 in solids]
        value, limiting = min(values)
        add(label + ' swept retention', value, obstacle=limiting)
        for name, curve in zip(['LTE', 'GNSS'], rf, strict=True):
            add(label + ' ' + name, point_box_distance(curve['xyz'], low, high).min()
                - .715 - curve['travel_bound']/2)
        for index, other in enumerate(wires):
            if index in patch['wires']:
                continue  # Only explicitly owned conductors may touch this insulating block.
            radii = physical_radii(other, wire_spec['wire'])[0]
            add(label + ' opposite charge lead',
                (point_box_distance(other['xyz'], low, high)-radii).min()
                - wire_spec['wire']['free_route_position_allowance_mm']-other['travel_bound']/2)
        for clip in model['clips']:
            add(label + ' guide ' + clip['name'],
                box_gap(low, high, np.array(clip['low']), np.array(clip['high'])+[0, 0, .1]))
        for antenna in p['antenna_reservations']:
            center, size = np.array(antenna['center']), np.array(antenna['size'])
            add(label + ' ' + antenna['label'], box_gap(low, high, center-size/2, center+size/2))
        add(label + ' lid', p['body']['size'][2]-high[2])
        if patch['anchor'] == 'pcb':
            add(label + ' cavity X', p['body']['cavity'][0]/2-max(abs(low[0]), abs(high[0])))
            add(label + ' cavity Y', p['body']['cavity'][1]/2-max(abs(low[1]), abs(high[1])))
        else:
            # Only the r16 dedicated terminal tail pocket is an intentional owner.
            cy = [-3.3, 6][patch['wires'][0]]
            corner_radius = np.hypot(max(abs(low[1]-cy), abs(high[1]-cy)),
                                     max(abs(low[2]-13.3), abs(high[2]-13.3)))
            add(label + ' pocket radial wall', 2.1-.05-corner_radius)
            add(label + ' pocket back', 22.6-.05-high[0], .05)
        for wire_index in patch['wires']:
            curve = wires[wire_index]
            arc = (curve['arc_lower'] + curve['arc_upper'])/2
            end = patch['anchor'] == 'pcb'
            offset = arc[-1]-arc if end else arc
            lower, upper = patch['bare_capture_from_tip_mm']
            selected = (offset >= lower-curve['travel_bound']) & (offset <= upper+curve['travel_bound'])
            # The minimum filled box is eroded for total placement/service error. Retain the same
            # free-wire uncertainty used by r18; do not substitute tip error here.
            error = spec['nominal_envelope_position_allowance_mm']
            inner_low, inner_high = a+error, b-error
            if end:
                inner_low[2] = a[2]
            cover = (wire_spec['wire']['conductor_diameter_incoming_max_mm']/2
                     + wire_spec['wire']['free_route_position_allowance_mm']
                     + curve['travel_bound']/2)
            margin = np.minimum(curve['xyz'][selected]-inner_low,
                                inner_high-curve['xyz'][selected]).min() - cover
            add(label + f' wire {wire_index} bare conductor cover', margin, spec['minimum_bare_conductor_cover_mm'])
            strip = wire_spec['wire']['pcb_strip_mm' if end else 'terminal_strip_mm']
            add(label + f' wire {wire_index} capture before PTFE', strip-wire_spec['wire']['strip_length_tolerance_mm']
                - wire_spec['wire']['free_route_position_allowance_mm']-upper, .2)
            # Quantify deformation of the captured curve relative to its owning end.
            # This is an imposed static displacement, not an elastomer strain/force result.
            length = np.linspace(lower, upper, 41)
            sampled = np.array([[np.interp(arc[-1]-s if end else s, arc, curve['xyz'][:,j])
                                 for j in range(3)] for s in length])
            if end:
                sampled -= shift
            patch_info = dict(patch=label+f'-wire-{wire_index}', captured_points_owner_frame_mm=sampled.tolist())
            checks[-1]['attachment_geometry'] = patch_info
    for i, (one, _, _, a, b) in enumerate(boxes):
        for two, _, _, c, d in boxes[i+1:]:
            add(one['id'] + ' versus ' + two['id'], box_gap(a,b,c,d))
    return dict(pose_index=row['pose_index'], pass_=all(c['pass_'] for c in checks), checks=checks)


def build():
    spec = json.loads((OUT/'restraint.json').read_text())
    validate(spec)
    model = json.loads((ROOT/spec['route_source']).read_text())
    wire_spec = json.loads((ROOT/'assembly/internal-charge-r02/harness.json').read_text())
    reliefs = json.loads((ROOT/'mechanical/swim-r18-charge-clearance/retainer-reliefs.json').read_text())
    names = ['assembly/internal-charge-r03/restraint.json', spec['route_source'],
             'assembly/internal-charge-r02/harness.json',
             'mechanical/swim-r18-charge-clearance/retainer-reliefs.json',
             'scripts/check_charge_restraint.py', 'scripts/check_charge_thermal_clearance.py',
             'scripts/internal_harness_geometry.py', 'scripts/check_internal_harness.py',
             'scripts/check_cable_integration.py', 'scripts/check_thermal_assembly.py',
             'mechanical/swim-r11-thermal-fit/parameters.json',
             'mechanical/swim-r11-thermal-fit/retention.json',
             'mechanical/swim-r11-thermal-fit/antenna-fit.json']
    hashes = {name:sha(ROOT/name) for name in names}
    rows = []
    for row in model['poses']:
        result = check_pose(spec, row, model, wire_spec, reliefs)
        rows.append(result)
        print(row['pose_index'], 'PASS' if result['pass_'] else 'HOLD',
              [(c['name'], round(c['value'],6)) for c in result['checks'] if not c['pass_']], flush=True)
    if any(sha(ROOT/name) != digest for name,digest in hashes.items()):
        raise ValueError('Source changed during analysis')
    reference = {c['attachment_geometry']['patch']: np.array(c['attachment_geometry']['captured_points_owner_frame_mm'])
                 for c in rows[13]['checks'] if 'attachment_geometry' in c}
    motion = {name:0.0 for name in reference}
    for row in rows:
        for check in row['checks']:
            if 'attachment_geometry' not in check:
                continue
            d = check['attachment_geometry'];name=d['patch']
            motion[name] = max(motion[name],float(np.linalg.norm(
                np.array(d['captured_points_owner_frame_mm'])-reference[name],axis=1).max()))
    report = dict(result='STATIC_STAKING_ENVELOPES_PASS' if all(v['pass_'] for v in rows) else 'HOLD',
                  inputs=hashes, total_poses=len(rows), passing_poses=sum(v['pass_'] for v in rows),
                  poses=rows, imposed_capture_displacement_from_nominal_mm=motion,
                  prototype_restraint_geometry_implemented=True, holding_force_qualified=False,
                  physical_qualification=False, continuous_motion_accepted=False, manufacturing_release=False)
    (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    raise SystemExit(0 if build()['result']=='STATIC_STAKING_ENVELOPES_PASS' else 1)
