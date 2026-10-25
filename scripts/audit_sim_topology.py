"""Measure SIM paths and check that connector copper reaches the ESD land first."""

import hashlib
import heapq
import itertools
import json
import math
import sys
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_power_paths import make_graph


def shortest(graph, start, end):
    serial = itertools.count()
    queue = [(0, next(serial), start)]
    distances = {start: 0}
    previous = {}
    while queue:
        cost, _, node = heapq.heappop(queue)
        if cost != distances[node]:
            continue
        if node == end:
            steps = []
            while node != start:
                node, edge = previous[node]
                if edge["kind"] != "ideal_copper_junction":
                    steps.append(edge)
            return dict(
                length_mm=cost,
                vias=sum(s["kind"] == "via" for s in steps),
                track_ids=list(
                    dict.fromkeys(
                        s["id"] for s in reversed(steps) if s["kind"] == "track"
                    )
                ),
            )
        for other, _, metadata in graph[node]:
            new = cost + metadata.get("length_mm", 0)
            if new < distances.get(other, math.inf):
                distances[other] = new
                previous[other] = (node, metadata)
                heapq.heappush(queue, (new, next(serial), other))
    raise RuntimeError("Disconnected SIM path")


def bypasses_esd_land(geometry, esd, start, end):
    """Cut actual ESD land copper out of this net, then test physical continuity.

    Each remaining polygon is a separate object. Vias join every spanned layer.
    This tests layout topology, not ESD current or IEC immunity.
    """
    cut = unary_union([Polygon(p) for p in esd["poly"]]).buffer(0.001)
    items = []
    for kind, rows in [
        ("pad", geometry["pads"]),
        ("track", geometry["tracks"]),
        ("via", geometry["vias"]),
    ]:
        for item in rows:
            if item["net"] != esd["net"]:
                continue
            layers = item.get("layers", [item.get("layer")])
            shape = (
                unary_union([Polygon(p) for p in item["poly"]])
                if kind == "pad"
                else LineString([item["start"], item["end"]]).buffer(
                    item["width"] / 2, quad_segs=32
                )
                if kind == "track"
                else Point(item["pos"]).buffer(item["diameter"] / 2, quad_segs=96)
            )
            if kind == "via" and shape.intersects(cut):
                raise ValueError(
                    "ESD land overlaps a via; inspect this topology separately"
                )
            shape = shape.difference(cut) if set(layers) & set(esd["layers"]) else shape
            if shape.is_empty:
                continue
            for part in getattr(shape, "geoms", [shape]):
                if part.area:
                    items.append(dict(id=item["id"], shape=part, layers=layers))
    parents = list(range(len(items)))

    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    for layer in sorted({layer for item in items for layer in item['layers']}):
        ids = [i for i, item in enumerate(items) if layer in item["layers"]]
        shapes = [items[i]["shape"] for i in ids]
        tree = STRtree(shapes)
        for a, i in enumerate(ids):
            for j in tree.query(shapes[a].buffer(0.000002)):
                if shapes[a].distance(shapes[j]) <= 0.000002:
                    parents[root(ids[j])] = root(i)
    first = {root(i) for i, x in enumerate(items) if x["id"] == start["id"]}
    last = {root(i) for i, x in enumerate(items) if x["id"] == end["id"]}
    assert first and last
    return bool(first & last)


def main():
    r = Path(sys.argv[1])
    g = json.loads((r / "evidence/route-geometry.json").read_text())
    assert (
        g["source_sha256"]
        == hashlib.sha256(
            (r / "hardware/collar-tracker.kicad_pcb").read_bytes()
        ).hexdigest()
    )
    pads = {(p["ref"], p["pin"]): p for p in g["pads"]}

    mapping = [("SIM_1V8", "1"), ("SIM_RST", "2"), ("SIM_CLK", "3"), ("SIM_IO", "7")]
    rows = []
    for net, connector_pin in mapping:
        net = "/" + net
        clamps = [p for p in g["pads"] if p["net"] == net and p["ref"] in ["D1", "D2"]]
        assert len(clamps) == 1, "Expected exactly one SIM clamp land"
        esd_ref, esd_pin = clamps[0]["ref"], clamps[0]["pin"]
        graph, terminals = make_graph(g, net, 35, 20, 0.8)
        modem = [p for p in g["pads"] if p["net"] == net and p["ref"] == "U1"]
        assert len(modem) == 1
        m = modem[0]
        start, clamp, end = ("J6", connector_pin), (esd_ref, esd_pin), ("U1", m["pin"])
        rows.append(
            dict(
                net=net,
                connector=".".join(start),
                esd=".".join(clamp),
                modem=".".join(end),
                connector_to_esd=shortest(graph, terminals[start], terminals[clamp]),
                esd_to_modem=shortest(graph, terminals[clamp], terminals[end]),
                connector_to_modem=shortest(graph, terminals[start], terminals[end]),
                bypasses_esd_land=bypasses_esd_land(
                    g, pads[clamp], pads[start], pads[end]
                ),
            )
        )
    report = dict(
        source_sha256=g["source_sha256"],
        paths=rows,
        scope="Track centerline lengths exclude ideal pad/junction spreading. ESD-land cut is a copper-topology check, not a powered ESD test. No plane shortcut is used.",
    )
    (r / "evidence/esd-paths.json").write_text(json.dumps(report, indent=2) + "\n")
    for row in rows:
        print(
            row["net"],
            "entry",
            row["connector_to_esd"]["length_mm"],
            "mm",
            row["connector_to_esd"]["vias"],
            "vias; bypass",
            row["bypasses_esd_land"],
        )


if __name__ == "__main__":
    main()
