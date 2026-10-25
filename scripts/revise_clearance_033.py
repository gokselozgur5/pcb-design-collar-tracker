#!/usr/bin/env python3
"""Apply measured JLC findings to an isolated, unreleased manufacturing trial.

KiCad Python required. The U5 land variant is an engineering change from the
generic TN0018 +0.10 mm recommendation, not an ST-approved production footprint.
Its centers and pitch are fixed; full maximum-size nominal terminals still fit.
"""
from pathlib import Path
import hashlib,json,shutil
import pcbnew as k

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/35x28-zero-r033/hardware'
T=ROOT/'experiments/35x28-clearance-r033'; HW=T/'hardware'; E=T/'evidence'
H='345544f51eec67767cb7154620392a062bba0ac8ea19051c3e0de5a2beee255b'
assert hashlib.sha256((BASE/'collar-tracker.kicad_pcb').read_bytes()).hexdigest()==H
assert not (ROOT/'release/collar-tracker-0.3.3-35x28-dfm.zip').exists()
if not HW.exists():shutil.copytree(BASE,HW)
E.mkdir(exist_ok=True)
b=k.LoadBoard(str(BASE/'collar-tracker.kicad_pcb'))
fps={f.GetReference():f for f in b.GetFootprints()}
def rect(g,x,y,w,h):
 poly=k.SHAPE_POLY_SET();poly.NewOutline()
 for a,c in [(x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2),(x-w/2,y+h/2)]:poly.Append(round(a*1e6),round(c*1e6))
 g.SetPolyShape(poly)

for p in fps['U2'].Pads():
 if p.GetNumber() in ['2','3','4','7','8','9']:p.SetLocalSolderMaskMargin(25000)
center=[g for g in fps['U2'].GraphicalItems() if g.GetLayer()==k.F_Mask and abs(g.GetBoundingBox().GetWidth()-1550000)<100]
assert len(center)==1
rect(center[0],123,116.5,1.50,2.90)
for p in fps['FB1'].Pads():p.SetLocalSolderMaskMargin(25000)
for p in fps['U5'].Pads():
 assert p.GetSize()==k.VECTOR2I_MM(.375,.35)
 p.SetSize(k.VECTOR2I(375000,340000))

oldnew={(102028300,106066700):(101980000,106115000),
        (102028300,107650000):(101980000,107601700)}
changed=[]
for t in b.GetTracks():
 if t.GetClass()=='PCB_VIA':continue
 uid=t.m_Uuid.AsString()
 if uid=='19e21e05-364f-49a2-9bd5-88dab5ac95fb':
  assert t.GetNetname()=='/GND' and t.GetWidth()==200000
  t.SetWidth(300000);changed.append(uid)
 if t.GetNetname()=='/SWDIO' and t.GetLayer()==k.B_Cu:
  touched=False
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   p=get();q=oldnew.get((p.x,p.y))
   if q is not None:setter(k.VECTOR2I(*q));touched=True
  if touched:changed.append(uid)
assert len(changed)==4
for g in b.GetDrawings():
 if g.GetClass()=='PCB_TEXT' and g.GetText()=='COLLAR 0.3.2 TEST':g.SetText('COLLAR 0.3.3 TEST')
b.GetTitleBlock().SetRevision('0.3.3-DFM')
k.ZONE_FILLER(b).Fill(b.Zones())
assert k.SaveBoard(str(HW/'collar-tracker.kicad_pcb'),b)
(E/'changes.json').write_text(json.dumps({
 'base':str(BASE/'collar-tracker.kicad_pcb'),'base_sha256':H,
 'actual_baseline_jlc_record':'637103970472071169','baseline_jlc_counts':{'danger':0,'warning':40},
 'changes':[
  'U2: six small mask expansions 0.050 -> 0.025 mm; center mask 1.55 -> 1.50 mm wide. Copper and stencil preserved. Positive expansion and exposed copper checked; JLC LDI supports 1:1 openings.',
  'U5: each land local size .375 x .350 -> .375 x .340 mm, with centers, orientation and 0.5 mm pitch preserved. Paste/mask follow copper. Area reduction 2.857%; nominal terminal .275 x .250 and maximum-size .315 x .290 still contained. Deviates by .010 mm from generic ST TN0018 width guidance; assembly validation remains required.',
  'FB1: both mask openings expanded .025 mm; unchanged copper/paste.',
  'U1.30: one GND connection widened .200 -> .300 mm, matching the pad width, to join the mask-adjacent GND sliver without adding a ground void.',
  'J7.1: adjacent SWDIO three-segment route shifted left .0483 mm; 45 degree entry/exit maintained; unchanged width/nets.',
  'Ground zones refilled; bottom revision label and title updated. No DRC rule/severity/exclusion changes.'
 ],'track_ids':changed,'supplier_status':'PENDING','production_status':'DFM prototype; not qualified PCBA'},indent=2)+'\n')
print(HW/'collar-tracker.kicad_pcb')
