#!/usr/bin/env python3
"""Read-only verification of the conditional dock geometry and saved evidence."""
import hashlib
import json
from pathlib import Path
import re

from check_charge_dock import evaluate
from inspect_enclosure_mesh import inspect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/swim-r13-charge-dock'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def require(ok,message):
    if not ok:
        raise ValueError(message)


def verify(check_baseline=True):
    if check_baseline:
        from verify_pack_retention import verify as verify_pack
        verify_pack()
    cp=json.loads((OUT/'checkpoint.json').read_text())
    require(cp['revision']=='r13' and not cp['production_release'],'Wrong dock release scope')
    for name,digest in cp['files'].items():
        p=(ROOT/name).resolve()
        require(p.is_relative_to(ROOT) and sha(p)==digest,'Changed dock artifact: '+name)
    s=json.loads((OUT/'dock.json').read_text())
    saved=json.loads((OUT/'checks.json').read_text())
    current=evaluate(s)
    require(all(saved[k]==v for k,v in current.items()),'Dock analysis differs from saved source')
    require(current['result']=='CONDITIONAL_DOCK_GEOMETRY_PASS' and
            not any(current['qualification'].values()),'Incorrect dock qualification claim')
    mesh=json.loads((OUT/'mesh-checks.json').read_text())
    for report in [saved,mesh]:
        for name,digest in report['inputs'].items():
            require(sha(ROOT/name)==digest,'Changed dock input: '+name)
    require({m['file'] for m in mesh['meshes']}=={'body.stl','lower.stl','upper.stl'},'Wrong dock meshes')
    for m in mesh['meshes']:
        require(inspect(OUT/m['file'])==m,'Dock mesh differs: '+m['file'])
    require(set(mesh['diagnostics'])=={'body','lower','upper'},'Missing CAD diagnostics')
    for name,diagnostic in mesh['diagnostics'].items():
        require(not re.search(r'WARNING|ERROR',diagnostic) and re.search(r'Simple:\s+yes',diagnostic),
                'CAD mesh warning: '+name)
    expected={'pin_interference':True,'collar_interference':True,'harness_interference':True,
              'key_reversed':False,'key_short_control':True,'small_bore_control':False}
    require({c['case'] for c in mesh['controls']}==set(expected),'Missing CAD control')
    for c in mesh['controls']:
        empty=expected[c['case']]
        require(c['empty']==empty and c['expected_empty']==empty and
                c['returncode']==(1 if empty else 0) and
                (c['interference_volume_mm3']==0 if empty else c['interference_volume_mm3']>0),
                'Failed CAD control: '+c['case'])
    for name,digest in mesh['previews'].items():
        require(sha(OUT/name)==digest,'Changed dock preview: '+name)
    require(not mesh['physical_qualification'],'Unexpected physical acceptance')
    return dict(revision='r13',result='SAVED_CONDITIONAL_DOCK_GEOMETRY_VERIFIED',
                checks=len(current['checks']),closed_meshes=3,cad_controls=6,
                files=len(cp['files']),physical_qualification=False)


if __name__=='__main__':
    print(json.dumps(verify(),indent=2))
