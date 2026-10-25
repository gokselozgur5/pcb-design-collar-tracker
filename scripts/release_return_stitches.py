#!/usr/bin/env python3
"""Remove return-only stitches for rerouting; preserve local GND and RF returns.

The result intentionally needs fresh return coverage. Run with KiCad Python.
Only a disposable joint-routing trial is accepted; this is not a release step.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import pcbnew as k
from trim_power_r05_tails import islands


def distance(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    f = min(1, max(0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy))) if dx or dy else 0
    return math.hypot(p[0] - a[0] - f * dx, p[1] - a[1] - f * dy)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trial', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    assert args.trial.name in {'power-r05e-native-joint', 'power-r05f-return-reset'}, 'Use an isolated routing experiment'
    assert not args.output.exists(), 'Preserve earlier receipts'
    pcb = args.trial / 'hardware/collar-tracker.kicad_pcb'
    before = hashlib.sha256(pcb.read_bytes()).hexdigest()
    board = k.LoadBoard(str(pcb))
    xy = lambda p: (p.x / 1e6, p.y / 1e6)
    rf = {'/LTE_RF', '/LTE_ANT', '/GPS_RF', '/GNSS_ANT', '/GNSS_FEM_IN', '/GNSS_FEM_OUT', '/FILT_OUT', '/AMP_IN'}
    pads = [p for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() == '/GND']
    tracks = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK' and (t.GetNetname() == '/GND' or t.GetNetname() in rf)]
    candidates, protected = [], []
    for via in list(board.GetTracks()):
        if via.GetClass() != 'PCB_VIA' or via.GetNetname() != '/GND':
            continue
        x, y = pos = xy(via.GetPosition())
        radius = via.GetWidth(k.F_Cu) / 2e6
        reasons = []
        for pad in pads:
            bb = pad.GetBoundingBox()
            gap = math.hypot(max(bb.GetLeft() / 1e6 - x, 0, x - bb.GetRight() / 1e6),
                             max(bb.GetTop() / 1e6 - y, 0, y - bb.GetBottom() / 1e6)) - radius
            if gap <= .001:
                reasons.append('touches ground pad')
                break
        for t in tracks:
            gap = distance(pos, xy(t.GetStart()), xy(t.GetEnd())) - radius - t.GetWidth() / 2e6
            if t.GetNetname() == '/GND' and gap <= .001:
                reasons.append('touches local ground track')
            elif t.GetNetname() in rf and gap <= 2:
                reasons.append('within 2 mm of RF copper')
        row = {'id': via.m_Uuid.AsString(), 'position': pos, 'reasons': sorted(set(reasons))}
        if reasons:
            protected.append(row)
        else:
            candidates.append((via, row))
    ground = islands(board, {'/GND'})
    if args.apply:
        for via, _ in candidates:
            board.Delete(via)
        assert islands(board, {'/GND'}) == ground, 'Local ground-pad connectivity changed'
        k.ZONE_FILLER(board).Fill(board.Zones())
        assert k.SaveBoard(str(pcb), board)
    data = {'before_sha256': before, 'source_sha256': hashlib.sha256(pcb.read_bytes()).hexdigest(),
            'applied': args.apply, 'return_only_vias': [r for _, r in candidates], 'protected': protected,
            'local_ground_pad_islands_preserved': len(ground),
            'scope': 'Local ground and nearby RF vias retained. Return coverage is deliberately unfinished and must be rebuilt before DFM.'}
    args.output.write_text(json.dumps(data, indent=2) + '\n')
    print('Return-only vias:', len(candidates), '; retained local/RF vias:', len(protected), '; applied:', args.apply)


if __name__ == '__main__':
    main()
