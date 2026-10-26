#!/usr/bin/env python3
"""Read-only verification of the r19 prototype, including the frozen r18 baseline."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from inspect_enclosure_mesh import inspect
from verify_charge_thermal_clearance import verify as verify_parent

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assembly/internal-charge-r03'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def require(ok,message):
    if not ok:raise ValueError(message)


def evidence():
    verify_parent()
    spec=json.loads((OUT/'restraint.json').read_text())
    checks=json.loads((OUT/'checks.json').read_text())
    cad=json.loads((OUT/'cad-checks.json').read_text())
    drawing=json.loads((OUT/'drawing-checks.json').read_text())
    require(spec['revision']=='CT-INTERNAL-CHARGE-003-A','Wrong revision')
    require(checks['result']=='STATIC_STAKING_ENVELOPES_PASS' and checks['total_poses']==checks['passing_poses']==27,'Missing passing poses')
    require([r['pose_index'] for r in checks['poses']]==list(range(27)),'Missing or reordered poses')
    for row in checks['poses']:
        require(row['pass_'] and len(row['checks'])==52 and len({c['name'] for c in row['checks']})==52,'Missing checks')
        for c in row['checks']:
            require(c['pass_'] and c['value']>=c['minimum']-1e-8,'Incorrect check result')
    require(not spec['adhesion_to_PTFE_relied_on'],'Unqualified PTFE bond')
    for record in [spec,checks,cad]:
        require(not record['physical_qualification'] and not record['manufacturing_release'],'Unexpected release')
    require(not checks['continuous_motion_accepted'] and not checks['holding_force_qualified'],'Unproven motion or strength')
    for record in [checks,cad,drawing]:
        for name,digest in record['inputs'].items():
            require(sha(ROOT/name)==digest,'Changed input: '+name)
    sources=json.loads((ROOT/'references/charge-restraint-r19/sources.json').read_text())
    for s in sources['sources']:
        local=ROOT/'references/charge-restraint-r19'/s['file']
        # Public links and inspected-source identities travel with the checkout;
        # third-party PDF caches are optional, not silently downloaded here.
        if local.exists():require(sha(local)==s['sha256'],'Changed local material reference')
    expected={'staking-envelopes.stl'}|{f'{col}-{suffix}.stl' for col in ['red','black'] for suffix in ['fixture','fixture-wire','fixture-witness']}
    require({m['file'] for m in cad['meshes']}==expected,'Missing CAD artifact')
    for mesh in cad['meshes']:
        require(inspect(OUT/mesh['file'],allow_separate=mesh['file']=='staking-envelopes.stl')==mesh,'Changed/invalid mesh')
    require({c['name'] for c in cad['controls']}=={'staking-collision','displaced-staking-control','red-fixture-collision','black-fixture-collision','red-raised-floor-control','black-raised-floor-control'},'Missing CAD control')
    for c in cad['controls']:
        if c.get('engine')=='Manifold 3.5.4':
            require(c['status']=='Error.NoError','Geometry kernel error')
            if c['name'].endswith('collision'):
                require(c['empty'] and c['triangles']==0 and c['volume_mm3']==0,'CAD interference')
            else:
                require(not c['empty'] and c['triangles']>0 and c['volume_mm3']>0,'Missing failing control')
        else:
            require(not re.search('WARNING|ERROR',c['diagnostic']),'CAD warning/error')
            if c['name'].endswith('collision'):
                require(c['empty'] and c['returncode']==1 and c['volume_mm3']==0,'CAD interference')
            else:
                require(not c['empty'] and c['returncode']==0 and c['volume_mm3']>0,'Missing failing control')
    require([t['colour'] for t in cad['forming_tools']]==['red','black'],'Missing forming tool')
    for tool in cad['forming_tools']:
        require(tool['minimum_clearance_bound_mm']>=spec['fixture']['minimum_radial_clearance_mm'],'Insufficient tool clearance')
        require(tool['minimum_floor_mm']>=spec['fixture']['minimum_floor_mm']-1e-8,'Insufficient floor')
        require(tool['vertical_removal_open'] and not tool['length_tolerance_qualified'],'Incorrect tool scope')
    require(set(cad['previews'])=={'restraint-preview.png','red-fixture-preview.png','black-fixture-preview.png'},'Missing preview')
    for name,digest in {**cad['previews'],**drawing['files']}.items():
        require(sha(OUT/name)==digest,'Changed drawing/preview: '+name)
    return dict(result='PASS',revision='r19',static_poses=27,checks_per_pose=52,
                staking_regions=3,forming_tools=2,closed_meshes=7,cad_controls=6,
                holding_force_qualified=False,continuous_motion_accepted=False,
                physical_qualification=False,manufacturing_release=False)


def record():
    evidence()
    files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='checkpoint.json']
    files.append(ROOT/'references/charge-restraint-r19/sources.json')
    files+=[ROOT/'scripts'/name for name in ['check_charge_restraint.py','export_charge_restraint.py','charge_fixture_csg.py','make_charge_restraint_sheet.py','verify_charge_restraint.py']]
    files.append(ROOT/'tests/test_charge_restraint.py')
    checkpoint=dict(revision='r19',manufacturing_release=False,files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)})
    path=OUT/'checkpoint.json'
    if path.exists():require(json.loads(path.read_text())==checkpoint,'Preserve the r19 checkpoint; use a successor')
    else:path.write_text(json.dumps(checkpoint,indent=2)+'\n')


def verify():
    result=evidence()
    checkpoint=json.loads((OUT/'checkpoint.json').read_text())
    require(checkpoint['revision']=='r19' and not checkpoint['manufacturing_release'],'Wrong checkpoint')
    for name,digest in checkpoint['files'].items():
        require(sha(ROOT/name)==digest,'Changed r19 checkpoint: '+name)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--record',action='store_true')
    if parser.parse_args().record:record()
    print(json.dumps(verify(),indent=2))
