#!/usr/bin/env python3
"""Create the source-bound R3 junction trial without altering tested r05i."""
import hashlib
import json
from pathlib import Path
import shutil

import pcbnew as k
from trim_power_r05_tails import islands

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'experiments/power-r05i-rf-stack'
TARGET = ROOT / 'experiments/power-r05j-rf-junctions'
EXPECTED = '0db809c4ecefbf577db1001164886709708f02ab6ba54f7a572e948583d726a1'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE / 'hardware/collar-tracker.kicad_pcb') == EXPECTED
assert not TARGET.exists(), 'Preserve earlier experiments'
shutil.copytree(SOURCE / 'hardware', TARGET / 'hardware', ignore=shutil.ignore_patterns(
    '*.local-routing.json', '*.detour-proposal.json', '*.kicad_prl'))
(TARGET / 'evidence').mkdir()
pcb = TARGET / 'hardware/collar-tracker.kicad_pcb'
board = k.LoadBoard(str(pcb))
nets = {p.GetNetname() for f in board.GetFootprints() for p in f.Pads()}
before = islands(board, nets)
tracks = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
xy = lambda p: [p.x / 1e6, p.y / 1e6]
v = lambda p: k.VECTOR2I(*(round(x * 1e6) for x in p))

changes = [
    dict(net='/LTE_RF', removed=[
        '22d6dd2d-1fd0-41f6-a2ac-10b576bbee88',
        'f3a68b86-a912-40e8-a52a-ce822e3d7de0'],
        points=[[113.25003, 118.625], [113.25003, 119.15], [112.1, 120.3]]),
    dict(net='/LTE_ANT', removed=[
        'adf13514-e385-4d81-ab84-acc428a440eb',
        '9dbd134d-d92c-4ebe-8a54-2bc1251255b6',
        '6ec8d125-5ec8-4414-bb99-5be985a321e6'],
        points=[[114.01, 120.3], [114.01, 122.37], [113.98, 122.4]]),
]
for change in changes:
    change['old_tracks'] = []
    for uid in change['removed']:
        track = tracks[uid]
        assert track.GetClass() == 'PCB_TRACK' and track.GetLayer() == k.F_Cu
        assert track.GetNetname() == change['net'] and track.GetWidth() == 360000
        netcode = track.GetNetCode()
        change['old_tracks'].append(dict(id=uid, start=xy(track.GetStart()),
                                         end=xy(track.GetEnd()), width_mm=.36))
        board.Delete(track)
    change['added_tracks'] = []
    for a, b in zip(change['points'], change['points'][1:]):
        track = k.PCB_TRACK(board)
        track.SetLayer(k.F_Cu)
        track.SetNetCode(netcode)
        track.SetStart(v(a)); track.SetEnd(v(b)); track.SetWidth(360000)
        track.SetLocked(True)
        board.Add(track)
        change['added_tracks'].append(dict(id=track.m_Uuid.AsString(), start=a,
                                           end=b, width_mm=.36))
assert islands(board, nets) == before, 'Terminal groups changed; do not save'
board.GetTitleBlock().SetRevision('0.5j-RF-junctions-WIP')
for drawing in board.GetDrawings():
    if drawing.GetClass() == 'PCB_TEXT' and drawing.GetText() == 'CT 0.5I':
        drawing.SetText('CT 0.5J')
k.ZONE_FILLER(board).Fill(board.Zones())
assert k.SaveBoard(str(pcb), board)
assert sha(SOURCE / 'hardware/collar-tracker.kicad_pcb') == EXPECTED
for suffix in ['kicad_pro', 'kicad_dru', 'kicad_sch']:
    assert sha(pcb.with_suffix('.'+suffix)) == sha(SOURCE / 'hardware' / ('collar-tracker.'+suffix))
(TARGET / 'evidence/rf-junction-seed.json').write_text(json.dumps(dict(
    baseline_sha256=EXPECTED, source_sha256=sha(pcb), changes=changes,
    terminal_groups_preserved=len(before),
    scope='Two LTE route changes only. No pad, via, plane, stack or circuit change. '
          'The main path becomes longer to reduce the tuning stubs and balance R3 entries. '
          'RF loss, impedance and assembly process remain unqualified.'), indent=2)+'\n')
print('Created r05j; terminal groups preserved. Fresh checks required.')
