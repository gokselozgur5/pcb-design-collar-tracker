#!/usr/bin/env python3
"""Export an outer-layer routing copy; represent local GND as obstacles.

The native board, its pad apertures and its two inner planes are not modified.
"""
import hashlib
import json
import math
from pathlib import Path
import sys
import pcbnew as k

root = Path(sys.argv[1]).resolve()
pcb = root / 'hardware/collar-tracker.kicad_pcb'
board = k.LoadBoard(str(pcb))
vector = lambda xy: k.VECTOR2I(*(round(v * 1e6) for v in xy))
xy = lambda v: (v.x / 1e6, v.y / 1e6)
keepout_count = 0


def keepout(points, layer, tracks=True):
    global keepout_count
    zone = k.ZONE(board)
    zone.SetLayer(layer)
    zone.SetIsRuleArea(True)
    zone.SetDoNotAllowTracks(tracks)
    zone.SetDoNotAllowVias(True)
    zone.SetDoNotAllowZoneFills(False)
    zone.SetDoNotAllowPads(False)
    zone.SetDoNotAllowFootprints(False)
    outline = zone.Outline()
    outline.NewOutline()
    for point in points:
        outline.Append(vector(point))
    board.Add(zone)
    keepout_count += 1


for zone in list(board.Zones()):
    if not zone.GetIsRuleArea():
        board.Delete(zone)
ground_items = []
for track in list(board.GetTracks()):
    if track.GetNetname() != '/GND':
        continue
    ground_items.append(track)
    if track.GetClass() == 'PCB_VIA':
        x, y = xy(track.GetPosition())
        radius = (track.GetWidth(k.F_Cu) / 2e6 + .005) / math.cos(math.pi / 16)
        points = [(x + radius * math.cos(i * math.pi / 8),
                   y + radius * math.sin(i * math.pi / 8)) for i in range(16)]
        for layer in [k.F_Cu, k.B_Cu]:
            keepout(points, layer)
    else:
        ax, ay = xy(track.GetStart())
        bx, by = xy(track.GetEnd())
        length = math.hypot(bx - ax, by - ay)
        if length < 1e-6:
            continue
        ux, uy = (bx - ax) / length, (by - ay) / length
        nx, ny = -uy, ux
        half = track.GetWidth() / 2e6 + .005
        keepout([(ax - ux * half + nx * half, ay - uy * half + ny * half),
                 (bx + ux * half + nx * half, by + uy * half + ny * half),
                 (bx + ux * half - nx * half, by + uy * half - ny * half),
                 (ax - ux * half - nx * half, ay - uy * half - ny * half)], track.GetLayer())
for item in ground_items:
    board.Delete(item)
hidden_pads = 0
for footprint in board.GetFootprints():
    for pad in footprint.Pads():
        if pad.GetNetname() == '/GND' or pad.GetNetname().startswith('unconnected-') or not pad.GetNetname():
            pad.SetNetCode(0)
            bb = pad.GetBoundingBox()
            points = [(bb.GetLeft()/1e6, bb.GetTop()/1e6), (bb.GetRight()/1e6, bb.GetTop()/1e6),
                      (bb.GetRight()/1e6, bb.GetBottom()/1e6), (bb.GetLeft()/1e6, bb.GetBottom()/1e6)]
            for layer in [k.F_Cu, k.B_Cu]:
                if pad.IsOnLayer(layer):
                    keepout(points, layer)
            hidden_pads += 1
        elif pad.GetShape() in [k.PAD_SHAPE_ROUNDRECT, k.PAD_SHAPE_OVAL, k.PAD_SHAPE_CIRCLE]:
            pad.SetShape(k.PAD_SHAPE_RECT)
dsn = root / 'build/collar-tracker.dsn'
assert k.ExportSpecctraDSN(board, str(dsn))
settings = '(autoroute_settings (autoroute on) (postroute on) (vias on)\n'
for name, active, direction in [('F.Cu', 'on', 'horizontal'), ('In1.Cu', 'off', 'horizontal'),
                                ('In2.Cu', 'off', 'horizontal'), ('B.Cu', 'on', 'vertical')]:
    settings += f' (layer_rule {name} (active {active}) (preferred_direction {direction}) (preferred_direction_trace_costs 1.0) (against_preferred_direction_trace_costs 1.5))\n'
settings += ')'
text = dsn.read_text().replace('    (boundary', '    ' + settings + '\n    (boundary', 1)
text = text.replace('(clearance 50 (type smd_smd))', '(clearance 150 (type smd_smd))')
text = text.replace('        (clearance 200)\n', '        (clearance 200)\n        (clearance 150 (type smd_smd))\n')
dsn.write_text(text)
(root / 'evidence/router-export.json').write_text(json.dumps({
    'source_sha256': hashlib.sha256(pcb.read_bytes()).hexdigest(),
    'dsn_sha256': hashlib.sha256(dsn.read_bytes()).hexdigest(),
    'ground_items_hidden': len(ground_items), 'ground_and_nc_pads_hidden': hidden_pads,
    'keepouts_added': keepout_count, 'routing_layers': ['F.Cu', 'B.Cu'],
    'scope': 'Router copy only; native manufacturing geometry unchanged.'
}, indent=2) + '\n')
print('DSN:', dsn, 'ground items hidden:', len(ground_items), 'keepouts:', keepout_count)
