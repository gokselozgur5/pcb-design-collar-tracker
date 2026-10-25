#!/usr/bin/env python3
"""Normalize native copper contacts for a precision-preserving DSN routing copy.

Run with geometry Python. This does not edit the native board or its rules.
Requires a current native-ground export and source-matched geometry/inventory.
Always verify the generated model and native SES round-trip before accepting it.
"""

import argparse
from pathlib import Path
import json
import hashlib
import math
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import nearest_points, unary_union
from shapely.strtree import STRtree

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("trial", type=Path)
parser.add_argument("--input-stem", required=True)
parser.add_argument("--output-stem", default="contact-minimal")
args = parser.parse_args()
assert all(Path(stem).name == stem for stem in [args.input_stem, args.output_stem])
r = args.trial
input_dsn = r / f"build/{args.input_stem}.dsn"
out = r / f"build/{args.output_stem}.dsn"
assert not out.exists(), "Choose a new output stem; preserve earlier evidence"
export = json.loads((r / f"evidence/{args.input_stem}-export.json").read_text())
assert export["ground_model"] == "fixed native copper and inner planes"
assert export["dsn_sha256"] == hashlib.sha256(input_dsn.read_bytes()).hexdigest()
g = json.loads((r / "evidence/route-geometry.json").read_text())
native = r / "hardware/collar-tracker.kicad_pcb"
assert g["source_sha256"] == hashlib.sha256(native.read_bytes()).hexdigest()
assert export["source_sha256"] == g["source_sha256"]
inventory = json.loads((r / "evidence/layout-inventory.json").read_text())
assert inventory["source_sha256"] == g["source_sha256"], "Stale plane inventory"
for layer in ["In1.Cu", "In2.Cu"]:
    plane = inventory["planes"][layer]
    assert plane["zone_nets"] == ["/GND"] and plane["filled_outline_count"] == 1
    assert not plane["ground_vias_outside"], "Plane connectivity is not established"
assert all(v["diameter"] == 0.6 and v["drill"] == 0.2 for v in g["vias"])
protected = set(json.loads((r / "evidence/protected-fanout.json").read_text()))
rf = {
    "/LTE_RF",
    "/LTE_ANT",
    "/GPS_RF",
    "/GNSS_ANT",
    "/GNSS_FEM_IN",
    "/GNSS_FEM_OUT",
    "/FILT_OUT",
    "/AMP_IN",
}


def fixed(x):
    return x["net"] == "/GND" or x["net"] in rf or x["id"] in protected


def rounded(p):
    return tuple(round(float(x), 4) for x in p)


def line(a, b):
    return LineString([rounded(a), rounded(b)])


tracks = [
    dict(t, line=line(t["start"], t["end"]), fixed=fixed(t))
    for t in g["tracks"]
    if rounded(t["start"]) != rounded(t["end"])
]
bridges = []
outside = []
objects = []
for t in tracks:
    objects.append(
        dict(
            t,
            kind="track",
            layers=[t["layer"]],
            spine=t["line"],
            shape=t["line"].buffer(t["width"] / 2, quad_segs=32),
        )
    )
for p in g["pads"]:
    if not p["net"] or p["net"].startswith("unconnected-"):
        continue
    objects.append(
        dict(
            p,
            kind="pad",
            fixed=False,
            spine=Point(rounded(p["pos"])),
            shape=unary_union([Polygon(q) for q in p["poly"]]),
        )
    )
for v in g["vias"]:
    objects.append(
        dict(
            v,
            kind="via",
            fixed=fixed(v),
            spine=Point(rounded(v["pos"])),
            shape=Point(rounded(v["pos"])).buffer(v["diameter"] / 2, quad_segs=96),
        )
    )
parents = list(range(len(objects)))


def root(i):
    while parents[i] != i:
        parents[i] = parents[parents[i]]
        i = parents[i]
    return i


def union(i, j):
    parents[root(j)] = root(i)


# The source-matched inventory establishes both continuous GND planes.
gndvias = [
    i for i, x in enumerate(objects) if x["kind"] == "via" and x["net"] == "/GND"
]
for i in gndvias[1:]:
    union(gndvias[0], i)
candidates = []
for layer in ["F.Cu", "B.Cu"]:
    ids = [i for i, x in enumerate(objects) if layer in x["layers"]]
    shapes = [objects[i]["shape"] for i in ids]
    tree = STRtree(shapes)
    for ai, i in enumerate(ids):
        a = objects[i]
        for bi in tree.query(shapes[ai].buffer(0.0001)):
            j = ids[bi]
            if j <= i:
                continue
            b = objects[j]
            if a["net"] != b["net"] or shapes[ai].distance(shapes[bi]) > 0.0001:
                continue
            pp, qq = nearest_points(a["spine"], b["spine"])
            p, q = rounded(pp.coords[0]), rounded(qq.coords[0])
            distance = math.dist(p, q)
            if distance < 0.00005:
                union(i, j)
                continue
            existing = unary_union([shapes[ai], shapes[bi]])
            extra = (
                LineString([p, q])
                .buffer(0.1, quad_segs=32)
                .difference(existing.buffer(0.0002))
                .area
            )
            candidates.append(
                (extra > 1e-6, distance + 5 * extra, i, j, layer, p, q, extra)
            )
