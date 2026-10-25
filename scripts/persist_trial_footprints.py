#!/usr/bin/env python3
"""Persist project-specific footprints and update PCB/schematic library links.

Run with KiCad Python on the isolated 0.3.3 trial. This corrects stale library
identity; it does not certify the physical footprint for manufacture.
"""
from pathlib import Path
import hashlib
import json
import re
import sys
import pcbnew as k

ROOT=Path(__file__).resolve().parents[1]
TRIAL=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'experiments/35x28-zero-r033'
assert TRIAL.is_relative_to(ROOT/'experiments')
HW=TRIAL/'hardware'
LIB=HW/'Collar033.pretty'
BASE=ROOT/'experiments/35x28-mask-r032/hardware'
assert not (ROOT/'release/collar-tracker-0.3.3-35x28-dfm.zip').exists(), 'Released revision is immutable'
assert hashlib.sha256((BASE/'collar-tracker.kicad_pcb').read_bytes()).hexdigest()=='4dbc5ce1fe08628c8239f155c70aed1a46200ec83cbfd1dc0b765716c79e0b18'
LIB.mkdir(exist_ok=True)
base=k.LoadBoard(str(BASE/'collar-tracker.kicad_pcb'))
original={f.GetReference():f.GetFPIDAsString() for f in base.GetFootprints()}
b=k.LoadBoard(str(HW/'collar-tracker.kicad_pcb'))
io=k.PCB_IO_KICAD_SEXPR()
changes=[]
for f in b.GetFootprints():
    ref=f.GetReference()
    name=ref+'_'+original[ref].split(':',1)[1]
    after='Collar033:'+name
    f.SetFPIDAsString(after)
    c=k.FOOTPRINT(f)
    if c.GetLayer()==k.B_Cu:c.SetLayerAndFlip(k.F_Cu)
    c.SetOrientationDegrees(0)
    c.SetPosition(k.VECTOR2I_MM(0,0))
    c.SetReference('REF**')
    for pad in c.Pads():pad.SetNetCode(0)
    io.FootprintSave(str(LIB),c)
    path=LIB/(name+'.kicad_mod')
    changes.append({'ref':ref,'original_id':original[ref],'project_id':after,
                    'library_file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
assert len(changes)==53
text=(BASE/'fp-lib-table').read_text().rstrip()
assert text.endswith(')')
text=text[:-1]+'\n(lib (name "Collar033") (type "KiCad") (uri "${KIPRJMOD}/Collar033.pretty") (options "") (descr "Project-specific geometry; see library-provenance.json")))\n'
(HW/'fp-lib-table').write_text(text)
# Preserve every connection/property except the footprint identifier.
sch=(HW/'collar-tracker.kicad_sch').read_text()
blocks=re.split(r'(?=\(symbol \(lib_id )',sch)
byref={c['ref']:c for c in changes}
count=0
for i,block in enumerate(blocks):
    if not block.startswith('(symbol (lib_id '):continue
    m=re.search(r'\(property "Reference" "([^"]+)"',block)
    if not m or m[1] not in byref:continue
    c=byref[m[1]]
    old='(property "Footprint" "'+c['original_id']+'"'
    new='(property "Footprint" "'+c['project_id']+'"'
    assert block.count(old)+block.count(new)==1,c
    blocks[i]=block.replace(old,new,1)
    count+=1
assert count==53
(HW/'collar-tracker.kicad_sch').write_text(''.join(blocks))
assert k.SaveBoard(str(HW/'collar-tracker.kicad_pcb'),b)
(HW/'library-provenance.json').write_text(json.dumps({
    'baseline_pcb':str(BASE/'collar-tracker.kicad_pcb'),
    'baseline_sha256':hashlib.sha256((BASE/'collar-tracker.kicad_pcb').read_bytes()).hexdigest(),
    'purpose':'Explicit local definitions for project-specific pad/mask/paste/graphics. No DRC rule suppression; no assertion of manufacturing or circuit qualification.',
    'footprints':changes},indent=2)+'\n')
print('53 project library definitions and matching schematic/PCB links persisted.')
