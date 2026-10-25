#!/usr/bin/env python3
"""Measure reference coverage and exposed lower copper; this is not an EM solver."""
import argparse
import hashlib
import json
from pathlib import Path

from shapely import make_valid
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

PORT_NETS = {'/LTE_RF', '/LTE_ANT', '/GPS_RF', '/GNSS_ANT',
             '/GNSS_FEM_IN', '/GNSS_FEM_OUT'}
MATCHING_NETS = {'/FILT_OUT', '/AMP_IN'}


def copper(polygons):
    # KiCad saved fills may be fractured contours whose holes connect through
    # zero-area slits. Preserve holes with make_valid rather than filling them.
    return unary_union([make_valid(Polygon(p['outer'], p['holes'])) for p in polygons])


def analyze(data):
    plane = copper(data['zones'][0]['poly'])
    mismatches = [p for p in data['contains_probes']
                  if plane.covers(Point(p['pos'])) != p['inside']
                  and plane.boundary.distance(Point(p['pos'])) > 0.000002]
    assert not mismatches, 'Independent fill polygons disagree with native Contains'
    rows = []
    for t in data['tracks']:
        if t['net'] not in PORT_NETS | MATCHING_NETS:
            continue
        assert t['layer'] == 'F.Cu'
        line = LineString([t['start'], t['end']])
        shape = line.buffer(t['width']/2, quad_segs=32)
        rows.append(dict(id=t['id'], net=t['net'], width_mm=t['width'],
                         kind='50-ohm port route' if t['net'] in PORT_NETS else 'FEM interstage matching',
                         length_mm=line.length,
                         unbacked_centerline_mm=line.difference(plane).length,
                         unbacked_copper_mm2=shape.difference(plane).area))
    pads = []
    for p in data['pads']:
        shape = copper(p['poly'])
        lower = []
        for t in data['tracks']:
            if t['layer'] not in {'In2.Cu', 'In3.Cu'} or t['net'] == '/GND':
                continue
            distance = shape.distance(LineString([t['start'], t['end']]).buffer(t['width']/2))
            if distance < .2:
                lower.append(dict(id=t['id'], net=t['net'], layer=t['layer'], clearance_mm=distance))
        pads.append(dict(ref=p['ref'], pin=p['pin'], net=p['net'],
                         reference_overlap_fraction=shape.intersection(plane).area/shape.area,
                         lower_copper_within_02mm=lower))
    return dict(source_sha256=data['source_sha256'], native_contains_probes=len(data['contains_probes']),
                native_contains_disagreements=len(mismatches), tracks=rows, pads=pads,
                port_route_count=sum(r['net'] in PORT_NETS for r in rows),
                port_route_unbacked_copper_mm2=sum(r['unbacked_copper_mm2'] for r in rows if r['net'] in PORT_NETS),
                port_route_widths_mm=sorted({r['width_mm'] for r in rows if r['net'] in PORT_NETS}),
                matching_route_widths_mm=sorted({r['width_mm'] for r in rows if r['net'] in MATCHING_NETS}),
                scope='Geometric projection onto the saved In1.Cu fill. No impedance, insertion-loss, fringe-field, antenna or physical RF acceptance.',
                rf_acceptance='HOLD')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('geometry', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    data = json.loads(args.geometry.read_text())
    result = analyze(data)
    result['input_sha256'] = hashlib.sha256(args.geometry.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ['source_sha256', 'native_contains_probes',
        'native_contains_disagreements', 'port_route_widths_mm', 'port_route_unbacked_copper_mm2', 'rf_acceptance']}))


if __name__ == '__main__':
    main()
