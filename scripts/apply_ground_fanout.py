#!/usr/bin/env python3
"""Apply a checked fanout plan once; keep a native pre-routing snapshot."""
import hashlib
import json
from pathlib import Path
import sys

import pcbnew as k

root = Path(sys.argv[1])
pcb = root / 'hardware/collar-tracker.kicad_pcb'
plan = json.loads((root / 'evidence/ground-plan.json').read_text())
assert not plan['failures'], 'Unplanned grounds must be resolved before applying'
assert hashlib.sha256(pcb.read_bytes()).hexdigest() == plan['source_sha256'], 'Stale plan'
board = k.LoadBoard(str(pcb))
assert not any(t.GetNetname() == '/GND' for t in board.GetTracks()), 'Already applied'
net = board.FindNet('/GND')
vector = lambda xy: k.VECTOR2I(*(round(v * 1e6) for v in xy))
for pos in plan['vias']:
    via = k.PCB_VIA(board)
    via.SetPosition(vector(pos))
    via.SetWidth(600000)
    via.SetDrill(200000)
    via.SetViaType(k.VIATYPE_THROUGH)
    via.SetLayerPair(k.F_Cu, k.B_Cu)
    via.SetNet(net)
    via.SetFrontTentingMode(k.TENTING_MODE_TENTED)
    via.SetBackTentingMode(k.TENTING_MODE_TENTED)
    via.SetLocked(True)
    board.Add(via)
for stub in plan['stubs']:
    for start, end in zip(stub['points'], stub['points'][1:]):
        if vector(start) == vector(end):
            continue
        track = k.PCB_TRACK(board)
        track.SetStart(vector(start))
        track.SetEnd(vector(end))
        track.SetWidth(round(stub['width'] * 1e6))
        track.SetLayer(board.GetLayerID(stub['layer']))
        track.SetNet(net)
        track.SetLocked(True)
        board.Add(track)
board.BuildConnectivity()
k.ZONE_FILLER(board).Fill(board.Zones())
assert k.SaveBoard(str(pcb), board)
backup = root / 'build/ground-base.kicad_pcb'
assert not backup.exists(), 'Preserve the prior ground snapshot'
backup.write_bytes(pcb.read_bytes())
(root / 'evidence/ground-applied.json').write_text(json.dumps({
    'source_sha256': plan['source_sha256'], 'ground_board_sha256': hashlib.sha256(pcb.read_bytes()).hexdigest(),
    'ground_pads_planned': plan['ground_pads'], 'ground_vias': len(plan['vias']),
    'ground_stub_max_mm': max(s['length'] for s in plan['stubs']),
    'scope': 'Applied and filled; native DRC and connectivity must be checked separately.'
}, indent=2) + '\n')
print('Applied', len(plan['vias']), 'ground vias for', plan['ground_pads'], 'ground pads.')
