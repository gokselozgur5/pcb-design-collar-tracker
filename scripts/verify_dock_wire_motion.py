#!/usr/bin/env python3
"""Verify the r14 source identity, continuous calculation and saved CAD evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from check_dock_wire_motion import evaluate
from inspect_enclosure_mesh import inspect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/swim-r14-wire-motion'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def require(ok,message):
    if not ok:raise ValueError(message)


def evidence():
    spec=json.loads((OUT/'dock.json').read_text())
    saved=json.loads((OUT/'checks.json').read_text())
    current=evaluate(spec)
    require(all(saved[k]==v for k,v in current.items()),'Wire analysis differs from source')
    require(current['result']=='CONDITIONAL_WIRE_GEOMETRY_PASS','Wire geometry failed')
    require(not spec['production_release'] and not current['physical_qualification'] and
            not spec['motion']['factory_endpoint_retention_qualified'] and
            not spec['motion']['cyclic_flex_qualified'],'Unexpected physical acceptance')
    mesh=json.loads((OUT/'mesh-checks.json').read_text())
    for report in [saved,mesh]:
        for name,digest in report['inputs'].items():
            require(sha(ROOT/name)==digest,'Changed wire-study input: '+name)
    require({m['file'] for m in mesh['meshes']}=={'lower.stl','upper.stl'},'Wrong wire-study meshes')
    for m in mesh['meshes']:
        require(inspect(OUT/m['file'])==m,'Mesh evidence differs: '+m['file'])
    require(set(mesh['diagnostics'])=={'lower','upper'},'Missing CAD diagnostics')
    for name,diagnostic in mesh['diagnostics'].items():
        require(not re.search(r'WARNING|ERROR',diagnostic) and re.search(r'Simple:\s+yes',diagnostic),
                'CAD warning: '+name)
    expected={'pin_interference':True,'collar_interference':True,'wire_interference':True,
              'stationary_interference':True,'key_reversed':False,'old_housing_control':False}
    require({c['case'] for c in mesh['controls']}==set(expected),'Missing wire CAD control')
    for c in mesh['controls']:
        empty=expected[c['case']]
        require(c['empty']==empty and c['expected_empty']==empty and c['returncode']==(1 if empty else 0)
                and (c['interference_volume_mm3']==0 if empty else c['interference_volume_mm3']>0),
                'Failed CAD control: '+c['case'])
    require(set(mesh['previews'])=={'review.png','motion.png','mounted.png'},'Missing wire preview')
    for name,digest in mesh['previews'].items():
        require(sha(OUT/name)==digest,'Changed wire preview: '+name)
    require(not mesh['physical_qualification'],'Unexpected physical CAD acceptance')
    return current


def record():
    evidence()
    names=['README.md','dock.json','dock.scad','checks.json','parameters.scad',
           'lower.stl','upper.stl','mesh-checks.json','review.png','motion.png','mounted.png',
           'wire-motion-sheet.svg','wire-motion-sheet.pdf','wire-motion-sheet.png']
    files=[OUT/name for name in names]
    files += [ROOT/'scripts'/name for name in ['check_dock_wire_motion.py','export_dock_wire_motion.py',
                                             'make_dock_wire_sheet.py','verify_dock_wire_motion.py']]
    files += [ROOT/'tests/test_dock_wire_motion.py']
    cp=dict(revision='r14',production_release=False,physical_qualification=False,
            files={str(p.relative_to(ROOT)):sha(p) for p in files})
    path=OUT/'checkpoint.json'
    if path.exists():
        require(json.loads(path.read_text())==cp,'Preserve the recorded checkpoint; use a successor revision')
    else:path.write_text(json.dumps(cp,indent=2)+'\n')


def verify(check_baseline=True):
    if check_baseline:
        from verify_charge_dock import verify as verify_previous
        verify_previous()
    current=evidence()
    cp=json.loads((OUT/'checkpoint.json').read_text())
    require(cp['revision']=='r14' and not cp['production_release'] and not cp['physical_qualification'],
            'Wrong wire-study scope')
    for name,digest in cp['files'].items():
        p=(ROOT/name).resolve()
        require(p.is_relative_to(ROOT) and sha(p)==digest,'Changed wire artifact: '+name)
    return dict(revision='r14',result='SAVED_CONDITIONAL_WIRE_GEOMETRY_VERIFIED',
                checks=len(current['checks']),closed_meshes=2,cad_controls=6,files=len(cp['files']),
                continuous_radius_lower_bound_mm=current['continuous_radius_lower_bound'],physical_qualification=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record',action='store_true',help='Record a new immutable checkpoint after generating/reviewing its evidence')
    args=parser.parse_args()
    if args.record:record()
    print(json.dumps(verify(),indent=2))
