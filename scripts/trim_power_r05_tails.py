#!/usr/bin/env python3
"""Remove reported rail tails only when every affected pad island is unchanged."""
import argparse
import hashlib
import json
from pathlib import Path
import pcbnew as k

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05-supervised'
PCB = TRIAL / 'hardware/collar-tracker.kicad_pcb'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def islands(board, nets):
    board.BuildConnectivity()
    connectivity = board.GetConnectivity()
    seen, result = set(), []
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if pad.GetNetname() not in nets or pad.m_Uuid.AsString() in seen:
                continue
            todo, pins = [pad], []
            while todo:
                item = todo.pop()
                uid = item.m_Uuid.AsString()
                if uid in seen:
                    continue
                seen.add(uid)
                if item.GetClass() == 'PAD':
                    pins.append(uid)
                todo.extend(t for t in connectivity.GetConnectedTracks(item)
                            if t.GetNetname() == pad.GetNetname())
                todo.extend(p for p in connectivity.GetConnectedPads(item)
                            if p.GetNetname() == pad.GetNetname())
            result.append((pad.GetNetname(), tuple(sorted(pins))))
    return sorted(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--drc', default='local-route2-drc.json')
    parser.add_argument('--state', help='Previous receipt in evidence/; otherwise use local-routing.json')
    parser.add_argument('--output', default='trimmed-rail-tails.json')
    args = parser.parse_args()
    assert all(Path(name).name == name for name in [args.drc, args.output] + ([args.state] if args.state else []))
    receipt = TRIAL / 'evidence' / args.output
    assert not receipt.exists(), 'Preserve earlier evidence'
    state = TRIAL / 'evidence' / args.state if args.state else PCB.with_suffix('.local-routing.json')
    stage = json.loads(state.read_text())
    before_sha = sha(PCB)
    assert stage['source_sha256'] == before_sha
    drc_path = TRIAL / 'evidence' / args.drc
    drc = json.loads(drc_path.read_text())
    assert all(v['type'] == 'track_dangling' for v in drc['violations'])
    board = k.LoadBoard(str(PCB))
    tracks = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    ids = [v['items'][0]['uuid'] for v in drc['violations']]
    assert ids and all(uid in tracks for uid in ids)
    nets = {tracks[uid].GetNetname() for uid in ids}
    assert nets <= {'/VSYS', '/VDD_NRF'}, 'Review a different tail before deletion'
    before = islands(board, nets)
    removed = []
    for uid in ids:
        track = tracks[uid]
        assert track.GetClass() == 'PCB_TRACK'
        removed.append({'id': uid, 'net': track.GetNetname()})
        board.Delete(track)
    assert islands(board, nets) == before, 'Deletion changes connected pad groups; source was not saved'
    k.ZONE_FILLER(board).Fill(board.Zones())
    assert k.SaveBoard(str(PCB), board)
    receipt.write_text(json.dumps({
        'before_sha256': before_sha, 'source_sha256': sha(PCB),
        'drc_sha256': sha(drc_path), 'input_state_sha256': sha(state),
        'removed': removed, 'affected_pad_islands_preserved': len(before),
        'scope': 'Native pin-island invariant only; fresh DRC still required.'}, indent=2) + '\n')
    print('Removed', len(removed), 'tails; preserved', len(before), 'affected pad islands')


if __name__ == '__main__':
    main()
