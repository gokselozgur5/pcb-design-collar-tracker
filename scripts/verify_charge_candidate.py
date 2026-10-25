#!/usr/bin/env python3
"""Read-only source, circuit, geometry, assembly and supplier evidence checks."""
import csv
import json
from pathlib import Path

from check_charge_preservation import compute as preservation
from check_charge_r05l import compute as charge
from verify_power_pin_candidate import check_files, read, require, sha
from verify_routing_candidate import verify_supplier

ROOT=Path(__file__).resolve().parents[1]
TRIAL=ROOT/'experiments/power-r05l-charge-interlock'
MECH=ROOT/'mechanical/swim-r07-charge-interlock'
PACKAGE='collar-tracker-05l-charge-final4-40x32-dfm'


def verify():
    e,a,h=TRIAL/'evidence',TRIAL/'assembly',TRIAL/'hardware'
    manifest=read(e/'charge-checkpoint.json');count=check_files(TRIAL,manifest)
    source=sha(h/'collar-tracker.kicad_pcb')
    require(source==manifest['source_sha256'],'Wrong source identity')
    require(not manifest['manufacturing_release'] and manifest['electrical_acceptance']==
            manifest['rf_acceptance']=='HOLD','Incorrect acceptance scope')
    require(preservation()==read(e/'source-preservation.json'),'Stale source comparison')
    calculated=charge()
    require(calculated==read(e/'charge-check.json') and calculated['result']=='CONDITIONAL_DESIGN_PASS'
            and not calculated['electrical_release'],'Charge model differs')
    exported=read(e/PACKAGE/'manifest.json');drc=read(e/PACKAGE/'drc.json');erc=read(e/PACKAGE/'erc.json')
    require(not any(drc[k] for k in ['violations','unconnected_items','schematic_parity']) and
            all(not s['violations'] for s in erc['sheets']),'Native checks failed')
    prior=ROOT/'experiments/power-r05k-selected-parts/evidence/collar-tracker-05k-parts-40x32-dfm'
    require(drc['ignored_checks']==read(prior/'drc.json')['ignored_checks'] and
            erc['ignored_checks']==read(prior/'erc.json')['ignored_checks'],'Ignored rules changed')
    records=verify_supplier(TRIAL,manifest,source,exported['copper_layers'])
    names=['route-geometry','layout-inventory','attachment-review','passive-copper-review',
           'contact-components','esd-paths','card-insertion-review','power-path-review',
           'rf-reference.native','rf-reference-check','components.native']
    reports={n:read(e/(n+'.json')) for n in names}
    require(all(d['source_sha256']==source for d in reports.values()),'Stale final-source report')
    inv=reports['layout-inventory']
    require((inv['footprints'],inv['ground_pads'],inv['ground_vias'],inv['non_ground_vias'],
             inv['returns_outside_2mm'],inv['ground_layer_tracks'])==(87,109,122,154,0,0),'Layout inventory changed')
    require(set(inv['planes'])=={'In1.Cu','In4.Cu'} and all(p['zone_nets']==['/GND'] and
            p['filled_outline_count']==1 and not p['ground_vias_outside'] for p in inv['planes'].values()),'Ground fill failed')
    require(not reports['contact-components']['ground_pads_without_track_path_to_via'],'Missing local GND path')
    require(all(p['connected'] for p in reports['power-path-review']['paths']),'Power backbone opened')
    require(all(p['via'] and p['local_path_mm'] is not None for p in reports['attachment-review']['grounds']),
            'Missing local attachment')
    require(reports['card-insertion-review']['pcb_entry_projection_clear'] and
            not reports['card-insertion-review']['overlap_candidates'],'SIM insertion obstructed')
    require(len(reports['esd-paths']['paths'])==4 and all(p['connector_to_esd'] and p['esd_to_modem'] and
            not p['bypasses_esd_land'] for p in reports['esd-paths']['paths']),'SIM clamp bypass')
    rf=reports['rf-reference-check']
    require(rf['native_contains_disagreements']==0 and rf['port_route_unbacked_copper_mm2']==0,
            'RF reference screen failed')
    native=reports['components.native'];byref={p['ref']:p for p in native['parts']}
    bom={r['ref']:r for r in csv.DictReader((h/'bom.csv').open())}
    fitted={r:p for r,p in bom.items() if p['mpn'] and p['dnp']=='False'}
    netlist=read(e/'native-netlist.json')
    require(len(bom)==87 and len(fitted)==81 and set(bom)==set(byref),'BOM reference set differs')
    require(netlist['parts']=={r:p['value'] for r,p in bom.items()} and
            all(netlist['mpns'][r]==p['mpn'] for r,p in bom.items()),'Schematic/BOM fields differ')
    assembly=read(a/'assembly-check.json')
    require(assembly['source_sha256']==source and assembly['schematic_sha256']==netlist['schematic_sha256'] and
            assembly['exact_fitted_mpn_references']==81 and assembly['unique_mpns']==44 and
            not any(assembly[k] for k in ['supplier_rotation_qualified','procurement_accepted','smt_dfm_analyzed']),
            'Assembly scope changed')
    require(all(sha(ROOT/p)==v for p,v in assembly['inputs'].items()) and
            all(sha(a/p)==v for p,v in assembly['outputs'].items()),'Assembly inputs changed')
    rows=list(csv.DictReader((a/'candidate-cpl.csv').open()))
    require(len(rows)==len(fitted) and {r['Designator'] for r in rows}==set(fitted),'CPL part set differs')
    for row in rows:
        p=byref[row['Designator']];x,y=p['native_position_mm']
        require(abs(float(row['Mid X'].removesuffix('mm'))-(x-100))<1e-5 and
                abs(float(row['Mid Y'].removesuffix('mm'))-(128-y))<1e-5 and
                row['Layer']==p['side'] and abs(float(row['Rotation'])-p['native_angle_degrees']%360)<1e-5,
                'CPL pose differs: '+row['Designator'])
    fit=read(MECH/'populated-fit.json');mesh=read(MECH/'mesh-checks.json');shell=read(MECH/'checks.json')
    require(fit['pcb_sha256']==mesh['pcb_sha256']==shell['source_sha256']==source,'Wrong mechanical PCB')
    require(shell['all_declared_geometry_checks_pass'] and
            shell['parameter_sha256']==sha(MECH/'parameters.json') and
            shell['checker_sha256']==sha(ROOT/'scripts/build_swim_enclosure.py'),'Stale shell checks')
    require(fit['result']=='GEOMETRY_PASS' and [s['thickness_mm'] for s in fit['scenarios']]==[.71,.81,.84088,.91]
            and all(s['pass_'] and s['checked']==85 and s['old_carrier_violations'] for s in fit['scenarios']),
            'Fit scenario/negative control missing')
    require(all(sha(ROOT/p)==v for p,v in fit['inputs'].items()) and
            fit['checker_sha256']==sha(ROOT/'scripts/check_charge_fit.py') and
            fit['base_checker_sha256']==sha(ROOT/'scripts/audit_populated_fit.py'),'Stale fit inputs')
    require(all(sha(MECH/p)==v for p,v in mesh['cad_input_sha256'].items()) and
            mesh['exporter_sha256']==sha(ROOT/'scripts/export_charge_enclosure.py'),'Stale CAD export')
    require(len(mesh['meshes'])==8 and all(m['closed_oriented_manifold'] and sha(MECH/m['file'])==m['sha256']
            for m in mesh['meshes']),'Mesh integrity failed')
    controls=mesh['intersection_controls']
    require(len(controls)==2 and controls[0]['empty'] and not controls[1]['empty'] and
            controls[1]['interference_volume_mm3']>0,'CAD negative control failed')
    require(all(sha(MECH/p)==v for p,v in mesh['previews'].items()),'Preview changed')
    require(all(sha(ROOT/p)==v for p,v in manifest['external_inputs'].items()),'External review inputs changed')
    return dict(revision='r05l charge interlock',result='PASS',files=count,source_sha256=source,
                zip_sha256=manifest['zip_sha256'],supplier_records=records,
                native_drc={k:len(drc[k]) for k in ['violations','unconnected_items','schematic_parity']},
                exact_fitted_mpn_references=81,unique_mpns=44,charge_window_implemented=True,
                temperature_model=calculated['result'],populated_envelopes=85,
                electrical_acceptance='HOLD',rf_acceptance='HOLD',manufacturing_release=False,
                physical_ingress_test=False)


if __name__=='__main__':print(json.dumps(verify(),indent=2))
