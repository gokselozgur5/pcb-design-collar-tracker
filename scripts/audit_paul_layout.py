#!/usr/bin/env python3
"""Record native ground/RF/footprint invariants for an isolated Paul trial.

This read-only inventory does not replace DRC, ESD review, current/thermal
analysis, supplier DFM or physical tests. Run with KiCad's Python.
"""
import collections
import hashlib
import json
import math
from pathlib import Path
import sys

import pcbnew as k

root = Path(__file__).resolve().parents[1]
trial = Path(sys.argv[1]).resolve()
source = trial / 'hardware/collar-tracker.kicad_pcb'
baseline = root / 'experiments/35x28-clearance-r034/hardware/collar-tracker.kicad_pcb'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(baseline) == '597ebdee59550b6d07eb104274eabee57b038ea6c87da2dec38c1201f78c89b2'
before = sha(source)
board, old = k.LoadBoard(str(source)), k.LoadBoard(str(baseline))
xy = lambda point: [point.x/1e6, point.y/1e6]
rf_nets = {'/LTE_RF','/LTE_ANT','/GPS_RF','/GNSS_ANT','/GNSS_FEM_IN','/GNSS_FEM_OUT','/FILT_OUT','/AMP_IN'}


def rf_tracks(b):
    result = collections.Counter()
    for t in b.GetTracks():
        if t.GetNetname() not in rf_nets:
            continue
        assert t.GetClass() == 'PCB_TRACK'
        ends = tuple(sorted((tuple(xy(t.GetStart())), tuple(xy(t.GetEnd())))))
        result[(t.GetNetname(), ends, t.GetWidth(), t.GetLayer())] += 1
    return result


vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
grounds = [v for v in vias if v.GetNetname() == '/GND']
signals = [v for v in vias if v.GetNetname() != '/GND']
assert grounds
planes = {}
for layer in [k.In1_Cu, k.In2_Cu]:
    zones = [z for z in board.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(layer)]
    planes[board.GetLayerName(layer)] = dict(
        zone_nets=[z.GetNetname() for z in zones],
        filled_outline_count=sum(z.GetFilledPolysList(layer).OutlineCount() for z in zones),
        ground_vias_outside=[v.m_Uuid.AsString() for v in grounds
                             if not any(z.GetNetname() == '/GND' and
                                        z.GetFilledPolysList(layer).Contains(v.GetPosition())
                                        for z in zones)])
returns = [dict(id=v.m_Uuid.AsString(), net=v.GetNetname(), pos=xy(v.GetPosition()),
                nearest_ground_mm=min(math.dist(xy(v.GetPosition()),xy(g.GetPosition())) for g in grounds))
           for v in signals]
fps = {f.GetReference(): f for f in board.GetFootprints()}
socket = fps['J6']
esd = fps['D1']
result = dict(
    source_sha256=before, baseline_sha256=sha(baseline),
    footprints=len(fps), pads=sum(len(list(f.Pads())) for f in fps.values()),
    ground_pads=sum(p.GetNetname() == '/GND' for f in fps.values() for p in f.Pads()),
    ground_vias=len(grounds), non_ground_vias=len(signals),
    inner_tracks=sum(t.GetClass()=='PCB_TRACK' and t.GetLayer() in [k.In1_Cu,k.In2_Cu]
                     for t in board.GetTracks()),
    planes=planes, rf_segments_preserved=(rf_tracks(board)==rf_tracks(old)),
    rf_segments=sum(rf_tracks(board).values()),
    via_sizes_mm=sorted({(v.GetWidth(k.F_Cu)/1e6,v.GetDrill()/1e6) for v in vias}),
    returns=returns, returns_outside_2mm=sum(r['nearest_ground_mm']>2 for r in returns),
    socket=dict(position=xy(socket.GetPosition()), angle=socket.GetOrientationDegrees(),
                side=board.GetLayerName(socket.GetLayer()),
                pads=[dict(pin=p.GetNumber(),net=p.GetNetname(),position=xy(p.GetPosition())) for p in socket.Pads()]),
    esd=dict(position=xy(esd.GetPosition()), side=board.GetLayerName(esd.GetLayer()),
             pads=[dict(pin=p.GetNumber(),net=p.GetNetname(),size=xy(p.GetSize()),
                        position=xy(p.GetPosition())) for p in esd.Pads()]),
    scope='Native inventory only. Ground via centers checked against saved fills; RF identity does not qualify impedance. Return spacing is a screening target. DRC, physical access, ESD topology, power, assembly and manufacturer acceptance are separate.')
assert sha(source) == before
(trial/'evidence/layout-inventory.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({key:result[key] for key in ['source_sha256','footprints','ground_pads','ground_vias',
    'inner_tracks','planes','rf_segments_preserved','rf_segments','returns_outside_2mm']},indent=2))
