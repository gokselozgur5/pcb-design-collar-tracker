#!/usr/bin/env python3
"""Apply checked signal-via moves without changing any native terminal group."""
from pathlib import Path
import argparse
import hashlib
import json
import pcbnew as k
from trim_power_r05_tails import islands

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('trial',type=Path)
args=parser.parse_args();trial=args.trial.resolve()
assert trial.name=='power-r05h-six-layer'
pcb=trial/'hardware/collar-tracker.kicad_pcb'
plan_path=trial/'evidence/return-via-moves-plan.json'
plan=json.loads(plan_path.read_text())
receipt=trial/'evidence/return-via-moves-applied.json'
assert not receipt.exists()
before=hashlib.sha256(pcb.read_bytes()).hexdigest()
assert plan['before_sha256']==before
board=k.LoadBoard(str(pcb))
nets={p.GetNetname() for f in board.GetFootprints() for p in f.Pads()}
groups=islands(board,nets)
items={t.m_Uuid.AsString():t for t in board.GetTracks()}
layers={board.GetLayerName(l):l for l in [k.F_Cu,k.In2_Cu,k.In3_Cu,k.B_Cu]}
vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6))
added=[]
for move in plan['moves']:
    via=items[move['id']]
    assert via.GetClass()=='PCB_VIA' and via.GetNetname()==move['net']!='/GND'
    assert via.GetPosition()==vec(move['old'])
    via.SetPosition(vec(move['new']))
    segments=[dict(start=move['old'],end=move['new'],layer=l,width=w)
              for l,w in move['stubs'].items()]+move['bridges']
    for seg in segments:
        assert seg['layer'] in layers
        track=k.PCB_TRACK(board);track.SetStart(vec(seg['start']));track.SetEnd(vec(seg['end']))
        track.SetWidth(k.FromMM(seg['width']));track.SetLayer(layers[seg['layer']])
        track.SetNet(board.FindNet(move['net']));track.SetLocked(True);board.Add(track)
        added.append(track.m_Uuid.AsString())
assert islands(board,nets)==groups, 'A via move changed terminal connectivity'
k.ZONE_FILLER(board).Fill(board.Zones())
(trial/'build/before-via-moves.kicad_pcb').write_bytes(pcb.read_bytes())
assert k.SaveBoard(str(pcb),board)
receipt.write_text(json.dumps(dict(before_sha256=before,
    source_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),
    plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),
    moved=len(plan['moves']),new_tracks=added,terminal_groups_preserved=len(groups),
    scope='Native terminal groups retained; full DRC and return measurement pending.'
),indent=2)+'\n')
print('Moved',len(plan['moves']),'signal vias; all terminal groups preserved')
