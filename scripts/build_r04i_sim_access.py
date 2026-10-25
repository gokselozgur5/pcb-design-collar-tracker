"""Move the upper SIM protection beside the card-entry corridor.

This creates an isolated, unrouted trial from the exact r04h checkpoint.
It preserves the source and never represents the trial as accepted.
Run with scripts/kicad-python from the repository root.
"""

import hashlib
import json
import shutil
from pathlib import Path

import pcbnew as k


src = Path("experiments/paul-nanosim-r04h-review-40x32")
dst = Path("experiments/paul-nanosim-r04i-sim-access-40x32")
expected = "9c65b1b2f845d76e16e4a2598b5ec0d2894ee1e812cba25a538d53ae0a028aea"
parent = src / "hardware/collar-tracker.kicad_pcb"
assert hashlib.sha256(parent.read_bytes()).hexdigest() == expected
assert not dst.exists(), "Preserve an existing trial; do not overwrite it"
shutil.copytree(src / "hardware", dst / "hardware")
hw, ev = dst / "hardware", dst / "evidence"
ev.mkdir()
(dst / "build").mkdir()
for name in ["placement-extra.json", "protected-fanout.json"]:
    shutil.copy2(src / "evidence" / name, ev / name)

# Equivalent clamp channels are exchanged; preserve all other schematic bytes.
schema = hw / "collar-tracker.kicad_sch"
text = schema.read_text()
for before, after in [
    ('(label "SIM_CLK" (at 491.4900 285.7500 0)', '(label "SIM_RST" (at 491.4900 285.7500 0)'),
    ('(label "SIM_RST" (at 491.4900 290.8300 0)', '(label "SIM_CLK" (at 491.4900 290.8300 0)'),
]:
    assert text.count(before) == 1
    text = text.replace(before, after)
schema.write_text(text)
data = json.loads((hw / "design.json").read_text())
part = next(p for p in data["parts"] if p["ref"] == "D1")
part["nets"].update({"1": "SIM_RST", "3": "SIM_CLK"})
(hw / "design.json").write_text(json.dumps(data, indent=2) + "\n")

b = k.LoadBoard(str(parent))
xy = lambda p: [p.x / 1e6, p.y / 1e6]
vec = lambda p: k.VECTOR2I(round(p[0] * 1e6), round(p[1] * 1e6))
g = json.loads((src / "evidence/route-geometry.json").read_text())
assert g["source_sha256"] == expected
remove = {
    "40fcc04e-558a-486c-a966-e209c1f54f53",  # Old clock entry and upper exit.
    "693c4922-5060-417f-98a3-7023ce9503df",
    "b7ae2f05-9ed2-4106-8ad3-b8f32a44936f",
    "4f21f609-a353-41a5-ad84-0e0961fabff3",
    "7b1bd5a5-c479-40ae-b6f3-73eea56d751b",
    "b8d799e9-82a7-415b-ba47-c6ea91a6a960",
    "a83cf23f-bf77-4dcf-83d0-51c91ffda02d",
    "a99bf524-677c-41aa-b47f-6d1d17444390",  # Old supply exit via.
    "6b70ea3c-d79a-4a1e-afc6-3fe9449fd8cc",  # Old D1/C10 ground stubs.
    "e891d76f-3cec-448d-b72a-bde0d1257acb",
}
for t in g["tracks"]:
    if t["net"] == "/SIM_RST" and min(t["start"][1], t["end"][1]) < 103:
        if t["id"] != "c1bc9657-b057-4d6e-87ba-7c4c338cf3aa":
            remove.add(t["id"])
    if t["net"] == "/SIM_1V8" and min(t["start"][1], t["end"][1]) < 103:
        remove.add(t["id"])
items = {t.m_Uuid.AsString(): t for t in b.GetTracks()}
assert remove <= set(items)
for ident in remove:
    b.Delete(items[ident])
