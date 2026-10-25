#!/usr/bin/env python3
"""Estimate actual copper path resistance; never substitute for powered tests.

Run with geometry Python after exporting current route-geometry.json. The graph
uses real track widths, centerline lengths, via barrels and touching pad copper.
Pad/current-spreading resistance and component/contact resistance are omitted.
Results are estimates for the stated copper assumptions, not certified limits.
"""
import argparse
import collections
import hashlib
import heapq
import itertools
import json
import math
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import nearest_points, unary_union


def make_graph(geometry, net, copper_um, plating_um, thickness_mm):
    tracks = [dict(t, line=LineString([t['start'], t['end']]))
              for t in geometry['tracks'] if t['net'] == net]
    pads = [p for p in geometry['pads'] if p['net'] == net and p['pin']]
    vias = [v for v in geometry['vias'] if v['net'] == net]
    cuts = [{0.0, t['line'].length} for t in tracks]
    joins = []
    terminal_nodes = {}
    # Connect actual copper intersections. A short ideal junction models each
    # overlap; it does not assign a fictitious resistance to a component pad.
    for i, a in enumerate(tracks):
        for j, b in enumerate(tracks[:i]):
            if a['layer'] != b['layer']:
                continue
            if a['line'].distance(b['line']) > (a['width'] + b['width']) / 2 + 1e-6:
                continue
            pa, pb = nearest_points(a['line'], b['line'])
            da, db = a['line'].project(pa), b['line'].project(pb)
            cuts[i].add(da); cuts[j].add(db)
            joins.append(((i, da), (j, db)))
    for pad in pads:
        terminal = ('pad', pad['id'])
        terminal_nodes[(pad['ref'], pad['pin'])] = terminal
        poly = unary_union([Polygon(p) for p in pad['poly']])
        for i, t in enumerate(tracks):
            if t['layer'] not in pad['layers']:
                continue
            if t['line'].distance(poly) <= t['width'] / 2 + 1e-6:
                p, _ = nearest_points(t['line'], poly)
                distance = t['line'].project(p)
                cuts[i].add(distance)
                joins.append(((i, distance), terminal))
    for via in vias:
        for i, t in enumerate(tracks):
            if t['layer'] not in via['layers']:
                continue
            center = Point(via['pos'])
            if t['line'].distance(center) <= (via['diameter'] + t['width']) / 2 + 1e-6:
                distance = t['line'].project(center)
                cuts[i].add(distance)
                joins.append(((i, distance), ('via', via['id'], t['layer'])))
        for pad in pads:
            poly = unary_union([Polygon(p) for p in pad['poly']])
            if Point(via['pos']).distance(poly) <= via['diameter'] / 2 + 1e-6:
                for layer in set(pad['layers']) & set(via['layers']):
                    joins.append((('via', via['id'], layer), ('pad', pad['id'])))
    graph = collections.defaultdict(list)
    def add(a, b, ohms, metadata):
        graph[a].append((b, ohms, metadata)); graph[b].append((a, ohms, metadata))
    rho = 1.724e-8  # Copper resistivity at 20 C, ohm metres.
    for i, t in enumerate(tracks):
        distances = sorted(cuts[i])
        for a, b in zip(distances, distances[1:]):
            length = b - a
            resistance = rho * length * 1e-3 / (t['width'] * 1e-3 * copper_um * 1e-6)
            add((i, a), (i, b), resistance,
                dict(kind='track', id=t['id'], length_mm=length,
                     width_mm=t['width'], layer=t['layer']))
    for a, b in joins:
        add(a, b, 0, dict(kind='ideal_copper_junction'))
    for via in vias:
        # Full board thickness is conservative for an F.Cu to B.Cu transition.
        diameter = via['drill'] * 1e-3
        plating = plating_um * 1e-6
        area = math.pi * ((diameter / 2 + plating) ** 2 - (diameter / 2) ** 2)
        resistance = rho * thickness_mm * 1e-3 / area
        add(('via', via['id'], 'F.Cu'), ('via', via['id'], 'B.Cu'), resistance,
            dict(kind='via', id=via['id'], drill_mm=via['drill']))
    return graph, terminal_nodes


