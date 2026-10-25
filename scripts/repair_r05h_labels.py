#!/usr/bin/env python3
"""Apply measured label offsets and balance the short C30 ground attachment."""
from pathlib import Path
import hashlib
import json
import pcbnew as k
from trim_power_r05_tails import islands

r = Path(__file__).resolve().parents[1] / 'experiments/power-r05h-six-layer'
p = r / 'hardware/collar-tracker.kicad_pcb'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
plan_path = r / 'evidence/label-repair-plan.json'
plan = json.loads(plan_path.read_text())
out = r / 'evidence/label-repair-applied.json'
before = sha(p)
assert before == plan['source_sha256'] and not out.exists()
b = k.LoadBoard(str(p))
nets = {p.GetNetname() for f in b.GetFootprints() for p in f.Pads()}
groups = islands(b, nets)
items = {g.m_Uuid.AsString(): g for g in b.GetDrawings()}
for row in plan['changes']:
    t = items[row['id']]
    assert t.GetClass() == 'PCB_TEXT' and t.GetText() == row['text'] and t.GetLayer() == k.B_SilkS
    t.SetPosition(t.GetPosition() + k.VECTOR2I(*(round(v * 1e6) for v in row['delta_mm'])))
t = next(t for t in b.GetTracks() if t.m_Uuid.AsString() == '6c6b830c-3dcc-4a5c-ad0d-66cc67bd0510')
assert t.GetNetname() == '/GND' and t.GetLayer() == k.F_Cu and t.GetWidth() == 400000
assert tuple(t.GetStart()) == (135980000,108500000) and tuple(t.GetEnd()) == (136800000,108500000)
t.SetWidth(200000)
assert islands(b, nets) == groups
k.ZONE_FILLER(b).Fill(b.Zones())
(r / 'build/before-label-repair.kicad_pcb').write_bytes(p.read_bytes())
assert k.SaveBoard(str(p), b)
out.write_text(json.dumps(dict(before_sha256=before,source_sha256=sha(p),
    plan_sha256=sha(plan_path),changes=plan['changes'],
    c30_ground=dict(track_id=t.m_Uuid.AsString(),length_mm=.82,old_width_mm=.4,new_width_mm=.2,
                    reason='Match the 0.2 mm supply-side attachment without changing either land or the local GND via.'),
    native_terminal_groups_preserved=len(groups),
    scope='Fresh native, copper/return and supplier checks required.'),indent=2)+'\n')
print('Moved two full-size labels; balanced C30 short attachment; terminal groups preserved')
