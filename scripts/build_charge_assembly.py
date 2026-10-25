#!/usr/bin/env python3
"""Build the r05l candidate assembly files from native exports."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT=Path(__file__).resolve().parents[1]
TRIAL=ROOT/'experiments/power-r05l-charge-interlock'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main(xml_path):
    e,a,h=TRIAL/'evidence',TRIAL/'assembly',TRIAL/'hardware'
    native=json.loads((e/'components.native.json').read_text())
    assert sha(h/'collar-tracker.kicad_pcb')==native['source_sha256']
    xml=ET.parse(xml_path).getroot()
    inventory=dict(schematic_sha256=sha(h/'collar-tracker.kicad_sch'),exporter=xml.findtext('./design/tool'),
        parts={c.attrib['ref']:c.findtext('value') for c in xml.findall('./components/comp')},
        mpns={c.attrib['ref']:next((p.attrib['value'] for p in c.findall('property') if p.attrib['name']=='MPN'),'')
              for c in xml.findall('./components/comp')},
        nets={n.attrib['name']:sorted(p.attrib['ref']+'.'+p.attrib['pin'] for p in n.findall('node'))
              for n in xml.findall('./nets/net')})
    (e/'native-netlist.json').write_text(json.dumps(inventory,indent=2)+'\n')
    bom=list(csv.DictReader((h/'bom.csv').open()))
    fitted={r['ref']:r for r in bom if r['mpn'] and r['dnp']=='False'}
    assert len(bom)==87 and len(fitted)==81
    assert all(inventory['parts'][r]==p['value'] and inventory['mpns'][r]==p['mpn'] for r,p in fitted.items())
    # The four bare pad/harness interfaces and two DNP tuning capacitors have
    # no placed component. Their external hardware remains in the build scope.
    by_mpn={}
    for ref,row in fitted.items():by_mpn.setdefault(row['mpn'],[]).append(ref)
    with (a/'candidate-bom.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['Designators','Quantity','Manufacturer Part Number','Values','Package','Status'])
        for mpn,refs in sorted(by_mpn.items()):
            packages={fitted[r]['footprint'].split(':',1)[1].removeprefix(r+'_') for r in refs}
            writer.writerow([','.join(sorted(refs)),len(refs),mpn,'; '.join(sorted({fitted[r]['value'] for r in refs})),
                             '; '.join(sorted(packages)),'Prototype candidate; procurement and SMT acceptance open'])
    rows=list(csv.DictReader((a/'native-positions.csv').open()))
    placements=[r for r in rows if r['Ref'] in fitted]
    assert len(placements)==81 and {r['Ref'] for r in placements}==set(fitted)
    with (a/'candidate-cpl.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['Designator','Mid X','Mid Y','Layer','Rotation'])
        for r in sorted(placements,key=lambda p:p['Ref']):
            writer.writerow([r['Ref'],r['PosX']+'mm',r['PosY']+'mm',r['Side'],f"{float(r['Rot'])%360:.6f}"])
    receipt=dict(source_sha256=native['source_sha256'],schematic_sha256=inventory['schematic_sha256'],
        exact_fitted_mpn_references=len(fitted),unique_mpns=len(by_mpn),
        dnp=['C11','C12'],unplaced_interfaces=['J3','J4','J5','J7'],
        coordinate_convention='KiCad native drill/place origin (100,128) mm: X right, Y up, no bottom X negation; angles reduced modulo 360 only.',
        supplier_rotation_qualified=False,procurement_accepted=False,smt_dfm_analyzed=False,
        inputs={str(p.relative_to(ROOT)):sha(p) for p in [h/'bom.csv',a/'native-positions.csv',e/'components.native.json',e/'native-netlist.json',Path(__file__).resolve()]},
        outputs={p.name:sha(p) for p in [a/'candidate-bom.csv',a/'candidate-cpl.csv']})
    (a/'assembly-check.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ['exact_fitted_mpn_references','unique_mpns','supplier_rotation_qualified']}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('native_netlist',type=Path)
    main(parser.parse_args().native_netlist)
