#!/usr/bin/env python3
"""Restore two original modem exits and reserve the historical COEX ground site."""
from pathlib import Path
import hashlib
import json
import pcbnew as k
from trim_power_r05_tails import islands

root = Path(__file__).resolve().parents[1]
trial = root / 'experiments/power-r05h-six-layer'
pcb = trial / 'hardware/collar-tracker.kicad_pcb'
ev = trial / 'evidence'
out = ev / 'restored-signal-exits.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = sha(pcb)
route = json.loads((ev / 'last-crossings-routing.json').read_text())
plan = json.loads((ev / 'final-return-repair-plan.json').read_text())
applied = json.loads((ev / 'final-return-repair-applied.json').read_text())
assert before == route['source_sha256'] and not out.exists()
b = k.LoadBoard(str(pcb))
assert b.GetCopperLayerCount() == 6
nets = {p.GetNetname() for f in b.GetFootprints() for p in f.Pads()}
protected = islands(b, nets - {'/HEALTH_INT', '/I2C_SDA'})
vec = lambda p: k.VECTOR2I(round(p[0] * 1e6), round(p[1] * 1e6))
items = {t.m_Uuid.AsString(): t for t in b.GetTracks()}
assert len(route['routes']) == 1 and route['routes'][0]['net'] == '/HEALTH_INT'
points = route['routes'][0]['points']
removed = []
for a, z in zip(points, points[1:]):
    if a[2] == z[2]:
        matches = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK'
                   and t.GetNetname() == '/HEALTH_INT' and t.GetLayer() == a[2]
                   and {tuple(t.GetStart()), tuple(t.GetEnd())} == {tuple(vec(a)), tuple(vec(z))}]
    else:
        assert vec(a) == vec(z)
        matches = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA'
                   and t.GetNetname() == '/HEALTH_INT' and t.GetPosition() == vec(a)]
    assert len(matches) == 1, (a, z, len(matches))
    removed.append(matches[0].m_Uuid.AsString())
    b.Delete(matches[0])
assert len(applied['new_tracks']) == 4
for uid in applied['new_tracks']:
    t = items[uid]
    assert t.GetClass() == 'PCB_TRACK' and t.GetNetname() in {'/HEALTH_INT', '/I2C_SDA'}
    b.Delete(t)
for row in plan['cuts']:
    t = k.PCB_TRACK(b)
    t.SetStart(vec(row['start'])); t.SetEnd(vec(row['end']))
    t.SetWidth(k.FromMM(row['width']))
    t.SetLayer(k.F_Cu if row['layer'] == 'F.Cu' else k.B_Cu)
    t.SetNet(b.FindNet(row['net'])); t.SetUuid(k.KIID(row['id']))
    t.SetLocked(True); b.Add(t)
ground = items[applied['ground_id']]
assert ground.GetNetname() == '/GND' and ground.GetPosition() == vec(plan['ground_add'])
ground.SetPosition(vec([120.05, 112.975]))
assert islands(b, nets - {'/HEALTH_INT', '/I2C_SDA'}) == protected
assert all(len(islands(b, {n})) == 1 for n in ['/HEALTH_INT', '/I2C_SDA'])
k.ZONE_FILLER(b).Fill(b.Zones())
(trial / 'build/before-restored-signal-exits.kicad_pcb').write_bytes(pcb.read_bytes())
assert k.SaveBoard(str(pcb), b)
out.write_text(json.dumps(dict(before_sha256=before, source_sha256=sha(pcb),
    removed_reroute_ids=removed, removed_cut_piece_ids=applied['new_tracks'],
    restored_track_ids=[r['id'] for r in plan['cuts']], ground_id=applied['ground_id'],
    ground_position_mm=[120.05, 112.975], protected_terminal_groups=len(protected),
    scope='Original signal exits restored; fresh native and return audits required.'), indent=2) + '\n')
print('Restored I2C_SDA and HEALTH_INT exits; unrelated terminal groups retained')
