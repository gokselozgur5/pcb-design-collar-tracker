#!/usr/bin/env python3
"""Rework the crowded charger exits in the saved r04 routing checkpoint.

Preserve the source snapshot and bind this one-time adjustment to its input hash.
The resulting board still requires routing, refill and native DRC acceptance.
"""
import hashlib
import json
from pathlib import Path
import sys

import pcbnew as k

root = Path(sys.argv[1]).resolve()
pcb = root / 'hardware/collar-tracker.kicad_pcb'
before = hashlib.sha256(pcb.read_bytes()).hexdigest()
assert before == 'e3be5847acc153015e30ff12c4b2ebabff3d641cde4890942037d2526835f79d'
snapshot = root / 'build/before-charger-local-rework.kicad_pcb'
assert not snapshot.exists()
snapshot.write_bytes(pcb.read_bytes())
b = k.LoadBoard(str(pcb))
point = lambda x, y: k.VECTOR2I(round(x*1e6), round(y*1e6))
xy = lambda v: (v.x/1e6, v.y/1e6)


def track(net, a, z, layer, width):
    t = k.PCB_TRACK(b)
    t.SetNet(b.FindNet(net)); t.SetStart(point(*a)); t.SetEnd(point(*z))
    t.SetLayer(layer); t.SetWidth(round(width*1e6)); t.SetLocked(True)
    b.Add(t)


def via(net, pos):
    v = k.PCB_VIA(b)
    v.SetNet(b.FindNet(net)); v.SetPosition(point(*pos))
    v.SetWidth(600000); v.SetDrill(200000)
    v.SetViaType(k.VIATYPE_THROUGH); v.SetLayerPair(k.F_Cu, k.B_Cu)
    v.SetFrontTentingMode(k.TENTING_MODE_TENTED)
    v.SetBackTentingMode(k.TENTING_MODE_TENTED)
    v.SetLocked(True); b.Add(v)


# Move C17's local return away from the signal/power exits, keeping a short
# direct ground connection to both inner planes.
old_ground, new_ground = (101.1,122.2), (103.2,120.0)
moved = 0
for t in list(b.GetTracks()):
    if t.GetNetname() != '/GND':
        continue
    if t.GetClass() == 'PCB_VIA' and xy(t.GetPosition()) == old_ground:
        t.SetPosition(point(*new_ground)); moved += 1
    elif t.GetClass() == 'PCB_TRACK':
        if xy(t.GetStart()) == old_ground: t.SetStart(point(*new_ground))
        if xy(t.GetEnd()) == old_ground: t.SetEnd(point(*new_ground))
assert moved == 1

# Discard only the long trial CHG_FAULT detour. Restore its known modem stub
# from the first route, then give the charger pin a local layer transition.
for t in list(b.GetTracks()):
    if t.GetNetname() == '/CHG_FAULT': b.Delete(t)
first = k.LoadBoard(str(root/'build/routed-1.kicad_pcb'))
for t in first.GetTracks():
    if t.GetNetname() != '/CHG_FAULT': continue
    if t.GetClass() == 'PCB_VIA': via('/CHG_FAULT',xy(t.GetPosition()))
    else: track('/CHG_FAULT',xy(t.GetStart()),xy(t.GetEnd()),t.GetLayer(),t.GetWidth()/1e6)
for a,z in [((102.4,123.0),(101.8,123.0)),((101.8,123.0),(101.1,123.7))]:
    track('/CHG_FAULT',a,z,k.F_Cu,.2)
via('/CHG_FAULT',(101.1,123.7))

# A wider continuous input trunk replaces the stair-stepped local route.
# Move its connector via right to leave an outer-layer battery corridor.
for t in list(b.GetTracks()):
    if t.GetNetname() == '/VIN_5V': b.Delete(t)
for a,z in [((102,122.28),(103.82,122.28)),((103.82,122.28),(104.6,121.5)),
            ((102,122.28),(101.95,122.33)),((101.95,122.33),(101.95,123.85)),
            ((101.95,123.85),(101.7,124.1)),((101.7,124.1),(101.7,124.8)),
            ((101.7,124.8),(101.6,124.9))]:
    track('/VIN_5V',a,z,k.B_Cu,.4)
track('/VIN_5V',(104.6,122.2),(104.6,121.5),k.F_Cu,.2)
track('/VIN_5V',(101.6,124.9),(101.6,125.2),k.F_Cu,.4)
track('/VIN_5V',(101.6,125.2),(101.25,125.55),k.F_Cu,.4)
track('/VIN_5V',(101.25,125.55),(101.25,126.2),k.F_Cu,.4)
via('/VIN_5V',(104.6,121.5)); via('/VIN_5V',(101.6,124.9))

for a,z in [((102.4,122.6),(101.6,122.6)),((101.6,122.6),(101.4,122.8)),
            ((101.4,122.8),(100.75,122.8))]:
    track('/VBAT',a,z,k.F_Cu,.2)
via('/VBAT',(100.75,122.8))

b.BuildConnectivity(); k.ZONE_FILLER(b).Fill(b.Zones())
assert k.SaveBoard(str(pcb),b)
report = dict(before_sha256=before,source_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),
              c17_ground_via_before=old_ground,c17_ground_via_after=new_ground,
              input_width_mm=.4,local_signal_transition_mm=[101.1,123.7],
              scope='Local charger escape adjustment; fresh native DRC and routing required.')
(root/'evidence/charger-local-rework.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
