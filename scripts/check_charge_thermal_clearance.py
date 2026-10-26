#!/usr/bin/env python3
"""Supplement the frozen r17 screen with charge-wire thermal/retainer envelopes.

The charge checker in r17 uses nominal component and retention envelopes. This
successor checks the same declared allowances already used for RF. Static curve
acceptance does not establish restraint, continuous motion or physical release.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np
from shapely import distance, points
from shapely.geometry import box
from shapely.ops import unary_union

from check_cable_integration import check_charge_pose, check_rf, validate_model, p, r, parts
from check_internal_harness import point_box_distance
from check_thermal_assembly import retention_solids
from internal_harness_geometry import evaluate, physical_radii

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/swim-r18-charge-clearance'
BASE = ROOT / 'mechanical/swim-r17-cable-integration'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def retention_envelopes(reliefs):
    """Expand each actual section after cutting, so notches shrink under error."""
    rails, ribs, posts, frames = retention_solids(p, r)
    q = r['motion_screen']
    levels = sorted({r['frame']['bottom_z_mm'],
                     r['frame']['bottom_z_mm'] + r['frame']['height_mm'],
                     *[v['bottom_z_mm'] for v in reliefs['cuts']]})
    actual = []
    for name, shape, low, high in frames:
        if name != 'retainer frame' or not reliefs['cuts']:
            actual.append((name, shape, low, high))
            continue
        for z0, z1 in zip(levels, levels[1:]):
            section = shape
            for cut in reliefs['cuts']:
                if z0 >= cut['bottom_z_mm']:
                    section = section.difference(box(*cut['xy_mm']))
            if not section.is_empty:
                actual.append((name, section, z0, z1))
    spread = q['retainer_to_body_xy_mm'] + .025 + q['thermal_xy_allowance_mm']
    swept = [(name, shape.buffer(spread, join_style='mitre'),
              low + q['retainer_bottom_z_mm'][0] - r['frame']['bottom_z_mm'],
              high + q['retainer_bottom_z_mm'][1] - r['frame']['bottom_z_mm'] + .05)
             for name, shape, low, high in actual]
    rails = [(name, shape.buffer(.36 + .025 + q['thermal_xy_allowance_mm'],
                                 join_style='mitre'),
              low - .05 - q['thermal_z_allowance_mm'],
              high + .05 + q['thermal_z_allowance_mm'])
             for name, shape, low, high in rails]
    return rails + ribs + posts + swept


def supplemental(model, index, reliefs, count=4001):
    spec = json.loads((ROOT/'assembly/internal-charge-r02/harness.json').read_text())
    row = model['poses'][index]
    shift = np.asarray(row['pcb_pose_mm']) - [0, 0, spec['pcb_nominal_top_mm']]
    q = r['motion_screen']
    thermal = np.array([q['thermal_xy_allowance_mm']]*2 + [q['thermal_z_allowance_mm']])
    solids = retention_envelopes(reliefs)
    checks = []
    for wire, control in zip(spec['wires'], row['charge_controls'], strict=True):
        curve = evaluate(control, count)
        xyz = curve['xyz']
        radius = (physical_radii(curve, spec['wire'])[0]
                  + spec['wire']['free_route_position_allowance_mm'] + curve['travel_bound']/2)
        obstacles = []
        for part in parts:
            if part['ref'] == 'J3':
                continue
            x, y, u, v = part['envelope_xy_bounds_mm']
            z0, z1 = part['envelope_z_mm']
            lo = np.array([x, y, z0]) + shift - thermal
            hi = np.array([u, v, z1]) + shift + thermal
            # Preserve the r11 lower-face thickness sensitivity as well.
            if part['side'] == 'bottom':
                lo[2] -= .91 - .84088
            gaps = point_box_distance(xyz, lo, hi) - radius
            i = int(gaps.argmin())
            obstacles.append(dict(obstacle=part['ref'], value=float(gaps[i]), xyz_mm=xyz[i].tolist()))
        mechanical = []
        for name, shape, low, high in solids:
            planar = distance(shape, points(xyz[:, :2]))
            vertical = np.maximum(0, np.maximum(low-xyz[:, 2], xyz[:, 2]-high))
            gaps = np.hypot(planar, vertical) - radius
            i = int(gaps.argmin())
            mechanical.append(dict(obstacle=name, value=float(gaps[i]), xyz_mm=xyz[i].tolist()))
        for label, candidates in [('thermal component envelopes', obstacles),
                                  ('swept retention envelopes', mechanical)]:
            limiting = min(candidates, key=lambda v: v['value'])
            checks.append(dict(name=wire['colour']+' '+label, **limiting,
                               minimum=spec['minimum_gap_mm'],
                               pass_=limiting['value'] >= spec['minimum_gap_mm']-1e-8))
    return dict(pose_index=index, checks=checks, pass_=all(v['pass_'] for v in checks))


def validate_reliefs(reliefs):
    bottom = r['frame']['bottom_z_mm']
    top = bottom + r['frame']['height_mm']
    tabs = unary_union([box(*v) for v in r['capture_tabs_xy_mm']+r['north_tabs_xy_mm']])
    for cut in reliefs['cuts']:
        values = cut['xy_mm'] + [cut['bottom_z_mm']]
        if not np.isfinite(values).all() or not bottom < cut['bottom_z_mm'] < top:
            raise ValueError('Invalid relief dimensions')
        x, y, u, v = cut['xy_mm']
        if x >= u or y >= v or box(x, y, u, v).intersects(tabs):
            raise ValueError('Relief removes a PCB capture tab')
        if cut['bottom_z_mm'] - bottom < reliefs['minimum_remaining_height_mm']:
            raise ValueError('Relief removes the lower frame bridge')
        for key in r['radial_keys']:
            if box(*key['xy_mm']).intersects(box(x, y, u, v)):
                raise ValueError('Relief overlaps a radial key')
    if reliefs['physical_strength_qualified']:
        raise ValueError('Geometric relief does not establish frame strength')


def build(baseline=False):
    source = BASE/'routing.json' if baseline else OUT/'routing.json'
    model = json.loads(source.read_text())
    reliefs = json.loads((OUT/'retainer-reliefs.json').read_text())
    if baseline:
        reliefs = copy.deepcopy(reliefs)
        reliefs['cuts'] = []
    validate_model(model)
    validate_reliefs(reliefs)
    previous = json.loads((BASE/'routing.json').read_text())
    if any(a['cables'][0] != b['cables'][0] for a, b in zip(model['poses'], previous['poses'])):
        raise ValueError('This successor retains the accepted LTE source curves')
    dependencies = json.loads((BASE/'checks.json').read_text())['inputs']
    names = list(dependencies) + [str(source.relative_to(ROOT)),
                                  'mechanical/swim-r18-charge-clearance/retainer-reliefs.json',
                                  'scripts/check_charge_thermal_clearance.py']
    hashes = {name: sha(ROOT/name) for name in names}
    poses = []
    rf = check_rf(model)
    for i in range(27):
        extra = supplemental(model, i, reliefs)
        if not extra['pass_']:
            extra = supplemental(model, i, reliefs, 16001)
        original = check_charge_pose(model, i)
        poses.append(dict(pose_index=i, original=original, thermal=extra, rf=rf[i],
                          pass_=extra['pass_'] and original['pass_'] and rf[i]['pass_']))
        failures = [c['name'] for c in original['checks']+extra['checks']+rf[i]['checks'] if not c['pass_']]
        print(i, 'PASS' if poses[-1]['pass_'] else 'HOLD', failures, flush=True)
    if any(sha(ROOT/name) != digest for name, digest in hashes.items()):
        raise ValueError('Source changed during check')
    result = dict(result='THERMAL_STATIC_ROUTE_PASS' if all(v['pass_'] for v in poses) else 'HOLD',
                  inputs=hashes, baseline=baseline, poses=poses,
                  passing_poses=sum(v['pass_'] for v in poses), total_poses=27,
                  physical_qualification=False, manufacturing_release=False,
                  restraint_implemented=False, continuous_motion_accepted=False)
    dest = OUT/('baseline-failures.json' if baseline else 'checks.json')
    dest.write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args()
    result = build(args.baseline)
    print(result['result'], result['passing_poses'], '/ 27')
    raise SystemExit(result['result'] == 'HOLD' and not args.baseline)
