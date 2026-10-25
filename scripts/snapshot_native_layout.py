#!/usr/bin/env python3
"""Refresh routing metadata from the authoritative PCB without changing it."""
import argparse
import hashlib
import json
from pathlib import Path

import pcbnew as k
from seed_power_r05_pcb import export_placement, polys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trial', type=Path)
    args = parser.parse_args()
    trial = args.trial.resolve()
    pcb = trial / 'hardware/collar-tracker.kicad_pcb'
    before = hashlib.sha256(pcb.read_bytes()).hexdigest()
    board = k.LoadBoard(str(pcb))
    poses = {f.GetReference(): [f.GetPosition().x / 1e6, f.GetPosition().y / 1e6,
             f.GetOrientationDegrees(), 'B' if f.IsFlipped() else 'F'] for f in board.GetFootprints()}
    (trial / 'build/placement.json').write_text(json.dumps(poses, indent=2) + '\n')
    export_placement(board, set(), output=pcb, trial=trial)
    keepouts = [{'layer': board.GetLayerName(z.GetLayer()), 'tracks': z.GetDoNotAllowTracks(),
                 'vias': z.GetDoNotAllowVias(), 'poly': polys(z.Outline())}
                for z in [*board.Zones(), *(z for f in board.GetFootprints() for z in f.Zones())]
                if z.GetIsRuleArea()]
    (trial / 'evidence/placement-extra.json').write_text(json.dumps(
        {'source_sha256': before, 'keepouts': keepouts}, indent=2) + '\n')
    assert hashlib.sha256(pcb.read_bytes()).hexdigest() == before
    print(json.dumps({'source_sha256': before, 'placements': len(poses), 'keepouts': len(keepouts)}))


if __name__ == '__main__':
    main()
