#!/usr/bin/env python3
"""Verify the saved r09 requested-pack study with Python's standard library."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'mechanical/swim-r09-pack-request'
PCB_SHA = '241c84d6ba98793c37344e1e46ddc4918e7b05322ba87daea7c9a90ffb8379b3'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify():
    checkpoint = json.loads((OUT/'checkpoint.json').read_text())
    require(checkpoint['revision']==OUT.name and checkpoint['pcb_sha256']==PCB_SHA
            and checkpoint['production_release'] is False, 'Wrong study or release status')
    for name, digest in checkpoint['files'].items():
        path = (ROOT/name).resolve()
        require(path.is_relative_to(ROOT), 'Pack checkpoint leaves repository')
        require(sha(path)==digest, 'Pack study changed: '+name)
    request_path = ROOT/'assembly/pack-r03/request.json'
    request = json.loads(request_path.read_text())
    require(request['status']=='SUPPLIER_REQUEST_NOT_AN_APPROVED_PART'
            and not request['manufacturer_confirmed']
            and not request['lead_and_connector_drawing_approved'], 'Request overstates approval')
    pack = json.loads((OUT/'pack-fit.json').read_text())
    require(pack['result']=='REQUESTED_ENVELOPE_GEOMETRY_PASS'
            and pack['request_sha256']==sha(request_path)
            and pack['checker_sha256']==sha(ROOT/'scripts/check_pack_request.py'), 'Stale pack model')
    require(not any(pack[k] for k in ['supplier_part_selected','electrical_release',
                                    'physical_thermal_qualified','physical_ingress_qualified']),
            'Geometry is not supplier/physical approval')
    require(all(c['pass_'] for c in pack['checks']), 'Pack envelope check failed')
    for name, digest in pack['base_inputs'].items():
        require(sha(ROOT/name)==digest, 'Base r08 geometry changed')
    native = json.loads((OUT/'components.native.json').read_text())
    require(native['source_sha256']==PCB_SHA==sha(ROOT/native['source']), 'PCB identity changed')
    netlist_path = ROOT/'experiments/power-r05l-charge-interlock/evidence/native-netlist.json'
    require(sha(netlist_path)==pack['native_netlist_sha256'], 'Native pinout source changed')
    nets = json.loads(netlist_path.read_text())['nets']
    for row in request['factory_interface']:
        require(row['pin'] in nets['/'+row['signal']], 'Factory pinout differs from native source')
    fit = json.loads((OUT/'antenna-fit.json').read_text())
    require(fit['pcb_sha256']==PCB_SHA and fit['result']=='CONDITIONAL_GEOMETRY_PASS', 'Antenna fit failed')
    require(not fit['physical_rf_qualified'] and not fit['physical_ingress_qualified']
            and not fit['production_assembly_complete'], 'Fit study overstates qualification')
    require([s['thickness_mm'] for s in fit['scenarios']]==[.71,.81,.84088,.91], 'Incomplete thickness sweep')
    for s in fit['scenarios']:
        require(len(s['parts'])==85 and len(s['cables'])==2 and len(s['clips'])==4
                and all(c['pass_'] for c in s['checks']), 'Incomplete/failed populated fit')
    for name,digest in fit['inputs'].items():
        require(sha(ROOT/name)==digest, 'Stale cable input: '+name)
    for name,digest in fit['generated'].items():
        require(sha(OUT/name)==digest, 'Stale generated geometry: '+name)
    shell = json.loads((OUT/'checks.json').read_text())
    require(shell['source_sha256']==PCB_SHA
            and shell['parameter_sha256']==sha(OUT/'parameters.json')
            and shell['checker_sha256']==sha(ROOT/'scripts/build_swim_r08_geometry.py')
            and all(c['pass_'] for c in shell['checks']), 'Stale/failed shell checks')
    mesh = json.loads((OUT/'mesh-checks.json').read_text())
    require(mesh['exporter_sha256']==sha(ROOT/'scripts/export_pack_enclosure.py'), 'Stale mesh exporter')
    require(mesh['pcb_sha256']==PCB_SHA and len(mesh['meshes'])==8, 'Incomplete mesh set')
    for name,digest in mesh['cad_input_sha256'].items():
        require(sha(OUT/name)==digest, 'Stale CAD export input: '+name)
    for row in mesh['meshes']:
        require(row['closed_oriented_manifold'] and row['connected_surfaces']==1
                and row['bad_edge_count']==0 and sha(OUT/row['file'])==row['sha256'],
                'Invalid exported mesh')
    require(set(mesh['previews'])=={'exploded.png','section.png','mounted.png','populated.png','routing.png'},
            'Incomplete preview set')
    for name,digest in mesh['previews'].items():
        require(sha(OUT/name)==digest, 'Stale preview')
    for key in ['intersection_controls','guide_intersection_controls']:
        current, old = mesh[key]
        require(current['empty'] and current['returncode']==1 and current['interference_volume_mm3']==0,
                'Current CAD intersects')
        require(not old['empty'] and old['returncode']==0 and old['interference_volume_mm3']>0,
                'CAD negative control did not discriminate')
    return dict(result='SAVED_REQUESTED_ENVELOPE_VERIFIED', files=len(checkpoint['files']),
                rigid_size_mm=pack['rigid_size_mm'], supplier_part_selected=False,
                electrical_release=False, physical_ingress_qualified=False)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
