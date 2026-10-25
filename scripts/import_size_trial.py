#!/usr/bin/env python3
"""Import and fill an isolated size trial; enforce the routing experiment rules."""
import json,sys
from pathlib import Path
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else ROOT/'experiments/35x28';PCB=OUT/'hardware/collar-tracker.kicad_pcb'
inner2=json.loads((OUT/'evidence/source.json').read_text()).get('inner2_signal',False)
b=k.LoadBoard(str(PCB));ses=Path(sys.argv[1]).resolve()
assert k.ImportSpecctraSES(b,str(ses))
widened=0
placement=json.loads((OUT/'build/placement.json').read_text())
for f in b.GetFootprints():
    x,y,r,side=placement[f.GetReference()]
    assert abs(f.GetPosition().x/1e6-x)<.001 and abs(f.GetPosition().y/1e6-y)<.001
    assert abs((f.GetOrientationDegrees()-r+180)%360-180)<.001 and f.IsFlipped()==(side=='B')
for t in b.GetTracks():
    if isinstance(t,k.PCB_VIA):
        assert abs(t.GetWidth(k.F_Cu)/1e6-.6)<.001
        t.SetViaType(k.VIATYPE_THROUGH);t.SetLayerPair(k.F_Cu,k.B_Cu);t.SetDrill(k.FromMM(.2))
        t.SetFrontTentingMode(k.TENTING_MODE_TENTED);t.SetBackTentingMode(k.TENTING_MODE_TENTED)
    else:
        # The router's separate fanout pass can still neck traces despite its
        # general automatic_neckdown=false setting. Restore the trial minimum;
        # independent DRC must reject any clearance introduced by this change.
        if t.GetWidth()<k.FromMM(.2):t.SetWidth(k.FromMM(.2));widened+=1
        assert t.GetLayer() in ([k.F_Cu,k.In2_Cu,k.B_Cu] if inner2 else [k.F_Cu,k.B_Cu]), 'Reserved ground layer contains tracks'
k.ZONE_FILLER(b).Fill(b.Zones());assert k.SaveBoard(str(PCB),b)
print(json.dumps({'tracks':sum(not isinstance(t,k.PCB_VIA) for t in b.GetTracks()),'vias':sum(isinstance(t,k.PCB_VIA) for t in b.GetTracks()),'inner_tracks':sum(t.GetClass()=='PCB_TRACK' and t.GetLayer() in [k.In1_Cu,k.In2_Cu] for t in b.GetTracks()),'placement':'matches','fanout_segments_widened_to_020':widened}))
