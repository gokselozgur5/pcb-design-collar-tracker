#!/usr/bin/env python3
"""Read-only integrity check for the r17 static four-cable geometry candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from inspect_enclosure_mesh import inspect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/swim-r17-cable-integration'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def require(ok,message):
    if not ok:raise ValueError(message)


def evidence():
    model=json.loads((OUT/'routing.json').read_text())
    report=json.loads((OUT/'checks.json').read_text())
    cad=json.loads((OUT/'cad-checks.json').read_text())
    require(model['revision']=='r17','Wrong routing revision')
    require([r['pose_index'] for r in model['poses']]==list(range(27)),'Missing model pose')
    require(report['result']=='SAMPLED_FOUR_CABLE_GEOMETRY_PASS','Unresolved four-cable geometry')
    require(report['passing_poses']==report['total_poses']==27,'Missing passing pose')
    require([r['pose_index'] for r in report['poses']]==list(range(27)),'Missing checked pose')
    for i,row in enumerate(report['poses']):
        require(row['pcb_pose_mm']==model['poses'][i]['pcb_pose_mm'],'Wrong correlated PCB pose')
        require(row['pass_'] and row['rf']['pass_'] and row['charge']['pass_'],'Failed integrated pose')
        for group,count in [('rf',29),('charge',49)]:
            checks=row[group]['checks']
            require(len(checks)==count and len({c['name'] for c in checks})==count,'Missing geometric check')
            require(all(c['pass_'] for c in checks),'Failed individual check')
            for c in checks:
                if 'value' in c:require(c['value']>=c['minimum']-1e-8,'Incorrect geometry flag')
        tolerance=report['fixed_length_numerical_tolerance_mm']
        require(tolerance==.001 and row['charge']['fixed_length_pass'],'Incorrect length acceptance')
        for (lo,hi),target in zip(row['charge']['fixed_length_intervals_mm'],model['wire_target_lengths_mm'],strict=True):
            require(target-tolerance<=lo<=hi<=target+tolerance,'Charge wire length changed')
    for item in [model,report]:
        require(not any(item[k] for k in ['physical_qualification','manufacturing_release','continuous_motion_accepted']),'Unexpected physical acceptance')
    for item in [report,cad]:
        for name,digest in item['inputs'].items():require(sha(ROOT/name)==digest,'Changed routing evidence input: '+name)
    require({m['file'] for m in cad['meshes']}=={'lte-guide-witness.stl','gnss-guide-witness.stl'},'Missing RF witness')
    for m in cad['meshes']:require(inspect(OUT/m['file'],allow_separate=True)==m,'Changed RF witness mesh')
    require({c['name'] for c in cad['controls']}=={'guide_collision','guide_wall_control'},'Missing CAD control')
    for c in cad['controls']:
        require(not re.search('WARNING|ERROR',c['diagnostic']),'CAD diagnostic')
        if c['name']=='guide_collision':
            require(c['empty'] and c['volume_mm3']==0 and c['returncode']==1 and 'Current top level object is empty.' in c['diagnostic'],'Existing lid collision')
        else:
            require(not c['empty'] and abs(c['volume_mm3']-.027)<=1e-6 and c['returncode']==0,'Failed guide-wall control')
    require(not cad['physical_qualification'] and sha(OUT/'review.png')==cad['preview_sha256'],'Invalid CAD review scope or image')
    return dict(result='PASS',revision='r17',static_poses=27,rf_checks_per_pose=29,charge_checks_per_pose=49,
                existing_lid_guides=True,closed_witness_meshes=2,cad_controls=2,
                continuous_motion_accepted=False,physical_qualification=False,manufacturing_release=False,
                scope='Saved source and evidence integrity; no physical or continuous-motion acceptance')


def record():
    evidence()
    files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='checkpoint.json']
    files += [ROOT/'scripts'/n for n in ['check_cable_integration.py','export_cable_integration.py','verify_cable_integration.py']]
    files.append(ROOT/'tests/test_cable_integration.py')
    checkpoint=dict(revision='r17',manufacturing_release=False,files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)})
    path=OUT/'checkpoint.json'
    if path.exists():require(json.loads(path.read_text())==checkpoint,'Preserve the r17 checkpoint; use a successor')
    else:path.write_text(json.dumps(checkpoint,indent=2)+'\n')


def verify():
    result=evidence();checkpoint=json.loads((OUT/'checkpoint.json').read_text())
    require(checkpoint['revision']=='r17' and not checkpoint['manufacturing_release'],'Invalid checkpoint scope')
    for name,digest in checkpoint['files'].items():require(sha(ROOT/name)==digest,'Changed r17 checkpoint: '+name)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--record',action='store_true')
    if parser.parse_args().record:record()
    print(json.dumps(verify(),indent=2))
