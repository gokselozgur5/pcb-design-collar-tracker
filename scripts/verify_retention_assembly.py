#!/usr/bin/env python3
"""Read-only verification of the saved r10 geometry; no physical qualification."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/swim-r10-retention'
PCB_SHA='241c84d6ba98793c37344e1e46ddc4918e7b05322ba87daea7c9a90ffb8379b3'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def require(condition,message):
    if not condition:
        raise ValueError(message)


def verify():
    checkpoint=json.loads((OUT/'checkpoint.json').read_text())
    require(checkpoint['revision']==OUT.name and checkpoint['pcb_sha256']==PCB_SHA
            and not checkpoint['production_release'],'Wrong retention checkpoint')
    for name,digest in checkpoint['files'].items():
        path=(ROOT/name).resolve()
        require(path.is_relative_to(ROOT) and sha(path)==digest,'Changed retention artifact: '+name)
    native=json.loads((OUT/'components.native.json').read_text())
    require(native['source_sha256']==PCB_SHA==sha(ROOT/native['source']),'PCB identity changed')
    report=json.loads((OUT/'retention-checks.json').read_text())
    require(report['result']=='CONDITIONAL_RETENTION_GEOMETRY_PASS'
            and report['pcb_sha256']==PCB_SHA
            and not report['physical_retention_qualified']
            and not report['physical_ingress_qualified'],'Wrong retention result/scope')
    require(report['checker_sha256']==sha(ROOT/'scripts/check_retention_assembly.py')
            and report['retention_input_sha256']==sha(OUT/'retention.json'),'Stale retention report')
    for name,digest in report['base_inputs'].items():
        require(sha(ROOT/name)==digest,'Preserved r09 input changed')
    require(all(c['pass_'] for c in report['checks']),'Retention clearance/capture check failed')
    require(len(report['minimum_component_gaps'])==85
            and all(c['gap_mm']>=.2-1e-8 for c in report['minimum_component_gaps'].values()),
            'Incomplete or failed swept component checks')
    require(len(report['tab_overlap_cases'])==27
            and all(c['pass_'] and len(c['overlap_area_mm2'])==4 and min(c['overlap_area_mm2'])>=.1
                    for c in report['tab_overlap_cases']),'Incomplete or failed capture contacts')
    motion=report['cable_motion']
    require(motion['all_sampled_cases_pass'] and len(motion['cases'])==27,'Incomplete cable motion screen')
    for case in motion['cases']:
        require(case['pass_'] and case['cable_gap_mm']>=.2
                and case['guide_center_shift_mm']<1e-8 and len(case['cables'])==2,'Cable pose failed')
        require(all(c['pass_'] and c['minimum_component_gap_mm']>=.2
                    and c['minimum_radius_mm']>=3 and abs(c['length_mm']-98.5)<.01
                    for c in case['cables']),'Cable component/bend/length check failed')
    clearance=json.loads((OUT/'moving-cable-checks.json').read_text())
    require(clearance['result']=='SAMPLED_CABLE_CLEARANCE_PASS'
            and not clearance['physical_flex_qualified'] and len(clearance['cases'])==27,
            'Incomplete moving-cable obstacle checks')
    for name,digest in clearance['inputs'].items():
        require(sha(ROOT/name)==digest,'Stale moving-cable input: '+name)
    for case in clearance['cases']:
        require(case['pass_'] and len(case['cables'])==2,'Moving-cable pose failed')
        for cable in case['cables']:
            require(cable['pass_'] and len(cable['checks'])==7
                    and all(c['pass_'] and c['gap_mm']>=(0 if c['name']=='lid' else .2)
                            for c in cable['checks']),'Cable wall/self/antenna/retention clearance failed')
    fit=json.loads((OUT/'antenna-fit.json').read_text())
    require(fit['pcb_sha256']==PCB_SHA and fit['result']=='CONDITIONAL_GEOMETRY_PASS'
            and not fit['production_assembly_complete'],'Wrong nominal fit scope')
    require([c['thickness_mm'] for c in fit['scenarios']]==[.71,.81,.84088,.91],
            'Incomplete board-thickness screen')
    for case in fit['scenarios']:
        require(len(case['parts'])==85 and len(case['clips'])==4 and len(case['cables'])==2
                and all(c['pass_'] for c in case['checks']),'Nominal populated fit failed')
    for name,digest in fit['inputs'].items():
        require(sha(ROOT/name)==digest,'Changed fit input: '+name)
    for name,digest in fit['generated'].items():
        require(sha(OUT/name)==digest,'Changed generated geometry: '+name)
    shell=json.loads((OUT/'checks.json').read_text())
    require(shell['source_sha256']==PCB_SHA
            and shell['parameter_sha256']==sha(OUT/'parameters.json')
            and shell['checker_sha256']==sha(ROOT/'scripts/build_swim_r08_geometry.py')
            and len(shell['checks'])==34 and all(c['pass_'] for c in shell['checks']),
            'Stale or failed shell/seal check')
    mesh=json.loads((OUT/'mesh-checks.json').read_text())
    require(mesh['pcb_sha256']==PCB_SHA and len(mesh['meshes'])==9
            and mesh['exporter_sha256']==sha(ROOT/'scripts/export_retention_enclosure.py'),
            'Incomplete or stale retention mesh set')
    for name,digest in mesh['cad_input_sha256'].items():
        require(sha(OUT/name)==digest,'Stale CAD input: '+name)
    for row in mesh['meshes']:
        require(sha(OUT/row['file'])==row['sha256'] and row['closed_oriented_manifold']
                and row['bad_edge_count']==row['collapsed_faces_at_1e_5mm']==0
                and row['connected_surfaces']==1,'Invalid mesh: '+row['file'])
    require(set(mesh['previews'])=={'exploded.png','section.png','mounted.png','populated.png','routing.png'},
            'Incomplete preview set')
    for name,digest in mesh['previews'].items():
        require(sha(OUT/name)==digest,'Changed preview')
    for key in ['intersection_controls','guide_intersection_controls']:
        good,bad=mesh[key]
        require(good['empty'] and good['returncode']==1 and good['interference_volume_mm3']==0,
                'Current CAD collision: '+key)
        require(not bad['empty'] and bad['returncode']==0 and bad['interference_volume_mm3']>0,
                'Missing failing CAD control: '+key)
    swept,keyed,reversed_key=mesh['retention_controls']
    require(all(c['empty'] and c['returncode']==1 and c['interference_volume_mm3']==0
                for c in [swept,keyed]),'Retention/current key CAD intersects')
    require(not reversed_key['empty'] and reversed_key['returncode']==0
            and reversed_key['interference_volume_mm3']>0,'Reversed key does not reject assembly')
    for directory in ['initial-clearance','initial-mesh']:
        initial=OUT/'evidence'/directory
        failed=json.loads((initial/'failure.json').read_text())
        require(failed['result']=='FAIL','Initial finding lost: '+directory)
        for name,digest in failed['files'].items():
            require(sha(initial/name)==digest,'Initial evidence changed: '+directory+'/'+name)
    return dict(revision=OUT.name,result='SAVED_CONDITIONAL_RETENTION_GEOMETRY_VERIFIED',
                files=len(checkpoint['files']),populated_envelopes=85,cable_pose_cases=27,
                closed_meshes=9,physical_retention_qualified=False,physical_ingress_qualified=False)


if __name__=='__main__':
    print(json.dumps(verify(),indent=2))
