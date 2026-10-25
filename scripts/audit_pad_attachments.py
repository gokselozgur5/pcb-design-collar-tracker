"""Measure passive pad attachments and local ground paths without plane shortcuts."""

import collections, hashlib, heapq, itertools, json, math, sys
from pathlib import Path
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_power_paths import make_graph

r = Path(sys.argv[1])
g = json.loads((r / "evidence/route-geometry.json").read_text())
assert (
    g["source_sha256"]
    == hashlib.sha256(
        (r / "hardware/collar-tracker.kicad_pcb").read_bytes()
    ).hexdigest()
)
pads = {p["id"]: p for p in g["pads"]}
byref = collections.defaultdict(list)
for p in g["pads"]:
    byref[p["ref"]].append(p)
passives = []
for ref, pp in sorted(byref.items()):
    if not ref.startswith(("C", "R", "L", "FB")) or len(pp) != 2:
        continue
    entries = []
    for p in sorted(pp, key=lambda x: x["pin"]):
        shape = unary_union([Polygon(q) for q in p["poly"]])
        attachments = []
        for t in g["tracks"]:
            if t["net"] != p["net"] or t["layer"] not in p["layers"]:
                continue
            line = LineString([t["start"], t["end"]])
            copper = line.buffer(t["width"] / 2, quad_segs=32)
            if copper.distance(shape) > 0.000002:
                continue
            outside = line.difference(shape.buffer(0.005)).length
            if outside > 0.05:
                attachments.append(
                    dict(id=t["id"], width_mm=t["width"], outside_length_mm=outside)
                )
        entries.append(
            dict(
                pin=p["pin"],
                net=p["net"],
                pad_area_mm2=shape.area,
                attachments=attachments,
                total_exit_width_mm=sum(a["width_mm"] for a in attachments),
                max_exit_width_mm=max([a["width_mm"] for a in attachments], default=0),
            )
        )
    totals = [p["total_exit_width_mm"] for p in entries]
    widths = [p["max_exit_width_mm"] for p in entries]
    ratio = max(totals) / min(totals) if min(totals) > 0 else None
    wr = max(widths) / min(widths) if min(widths) > 0 else None
    passives.append(
        dict(
            ref=ref,
            pads=entries,
            exit_width_sum_ratio=ratio,
            max_exit_width_ratio=wr,
            review_candidate=ratio is None or ratio > 2.01 or wr > 1.51,
        )
    )
graph, terminals = make_graph(g, "/GND", 35, 20, 0.8)
queue = []
dist = {}
prev = {}
source = {}
counter = itertools.count()
for v in g["vias"]:
    if v["net"] != "/GND":
        continue
    for layer in ["F.Cu", "B.Cu"]:
        n = ("via", v["id"], layer)
        dist[n] = 0
        source[n] = v["id"]
        heapq.heappush(queue, (0, next(counter), n))
while queue:
    cost, _, n = heapq.heappop(queue)
    if cost != dist[n]:
        continue
    for other, _, meta in graph[n]:
        new = cost + meta.get("length_mm", 0)
        if new < dist.get(other, math.inf):
            dist[other] = new
            prev[other] = (n, meta)
            source[other] = source[n]
            heapq.heappush(queue, (new, next(counter), other))
grounds = []
for (ref, pin), n in sorted(terminals.items()):
    steps = []
    bridges = []
    node = n
    while node in prev:
        node, meta = prev[node]
        if meta["kind"] == "track":
            steps.append(meta)
        if node[0] == "pad" and node[1] != n[1]:
            bridges.append(pads[node[1]]["ref"] + "." + pads[node[1]]["pin"])
    grounds.append(
        dict(
            pad=ref + "." + pin,
            local_path_mm=dist.get(n),
            via=source.get(n),
            track_ids=[s["id"] for s in steps],
            intermediate_pads=bridges,
        )
    )
report = dict(
    source_sha256=g["source_sha256"],
    passives=passives,
    grounds=grounds,
    scope="Copper geometry screens only. Width ratios are review cues, not solder-process acceptance; local ground lengths exclude pad spreading and plane shortcuts.",
)
(r / "evidence/attachment-review.json").write_text(json.dumps(report, indent=2) + "\n")
print(
    "Passive review candidates:",
    [
        (x["ref"], x["exit_width_sum_ratio"], x["max_exit_width_ratio"])
        for x in passives
        if x["review_candidate"]
    ],
)
print(
    "Longest local ground paths:",
    [
        (x["pad"], x["local_path_mm"], x["intermediate_pads"])
        for x in sorted(
            grounds,
            key=lambda x: x["local_path_mm"]
            if x["local_path_mm"] is not None
            else math.inf,
            reverse=True,
        )[:10]
    ],
)
print(
    "Ground paths through pads:",
    [(x["pad"], x["intermediate_pads"]) for x in grounds if x["intermediate_pads"]],
)
