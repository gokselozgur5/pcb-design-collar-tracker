#!/usr/bin/env python3
"""Remove isolated noncritical copper groups that reach no native pad.

Ground, RF and SIM are always retained. Native pad-island identity must remain
unchanged. Run with KiCad Python and perform fresh DRC after applying.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pcbnew as k
from trim_power_r05_tails import islands


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trial', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert args.trial.name == 'power-r05e-native-joint'
    assert not args.output.exists(), 'Preserve earlier receipts'
    pcb = args.trial / 'hardware/collar-tracker.kicad_pcb'
    before_sha = hashlib.sha256(pcb.read_bytes()).hexdigest()
    board = k.LoadBoard(str(pcb))
    protected = {'/GND', '/LTE_RF', '/LTE_ANT', '/GPS_RF', '/GNSS_ANT', '/GNSS_FEM_IN',
                 '/GNSS_FEM_OUT', '/FILT_OUT', '/AMP_IN', '/SIM_1V8', '/SIM_CLK', '/SIM_IO', '/SIM_RST'}
    nets = {p.GetNetname() for f in board.GetFootprints() for p in f.Pads()}
    before = islands(board, nets)
    cn = board.GetConnectivity()
    seen, groups = set(), []
    for seed in board.GetTracks():
        if seed.GetNetname() in protected or seed.m_Uuid.AsString() in seen:
            continue
        todo, items, pads = [seed], [], set()
        while todo:
            item = todo.pop()
            uid = item.m_Uuid.AsString()
            if uid in seen:
                continue
            seen.add(uid); items.append(item)
            pads.update(p.m_Uuid.AsString() for p in cn.GetConnectedPads(item)
                        if p.GetNetname() == seed.GetNetname())
            todo.extend(t for t in cn.GetConnectedTracks(item) if t.GetNetname() == seed.GetNetname())
        if not pads:
            groups.append(items)
    report = [{'net': items[0].GetNetname(), 'ids': [t.m_Uuid.AsString() for t in items]}
              for items in groups]
    for items in groups:
        for t in items:
            board.Delete(t)
    assert islands(board, nets) == before, 'Pruning changed native pin connectivity'
    k.ZONE_FILLER(board).Fill(board.Zones())
    assert k.SaveBoard(str(pcb), board)
    args.output.write_text(json.dumps({'before_sha256': before_sha,
        'source_sha256': hashlib.sha256(pcb.read_bytes()).hexdigest(), 'removed_groups': report,
        'native_pad_islands_preserved': len(before), 'scope': 'No-pad copper removed; native DRC still required.'}, indent=2) + '\n')
    print('Removed orphan groups:', len(groups), '; copper items:', sum(len(g) for g in groups))


if __name__ == '__main__':
    main()
