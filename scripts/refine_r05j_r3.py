#!/usr/bin/env python3
"""Move R3 by 0.30 mm so the adjacent RF bend clears all review contours."""
import hashlib
import json
from pathlib import Path
import shutil

import pcbnew as k
from trim_power_r05_tails import islands

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05j-rf-junctions'
pcb = TRIAL / 'hardware/collar-tracker.kicad_pcb'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before_sha = sha(pcb)
assert before_sha == '16246d219a4d72ea41f457073a369bd8e779141681e267db3d0049123ee6f7a4'
initial = TRIAL / 'initial-layout'
assert not initial.exists()
initial.mkdir()
shutil.copytree(TRIAL / 'hardware', initial / 'hardware',
                ignore=shutil.ignore_patterns('*.kicad_prl'))
shutil.move(str(TRIAL / 'evidence'), str(initial / 'evidence'))
(TRIAL / 'evidence').mkdir()
seed = json.loads((initial / 'evidence/rf-junction-seed.json').read_text())
board = k.LoadBoard(str(pcb))
nets = {p.GetNetname() for f in board.GetFootprints() for p in f.Pads()}
before = islands(board, nets)
v = lambda p: k.VECTOR2I(*(round(x * 1e6) for x in p))
xy = lambda p: [p.x / 1e6, p.y / 1e6]
r3 = next(f for f in board.GetFootprints() if f.GetReference() == 'R3')
old_position = xy(r3.GetPosition())
r3.Move(v([.3, 0]))
tracks = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
feed = tracks['260a5bab-f3fe-4bf3-b9ba-6ca7e7ba543f']
assert xy(feed.GetEnd()) == [112.99, 120.3]
feed.SetEnd(v([113.29, 120.3]))
points = [[114.31, 120.3], [114.31, 122.07], [113.98, 122.4]]
rows = next(c for c in seed['changes'] if c['net'] == '/LTE_ANT')['added_tracks']
for row, a, b in zip(rows, points, points[1:]):
    track = tracks[row['id']]
    track.SetStart(v(a)); track.SetEnd(v(b))
assert islands(board, nets) == before, 'Move changes terminal groups; do not save'
k.ZONE_FILLER(board).Fill(board.Zones())
assert k.SaveBoard(str(pcb), board)
(TRIAL / 'evidence/r3-refinement.json').write_text(json.dumps(dict(
    before_sha256=before_sha, source_sha256=sha(pcb),
    ref='R3', old_position_mm=old_position, new_position_mm=xy(r3.GetPosition()),
    extension_track=feed.m_Uuid.AsString(), new_input_end_mm=[113.29,120.3],
    output_tracks=[r['id'] for r in rows], output_points_mm=points,
    terminal_groups_preserved=len(before),
    reason='The initial junction fixed the immediate entry but crossed larger '
           'pad contours. A 0.30 mm R3 shift clears those contours without '
           'altering lands, vias, inner copper or the stack.'), indent=2)+'\n')
print('R3 moved 0.30 mm; original trial evidence preserved. Fresh checks required.')