fps = {f.GetReference(): f for f in b.GetFootprints()}
fps["D1"].SetPosition(vec([133.4, 99.7]))
fps["C10"].SetPosition(vec([136.0, 100.35]))
for p in fps["D1"].Pads():
    if p.GetNumber() in ["1", "3"]:
        p.SetNet(b.FindNet("/" + part["nets"][p.GetNumber()]))
items["3b0346b0-788e-4c27-a574-803cd4845b88"].SetPosition(vec([131.5, 99.7]))

routes = []
incoming = []
anchors = {}


def route(net, points, entry=False):
    ids = []
    for a, z in zip(points, points[1:]):
        t = k.PCB_TRACK(b)
        t.SetNet(b.FindNet(net))
        t.SetLayer(k.B_Cu)
        t.SetWidth(200000)
        t.SetStart(vec(a))
        t.SetEnd(vec(z))
        b.Add(t)
        ids.append(t.m_Uuid.AsString())
    routes.append(dict(net=net, points=points, ids=ids, entry=entry))
    if entry:
        incoming.extend(ids)


def via(net, pos):
    v = k.PCB_VIA(b)
    v.SetPosition(vec(pos))
    v.SetWidth(600000)
    v.SetDrill(200000)
    v.SetViaType(k.VIATYPE_THROUGH)
    v.SetLayerPair(k.F_Cu, k.B_Cu)
    v.SetNet(b.FindNet(net))
    v.SetFrontTentingMode(k.TENTING_MODE_TENTED)
    v.SetBackTentingMode(k.TENTING_MODE_TENTED)
    b.Add(v)
    return v.m_Uuid.AsString()


route("/SIM_CLK", [[124.46, 102.1], [124.46, 101.59], [124.2, 101.33],
                    [124.2, 99.2], [124.6, 98.8], [131.5, 98.8],
                    [131.75, 99.05], [132.3, 99.05]], True)
route("/SIM_RST", [[127, 102.1], [127, 100.7], [127.35, 100.35], [132.3, 100.35]], True)
route("/SIM_1V8", [[129.54, 102.1], [129.54, 101.25], [129.94, 100.85],
                    [134, 100.85], [134.5, 100.35]], True)
route("/GND", [[132.3, 99.7], [131.5, 99.7]])
route("/GND", [[136.48, 100.35], [137.2, 100.35]])
via("/GND", [137.2, 100.35])
route("/SIM_1V8", [[134.5, 100.35], [135.52, 100.35], [135.9, 100.35],
                    [136, 100.25], [136, 99.2]])
for net, points, pos in [
    ("/SIM_CLK", [[132.3, 99.05], [133.15, 99.05]], [133.15, 99.05]),
    ("/SIM_RST", [[132.3, 100.35], [133.15, 100.2]], [133.15, 100.2]),
    ("/SIM_1V8", [], [136, 99.2]),
]:
    if points:
        route(net, points)
    anchors[net] = dict(id=via(net, pos), pos=pos, layer="F.Cu")

k.ZONE_FILLER(b).Fill(b.Zones())
output = hw / "collar-tracker.kicad_pcb"
assert k.SaveBoard(str(output), b)
source_sha = hashlib.sha256(output.read_bytes()).hexdigest()
extra = json.loads((ev / "placement-extra.json").read_text())
for f in b.GetFootprints():
    extra["footprints"][f.GetReference()] = dict(pos=xy(f.GetPosition()), side=b.GetLayerName(f.GetLayer()))
extra["source_sha256"] = source_sha
(ev / "placement-extra.json").write_text(json.dumps(extra, indent=2) + "\n")
(ev / "route-starts.json").write_text(json.dumps(anchors, indent=2) + "\n")
(ev / "incoming-protection.json").write_text(json.dumps(incoming, indent=2) + "\n")
(ev / "sim-access-rework.json").write_text(json.dumps(dict(
    parent_sha256=expected, source_sha256=source_sha, removed=sorted(remove), routes=routes,
    anchors=anchors, scope="Placement and protected route anchors only. Native checks and routing pending."
), indent=2) + "\n")
print("Saved isolated SIM access trial:", source_sha)
