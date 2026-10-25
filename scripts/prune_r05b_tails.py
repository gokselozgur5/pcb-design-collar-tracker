#!/usr/bin/env python3
"""Remove obsolete rail/enable leaf segments with native pin-island invariants."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import pcbnew as k
from trim_power_r05_tails import islands

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05b-pin-exits'
PCB = TRIAL / 'hardware/collar-tracker.kicad_pcb'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--drc', required=True)
    parser.add_argument('--state', required=True)
    parser.add_argument('--stem', required=True)
    args = parser.parse_args()
    assert all(Path(s).name == s for s in (args.drc, args.state, args.stem))
    receipt = TRIAL / 'evidence' / (args.stem + '.json')
    assert not receipt.exists()
    source = sha(PCB)
    assert json.loads((TRIAL / 'evidence' / args.state).read_text())['source_sha256'] == source
    drc_path = TRIAL / 'evidence' / args.drc
    drc = json.loads(drc_path.read_text())
    assert not drc['schematic_parity']
    assert all(v['type'] in {'track_dangling', 'via_dangling', 'silk_over_copper'} for v in drc['violations'])
    ids = {v['items'][0]['uuid'] for v in drc['violations'] if v['type'] == 'track_dangling'}
    assert ids, 'No dangling leaf tracks to review'
    board = k.LoadBoard(str(PCB))
    indexed = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    assert ids <= set(indexed)
    nets = {indexed[uid].GetNetname() for uid in ids}
    assert nets <= {'/VSYS', '/VDD_NRF', '/VBAT', '/NRF_ENABLE', '/POWER_GOOD', '/VIO_DISCHARGE'}
    assert all(indexed[uid].GetNetname() not in {'/POWER_GOOD', '/VIO_DISCHARGE'}
               or indexed[uid].GetLength() <= 100000 for uid in ids), 'Review longer control branches separately'
    before = islands(board, nets)
    removed = []
    for uid in sorted(ids):
        track = indexed[uid]
        assert track.GetClass() == 'PCB_TRACK'
        removed.append({'id': uid, 'net': track.GetNetname()})
        board.Delete(track)
    assert islands(board, nets) == before, 'A populated connection would be changed'
    shutil.copy2(PCB, TRIAL / 'build' / (args.stem + '-before.kicad_pcb'))
    k.ZONE_FILLER(board).Fill(board.Zones())
    assert k.SaveBoard(str(PCB), board)
    receipt.write_text(json.dumps({'before_sha256': source, 'source_sha256': sha(PCB),
                                  'drc_sha256': sha(drc_path), 'removed': removed,
                                  'pad_islands_preserved': before,
                                  'acceptance': 'Fresh DRC is required; only native pin connectivity was preserved.'}, indent=2) + '\n')
    print(json.dumps({'removed': len(removed), 'source_sha256': sha(PCB)}))


if __name__ == '__main__':
    main()
