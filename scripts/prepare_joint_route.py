#!/usr/bin/env python3
"""Copy a native candidate and reserve local exits while allowing trunk rerouting.

RF, SIM, and ground copper stay fixed. The other local pad exits are protected
for 1.2 mm along their existing copper graph. This is a routing experiment;
native DRC and all functional layout audits are still required after import.
"""
import argparse
import hashlib
import heapq
import itertools
import json
import math
from pathlib import Path
import shutil

import pcbnew as k
from seed_power_r05_pcb import export_placement, polys
from trim_power_r05_tails import islands


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('trial', type=Path)
    parser.add_argument('--source-sha256', required=True)
    args = parser.parse_args()
    source, trial = args.source.resolve(), args.trial.resolve()
    assert trial.parent == source.parent and not trial.exists()
    original = source / 'hardware/collar-tracker.kicad_pcb'
    assert sha(original) == args.source_sha256
    shutil.copytree(source / 'hardware', trial / 'hardware', ignore=shutil.ignore_patterns(
        '*.kicad_prl', '*.local-routing.json', '*.detour-proposal.json', '*.lck'))
    for name in ['evidence', 'build', 'previews']:
        (trial / name).mkdir()
    pcb = trial / 'hardware/collar-tracker.kicad_pcb'
    board = k.LoadBoard(str(pcb))
    fixed_nets = {'/GND', '/LTE_RF', '/LTE_ANT', '/GPS_RF', '/GNSS_ANT',
                  '/GNSS_FEM_IN', '/GNSS_FEM_OUT', '/FILT_OUT', '/AMP_IN',
                  '/SIM_1V8', '/SIM_CLK', '/SIM_IO', '/SIM_RST'}
    nets = {p.GetNetname() for f in board.GetFootprints() for p in f.Pads()}
    before = islands(board, nets)
    split = []
    # Splitting keeps identical endpoints/widths/layers and allows the local
    # part of a long original segment to be fixed independently of its trunk.
    for t in list(board.GetTracks()):
        if t.GetNetname() in fixed_nets or t.GetClass() != 'PCB_TRACK':
            continue
        length = t.GetLength() / 1e6
        if length <= 1.0:
            continue
        a, z = t.GetStart(), t.GetEnd()
        start, end = (a.x, a.y), (z.x, z.y)
        count = math.ceil(length)
        points = [tuple(round(start[j] + (end[j] - start[j]) * i / count)
                        for j in range(2)) for i in range(count + 1)]
        new_ids = []
        for a, z in zip(points, points[1:]):
            part = k.PCB_TRACK(board)
            part.SetStart(k.VECTOR2I(*a)); part.SetEnd(k.VECTOR2I(*z))
            part.SetWidth(t.GetWidth()); part.SetLayer(t.GetLayer()); part.SetNet(t.GetNet())
            board.Add(part)
            new_ids.append(part.m_Uuid.AsString())
        split.append({'old_id': t.m_Uuid.AsString(), 'new_ids': new_ids})
        board.Delete(t)
    assert islands(board, nets) == before, 'Splitting changed native pad connectivity'
    cn = board.GetConnectivity()
    by_id = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    protected = {uid for uid, t in by_id.items() if t.GetNetname() in fixed_nets}
    pad_records = []
    for f in board.GetFootprints():
        for p in f.Pads():
            if not p.GetNetname() or p.GetNetname().startswith('unconnected-'):
                continue
            queue, distances, chosen = [], {}, set()
            serial = itertools.count()
            for t in cn.GetConnectedTracks(p):
                if t.GetNetname() == p.GetNetname():
                    heapq.heappush(queue, (0, next(serial), t.m_Uuid.AsString()))
            while queue:
                cost, _, uid = heapq.heappop(queue)
                if cost >= distances.get(uid, math.inf) or cost > 1.2:
                    continue
                distances[uid] = cost
                chosen.add(uid)
                t = by_id[uid]
                step = t.GetLength() / 1e6 if t.GetClass() == 'PCB_TRACK' else .05
                for other in cn.GetConnectedTracks(t):
                    if other.GetNetname() == p.GetNetname():
                        heapq.heappush(queue, (cost + step, next(serial), other.m_Uuid.AsString()))
            protected.update(chosen)
            pad_records.append({'pin': f.GetReference() + '.' + p.GetNumber(),
                                'net': p.GetNetname(), 'protected_ids': sorted(chosen)})
    for uid, t in by_id.items():
        t.SetLocked(uid in protected)
    board.GetTitleBlock().SetRevision('0.5d-joint-routing-WIP')
    k.ZONE_FILLER(board).Fill(board.Zones())
    assert k.SaveBoard(str(pcb), board)
    assert sha(original) == args.source_sha256, 'Original was modified'
    placement = {f.GetReference(): [f.GetPosition().x / 1e6, f.GetPosition().y / 1e6,
                 f.GetOrientationDegrees(), 'B' if f.IsFlipped() else 'F'] for f in board.GetFootprints()}
    (trial / 'build/placement.json').write_text(json.dumps(placement, indent=2) + '\n')
    export_placement(board, set(), output=pcb, trial=trial)
    keepouts = [{'layer': board.GetLayerName(z.GetLayer()), 'tracks': z.GetDoNotAllowTracks(),
                 'vias': z.GetDoNotAllowVias(), 'poly': polys(z.Outline())}
                for z in [*board.Zones(), *(z for f in board.GetFootprints() for z in f.Zones())]
                if z.GetIsRuleArea()]
    (trial / 'evidence/placement-extra.json').write_text(json.dumps({'keepouts': keepouts}, indent=2) + '\n')
    (trial / 'evidence/protected-local.json').write_text(json.dumps(sorted(protected), indent=2) + '\n')
    receipt = {'input_sha256': args.source_sha256, 'source_sha256': sha(pcb),
               'split_segments': split, 'protected_items': len(protected),
               'movable_items': len(by_id) - len(protected), 'fixed_nets': sorted(fixed_nets),
               'local_pins': pad_records, 'native_pad_islands_preserved': len(before),
               'scope': 'WIP joint routing model; native DRC and layout acceptance remain required.'}
    (trial / 'evidence/joint-preparation.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({key: receipt[key] for key in ['source_sha256', 'protected_items',
                      'movable_items', 'native_pad_islands_preserved']}))


if __name__ == '__main__':
    main()
