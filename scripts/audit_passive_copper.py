"""Measure unique copper at small passive lands; retain process limits."""

import hashlib
import json
import sys
from pathlib import Path

from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

r = Path(sys.argv[1])
g = json.loads((r / "evidence/route-geometry.json").read_text())
assert (
    g["source_sha256"]
    == hashlib.sha256(
        (r / "hardware/collar-tracker.kicad_pcb").read_bytes()
    ).hexdigest()
)
refs = sorted(
    {p["ref"] for p in g["pads"] if p["ref"].startswith(("C", "R", "L", "FB"))}
)
rows = []
for ref in refs:
    pads = sorted([p for p in g["pads"] if p["ref"] == ref], key=lambda p: p["pin"])
    if len(pads) != 2:
        continue
    details = []
    for pad in pads:
        shape = unary_union([Polygon(p) for p in pad["poly"]])
        copper = unary_union(
            [
                LineString([t["start"], t["end"]]).buffer(t["width"] / 2, quad_segs=48)
                for t in g["tracks"]
                if t["net"] == pad["net"] and t["layer"] in pad["layers"]
            ]
        )
        widths = {
            str(offset): shape.buffer(offset, quad_segs=48)
            .boundary.intersection(copper)
            .length
            for offset in [0.05, 0.15, 0.30]
        }
        details.append(
            dict(
                pin=pad["pin"],
                net=pad["net"],
                land_area_mm2=shape.area,
                copper_intersection_mm=widths,
            )
        )
    rows.append(
        dict(
            ref=ref,
            pads=details,
            ratios={
                key: max(p["copper_intersection_mm"][key] for p in details)
                / min(p["copper_intersection_mm"][key] for p in details)
                if min(p["copper_intersection_mm"][key] for p in details) > 0
                else None
                for key in ["0.05", "0.15", "0.3"]
            },
        )
    )
report = dict(
    source_sha256=g["source_sha256"],
    passives=rows,
    scope="Unique track-copper intersection with contours 0.05/0.15/0.30 mm outside each native land. This avoids duplicate-segment width sums. Nearby same-net branches can intersect larger contours. This is a geometry review cue, not a reflow, thermal or assembly acceptance criterion.",
)
(r / "evidence/passive-copper-review.json").write_text(
    json.dumps(report, indent=2) + "\n"
)
for row in rows:
    if row["ref"] in ["C2", "C20", "C21", "R1", "R9", "R10"]:
        print(
            row["ref"],
            [
                {
                    key: round(value, 4)
                    for key, value in p["copper_intersection_mm"].items()
                }
                for p in row["pads"]
            ],
        )
