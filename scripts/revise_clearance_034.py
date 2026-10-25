#!/usr/bin/env python3
"""Widen the symmetric U1.71 ground neck; preserve the released 0.3.3."""
from pathlib import Path
import hashlib,json,shutil
import pcbnew as k
R=Path(__file__).resolve().parents[1]
BASE=R/'experiments/35x28-clearance-r033/hardware'
T=R/'experiments/35x28-clearance-r034';HW=T/'hardware';E=T/'evidence'
H='ab78d20c04a6b872dec1dfaad2b50d3995f3112f852905cbfc1ee378c5b992ea'
assert hashlib.sha256((BASE/'collar-tracker.kicad_pcb').read_bytes()).hexdigest()==H
assert not T.exists(),'Keep all earlier trials intact'
assert not (R/'release/collar-tracker-0.3.4-35x28-dfm.zip').exists()
shutil.copytree(BASE,HW);E.mkdir()
b=k.LoadBoard(str(BASE/'collar-tracker.kicad_pcb'))
found=[]
for t in b.GetTracks():
 if t.m_Uuid.AsString()=='518a7bbe-4d4f-476f-95b5-f3a983aa1dff':
  assert t.GetNetname()=='/GND' and t.GetLayer()==k.F_Cu and t.GetWidth()==200000
  assert t.GetStart()==k.VECTOR2I(110750000,109424900)
  assert t.GetEnd()==k.VECTOR2I(110750000,107875000)
  t.SetWidth(300000);found.append(t.m_Uuid.AsString())
assert len(found)==1
for g in b.GetDrawings():
 if g.GetClass()=='PCB_TEXT' and g.GetText()=='COLLAR 0.3.3 TEST':g.SetText('COLLAR 0.3.4 TEST')
b.GetTitleBlock().SetRevision('0.3.4-DFM')
k.ZONE_FILLER(b).Fill(b.Zones())
assert k.SaveBoard(str(HW/'collar-tracker.kicad_pcb'),b)
(E/'changes.json').write_text(json.dumps({'base':str(BASE/'collar-tracker.kicad_pcb'),'base_sha256':H,
 'changed_track':found[0],'net':'/GND','pad':'U1.71','width_before_after_mm':[.2,.3],
 'other_changes':'GND refill, bottom revision label and title only. All pads, masks, stencil, components, nets, vias and rules unchanged.',
 'reason':'User reproduced a 0.08 mm mask-to-copper warning on 0.3.3. U1.71 has the symmetric thin ground neck of the previously corrected U1.30. Do not claim a single prior zero run proves repeatability.'},indent=2)+'\n')
print(HW/'collar-tracker.kicad_pcb')
