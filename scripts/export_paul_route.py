#!/usr/bin/env python3
"""Export an outer-layer routing copy, with native or obstacle-model grounds.

The native board, its pad apertures and its two inner planes are not modified.
"""
import hashlib
import argparse
import json
import math
from pathlib import Path
import sys
import pcbnew as k

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('trial', type=Path)
parser.add_argument('stem', nargs='?', default='collar-tracker')
parser.add_argument('--keep-locked', action='store_true')
parser.add_argument('--protect', type=Path)
parser.add_argument('--native-pads', action='store_true')
parser.add_argument('--native-ground', action='store_true',
                    help='Keep fixed GND copper, real pad shapes and the two inner planes')
args = parser.parse_args()
root, stem = args.trial.resolve(), args.stem
assert Path(stem).name == stem, 'Use a filename stem inside the trial'
keep_locked = args.keep_locked
native_pads = args.native_pads or args.native_ground
protect_path = args.protect
protected = set(json.loads(protect_path.read_text())) if protect_path else set()
pcb = root / 'hardware/collar-tracker.kicad_pcb'
board = k.LoadBoard(str(pcb))
assert protected <= {t.m_Uuid.AsString() for t in board.GetTracks()}, 'Stale protected-route list'
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
        if args.native_ground and zone.GetLayer() in [k.In1_Cu,k.In2_Cu]:
            assert zone.GetNetname() == '/GND'
            continue
        board.Delete(zone)
ground_items = []
for track in list(board.GetTracks()):
    if track.GetNetname() != '/GND':
        continue
    if args.native_ground:
        track.SetLocked(True)
        continue
    ground_items.append(track)
    # Use the native rounded copper outline rather than square-capped boxes.
    # The 1 um conservative allowance does not change native DRC clearances.
    layers = [k.F_Cu, k.B_Cu] if track.GetClass() == 'PCB_VIA' else [track.GetLayer()]
    for layer in layers:
        poly = k.SHAPE_POLY_SET()
        track.TransformShapeToPolygon(poly, layer, 1000, 1000, k.ERROR_OUTSIDE)
        for index in range(poly.OutlineCount()):
            outline = poly.COutline(index)
            keepout([xy(outline.CPoint(i)) for i in range(outline.PointCount())], layer)

for item in ground_items:
    board.Delete(item)
hidden_pads = 0
for footprint in board.GetFootprints():
    for pad in footprint.Pads():
        if not args.native_ground and (pad.GetNetname() == '/GND' or pad.GetNetname().startswith('unconnected-') or not pad.GetNetname()):
            pad.SetNetCode(0)
            bb = pad.GetBoundingBox()
            points = [(bb.GetLeft()/1e6, bb.GetTop()/1e6), (bb.GetRight()/1e6, bb.GetTop()/1e6),
                      (bb.GetRight()/1e6, bb.GetBottom()/1e6), (bb.GetLeft()/1e6, bb.GetBottom()/1e6)]
            for layer in [k.F_Cu, k.B_Cu]:
                if pad.IsOnLayer(layer):
                    keepout(points, layer)
            hidden_pads += 1
        elif not native_pads and pad.GetShape() in [k.PAD_SHAPE_ROUNDRECT, k.PAD_SHAPE_OVAL, k.PAD_SHAPE_CIRCLE]:
            pad.SetShape(k.PAD_SHAPE_RECT)
# Permit rip-up/optimization of signal routes in the exported copy only.
# Native GND is represented by obstacles; exact RF is restored by the importer.
rf_nets = {'/LTE_RF','/LTE_ANT','/GPS_RF','/GNSS_ANT','/GNSS_FEM_IN','/GNSS_FEM_OUT','/FILT_OUT','/AMP_IN'}
for track in board.GetTracks():
    if track.GetNetname() in rf_nets or args.native_ground and track.GetNetname() == '/GND':
        track.SetLocked(True)
    elif not keep_locked:
        track.SetLocked(track.m_Uuid.AsString() in protected)
dsn = root / f'build/{stem}.dsn'
assert k.ExportSpecctraDSN(board, str(dsn))
settings = '(autoroute_settings (autoroute on) (postroute on) (vias on)\n'
for name, active, direction in [('F.Cu', 'on', 'horizontal'), ('In1.Cu', 'off', 'horizontal'),
                                ('In2.Cu', 'off', 'horizontal'), ('B.Cu', 'on', 'vertical')]:
    settings += f' (layer_rule {name} (active {active}) (preferred_direction {direction}) (preferred_direction_trace_costs 1.0) (against_preferred_direction_trace_costs 1.5))\n'
settings += ')'
text = dsn.read_text().replace('    (boundary', '    ' + settings + '\n    (boundary', 1)
# Freerouting treats an unknown wiring type as USER_FIXED. KiCad's "route"
# token is not its "normal" token, even when the native track was unlocked.
# Keep "fix" items protected and make the intended movable routes explicit.
text = text.replace('(type route)', '(type normal)')
text = text.replace('(clearance 50 (type smd_smd))', '(clearance 150 (type smd_smd))')
text = text.replace('        (clearance 200)\n', '        (clearance 200)\n        (clearance 150 (type smd_smd))\n')
dsn.write_text(text)
(root / f'evidence/{stem}-export.json').write_text(json.dumps({
    'source_sha256': hashlib.sha256(pcb.read_bytes()).hexdigest(),
    'dsn_sha256': hashlib.sha256(dsn.read_bytes()).hexdigest(),
    'ground_items_hidden': len(ground_items), 'ground_and_nc_pads_hidden': hidden_pads,
    'keepouts_added': keepout_count, 'routing_layers': ['F.Cu', 'B.Cu'],
    'preserve_native_locks':keep_locked,
    'movable_route_type':'normal',
    'ground_model':'fixed native copper and inner planes' if args.native_ground else 'copper obstacles',
    'pad_model':'native KiCad DSN export' if native_pads else 'conservative rectangles',
    'explicitly_protected_route_items':len(protected),
    'retained_native_route_ids':sorted(t.m_Uuid.AsString() for t in board.GetTracks() if t.IsLocked()),
    'scope': 'Router copy only; native manufacturing geometry unchanged.'
}, indent=2) + '\n')
print('DSN:', dsn, 'ground items hidden:', len(ground_items), 'keepouts:', keepout_count)
