#!/usr/bin/env python3
"""Independently check searched poses against native pads and the full route screen."""
import copy
import json
from pathlib import Path

from check_internal_harness import BASE, OUT, ROOT, check, sha
from internal_harness_geometry import evaluate


def build():
    search_path = OUT/'fixed-length-search.json'
    search = json.loads(search_path.read_text())
    for name, digest in search['inputs'].items():
        if sha(ROOT/name) != digest:
            raise ValueError('Search input changed: ' + name)
    spec = json.loads((OUT/'harness.json').read_text())
    cases = json.loads((BASE/'retention-checks.json').read_text())['cable_motion']['cases']
    if [r['pose_index'] for r in search['poses']] != list(range(27)):
        raise ValueError('Missing or duplicate pose')
    nominal = [evaluate(w['controls_mm']) for w in spec['wires']]
    lengths = [(c['arc_lower'][-1]+c['arc_upper'][-1])/2 for c in nominal]
    rows, inputs = [], {}
    for candidate in search['poses']:
        index = candidate['pose_index']
        if candidate['pcb_pose_mm'] != cases[index]['pcb_pose_mm']:
            raise ValueError('Candidate/PCB pose mismatch')
        variant = copy.deepcopy(spec)
        for wire, control in zip(variant['wires'], candidate['controls'], strict=True):
            wire['controls_mm'] = control
        report = check(variant, pose_index=index)
        inputs.update(report['inputs'])
        bounded = [w['length_interval_mm'] for w in report['wires']]
        length_pass = all(lo >= target-.001 and hi <= target+.001
                          for (lo, hi), target in zip(bounded, lengths))
        row = dict(pose_index=index, pcb_pose_mm=candidate['pcb_pose_mm'],
                   fixed_length_intervals_mm=bounded, fixed_length_pass=length_pass,
                   geometry_checks=report['checks'],
                   pass_=length_pass and all(c['pass_'] for c in report['checks']))
        rows.append(row)
        print('Pose', index, 'PASS' if row['pass_'] else 'HOLD',
              [c['name'] for c in report['checks'] if not c['pass_']], flush=True)
    for path in [search_path, Path(__file__)]:
        inputs[str(path.relative_to(ROOT))] = sha(path)
    result = dict(result='SAMPLED_FIXED_LENGTH_GEOMETRY_PASS' if all(r['pass_'] for r in rows) else 'HOLD',
                  inputs=inputs, nominal_lengths_mm=[float(x) for x in lengths],
                  fixed_length_numerical_tolerance_mm=.001, poses=rows,
                  passing_poses=sum(r['pass_'] for r in rows), total_poses=len(rows),
                  physical_qualification=False, manufacturing_release=False,
                  continuous_motion_accepted=False,
                  scope='Independent continuous bounds for each static curve and correlated PCB pose. Not a proof of continuous deformation, endpoint restraint, service motion, thermal wire-length behavior or physical acceptance. CAD controls cover the published nominal route only.')
    (OUT/'fixed-length-checks.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result['result'], result['passing_poses'], '/', len(rows))
    return result


if __name__ == '__main__':
    build()
