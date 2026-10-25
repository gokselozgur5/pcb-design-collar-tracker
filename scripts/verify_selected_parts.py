#!/usr/bin/env python3
"""Read-only r05k source, component, assembly and same-ZIP supplier verification."""
import copy
import csv
import json
from pathlib import Path

from build_power_r05 import parse, child
from check_power_parts import verify as verify_power_parts
from verify_power_pin_candidate import check_files, read, require, sha
from verify_routing_candidate import verify_supplier

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/power-r05j-rf-junctions'
TRIAL=ROOT/'experiments/power-r05k-selected-parts'
EXPECTED_BASE='51fc05ccc66009995daa8c5d5466aa983436e00e7ff338f0ddfb0927c92b4580'
PACKAGE='collar-tracker-05k-parts-40x32-dfm'


def keyed_csv(path,key):
    rows=list(csv.DictReader(path.open()))
    result={r[key]:r for r in rows}
    require(len(result)==len(rows),'Duplicate CSV identity: '+str(path))
    return result


def verify_source():
    e,a,h=TRIAL/'evidence',TRIAL/'assembly',TRIAL/'hardware'
    source=sha(h/'collar-tracker.kicad_pcb')
    require(sha(BASE/'hardware/collar-tracker.kicad_pcb')==EXPECTED_BASE,'Tested baseline changed')
    selection=read(ROOT/'assembly/power-parts-r01/selection.json')
    receipt=read(e/'component-seed.json')
    require(receipt['source_sha256']==EXPECTED_BASE and receipt['candidate_sha256']==source and
            receipt['selection_sha256']==sha(ROOT/'assembly/power-parts-r01/selection.json'),'Wrong seed chain')
    power=verify_power_parts()
    before=keyed_csv(BASE/'hardware/bom.csv','ref');after=keyed_csv(h/'bom.csv','ref')
    profile=read(a/'fit-profile.json');definitions={p['ref']:p for p in profile['parts']}
    require(set(before)==set(after)==set(definitions) and len(after)==71,'Part set differs')
    fitted={r for r,p in after.items() if p['mpn'] and p['dnp']=='False'}
    require(len(fitted)==65 and {r for r,p in after.items() if p['dnp']=='True'}=={'C11','C12'},'Fitted count or DNP differs')
    require(set(after)-fitted-{'C11','C12'}=={'J3','J4','J5','J7'},'Unplaced interface set differs')
    for ref,row in after.items():
        expected=selection['changes'].get(ref,{}).get('to',before[ref]['value'])
        require(row['value']==expected,'Unexpected value: '+ref)
        require(all(row[k]==before[ref][k] for k in ['ref','footprint','dnp','onboard']),'Footprint or fit state changed: '+ref)
        require((row['mpn'] or None)==definitions[ref]['mpn'],'MPN/profile mismatch: '+ref)
    for ref,part in {**selection['resistors'],**selection['capacitors']}.items():
        require(after[ref]['mpn']==part['mpn'] and definitions[ref]['height_max_mm']==part['height_max_mm'],
                'Selected part differs: '+ref)
    # Compare the entire saved PCB structure, not merely a route count.
    pcbs=[]
    for folder,revision in [(BASE,'0.5j-RF-junctions-WIP'),(TRIAL,'0.5k-components-WIP')]:
        root=parse((folder/'hardware/collar-tracker.kicad_pcb').read_text())
        fields={}
        for item in root:
            if not isinstance(item,list):continue
            if item[0]=='footprint':
                p={str(x[1]):str(x[2]) for x in item if isinstance(x,list) and x[0]=='property'}
                fields[p['Reference']]=p
                item[:]=[x for x in item if not (isinstance(x,list) and x[0]=='property' and x[1] in ['Value','MPN','Design status'])]
            elif item[0]=='title_block':
                require(child(item,'rev')[1]==revision,'Unexpected board revision')
                child(item,'rev')[1]='<revision>'
            elif item[0]=='gr_text' and item[1] in ['CT 0.5J','CT 0.5K']:
                require(item[1]==('CT 0.5J' if folder==BASE else 'CT 0.5K'),'Wrong board label')
                item[1]='<revision label>'
        pcbs.append(root)
        if folder==TRIAL:
            require(set(fields)==set(after),'PCB references differ')
            require(all(fields[r]['Value']==p['value'] and fields[r].get('MPN','')==p['mpn'] for r,p in after.items()),'PCB BOM mismatch')
    require(pcbs[0]==pcbs[1],'Geometry, nets, stack or unrelated PCB state changed')
    for suffix in ['kicad_pro','kicad_dru']:
        require(sha(h/('collar-tracker.'+suffix))==sha(BASE/'hardware'/('collar-tracker.'+suffix)),'Native rules changed')
    geometry=[read(p/'evidence/route-geometry.json') for p in [BASE,TRIAL]]
    require(geometry[1]['source_sha256']==source,'Stale route export')
    require(all(geometry[0][k]==geometry[1][k] for k in geometry[0] if k not in ['source','source_sha256','silks']),
            'Native copper/land/mask/plane inventory differs')
    inventory=read(e/'native-netlist.json')
    original=read(ROOT/'experiments/power-r05-supervised/evidence/native-netlist.json')
    require(inventory['schematic_sha256']==sha(h/'collar-tracker.kicad_sch') and inventory['nets']==original['nets'],'Topology changed or stale native netlist')
    require(inventory['parts']=={r:p['value'] for r,p in after.items()} and
            all(inventory['mpns'][r]==p['mpn'] for r,p in after.items()),'Native schematic/BOM mismatch')
    schematic=parse((h/'collar-tracker.kicad_sch').read_text())
    symbols={}
    for s in schematic:
        if isinstance(s,list) and s[0]=='symbol' and child(s,'lib_id'):
            props={str(p[1]):str(p[2]) for p in s if isinstance(p,list) and p[0]=='property'}
            if not props['Reference'].startswith('#'):symbols[props['Reference']]=props
    require(set(symbols)==set(after) and all(symbols[r]['Value']==p['value'] and symbols[r]['MPN']==p['mpn'] for r,p in after.items()),'Saved schematic fields differ')
    native_before,native_after=[read(p/'evidence/components.native.json') for p in [BASE,TRIAL]]
    require(native_after['source_sha256']==source and len(native_after['parts'])==71,'Stale native placement')
    normalized=copy.deepcopy(native_after['parts'])
    for p in normalized:p['value']=before[p['ref']]['value']
    require(normalized==native_before['parts'],'Component placement or body/land box changed')
    fit=read(e/'thickness-fit.json')
    require(fit['source_sha256']==source and fit['all_pass'] and fit['original_carrier_rejected'] and
            fit['unresolved_resistor_height_reservations']==0,'Fit check failed')
    require([s['thickness_mm'] for s in fit['scenarios']]==[.71,.81,.84088,.91] and
            all(s['pass_'] and s['checked']==69 and not s['violations'] and s['original_carrier_violations'] for s in fit['scenarios']),
            'Fit scenario or negative control missing')
    require(all(sha(ROOT/p)==digest for p,digest in fit['inputs'].items()),'Stale fit inputs')
    assembly=read(a/'assembly-check.json')
    require(assembly['source_sha256']==source and assembly['schematic_sha256']==inventory['schematic_sha256'] and
            assembly['exact_fitted_mpn_references']==65 and not assembly['supplier_rotation_qualified'] and
            not assembly['procurement_accepted'] and not assembly['smt_dfm_analyzed'],'Assembly scope differs')
    require(all(sha(ROOT/p)==digest for p,digest in assembly['inputs'].items()) and
            all(sha(a/p)==digest for p,digest in assembly['outputs'].items()),'Stale assembly files')
    cpl=keyed_csv(a/'candidate-cpl.csv','Designator')
    require(set(cpl)==fitted,'CPL includes unplaced pads or omits fitted parts')
    native_by_ref={p['ref']:p for p in native_after['parts']}
    for ref,row in cpl.items():
        p=native_by_ref[ref];x,y=p['native_position_mm']
        require(abs(float(row['Mid X'].removesuffix('mm'))-(x-100))<1e-5 and
                abs(float(row['Mid Y'].removesuffix('mm'))-(128-y))<1e-5 and
                row['Layer']==p['side'] and
                abs(float(row['Rotation'])-p['native_angle_degrees']%360)<1e-5,'CPL pose differs: '+ref)
    return dict(source_sha256=source,exact_fitted_mpn_references=65,unique_mpns=assembly['unique_mpns'],
                unchanged_copper=True,model_result=power['result'])


