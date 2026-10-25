#!/usr/bin/env python3
"""Import a route while preserving native GND and exact RF pre-routing."""
import collections
import hashlib
import json
from pathlib import Path
import sys
import pcbnew as k

root, session = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
pcb = root / 'hardware/collar-tracker.kicad_pcb'
before_sha = hashlib.sha256(pcb.read_bytes()).hexdigest()
board = k.LoadBoard(str(pcb))
rf_nets = {'/LTE_RF','/LTE_ANT','/GPS_RF','/GNSS_ANT','/GNSS_FEM_IN','/GNSS_FEM_OUT','/FILT_OUT','/AMP_IN'}
point = lambda p: (p.x, p.y)


def signature(t):
    if t.GetClass() == 'PCB_VIA':
        return ('via', point(t.GetPosition()), t.GetWidth(k.F_Cu), t.GetDrill())
    return ('track', point(t.GetStart()), point(t.GetEnd()), t.GetWidth(), t.GetLayer())


ground_before = collections.Counter(signature(t) for t in board.GetTracks() if t.GetNetname() == '/GND')
rf = []
for t in board.GetTracks():
    if t.GetNetname() in rf_nets:
        assert t.GetClass() == 'PCB_TRACK'
        rf.append((t.GetNetname(), point(t.GetStart()), point(t.GetEnd()), t.GetWidth(), t.GetLayer()))
assert k.ImportSpecctraSES(board, str(session))
ground_after = collections.Counter(signature(t) for t in board.GetTracks() if t.GetNetname() == '/GND')
assert ground_before == ground_after, 'Router import changed native ground geometry'
for t in list(board.GetTracks()):
    if t.GetNetname() in rf_nets:
        board.Delete(t)
for net, start, end, width, layer in rf:
    t = k.PCB_TRACK(board)
    t.SetStart(k.VECTOR2I(*start)); t.SetEnd(k.VECTOR2I(*end))
    t.SetWidth(width); t.SetLayer(layer); t.SetNet(board.FindNet(net)); t.SetLocked(True)
    board.Add(t)
placement = json.loads((root / 'build/placement.json').read_text())
for f in board.GetFootprints():
    x,y,angle,side = placement[f.GetReference()]
    assert abs(f.GetPosition().x/1e6-x) < .001 and abs(f.GetPosition().y/1e6-y) < .001
    assert abs((f.GetOrientationDegrees()-angle+180)%360-180) < .001
    assert f.IsFlipped() == (side == 'B')
widened = 0
for t in board.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        assert t.GetWidth(k.F_Cu) == 600000
        t.SetDrill(200000); t.SetLayerPair(k.F_Cu,k.B_Cu)
        t.SetFrontTentingMode(k.TENTING_MODE_TENTED);t.SetBackTentingMode(k.TENTING_MODE_TENTED)
    else:
        assert t.GetLayer() in [k.F_Cu,k.B_Cu], 'Inner ground layer was routed'
        if t.GetWidth() < 200000:
            t.SetWidth(200000);widened += 1
board.BuildConnectivity()
k.ZONE_FILLER(board).Fill(board.Zones())
assert k.SaveBoard(str(pcb),board)
result = {'before_sha256':before_sha,'source_sha256':hashlib.sha256(pcb.read_bytes()).hexdigest(),
          'session':str(session.relative_to(root)),'session_sha256':hashlib.sha256(session.read_bytes()).hexdigest(),
          'ground_items_preserved':sum(ground_before.values()),'rf_segments_restored_exactly':len(rf),
          'narrow_segments_widened_to_020':widened,'inner_tracks':0,
          'scope':'Import invariants only; native DRC and remaining opens must be checked.'}
(root/'evidence'/f'{session.stem}-import.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
