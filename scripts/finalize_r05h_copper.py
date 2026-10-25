#!/usr/bin/env python3
"""Trim only unused HEALTH_CS ends and identify the six-layer review revision."""
from pathlib import Path
import hashlib
import json
import pcbnew as k
from trim_power_r05_tails import islands

r = Path(__file__).resolve().parents[1] / 'experiments/power-r05h-six-layer'
p = r / 'hardware/collar-tracker.kicad_pcb'
receipt = r / 'evidence/final-copper-cleanup.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before_sha = sha(p)
assert not receipt.exists()
assert json.loads((r / 'evidence/trimmed-signal-tails.json').read_text())['source_sha256'] == before_sha
b = k.LoadBoard(str(p))
nets = {p.GetNetname() for f in b.GetFootprints() for p in f.Pads()}
before = islands(b, nets)
items = {t.m_Uuid.AsString(): t for t in b.GetTracks()}
t = items['d6041657-d05d-489d-81ef-ba738ab45e29']
assert t.GetClass() == 'PCB_TRACK' and t.GetNetname() == '/HEALTH_CS'
assert t.GetLayer() == k.F_Cu and t.GetWidth() == 200000
assert tuple(t.GetStart()) == (121426100, 122084900)
assert tuple(t.GetEnd()) == (126219900, 122084900)
t.SetStart(k.VECTOR2I(123024033, 122084900))
removed = ['a8374a01-ad14-4f78-a9c1-7445e5159125', 'cc41177a-2081-480f-95b3-1e3671007d34']
for uid in removed:
    tail = items[uid]
    assert tail.GetClass() == 'PCB_TRACK' and tail.GetNetname() == '/HEALTH_CS' and tail.GetLayer() == k.B_Cu
    b.Delete(tail)
assert islands(b, nets) == before, 'Cleanup changed a native terminal group; not saved'
legends = [x for x in b.GetDrawings() if x.GetClass() == 'PCB_TEXT' and x.GetText() == 'CT 0.5B']
assert len(legends) == 1
legends[0].SetText('CT 0.5H')
k.ZONE_FILLER(b).Fill(b.Zones())
assert k.SaveBoard(str(p), b)
receipt.write_text(json.dumps(dict(before_sha256=before_sha, source_sha256=sha(p),
    shortened_track=t.m_Uuid.AsString(), removed_length_mm=1.597933,
    removed_track_ids=removed, native_terminal_groups_preserved=len(before), legend='CT 0.5H',
    scope='Unused HEALTH_CS copper trimmed with live branch retained; fresh native and supplier checks required.'), indent=2) + '\n')
print('Unused HEALTH_CS ends trimmed; all terminal groups retained; CT 0.5H legend set')