def verify():
    e=TRIAL/'evidence';manifest=read(e/'parts-checkpoint.json')
    count=check_files(TRIAL,manifest)
    result=verify_source()
    require(result['source_sha256']==manifest['source_sha256'] and not manifest['manufacturing_release'] and
            manifest['electrical_acceptance']==manifest['rf_acceptance']=='HOLD','Wrong release state')
    exported=read(e/PACKAGE/'manifest.json')
    drc=read(e/PACKAGE/'drc.json');erc=read(e/PACKAGE/'erc.json')
    require(not any(drc[k] for k in ['violations','unconnected_items','schematic_parity']) and
            all(not s['violations'] for s in erc['sheets']),'Native check failed')
    previous=BASE/'evidence/collar-tracker-05j-rf-40x32-dfm'
    require(drc['ignored_checks']==read(previous/'drc.json')['ignored_checks'] and
            erc['ignored_checks']==read(previous/'erc.json')['ignored_checks'],'Disabled checks changed')
    records=verify_supplier(TRIAL,manifest,result['source_sha256'],exported['copper_layers'])
    return dict(revision='r05k selected component candidate',result='PASS',files=count,**result,
        zip_sha256=manifest['zip_sha256'],supplier_records=records,
        native_drc={k:len(drc[k]) for k in ['violations','unconnected_items','schematic_parity']},
        electrical_acceptance='HOLD',rf_acceptance='HOLD',manufacturing_release=False)


if __name__=='__main__':print(json.dumps(verify(),indent=2))
