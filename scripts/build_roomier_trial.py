#!/usr/bin/env python3
"""Test a 40 x 32 mm outline while preserving r04e placement and routed copper.

The user authorized growth if measured routing required it. This is a separate
experiment, not a new release or a claim that enlargement solves the layout.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import pcbnew as k

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--name", default="paul-nanosim-r04f-40x32")
args = parser.parse_args()
assert Path(args.name).name == args.name and args.name.startswith("paul-nanosim-")
parent = Path("experiments/paul-nanosim-r04e")
trial = Path("experiments") / args.name
source = parent / "hardware/collar-tracker.kicad_pcb"
source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
assert source_sha == "1628a83a707b4b8e541ee8ce598531841419c5f31f4a7d4e4456ea6fc5c65ff8"
assert not trial.exists(), "Preserve earlier trials"
shutil.copytree(parent / "hardware", trial / "hardware")
for name in ["evidence", "build"]:
    (trial / name).mkdir()
for name in ["protected-fanout.json", "placement-extra.json"]:
    shutil.copy2(parent / "evidence" / name, trial / "evidence" / name)
shutil.copy2(parent / "build/placement.json", trial / "build/placement.json")
extra_path = trial / "evidence/placement-extra.json"
extra = json.loads(extra_path.read_text())
extra["bounds"] = [98, 98, 138, 130]
extra_path.write_text(json.dumps(extra, indent=2) + "\n")
board = k.LoadBoard(str(source))


def vector(point):
    return k.VECTOR2I(*(round(value * 1e6) for value in point))


mapping = {(100, 100): (98, 98), (135, 100): (138, 98),
           (135, 128): (138, 130), (100, 128): (98, 130)}
edges = [item for item in board.GetDrawings() if item.GetLayer() == k.Edge_Cuts]
assert len(edges) == 4
for edge in edges:
    start = (edge.GetStart().x / 1e6, edge.GetStart().y / 1e6)
    end = (edge.GetEnd().x / 1e6, edge.GetEnd().y / 1e6)
    edge.SetStart(vector(mapping[start]))
    edge.SetEnd(vector(mapping[end]))
zones = list(board.Zones())
assert len(zones) == 2
for zone in zones:
    assert zone.GetNetname() == "/GND" and zone.GetLayer() in [k.In1_Cu, k.In2_Cu]
    outline = zone.Outline()
    outline.RemoveAllContours()
    outline.NewOutline()
    for point in [(98, 98), (138, 98), (138, 130), (98, 130)]:
        outline.Append(vector(point))
board.BuildConnectivity()
k.ZONE_FILLER(board).Fill(board.Zones())
output = trial / "hardware/collar-tracker.kicad_pcb"
assert k.SaveBoard(str(output), board)
report = dict(parent_sha256=source_sha,
              source_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
              bounds_mm=[98, 98, 138, 130], dimensions_mm=[40, 32],
              changes="Outline and two inner GND boundaries only; placement, tracks, vias, pads and rules retained.",
              scope="Routing-space experiment. Native checks, routing completion, mechanics and supplier DFM pending.")
(trial / "evidence/growth-trial.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
