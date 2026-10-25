#!/usr/bin/env python3
"""Exercise an owned footprint's flip and clean process shutdown without saving CAD."""
import json
import os
from pathlib import Path
import pcbnew as k


def main():
    board = k.BOARD()
    io = k.PCB_IO_KICAD_SEXPR()
    library = Path(os.environ['KICAD10_FOOTPRINT_DIR']) / 'Capacitor_SMD.pretty'
    footprint = io.FootprintLoad(str(library), 'C_0805_2012Metric')
    assert footprint is not None
    # Flip accesses BOARD::FlipLayer through the parent; an unowned object can
    # segfault instead of raising a catchable Python exception in KiCad 10.0.7.
    board.Add(footprint)
    footprint.SetPosition(k.VECTOR2I_MM(10, 10))
    def pads():
        return sorted((p.GetNumber(), p.GetPosition().x, p.GetPosition().y) for p in footprint.Pads())
    before = pads()
    footprint.SetLayerAndFlip(k.B_Cu)
    assert footprint.IsFlipped()
    footprint.SetLayerAndFlip(k.F_Cu)
    assert not footprint.IsFlipped() and pads() == before
    print(json.dumps({'kicad': k.Version(), 'owned_footprint_flip': 'PASS',
                      'board_files_written': 0, 'note': 'Also require process exit code 0.'}))


if __name__ == '__main__':
    main()
