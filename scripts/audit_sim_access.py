"""Check the SIM entry strip against populated bottom-side body/land bounds.

The GCT D6 drawing gives the nominal card width. A 0.20 mm lateral review
margin is added on each side; this is not enclosure or physical-fit acceptance.
Run with KiCad Python. An overlap returns failure without modifying the board.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

import pcbnew as k

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("trial", type=Path)
parser.add_argument("--output", type=Path)
args = parser.parse_args()
pcb = args.trial / "hardware/collar-tracker.kicad_pcb"
drawing = Path(__file__).resolve().parents[1] / "references/paul-nanosim-r04/SIM8051-drawing-D6.pdf"
assert hashlib.sha256(drawing.read_bytes()).hexdigest() == "4fa95562ce295d7916c8badd8efcfac60280980af34d3ce6f330e888c6da475a"
source_sha = hashlib.sha256(pcb.read_bytes()).hexdigest()
board = k.LoadBoard(str(pcb))
socket = next(f for f in board.GetFootprints() if f.GetReference() == "J6")
assert socket.GetLayer() == k.B_Cu and socket.GetOrientationDegrees() == 0
assert (socket.GetPosition().x, socket.GetPosition().y) == (127000000, 108000000)
nominal = [122.6, 98.0, 131.4, 101.9]
margin = 0.2
lane = [nominal[0] - margin, nominal[1], nominal[2] + margin, nominal[3]]


def bounds(item):
    box = item.GetBoundingBox()
    return [box.GetLeft() / 1e6, box.GetTop() / 1e6, box.GetRight() / 1e6, box.GetBottom() / 1e6]


def union(boxes):
    return [min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes)]


def distance(a, b):
    return math.hypot(max(a[0] - b[2], b[0] - a[2], 0),
                      max(a[1] - b[3], b[1] - a[3], 0))


parts = []
for f in board.GetFootprints():
    if f.GetLayer() != k.B_Cu or f.GetReference() == "J6":
        continue
    fab = [bounds(item) for item in f.GraphicalItems()
           if item.GetClass() == "PCB_SHAPE" and item.GetLayer() == k.B_Fab]
    lands = [bounds(p) for p in f.Pads() if p.IsOnLayer(k.B_Cu)]
    assert fab or lands, f.GetReference()
    envelope = union(fab + lands)
    parts.append(dict(ref=f.GetReference(), body_bounds_mm=union(fab) if fab else None,
                      body_and_land_bounds_mm=envelope,
                      clearance_to_nominal_lane_mm=distance(envelope, nominal),
                      clearance_to_margin_lane_mm=distance(envelope, lane)))
overlaps = [p["ref"] for p in parts if p["clearance_to_margin_lane_mm"] <= 0]
report = dict(source_sha256=source_sha, drawing=str(drawing.relative_to(Path(__file__).resolve().parents[1])),
              drawing_sha256=hashlib.sha256(drawing.read_bytes()).hexdigest(),
              socket_side="B.Cu", socket_angle_degrees=0, card_nominal_mm=[8.8, 12.3],
              nominal_entry_projection_mm=nominal, lateral_margin_mm=margin,
              reviewed_entry_projection_mm=lane, parts=sorted(parts, key=lambda p:p["ref"]),
              overlap_candidates=overlaps, pcb_entry_projection_clear=not overlaps,
              scope="Conservative native Fab-body plus copper-land XY bounds, with 0.20 mm lateral review margin. Socket contacts are excluded because they form the intended card interface. Tented vias and mask-covered traces are not raised bodies. Enclosure, tolerances beyond this margin, vertical fit and physical insertion/removal remain unqualified.")
assert hashlib.sha256(pcb.read_bytes()).hexdigest() == source_sha
out = args.output or args.trial / "evidence/card-insertion-review.json"
out.write_text(json.dumps(report, indent=2) + "\n")
print("SIM entry overlaps:", overlaps, "; bottom-side parts checked:", len(parts))
raise SystemExit(bool(overlaps))
