#!/usr/bin/env python3
"""Verify library cleanup removes native warnings without changing geometry/rules."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/35x28-mask-r032'
NEW=ROOT/'experiments/35x28-zero-r033'
old=json.loads((BASE/'evidence/geometry.json').read_text())
new=json.loads((NEW/'evidence/geometry.json').read_text())
old.pop('source');new.pop('source')
assert old==new, 'Physical geometry changed during library synchronization'
for extension in ['kicad_pro','kicad_dru']:
    filename='collar-tracker.'+extension
    assert (BASE/'hardware'/filename).read_bytes()==(NEW/'hardware'/filename).read_bytes(), 'Rules changed'
manifest=json.loads((NEW/'hardware/library-provenance.json').read_text())
assert len(manifest['footprints'])==53
sch=(NEW/'hardware/collar-tracker.kicad_sch').read_text()
for item in manifest['footprints']:
    path=NEW/'hardware/Collar033.pretty'/item['library_file']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
    token='(property "Footprint" "'+item['project_id']+'"'
    assert sch.count(token)==1,item['ref']
    sch=sch.replace(token,'(property "Footprint" "'+item['original_id']+'"',1)
assert sch==(BASE/'hardware/collar-tracker.kicad_sch').read_text(), 'Other schematic content changed'
previous=json.loads((BASE/'evidence/final-drc.json').read_text())
assert len(previous['violations'])==47
assert all(x['type']=='lib_footprint_mismatch' and x['severity']=='warning' for x in previous['violations'])
drc=json.loads((NEW/'evidence/library-drc.json').read_text())
assert not drc['violations'] and not drc['unconnected_items'] and not drc['schematic_parity']
def normalized(path):
    return '\n'.join(x for x in path.read_text().splitlines()
                     if not x.startswith(('%TF.CreationDate,','G04 Created by KiCad')))
unchanged=[]
for extension in ['gtl','g1','g2','gbl','gts','gbs','gtp','gbp','gto','gbo','gm1']:
    previous_file=next((ROOT/'release/collar-tracker-0.3.2-35x28-dfm').glob('*.'+extension))
    current_file=next((NEW/'evidence/gerbers').glob('*.'+extension))
    assert normalized(previous_file)==normalized(current_file), ('Gerber changed',extension)
    unchanged.append(current_file.name)
result={
 'status':'Native KiCad cleanup verified. Supplier DFM goal is still incomplete.',
 'native_before':{'errors':0,'warnings':47,'opens':0,'schematic_parity':0},
 'native_after':{'errors':0,'warnings':0,'opens':0,'schematic_parity':0},
 'copper_mask_paste_routing_vias_zones_legends_unchanged':True,
 'rule_files_severity_settings_exclusions_unchanged':True,
 'schematic_only_footprint_links_changed':True,
 'local_definitions':53,
 'all_11_gerber_layers_identical_except_creation_timestamp':unchanged,
 'source_pcb':str(NEW/'hardware/collar-tracker.kicad_pcb'),
 'pcb_sha256':hashlib.sha256((NEW/'hardware/collar-tracker.kicad_pcb').read_bytes()).hexdigest(),
 'supplier_upload_authorization':'Requested asynchronously; no answer yet. No user files uploaded.',
 'supplier_status':'No new supplier result. Last actual user report is 0.3.1: 0 Danger/45 Warning.',
 'release_status':'Working 0.3.3 source candidate only; current Gerber deliverable remains unchanged 0.3.2.'}
(NEW/'evidence/library-cleanup-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
