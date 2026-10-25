#!/usr/bin/env python3
"""Open the added long PG branch for an inner-layer reroute in the six-layer trial."""
from pathlib import Path
import hashlib
import json
import pcbnew as k
from trim_power_r05_tails import islands

root = Path(__file__).resolve().parents[1]
trial = root / 'experiments/power-r05h-six-layer'
pcb = trial / 'hardware/collar-tracker.kicad_pcb'
source = hashlib.sha256(pcb.read_bytes()).hexdigest()
assert source == '333b01e6c77dbef73636c9836018c9063845a93ba2af3a7d88379523771cb755'
old_path = root / 'experiments/power-r05c-return-corridors/evidence/route-geometry.json'
old = json.loads(old_path.read_text())
assert old['source_sha256'] == '74db248dedc96a0dd6f137ae8d443dc26bd2ce7fbad404614d4f19424e5acfd1'
original_ids = {t['id'] for t in old['tracks'] + old['vias']}
route = json.loads((root / 'experiments/power-r05f-return-reset/evidence/native1-routing.json').read_text())['routes']
assert len(route) == 1 and route[0]['net'] == '/POWER_GOOD'
segments, via_positions = set(), set()
xy = lambda p: (round(p[0], 6), round(p[1], 6))
for a, z in zip(route[0]['points'], route[0]['points'][1:]):
    if a[2] == z[2]:
        segments.add((a[2], tuple(sorted((xy(a), xy(z))))))
    else:
        assert xy(a) == xy(z)
        via_positions.add(xy(a))
out = trial / 'evidence/long-pg-released.json'
assert not out.exists()
board = k.LoadBoard(str(pcb))
assert board.GetCopperLayerCount() == 6
nets = {p.GetNetname() for f in board.GetFootprints() for p in f.Pads()}
protected = islands(board, nets - {'/POWER_GOOD'})
removed = []
for t in list(board.GetTracks()):
    if t.GetNetname() != '/POWER_GOOD' or t.m_Uuid.AsString() in original_ids:
        continue
    if t.GetClass() == 'PCB_TRACK':
        ends = tuple(sorted((xy((t.GetStart().x/1e6, t.GetStart().y/1e6)),
                             xy((t.GetEnd().x/1e6, t.GetEnd().y/1e6)))))
        if (t.GetLayer(), ends) not in segments:
            continue
    else:
        assert t.GetClass() == 'PCB_VIA'
        if xy((t.GetPosition().x/1e6,t.GetPosition().y/1e6)) not in via_positions:
            continue
    removed.append(dict(id=t.m_Uuid.AsString(), kind=t.GetClass()))
    board.Delete(t)
assert removed
assert islands(board, nets - {'/POWER_GOOD'}) == protected
pg_groups = islands(board, {'/POWER_GOOD'})
assert len(pg_groups) == 2, pg_groups
k.ZONE_FILLER(board).Fill(board.Zones())
(trial / 'build/before-pg-reroute.kicad_pcb').write_bytes(pcb.read_bytes())
assert k.SaveBoard(str(pcb), board)
out.write_text(json.dumps(dict(before_sha256=source,
    source_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),
    removed=removed, remaining_pg_terminal_groups=pg_groups,
    protected_terminal_groups=len(protected),
    scope='Only the added PG branch was released; fresh complete native DRC and rerouting required.'
), indent=2) + '\n')
print('Released added PG copper; exactly two PG terminal groups, all other terminal groups unchanged')
