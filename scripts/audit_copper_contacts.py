#!/usr/bin/env python3
"""Audit local connections using native pad polygons and actual track/via copper.

Plane fills are deliberately excluded, so every GND pad must reach a local via.
This geometry audit complements native DRC; it does not replace it.
"""

import argparse
from pathlib import Path
import json
import math
import hashlib
import collections
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("trial", type=Path)
args = parser.parse_args()
r = args.trial
g = json.loads((r / "evidence/route-geometry.json").read_text())
assert (
    g["source_sha256"]
    == hashlib.sha256(
        (r / "hardware/collar-tracker.kicad_pcb").read_bytes()
    ).hexdigest()
)
items = []
for p in g["pads"]:
    items.append(
        dict(p, kind="pad", shape=unary_union([Polygon(q) for q in p["poly"]]))
    )
for t in g["tracks"]:
    items.append(
        dict(
            t,
            kind="track",
            layers=[t["layer"]],
            shape=LineString([t["start"], t["end"]]).buffer(
                t["width"] / 2, quad_segs=32
            ),
        )
    )
for v in g["vias"]:
    items.append(
        dict(
            v, kind="via", shape=Point(v["pos"]).buffer(v["diameter"] / 2, quad_segs=96)
        )
    )
parents = list(range(len(items)))


def root(i):
    while parents[i] != i:
        parents[i] = parents[parents[i]]
        i = parents[i]
    return i


def union(i, j):
    parents[root(j)] = root(i)


for layer in ["F.Cu", "B.Cu"]:
    ids = [i for i, x in enumerate(items) if layer in x["layers"]]
    shapes = [items[i]["shape"] for i in ids]
    tree = STRtree(shapes)
    for a, i in enumerate(ids):
        for b in tree.query(shapes[a].buffer(0.000002)):
            j = ids[b]
            if j <= i or items[j]["net"] != items[i]["net"]:
                continue
            if shapes[a].distance(shapes[b]) <= 0.000002:
                union(i, j)
components = collections.defaultdict(list)
for i, x in enumerate(items):
    components[(x["net"], root(i))].append(x)
nets = collections.defaultdict(list)
for (net, _), component in components.items():
    ids = [x["id"] for x in component]
    pads = [x for x in component if x["kind"] == "pad"]
    vias = [x for x in component if x["kind"] == "via"]
    tracks = [x for x in component if x["kind"] == "track"]
    if net.startswith("unconnected-") or not net:
        continue
    nets[net].append(
        {
            "pads": [
                {"ref": p["ref"], "pin": p["pin"], "id": p["id"], "pos": p["pos"]}
                for p in pads
            ],
            "vias": [v["id"] for v in vias],
            "tracks": [t["id"] for t in tracks],
            "track_length_mm": sum(math.dist(t["start"], t["end"]) for t in tracks),
        }
    )
for net, cs in sorted(nets.items()):
    if len(cs) > 1 or net == "/GND":
        print(
            net, "components", len(cs), "pad-bearing", sum(bool(c["pads"]) for c in cs)
        )
        if net != "/GND":
            for c in cs:
                print(
                    " ",
                    ",".join(p["ref"] + "." + p["pin"] for p in c["pads"]),
                    len(c["vias"]),
                    "vias",
                    len(c["tracks"]),
                    "tracks",
                )
missing = [p for c in nets["/GND"] if not c["vias"] for p in c["pads"]]
print("GND pads without track-copper path to a GND via (planes ignored):", missing)
(r / "evidence/contact-components.json").write_text(
    json.dumps(
        {
            "source_sha256": g["source_sha256"],
            "tolerance_mm": 0.000002,
            "ground_pads_without_track_path_to_via": missing,
            "nets": nets,
            "scope": "Actual pad polygons, track capsules and through-via copper; plane fills excluded to expose local contacts. Confirm conclusions with native DRC.",
        },
        indent=2,
    )
    + "\n"
)