# Join only disconnected contact groups, preferring existing-copper links.
for _, _, i, j, layer, p, q, extra in sorted(candidates):
    if root(i) == root(j):
        continue
    a, b = objects[i], objects[j]
    union(i, j)
    fix = a["net"] == "/GND" or a["net"] in rf or (a["fixed"] and b["fixed"])
    kind = a["kind"] + "-" + b["kind"]
    bridges.append(
        dict(
            net=a["net"],
            layer=layer,
            line=LineString([p, q]),
            width=0.2,
            fixed=fix,
            id="model-" + kind,
        )
    )
    if extra > 1e-6:
        outside.append(
            dict(net=a["net"], kind=kind, start=p, end=q, added_copper_mm2=extra)
        )
assert not outside, "Model requires new physical copper; review the native layout first"
tracks += bridges
cuts = [{0.0, t["line"].length} for t in tracks]
for layer in ["F.Cu", "B.Cu"]:
    ix = [i for i, t in enumerate(tracks) if t["layer"] == layer]
    lines = [tracks[i]["line"] for i in ix]
    tree = STRtree(lines)
    for a, i in enumerate(ix):
        for b in tree.query(lines[a].buffer(0.00015)):
            j = ix[b]
            if j <= i or tracks[i]["net"] != tracks[j]["net"]:
                continue
            p, q = nearest_points(lines[a], lines[b])
            if p.distance(q) < 0.00015:
                cuts[i].add(lines[a].project(p))
                cuts[j].add(lines[b].project(q))
            for point in [Point(c) for c in lines[b].coords]:
                if point.distance(lines[a]) < 0.00015:
                    cuts[i].add(lines[a].project(point))
            for point in [Point(c) for c in lines[a].coords]:
                if point.distance(lines[b]) < 0.00015:
                    cuts[j].add(lines[b].project(point))
    for a, i in enumerate(ix):
        for v in g["vias"]:
            if v["net"] == tracks[i]["net"] and layer in v["layers"]:
                p = Point(rounded(v["pos"]))
                if p.distance(lines[a]) < 0.00015:
                    cuts[i].add(lines[a].project(p))
        for p in g["pads"]:
            if p["net"] == tracks[i]["net"] and layer in p["layers"]:
                q = Point(rounded(p["pos"]))
                if q.distance(lines[a]) < 0.00015:
                    cuts[i].add(lines[a].project(q))
rows = []
seen = set()
for t, distances in zip(tracks, cuts):
    ds = sorted(distances)
    for a, b in zip(ds, ds[1:]):
        x = rounded(t["line"].interpolate(a).coords[0])
        y = rounded(t["line"].interpolate(b).coords[0])
        if x == y:
            continue
        key = (t["net"], t["layer"], t["width"], tuple(sorted([x, y])))
        if key in seen:
            continue
        seen.add(key)
        kind = "fix" if t["fixed"] else "normal"
        rows.append(
            f"    (wire (path {t['layer']} {t['width'] * 1000:.4f} {x[0] * 1000:.4f} {-x[1] * 1000:.4f} {y[0] * 1000:.4f} {-y[1] * 1000:.4f}) (net {t['net']}) (type {kind}))"
        )
for v in g["vias"]:
    x, y = rounded(v["pos"])
    kind = "fix" if fixed(v) else "normal"
    rows.append(
        f'    (via "Via[0-3]_600:200_um" {x * 1000:.4f} {-y * 1000:.4f} (net {v["net"]}) (type {kind}))'
    )
s = input_dsn.read_text()
assert s.count("  (wiring\n") == 1
s = s.split("  (wiring\n")[0] + "  (wiring\n" + "\n".join(rows) + "\n  )\n)\n"
s = s.replace(str(input_dsn.resolve()), str(out.resolve()), 1)
out.write_text(s)
report = dict(
    source_sha256=g["source_sha256"],
    dsn_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
    input_dsn_sha256=export["dsn_sha256"],
    coordinate_resolution_mm=0.0001,
    copper_comparison_tolerance_mm=0.0002,
    original_tracks=len(g["tracks"]),
    original_vias=len(g["vias"]),
    connector_count=len(bridges),
    wire_count=len(rows) - len(g["vias"]),
    connectors=[
        dict(
            net=t["net"],
            layer=t["layer"],
            start=list(t["line"].coords[0]),
            end=list(t["line"].coords[-1]),
            width_mm=t["width"],
            fixed=t["fixed"],
        )
        for t in bridges
    ],
    connectors_with_new_copper=outside,
    scope="Routing model only: exact-center connections and split junctions. New copper is explicitly reported and requires native DRC after any import. No native source or clearance rule changed.",
)
(r / f"evidence/{args.output_stem}-model.json").write_text(
    json.dumps(report, indent=2) + "\n"
)
print(
    {
        k: v
        for k, v in report.items()
        if k not in ["connectors", "connectors_with_new_copper", "scope"]
    }
)
print("Connectors with added copper:", len(outside))
