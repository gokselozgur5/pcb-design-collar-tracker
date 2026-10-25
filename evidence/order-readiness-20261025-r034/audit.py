#!/usr/bin/env python3
"""Read-only native-board measurements; run with scripts/kicad-python.

2 mm is the old GIMP screening target, not an RF acceptance specification.
This script never refills, saves, reroutes or edits the source board.
"""
import collections
import csv
import hashlib
import json
import math
from pathlib import Path

import pcbnew as k

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
manifest = json.loads((ROOT / 'release/collar-tracker-0.3.4-verification.json').read_text())
source = Path(manifest['source'])
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(source) == manifest['source_sha256']
assert sha(manifest['zip']) == manifest['zip_sha256']
b = k.LoadBoard(str(source))
xy = lambda v: (v.x / 1e6, v.y / 1e6)
footprints = list(b.GetFootprints())
pads = [p for f in footprints for p in f.Pads()]
tracks = [t for t in b.GetTracks() if t.GetClass() != 'PCB_VIA']
vias = [v for v in b.GetTracks() if v.GetClass() == 'PCB_VIA']
ground_vias = [v for v in vias if v.GetNetname() == '/GND']
ground_pads = [p for p in pads if p.GetNetname() == '/GND']
zones = [z for z in b.Zones() if not z.GetIsRuleArea()]

returns = []
for v in vias:
    if v.GetNetname() == '/GND':
        continue
    nearest = min(ground_vias, key=lambda g: math.dist(xy(v.GetPosition()), xy(g.GetPosition())))
    returns.append(dict(uuid=v.m_Uuid.AsString(), net=v.GetNetname(), pos_mm=xy(v.GetPosition()),
                        nearest_ground_via=nearest.m_Uuid.AsString(),
                        nearest_ground_pos_mm=xy(nearest.GetPosition()),
                        nearest_mm=math.dist(xy(v.GetPosition()), xy(nearest.GetPosition()))))
returns.sort(key=lambda v: v['nearest_mm'], reverse=True)

zone_rows = []
for z in zones:
    poly = z.GetFilledPolysList(z.GetLayer())
    zone_rows.append(dict(layer=b.GetLayerName(z.GetLayer()), net=z.GetNetname(),
                          connection_mode=int(z.GetPadConnection()),
                          filled_outlines=poly.OutlineCount(),
                          ground_via_centers_in_fill=sum(poly.Contains(v.GetPosition()) for v in ground_vias)))

nrf_ground_pins = {str(n) for n in [1, 7, 13, 15, 20, 25, 30, 34, 36, 38, 39, 40, 41,
                                   43, 46, 51, 55, 60, 66, 71, 76, *range(105, 114)]}
u1 = next(f for f in footprints if f.GetReference() == 'U1')
actual_nrf_ground_pins = {p.GetNumber() for p in u1.Pads() if p.GetNetname() == '/GND'}
rows = list(csv.DictReader((ROOT / 'hardware/bom.csv').open()))
contacts = [r for r in rows if r['status'].startswith('onboard contact')]
fitted = [r for r in rows if r['dnp'] == 'False' and r not in contacts]
fitted_refs = {r['ref'] for r in fitted}
power_nets = ['/VIN_5V', '/VBAT', '/VSYS', '/VDD_NRF', '/VIO_1V8']
power = {net: dict(widths_mm=sorted({t.GetWidth()/1e6 for t in tracks if t.GetNetname() == net}),
                   segment_count=sum(t.GetNetname() == net for t in tracks)) for net in power_nets}
drc = json.loads((OUT / 'drc.json').read_text())
erc = json.loads((OUT / 'erc.json').read_text())

report = dict(
    source=str(source), source_sha256=sha(source), zip=manifest['zip'], zip_sha256=sha(manifest['zip']),
    copper_layers=b.GetCopperLayerCount(), thickness_mm=b.GetDesignSettings().GetBoardThickness()/1e6,
    footprints=len(footprints), footprint_sides=dict(collections.Counter(b.GetLayerName(f.GetLayer()) for f in footprints)),
    fitted_sides=dict(collections.Counter(b.GetLayerName(f.GetLayer()) for f in footprints if f.GetReference() in fitted_refs)),
    pads=len(pads), ground_pads=len(ground_pads), vias=len(vias), ground_vias=len(ground_vias),
    tracks=len(tracks), tracks_by_layer=dict(collections.Counter(b.GetLayerName(t.GetLayer()) for t in tracks)),
    min_track_width_mm=min(t.GetWidth()/1e6 for t in tracks), power_tracks=power,
    ground_track_segments=sum(t.GetNetname() == '/GND' for t in tracks),
    ground_track_total_length_mm=sum(math.dist(xy(t.GetStart()), xy(t.GetEnd())) for t in tracks if t.GetNetname() == '/GND'),
    zones=zone_rows, ground_pad_local_connection_modes=dict(collections.Counter(str(p.GetLocalZoneConnection()) for p in ground_pads)),
    nrf_ground_pin_numbers_match_official_list=actual_nrf_ground_pins == nrf_ground_pins,
    nrf_ground_pin_count=len(actual_nrf_ground_pins),
    ground_pin_reference='https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/gnd.html',
    return_screen=dict(target_mm=2, target_origin='GIMP tools/return_vias.py; not a universal EMI/RF acceptance threshold',
                       non_ground_vias=len(returns), within_target=sum(v['nearest_mm'] <= 2 for v in returns),
                       outside_target=sum(v['nearest_mm'] > 2 for v in returns), maximum_mm=max(v['nearest_mm'] for v in returns),
                       items=returns),
    bom=dict(entries=len(rows), fitted=len(fitted), contacts=len(contacts), dnp=sum(r['dnp']=='True' for r in rows),
             missing_exact_mpn=[r['ref'] for r in fitted if not r['mpn']]),
    native_checks=dict(drc_violations=len(drc['violations']), opens=len(drc['unconnected_items']),
                       parity=len(drc['schematic_parity']), erc_violations=sum(len(s['violations']) for s in erc['sheets']),
                       drc_ignored=drc['ignored_checks'], erc_ignored=erc['ignored_checks']),
    limitations=['No analog, thermal, RF impedance, EMC or powered validation.',
                 'Distance screening is Euclidean via-to-via, not a solved return-current path.',
                 'Ground via centers lie in saved filled zones; DRC checks netlist opens independently.',
                 'Only nRF ground pin membership was cross-checked with a manufacturer pin list in this audit.',
                 'Solid zone connections and remaining routed ground require assembly/return review; counts are not defect counts.'])
assert sha(source) == manifest['source_sha256'], 'Source changed during read-only audit'
assert sha(manifest['zip']) == manifest['zip_sha256'], 'Release ZIP changed during audit'
(OUT / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: report[key] for key in ['copper_layers', 'tracks_by_layer', 'ground_pads', 'ground_vias',
                                              'nrf_ground_pin_numbers_match_official_list', 'fitted_sides']}))
print(json.dumps({key: value for key, value in report['return_screen'].items() if key != 'items'}))