def path(graph, start, end):
    serial = itertools.count()
    queue = [(0, next(serial), start)]
    distances = {start: 0}; previous = {}
    while queue:
        cost, _, node = heapq.heappop(queue)
        if cost != distances[node]:
            continue
        if node == end:
            steps = []
            while node != start:
                node, edge_cost, metadata = previous[node]
                if edge_cost:
                    steps.append(dict(metadata, ohms=edge_cost))
            return cost, list(reversed(steps))
        for other, edge_cost, metadata in graph[node]:
            new = cost + edge_cost
            if new < distances.get(other, math.inf):
                distances[other] = new
                previous[other] = (node, edge_cost, metadata)
                heapq.heappush(queue, (new, next(serial), other))
    return None, []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trial', type=Path)
    parser.add_argument('--copper-um', type=float, default=35)
    parser.add_argument('--plating-um', type=float, default=20)
    parser.add_argument('--thickness-mm', type=float, default=.8)
    args = parser.parse_args()
    pcb = args.trial / 'hardware/collar-tracker.kicad_pcb'
    geometry = json.loads((args.trial / 'evidence/route-geometry.json').read_text())
    assert geometry['source_sha256'] == hashlib.sha256(pcb.read_bytes()).hexdigest(), 'Stale geometry'
    assert min(args.copper_um, args.plating_um, args.thickness_mm) > 0
    pairs = [('/VIN_5V', ('J3', '1'), ('U3', '10'), .5),
             ('/VBAT', ('J4', '1'), ('U3', '2'), 1.0),
             ('/VSYS', ('U3', '1'), ('FB1', '1'), 1.0),
             ('/VSYS', ('U3', '1'), ('J5', '3'), None),
             ('/VDD_NRF', ('FB1', '2'), ('U1', '14'), 1.0),
             ('/VDD_NRF', ('C3', '1'), ('U1', '14'), 1.0),
             ('/VDD_NRF', ('C4', '1'), ('U1', '14'), 1.0),
             ('/VSYS', ('U3', '1'), ('U4', '1'), None),
             ('/VSYS', ('C20', '1'), ('U4', '1'), None),
             ('/VIO_1V8', ('U4', '5'), ('U5', '9'), None),
             ('/VIO_1V8', ('U4', '5'), ('J5', '2'), None),
             ('/VIO_1V8', ('C21', '1'), ('U4', '5'), None)]
    rows = []
    for net, start, end, current in pairs:
        graph, terminals = make_graph(geometry, net, args.copper_um, args.plating_um, args.thickness_mm)
        resistance, steps = path(graph, terminals[start], terminals[end])
        tracks = [s for s in steps if s['kind'] == 'track']
        rows.append(dict(net=net, start='.'.join(start), end='.'.join(end), connected=resistance is not None,
                         estimated_ohms_20C=resistance, design_case_A=current,
                         estimated_drop_mV=None if resistance is None or current is None else current*resistance*1000,
                         track_length_mm=sum(s['length_mm'] for s in tracks),
                         narrow_length_mm=sum(s['length_mm'] for s in tracks if s['width_mm'] < .399),
                         widths_mm=sorted({s['width_mm'] for s in tracks}),
                         vias=sum(s['kind'] == 'via' for s in steps), steps=steps))
    report = dict(source_sha256=geometry['source_sha256'],
                  assumptions=dict(copper_um=args.copper_um, plating_um=args.plating_um,
                                   thickness_mm=args.thickness_mm, temperature_C=20,
                                   current_note='1 A is a design case, not a measured or specified modem peak. The auxiliary-port load is unspecified.'),
                  scope='Centerline DCR estimate with ideal pad/junction spreading. Excludes cell, ferrite, IC, contacts, temperature rise and dynamic impedance. Not bench or thermal acceptance.',
                  paths=rows)
    (args.trial / 'evidence/power-path-review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps([{k:v for k,v in row.items() if k != 'steps'} for row in rows], indent=2))


if __name__ == '__main__':
    main()
