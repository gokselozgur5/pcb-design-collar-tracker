#!/usr/bin/env python3
"""Read-only identity and result verification for the r18 static route correction."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from inspect_enclosure_mesh import inspect
from verify_cable_integration import verify as verify_parent

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'mechanical/swim-r18-charge-clearance'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def evidence():
    verify_parent()
    model = json.loads((OUT/'routing.json').read_text())
    report = json.loads((OUT/'checks.json').read_text())
    baseline = json.loads((OUT/'baseline-failures.json').read_text())
    cad = json.loads((OUT/'cad-checks.json').read_text())
    parent = json.loads((ROOT/'mechanical/swim-r17-cable-integration/routing.json').read_text())
    nominal = json.loads((OUT/'nominal-routing.json').read_text())
    require(nominal == dict(pose=model['poses'][13], clips=model['clips']),
            'CAD covers a different nominal assembly')
    require(model['revision'] == 'r18', 'Wrong revision')
    require(report['result'] == 'THERMAL_STATIC_ROUTE_PASS' and not report['baseline'],
            'Unresolved thermal static route')
    require(report['passing_poses'] == report['total_poses'] == 27, 'Missing passing poses')
    require([p['pose_index'] for p in report['poses']] == list(range(27)), 'Incomplete pose evidence')
    require(model['wire_target_lengths_mm'] == parent['wire_target_lengths_mm'], 'Wire lengths changed')
    for row, definition, old in zip(report['poses'], model['poses'], parent['poses'], strict=True):
        require(definition['cables'][0] == old['cables'][0] and definition['pcb_pose_mm'] == old['pcb_pose_mm'],
                'LTE geometry or PCB pose changed')
        require(row['pass_'] and row['original']['pass_'] and row['thermal']['pass_'] and row['rf']['pass_'], 'Failed pose')
        for group, count in [('original', 49), ('thermal', 4), ('rf', 29)]:
            checks = row[group]['checks']
            require(len(checks) == count and len({c['name'] for c in checks}) == count,
                    'Incomplete geometry check set')
            for c in checks:
                require(c['pass_'], 'Failed geometry check')
                if 'value' in c:
                    require(c['value'] >= c['minimum']-1e-8, 'Incorrect geometry flag')
        require(row['original']['fixed_length_pass'], 'Fixed-length result failed')
        for (lo, hi), target in zip(row['original']['fixed_length_intervals_mm'], model['wire_target_lengths_mm'], strict=True):
            require(target-.001 <= lo <= hi <= target+.001, 'Fixed-length interval failed')
    require(baseline['result'] == 'HOLD' and baseline['baseline'] and baseline['passing_poses'] == 0,
            'Missing old-geometry failure control')
    require(len(baseline['poses']) == 27 and all(not p['thermal']['pass_'] for p in baseline['poses']),
            'Incomplete old-geometry failure evidence')
    for item in [report, baseline, cad]:
        for name, digest in item['inputs'].items():
            require(sha(ROOT/name) == digest, 'Changed evidence input: '+name)
        require(not item['physical_qualification'], 'Unexpected physical acceptance')
    for item in [model, report, baseline]:
        require(not item['manufacturing_release'] and not item['continuous_motion_accepted'],
                'Unexpected release or movement acceptance')
    require(not report['restraint_implemented'], 'This change does not implement restraint')
    require({m['file'] for m in cad['meshes']} == {'red-wire.stl', 'black-wire.stl', 'retainer.stl', 'gnss-guide-witness.stl'},
            'Missing changed mesh')
    for m in cad['meshes']:
        require(inspect(OUT/m['file'], allow_separate=m['file']=='gnss-guide-witness.stl') == m, 'Changed or invalid mesh')
    require({c['name'] for c in cad['controls']} == {'added_material', 'removed_material', 'collision', 'metal_collision', 'gnss_guide_collision'},
            'Missing CAD control')
    for c in cad['controls']:
        require(not re.search('WARNING|ERROR', c['diagnostic']), 'CAD diagnostic')
        if c['name'] == 'removed_material':
            require(c['returncode'] == 0 and not c['empty'] and abs(c['volume_mm3']-3.255) < 1e-4,
                    'Incorrect frame removal')
        else:
            require(c['returncode'] == 1 and c['empty'] and c['volume_mm3'] == 0
                    and 'Current top level object is empty.' in c['diagnostic'], 'Unexpected CAD intersection')
    require(sha(OUT/'review.png') == cad['preview_sha256'], 'Changed review image')
    return dict(result='PASS', revision='r18', static_poses=27, charge_checks_per_pose=53,
                rf_checks_per_pose=29, existing_lid_guides=True,
                old_thermal_poses_passed=0, closed_meshes=4, cad_controls=5,
                restraint_implemented=False, continuous_motion_accepted=False,
                physical_qualification=False, manufacturing_release=False)


def record():
    evidence()
    files = [p for p in OUT.rglob('*') if p.is_file() and p.name != 'checkpoint.json']
    files += [ROOT/'scripts'/n for n in ['check_charge_thermal_clearance.py',
                                        'export_charge_thermal_clearance.py',
                                        'verify_charge_thermal_clearance.py']]
    files.append(ROOT/'tests/test_charge_thermal_clearance.py')
    result = dict(revision='r18', manufacturing_release=False,
                  files={str(p.relative_to(ROOT)): sha(p) for p in sorted(files)})
    dest = OUT/'checkpoint.json'
    if dest.exists():
        require(json.loads(dest.read_text()) == result, 'Preserve the r18 checkpoint; use a successor')
    else:
        dest.write_text(json.dumps(result, indent=2)+'\n')


def verify():
    result = evidence()
    checkpoint = json.loads((OUT/'checkpoint.json').read_text())
    require(checkpoint['revision'] == 'r18' and not checkpoint['manufacturing_release'], 'Wrong checkpoint scope')
    for name, digest in checkpoint['files'].items():
        require(sha(ROOT/name) == digest, 'Changed r18 checkpoint: '+name)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', action='store_true')
    if parser.parse_args().record:
        record()
    print(json.dumps(verify(), indent=2))
