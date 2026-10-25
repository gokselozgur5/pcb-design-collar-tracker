#!/usr/bin/env python3
"""Place only r05 additions against actual courtyard and copper geometry.

Uses Shapely. The planner does not modify the board or certify RF/mechanical fit.
Candidate pad positions avoid retained copper; native DRC remains authoritative.
"""
import hashlib
import json
from pathlib import Path
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree
from power_ground_plan import reserve

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05-supervised'


def poly(items):
    return unary_union([Polygon(p) for p in items]).buffer(0)


def run():
    path = TRIAL / 'evidence/placement-input.json'
    data = json.loads(path.read_text())
    seed = TRIAL / 'build/seed-before-placement.kicad_pcb'
    board = seed if seed.exists() else TRIAL / 'hardware/collar-tracker.kicad_pcb'
    assert data['source_sha256'] == hashlib.sha256(board.read_bytes()).hexdigest()
    bodies = {'F': [], 'B': []}
    copper = {'F': [], 'B': []}
    for f in data['footprints'].values():
        if f['movable']:
            continue
        body = poly(f['courtyards']) if f['courtyards'] else unary_union([
            poly(p['poly']) for p in f['pads']]).convex_hull.buffer(.25)
        bodies[f['side']].append(body)
        copper[f['side']] += [(poly(p['poly']), p['net'], 'pad') for p in f['pads']]
    # Keep new components out of the RF section and the SIM insertion volume.
    bodies['F'].append(box(118, 110, 131, 124))
    bodies['B'].append(box(122, 98, 132, 115))
    for t in data['tracks']:
        copper[t['side']].append((LineString([t['start'], t['end']]).buffer(t['width'] / 2), t['net'], 'track'))
    for v in data['vias']:
        shape = Point(v['pos']).buffer(v['diameter'] / 2)
        for side in ['F', 'B']:
            copper[side].append((shape, v['net'], 'via'))
    anchors = {
        'U6': (110, 101, 'F'), 'U7': (116, 101, 'F'),
        'U8': (117, 103.5, 'B'), 'Q1': (117, 107.5, 'B'),
        'U9': (111, 113, 'B'), 'C9': (101.8, 113.7, 'B'),
        'C25': (110, 104.5, 'F'), 'C26': (118, 104, 'F'),
        'C27': (108, 101, 'F'), 'C28': (114, 99, 'F'),
        'C29': (117, 101, 'B'), 'C30': (109, 113, 'B'),
        'R16': (108, 99, 'F'), 'R17': (110, 99, 'F'), 'R18': (112, 99, 'F'),
        'R19': (113, 103, 'F'), 'R20': (118, 99, 'F'),
        'R21': (117, 110, 'B'), 'R22': (117, 105.5, 'B'), 'R23': (113, 115.5, 'B')}
    order = ['U6', 'U7', 'U9', 'U8', 'Q1', 'C9', 'C25', 'C27', 'C28', 'C26',
             'C29', 'C30', 'R16', 'R17', 'R18', 'R19', 'R20', 'R21', 'R22', 'R23']
    inside = box(98.4, 98.4, 137.6, 129.6)
    extra = json.loads((TRIAL / 'evidence/placement-extra.json').read_text())
    keepouts = [(Polygon(p), z) for z in extra['keepouts'] for p in z['poly']]
    placements, searched, ground_stubs, ground_vias = {}, {}, [], []
    for ref in order:
        f = data['footprints'][ref]
        assert f['movable'] and f['side'] == 'F' and f['angle'] == 0
        ox, oy = f['pos']
        body = affinity.translate(poly(f['courtyards']), -ox, -oy)
        pads = [(affinity.translate(poly(p['poly']), -ox, -oy), p['net']) for p in f['pads']]
        ax, ay, preference = anchors[ref]
        variants = {}
        for side in ['F', 'B']:
            for angle in [0, 90, 180, 270]:
                transform = lambda p: affinity.rotate(
                    affinity.scale(p, xfact=1, yfact=-1 if side == 'B' else 1, origin=(0, 0)),
                    -angle, origin=(0, 0))
                variants[(side, angle)] = (transform(body), [(transform(p), n) for p, n in pads])
        positions = []
        for side in ['F', 'B']:
            for ix in range(395, 549):
                for iy in range(395, 517):
                    x, y = ix / 4, iy / 4
                    cost = (x - ax) ** 2 + (y - ay) ** 2 + (0 if side == preference else 36)
                    positions.append((cost, x, y, side))
        positions.sort()
        body_union = {s: unary_union(bodies[s]) for s in ['F', 'B']}
        trees = {s: STRtree([v[0] for v in copper[s]]) for s in ['F', 'B']}
        count, found = 0, False
        for _, x, y, side in positions:
            for angle in [0, 90, 180, 270]:
                count += 1
                local_body, local_pads = variants[(side, angle)]
                moved_body = affinity.translate(local_body, x, y)
                if not inside.covers(moved_body) or moved_body.buffer(.055).intersects(body_union[side]):
                    continue
                moved_pads, ok = [], True
                for p, net in local_pads:
                    moved = affinity.translate(p, x, y)
                    # Via-in-pad is disallowed even on the same net. Same-net
                    # surface copper can be retained without manufacturing shorts.
                    for idx in trees[side].query(moved.buffer(.205)):
                        other, other_net, kind = copper[side][idx]
                        if (kind == 'via' or net != other_net) and moved.distance(other) < .2005:
                            ok = False
                            break
                    if not ok:
                        break
                    moved_pads.append((moved, net))
                if not ok:
                    continue
                ground = reserve(ref, side, moved_pads, f['pads'], copper, trees, keepouts)
                if ground is None:
                    continue
                stubs, vias = ground
                placements[ref] = [x, y, angle, side]
                bodies[side].append(moved_body)
                copper[side].extend((p, net, 'pad') for p, net in moved_pads)
                for stub in stubs:
                    copper[side].append((LineString(stub['points']).buffer(stub['width'] / 2), '/GND', 'track'))
                for via in vias:
                    for layer in ['F', 'B']:
                        copper[layer].append((Point(via).buffer(.3), '/GND', 'via'))
                ground_stubs.extend(stubs)
                ground_vias.extend(vias)
                searched[ref] = count
                print(ref, placements[ref], 'candidates', count, flush=True)
                found = True
                break
            if found:
                break
        if not found:
            raise RuntimeError('No feasible placement for ' + ref + '; retain earlier result and review constraints')
    report = {'source_sha256': data['source_sha256'], 'placement_input_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'placements': placements, 'candidate_counts': searched, 'bounds_mm': data['bounds_mm'],
              'ground_stubs': ground_stubs, 'ground_vias': ground_vias,
              'scope': 'Courtyard/copper screen only. Native DRC, local ground returns, full routing, populated enclosure and RF review are still required.'}
    (TRIAL / 'evidence/placement-plan.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    run()
