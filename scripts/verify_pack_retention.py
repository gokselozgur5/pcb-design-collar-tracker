#!/usr/bin/env python3
"""Read-only source-bound r12 evidence check; no physical acceptance implied."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/swim-r12-pack-retention'
BASE=ROOT/'mechanical/swim-r11-thermal-fit'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def require(ok,message):
    if not ok:
        raise ValueError(message)


def verify(check_baseline=True):
    if check_baseline:
        from verify_thermal_assembly import verify as verify_thermal
        verify_thermal()
    checkpoint=json.loads((OUT/'checkpoint.json').read_text())
    require(checkpoint['revision']==OUT.name and not checkpoint['production_release'],'Wrong r12 scope')
    for name,digest in checkpoint['files'].items():
        path=(ROOT/name).resolve()
        require(path.is_relative_to(ROOT) and sha(path)==digest,'Changed r12 artifact: '+name)
    spec=json.loads((OUT/'pack-retention.json').read_text())
    motion=spec['motion']
    require(motion['feature_tolerance_mm']==.05 and motion['thermal_z_allowance_mm']==.08
            and motion['minimum_component_gap_mm']==.2,'r12 CAD collision envelope requires its pinned tolerance profile')
    r=json.loads((OUT/'pack-retention-checks.json').read_text())
    require(r['pcb_sha256']==checkpoint['pcb_sha256'],'Wrong PCB binding')
    require(r['result']=='CONDITIONAL_PACK_RETENTION_GEOMETRY_PASS'
            and not r['physical_pack_retention_qualified'] and not r['physical_ingress_qualified'],'Wrong r12 result')
    require(len(r['checks'])>=40 and all(c['pass_'] and c['value']>=c['minimum']-1e-8 for c in r['checks']),'Incomplete or failed checks')
    require(len(r['component_clearances'])==len(r['moving_pack_clearances'])==85,'Incomplete component set')
    require(min(x['gap_mm'] for x in r['component_clearances'].values())>=.2
            and min(min(x['body_gap_mm'],x['ntc_gap_mm']) for x in r['moving_pack_clearances'])>=.2,'Failed component gap')
    require(len(r['guaranteed_capture_areas_mm2'])==4 and min(r['guaranteed_capture_areas_mm2'])>=1,'Missing pack capture')
    for name,digest in r['inputs'].items():
        require(sha(ROOT/name)==digest,'Stale calculation input: '+name)
    mesh=json.loads((OUT/'mesh-checks.json').read_text())
    for name,digest in mesh['inputs'].items():
        require(sha(ROOT/name)==digest,'Stale CAD input: '+name)
    require({row['file'] for row in mesh['meshes']}=={'body.stl','carrier.stl'},'Wrong changed part set')
    from inspect_enclosure_mesh import inspect
    for row in mesh['meshes']:
        require(inspect(OUT/row['file'])==row,'Actual mesh differs: '+row['file'])
    unchanged={'lid.stl','retainer.stl','contact.stl','contact_seal.stl','magnet_plug.stl','dock.stl','boot.stl'}
    require(set(mesh['unchanged_parts'])==unchanged,'Incomplete unchanged part set')
    for name,digest in mesh['unchanged_parts'].items():
        require(sha(BASE/name)==digest,'Changed preserved part: '+name)
    controls={c['case']:c for c in mesh['cad_controls']}
    empty={'pack_components','pack_hardware','pack_ntc','pack_cradle'}
    positive={'pack_components_control','pack_ntc_control','pack_cradle_control'}
    require(set(controls)==empty|positive,'Incomplete CAD controls')
    for name,row in controls.items():
        require((row['empty'] and row['returncode']==1 and row['interference_volume_mm3']==0) if name in empty
                else (not row['empty'] and row['returncode']==0 and row['interference_volume_mm3']>0),'CAD control failed: '+name)
    require(set(mesh['previews'])=={'pack_exploded.png','pack_review.png','pack_section.png','mounted.png'},'Missing preview')
    for name,digest in mesh['previews'].items():
        require(sha(OUT/name)==digest,'Changed preview: '+name)
    initial=json.loads((OUT/'evidence/initial-fit/pack-retention-checks.json').read_text())
    require(initial['result']=='PACK_RETENTION_GEOMETRY_HOLD' and any(not c['pass_'] for c in initial['checks']),'Initial failure lost')
    return dict(revision=OUT.name,result='SAVED_CONDITIONAL_PACK_RETENTION_VERIFIED',files=len(checkpoint['files']),
                populated_envelopes=85,lifted_pack_envelopes=85,changed_closed_meshes=2,reused_r11_meshes=7,
                physical_pack_retention_qualified=False,physical_ingress_qualified=False)


if __name__=='__main__':
    print(json.dumps(verify(),indent=2))
