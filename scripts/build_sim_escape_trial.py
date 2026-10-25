#!/usr/bin/env python3
"""Build the reviewed inward-SIM-escape candidate from the pinned r04d source.

Preserves prior sources. Does not complete remaining routes or establish DFM.
"""

import argparse
from pathlib import Path
import json
import shutil
import hashlib
import pcbnew as k

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--name", default="paul-nanosim-r04e")
args = parser.parse_args()
assert Path(args.name).name == args.name and args.name.startswith("paul-nanosim-")
parent = Path("experiments/paul-nanosim-r04d")
r = Path("experiments") / args.name
source = parent / "hardware/collar-tracker.kicad_pcb"
assert (
    hashlib.sha256(source.read_bytes()).hexdigest()
    == "38882bf0111a0190a9a55e756b72be96f91e325de29d909a93c6a57759bbed44"
)
assert not r.exists()
r.mkdir()
shutil.copytree(parent / "hardware", r / "hardware")
(r / "build").mkdir()
(r / "evidence").mkdir()
for name in ["protected-fanout.json", "placement-extra.json"]:
    shutil.copy2(parent / "evidence" / name, r / "evidence" / name)
b = k.LoadBoard(str(source))
def vec(p):
    return k.VECTOR2I(*(round(x * 1e6) for x in p))


def xy(p):
    return [p.x / 1e6, p.y / 1e6]


fps = {f.GetReference(): f for f in b.GetFootprints()}
c4 = fps["C4"]
old = xy(c4.GetPosition())
c4.SetPosition(vec([old[0] - 0.5, old[1] + 0.2]))
component = json.loads((parent / "evidence/contact-components.json").read_text())
assert component["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
remove = {
    "3d0fb05a-70e6-4e3a-bd6f-63069183850a",
    "633b0740-2ec2-46c4-8caa-c1cacd5e13e7",
    "8a0a692e-730d-4914-aa41-1b947c70af91",
    "dfdb4a1c-f225-40a0-bc08-f4a3b5b122f3",
    "6d479c05-bc4a-4d6f-baed-c80425436370",
}
for net, pin in [("/SIM_IO", "17"), ("/SIM_CLK", "18")]:
    cs = [
        c
        for c in component["nets"][net]
        if any(p["ref"] == "U1" and p["pin"] == pin for p in c["pads"])
    ]
    assert len(cs) == 1 and not cs[0]["vias"]
    remove.update(cs[0]["tracks"])
tracks = {t.m_Uuid.AsString(): t for t in b.GetTracks()}
assert remove <= tracks.keys()
for ident in remove:
    b.Delete(tracks[ident])
v = k.Cast_to_PCB_VIA(tracks["be423635-3374-416f-bdce-7e2ccea2bd11"])
v.SetPosition(vec([106.1, 115.1]))
added = []


def route(net, layer, width, points):
    for a, z in zip(points, points[1:]):
        t = k.PCB_TRACK(b)
        t.SetStart(vec(a))
        t.SetEnd(vec(z))
        t.SetWidth(round(width * 1e6))
        t.SetLayer(layer)
        t.SetNet(b.FindNet(net))
        t.SetLocked(True)
        b.Add(t)
        added.append(t.m_Uuid.AsString())


def via(net, pos):
    v = k.PCB_VIA(b)
    v.SetPosition(vec(pos))
    v.SetWidth(600000)
    v.SetDrill(200000)
    v.SetViaType(k.VIATYPE_THROUGH)
    v.SetLayerPair(k.F_Cu, k.B_Cu)
    v.SetNet(b.FindNet(net))
    v.SetLocked(True)
    v.SetFrontTentingMode(k.TENTING_MODE_TENTED)
    v.SetBackTentingMode(k.TENTING_MODE_TENTED)
    b.Add(v)
    added.append(v.m_Uuid.AsString())


route(
    "/GND", k.F_Cu, 0.25, [(105.375, 115.24963), (105.95037, 115.24963), (106.1, 115.1)]
)
route(
    "/GND",
    k.B_Cu,
    0.4,
    [(105.975, 117), (105.325, 117.65), (105.325, 118), (104.6, 118)],
)
route("/VDD_NRF", k.B_Cu, 0.4, [(104.0733, 116.8), (104.225, 116.8), (104.425, 117)])
route(
    "/SIM_IO", k.F_Cu, 0.2, [(105.375, 116.24963), (105.85037, 116.24963), (106.1, 116)]
)
route(
    "/SIM_CLK",
    k.F_Cu,
    0.2,
    [
        (105.375, 116.74963),
        (106.2, 116.74963),
        (106.40037, 116.95),
        (106.85, 116.95),
        (107, 117.1),
    ],
)
via("/SIM_IO", (106.1, 116))
via("/SIM_CLK", (107, 117.1))
b.BuildConnectivity()
k.ZONE_FILLER(b).Fill(b.Zones())
pcb = r / "hardware/collar-tracker.kicad_pcb"
assert k.SaveBoard(str(pcb), b)
placement = {
    f.GetReference(): [
        *xy(f.GetPosition()),
        f.GetOrientationDegrees(),
        "B" if f.IsFlipped() else "F",
    ]
    for f in b.GetFootprints()
}
(r / "build/placement.json").write_text(json.dumps(placement, indent=2) + "\n")
extra = json.loads((r / "evidence/placement-extra.json").read_text())
extra["footprints"]["C4"]["pos"] = xy(c4.GetPosition())
(r / "evidence/placement-extra.json").write_text(json.dumps(extra, indent=2) + "\n")
(r / "evidence/sim-escape-change.json").write_text(
    json.dumps(
        dict(
            parent_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            source_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),
            C4_before=old,
            C4_after=xy(c4.GetPosition()),
            removed_ids=sorted(remove),
            added_ids=added,
            ground_via_moved=[106.1, 115.1],
            scope="Candidate inward SIM pin escapes; native clearance and complete routing pending.",
        ),
        indent=2,
    )
    + "\n"
)
print("Saved candidate", pcb)
