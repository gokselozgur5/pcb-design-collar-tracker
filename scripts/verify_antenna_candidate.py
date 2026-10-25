#!/usr/bin/env python3
"""Read-only r08 source/evidence verification; no new physical qualification."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/swim-r08-antennas'
PCB_SHA='241c84d6ba98793c37344e1e46ddc4918e7b05322ba87daea7c9a90ffb8379b3'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def require(condition,message):
    if not condition:
        raise ValueError(message)


def verify():
    checkpoint=json.loads((OUT/'checkpoint.json').read_text())
    for name,digest in checkpoint['files'].items():
        path=(ROOT/name).resolve()
        require(path.is_relative_to(ROOT),'Checkpoint path leaves repository')
        require(sha(path)==digest,'r08 source/evidence changed: '+name)
    native=json.loads((OUT/'components.native.json').read_text())
    require(native['source_sha256']==PCB_SHA==sha(ROOT/native['source']),'r08 PCB identity changed')
    fit=json.loads((OUT/'antenna-fit.json').read_text())
    require(fit['pcb_sha256']==PCB_SHA and fit['result']=='CONDITIONAL_GEOMETRY_PASS','r08 fit did not pass')
    require(not fit['physical_rf_qualified'] and not fit['physical_ingress_qualified']
            and not fit['production_assembly_complete'] and fit['limits'],'r08 overstates physical qualification')
    require([s['thickness_mm'] for s in fit['scenarios']]==[.71,.81,.84088,.91],'Incomplete thickness screen')
    for scenario in fit['scenarios']:
        require(scenario['result']=='CONDITIONAL_GEOMETRY_PASS' and all(c['pass_'] for c in scenario['checks']),
                'Failed cable/component condition')
        require(len(scenario['parts'])==85 and len(scenario['cables'])==2 and len(scenario['clips'])==4,
                'Incomplete populated assembly')
    for name,digest in fit['inputs'].items():
        require(sha(ROOT/name)==digest,'Stale antenna model input: '+name)
    for name,digest in fit['generated'].items():
        require(sha(OUT/name)==digest,'Generated antenna geometry changed: '+name)
    shell=json.loads((OUT/'checks.json').read_text())
    require(shell['source_sha256']==PCB_SHA and shell['parameter_sha256']==sha(OUT/'parameters.json')
            and shell['checker_sha256']==sha(ROOT/'scripts/build_swim_r08_geometry.py'),'Stale shell report')
    require(shell['all_declared_geometry_checks_pass'] and all(c['pass_'] for c in shell['checks']),
            'Shell/seal/fastener geometry failed')
    meshes=json.loads((OUT/'mesh-checks.json').read_text())
    require(meshes['pcb_sha256']==PCB_SHA and meshes['exporter_sha256']==sha(ROOT/'scripts/export_antenna_enclosure.py'),
            'Stale mesh export')
    for name,digest in meshes['cad_input_sha256'].items():
        require(sha(OUT/name)==digest,'CAD inputs changed: '+name)
    require(len(meshes['meshes'])==8,'Incomplete mesh set')
    for mesh in meshes['meshes']:
        require(sha(OUT/mesh['file'])==mesh['sha256'] and mesh['closed_oriented_manifold']
                and mesh['connected_surfaces']==1 and mesh['bad_edge_count']==0,'Mesh failed: '+mesh['file'])
    require(set(meshes['previews'])=={'exploded.png','section.png','mounted.png','populated.png','routing.png'},
            'Incomplete preview set')
    for name,digest in meshes['previews'].items():
        require(sha(OUT/name)==digest,'Stale preview: '+name)
    for key in ['intersection_controls','guide_intersection_controls']:
        current,old=meshes[key]
        require(current['empty'] and current['returncode']==1 and current['interference_volume_mm3']==0,
                'Current CAD interference remains: '+key)
        require(not old['empty'] and old['returncode']==0 and old['interference_volume_mm3']>0,
                'Missing discriminating CAD control: '+key)
    for case in ['initial-guide','straight-2mm-guide']:
        folder=OUT/'evidence'/case
        failure=json.loads((folder/'failure.json').read_text())
        require(failure['result']=='FAIL' and failure['intersection_volume_mm3']>0,'Lost initial finding')
        for name,digest in failure['files'].items():
            require(sha(folder/name)==digest,'Failed candidate evidence changed')
    return dict(revision='swim-r08-antennas',result='SAVED_CONDITIONAL_GEOMETRY_VERIFIED',
                pcb_sha256=PCB_SHA,source_files=len(checkpoint['files']),populated_envelopes=85,
                thickness_cases=4,antenna_candidates=2,cable_guides=4,closed_meshes=8,
                physical_ingress_qualified=False,physical_rf_qualified=False,production_assembly_complete=False)


if __name__=='__main__':
    print(json.dumps(verify(),indent=2))
