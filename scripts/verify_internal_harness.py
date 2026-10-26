#!/usr/bin/env python3
"""Read-only source/evidence integrity for the unreleased internal harness."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from inspect_enclosure_mesh import inspect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assembly/internal-charge-r02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def require(ok,message):
    if not ok:raise ValueError(message)


def evidence():
    spec=json.loads((OUT/'harness.json').read_text())
    route=json.loads((OUT/'route-checks.json').read_text())
    cad=json.loads((OUT/'cad-checks.json').read_text())
    motion=json.loads((OUT/'motion-screen.json').read_text())
    search=json.loads((OUT/'fixed-length-search.json').read_text())
    searched=json.loads((OUT/'fixed-length-checks.json').read_text())
    require(not spec['manufacturing_release'] and not spec['physical_qualification'],'Unexpected release claim')
    require(route['result']=='NOMINAL_ROUTE_SCREEN_PASS' and len(route['checks'])==41 and all(c['pass_'] for c in route['checks']),'Nominal route failed or lost checks')
    require(not route['manufacturing_release'] and not route['physical_qualification'],'Unexpected route qualification')
    for report in [route,cad,motion,search,searched]:
        for name,digest in report['inputs'].items():
            require(sha(ROOT/name)==digest,'Changed harness evidence input: '+name)
    meshes=json.loads((OUT/'wire-meshes.json').read_text())['meshes']
    require({m['file'] for m in meshes}=={'red-wire.stl','black-wire.stl'},'Missing wire mesh')
    for row in meshes:require(inspect(OUT/row['file'])==row,'Changed or invalid wire mesh')
    expected={'body_carrier_components_and_joint_envelopes','terminal_hole_passage','lowered_ground_wire_control'}
    require({c['name'] for c in cad['controls']}==expected,'Missing CAD control')
    for c in cad['controls']:
        require(not re.search('WARNING|ERROR',c['diagnostic']),'CAD emitted a diagnostic')
        if c['name']=='lowered_ground_wire_control':
            require(not c['empty'] and c['volume_mm3']>0,'Missed deliberate wire penetration')
        else:
            require(c['empty'] and c['volume_mm3']==0 and 'Current top level object is empty.' in c['diagnostic'],'CAD collision')
    require(sha(OUT/'review.png')==cad['preview_sha256'],'Changed assembled preview')
    require(len(motion['cases'])==27 and not motion['physical_qualification'] and not motion['manufacturing_release'],'Invalid movement scope')
    for c in motion['cases']:
        for w in c['wires']:
            require(w['fixed_length_pass']==(abs(w['fixed_length_error_mm'])<=motion['fixed_length_numerical_tolerance_mm']),'Incorrect length flag')
        require(c['pass_']==(c['pair_gap_mm']>=.2 and all(w['fixed_length_pass'] and w['geometry_screen_pass'] for w in c['wires'])),'Incorrect movement flag')
    require(motion['summary']['passing_poses']==sum(c['pass_'] for c in motion['cases']),'Incorrect movement summary')
    require(len(search['poses'])==len(searched['poses'])==27,'Missing searched pose')
    require(not searched['physical_qualification'] and not searched['manufacturing_release']
            and not searched['continuous_motion_accepted'],'Incorrect searched movement acceptance')
    expected_names={c['name'] for c in route['checks']}
    for i,c in enumerate(searched['poses']):
        require(c['pose_index']==i and c['pcb_pose_mm']==search['poses'][i]['pcb_pose_mm'],'Incorrect searched pose mapping')
        require({r['name'] for r in c['geometry_checks']}==expected_names and len(c['geometry_checks'])==41,'Lost independent pose checks')
        tolerance=searched['fixed_length_numerical_tolerance_mm']
        length_pass=all(lo>=target-tolerance and hi<=target+tolerance
                        for (lo,hi),target in zip(c['fixed_length_intervals_mm'],searched['nominal_lengths_mm']))
        require(c['fixed_length_pass']==length_pass,'Incorrect searched length flag')
        require(c['pass_']==(length_pass and all(r['pass_'] for r in c['geometry_checks'])),'Incorrect searched pose result')
    require(searched['passing_poses']==sum(c['pass_'] for c in searched['poses']),'Incorrect searched summary')
    return dict(result='PASS',scope='Saved candidate evidence integrity; not complete-harness acceptance',
                nominal_checks=len(route['checks']),closed_wire_meshes=2,cad_controls=3,
                motion_result=motion['result'],passing_motion_poses=motion['summary']['passing_poses'],
                searched_motion_result=searched['result'],searched_passing_poses=searched['passing_poses'],
                manufacturing_release=False,physical_qualification=False)


def record():
    evidence()
    paths=[p for p in OUT.rglob('*') if p.is_file() and p.name!='checkpoint.json']
    paths += [ROOT/'scripts'/n for n in ['internal_harness_geometry.py','check_internal_harness.py',
               'export_internal_harness.py','screen_internal_harness_motion.py','verify_internal_harness.py',
               'search_internal_harness_motion.py','check_internal_harness_motion.py']]
    paths += [ROOT/'tests/test_internal_harness.py',ROOT/'requirements-harness.txt']
    # This is an explicitly unreleased working candidate. Git preserves the
    # previous coherent snapshot; published PCB/mechanical archives are separate.
    cp=dict(revision='CT-INTERNAL-CHARGE-002-A',status='WIP_NOT_MANUFACTURING_RELEASE',
            files={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)})
    (OUT/'checkpoint.json').write_text(json.dumps(cp,indent=2)+'\n')


def verify():
    result=evidence();cp=json.loads((OUT/'checkpoint.json').read_text())
    require(cp['status']=='WIP_NOT_MANUFACTURING_RELEASE','Incorrect checkpoint scope')
    for name,digest in cp['files'].items():require(sha(ROOT/name)==digest,'Changed candidate snapshot: '+name)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--record',action='store_true')
    if parser.parse_args().record:record()
    print(json.dumps(verify(),indent=2))
