#!/usr/bin/env python3
"""Export actual placement and native Fab/land envelopes without changing a PCB.

Run with scripts/kicad-python. Fab outlines are not approved manufacturer bodies;
the separate fit profile adds drawing-derived limits and explicit allowances.
Coordinates are millimeters, centered on the board, with +Y toward native top.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pcbnew as k

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bbox(item):
    b = item.GetBoundingBox()
    return [b.GetLeft() / 1e6, b.GetTop() / 1e6,
            b.GetRight() / 1e6, b.GetBottom() / 1e6]


def union(boxes):
    if not boxes:
        return None
    return [min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes)]


def export(pcb):
    source_hash = sha(pcb)
    board = k.LoadBoard(str(pcb))
    edges = [d for d in board.GetDrawings() if d.GetLayer() == k.Edge_Cuts]
    assert len(edges) == 4 and all(d.GetShape() == k.SHAPE_T_SEGMENT for d in edges), \
        'This exporter currently requires the four-segment rectangular board outline'
    # GetBoardEdgesBoundingBox includes stroke thickness, which is not board size.
    points = [v for d in edges for v in (d.GetStart(), d.GetEnd())]
    native_bounds = [min(p.x for p in points) / 1e6, min(p.y for p in points) / 1e6,
                     max(p.x for p in points) / 1e6, max(p.y for p in points) / 1e6]
    cx = (native_bounds[0] + native_bounds[2]) / 2
    cy = (native_bounds[1] + native_bounds[3]) / 2

    def mapped(box):
        return [round(box[0] - cx, 6), round(cy - box[3], 6),
                round(box[2] - cx, 6), round(cy - box[1], 6)] if box else None

    parts = []
    for f in sorted(board.GetFootprints(), key=lambda x: x.GetReference()):
        top = f.GetLayer() == k.F_Cu
        assert top or f.GetLayer() == k.B_Cu, f.GetReference()
        fab = [bbox(g) for g in f.GraphicalItems()
               if g.GetClass() == 'PCB_SHAPE' and g.GetLayer() == (k.F_Fab if top else k.B_Fab)]
        lands = [bbox(p) for p in f.Pads() if p.IsOnLayer(f.GetLayer())]
        assert fab or lands, f.GetReference()
        parts.append(dict(
            ref=f.GetReference(), value=f.GetValue(),
            footprint=str(f.GetFPID().GetLibItemName()), side='top' if top else 'bottom',
            native_position_mm=[f.GetPosition().x / 1e6, f.GetPosition().y / 1e6],
            position_mm=[round(f.GetPosition().x / 1e6 - cx, 6), round(cy - f.GetPosition().y / 1e6, 6)],
            native_angle_degrees=f.GetOrientationDegrees(),
            dnp=bool(f.IsDNP()),
            fab_bounds_mm=mapped(union(fab)),
            land_bounds_mm=mapped(union(lands)),
            body_and_land_bounds_mm=mapped(union(fab + lands)),
        ))
    assert sha(pcb) == source_hash, 'Source changed during read-only export'
    return dict(
        schema=1, source=str(pcb.relative_to(ROOT)), source_sha256=source_hash,
        exporter_sha256=sha(Path(__file__)),
        coordinate_transform='X = native X - center X; Y = center Y - native Y; Z is set by enclosure parameters',
        native_center_mm=[cx, cy], native_bounds_mm=native_bounds,
        board_size_mm=[native_bounds[2] - native_bounds[0], native_bounds[3] - native_bounds[1],
                       board.GetDesignSettings().GetBoardThickness() / 1e6],
        parts=parts,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pcb', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert ROOT in output.parents, 'Keep generated evidence in this checkout'
    result = export(args.pcb.resolve())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(footprints=len(result['parts']),
                         dnp=[p['ref'] for p in result['parts'] if p['dnp']],
                         board_size_mm=result['board_size_mm'], source_sha256=result['source_sha256'])))


if __name__ == '__main__':
    main()
