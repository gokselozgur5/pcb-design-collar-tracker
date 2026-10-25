#!/usr/bin/env python3
"""Import local router output, verify source placement, fill actual ground planes."""
from pathlib import Path
import json,sys,math
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1]
pcb=ROOT/'hardware/collar-tracker.kicad_pcb'
b=k.LoadBoard(str(pcb))
ses=Path(sys.argv[1]).resolve()
assert k.ImportSpecctraSES(b,str(ses)), 'SES import failed'
placement=json.loads((ROOT/'build/pcb/placement.json').read_text())
for f in b.GetFootprints():
    x,y,r,s=placement[f.GetReference()]
    assert abs(f.GetPosition().x/1e6-x)<.001 and abs(f.GetPosition().y/1e6-y)<.001
    assert abs((f.GetOrientationDegrees()-r+180)%360-180)<.001
    assert f.IsFlipped()==(s=='B')
for t in b.GetTracks():
    if isinstance(t,k.PCB_VIA):
        t.SetViaType(k.VIATYPE_THROUGH);t.SetLayerPair(k.F_Cu,k.B_Cu)
        t.SetDrill(k.FromMM(.2));t.SetWidth(k.FromMM(.45))
        t.SetFrontTentingMode(k.TENTING_MODE_TENTED);t.SetBackTentingMode(k.TENTING_MODE_TENTED)
    else:
        assert t.GetLayer() in [k.F_Cu,k.In1_Cu,k.In2_Cu,k.B_Cu]
k.ZONE_FILLER(b).Fill(b.Zones())
assert k.SaveBoard(str(pcb),b)
print(json.dumps({'session':str(ses),'tracks':sum(not isinstance(t,k.PCB_VIA) for t in b.GetTracks()),'vias':sum(isinstance(t,k.PCB_VIA) for t in b.GetTracks()),'inner_signal_segments':sum(t.GetClass()=='PCB_TRACK' and t.GetLayer() in [k.In1_Cu,k.In2_Cu] for t in b.GetTracks()),'placement':'matches source','zones':len(b.Zones()),'rf_reference_plane_review':'OPEN; inner signal routes interrupt ground pours'}))
