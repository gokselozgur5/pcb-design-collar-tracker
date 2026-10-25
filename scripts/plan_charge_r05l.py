#!/usr/bin/env python3
"""Place r05l charge additions with full pin escapes; retain all existing parts."""
import hashlib
import json
from pathlib import Path
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree
from charge_pin_exits import reserve

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05l-charge-interlock'


def poly(polygons):
    return unary_union([Polygon(p) for p in polygons]).buffer(0)


def run():
    source = TRIAL / 'evidence/placement-input.json'
    data = json.loads(source.read_text())
    pcb = TRIAL / 'hardware/collar-tracker.kicad_pcb'
    assert data['source_sha256'] == hashlib.sha256(pcb.read_bytes()).hexdigest()
    target = TRIAL / 'evidence/placement-plan.json'
    assert not target.exists(), 'Preserve earlier placement evidence'
    bodies, copper = {s: [] for s in ['F', 'B']}, {s: [] for s in ['F', 'B']}
    for footprint in data['footprints'].values():
        if footprint['movable']:
            continue
        body = poly(footprint['courtyards']) if footprint['courtyards'] else unary_union([
            poly(p['poly']) for p in footprint['pads']]).convex_hull.buffer(.25)
        bodies[footprint['side']].append(body)
        copper[footprint['side']].extend((poly(p['poly']), p['net'], 'pad') for p in footprint['pads'])
    bodies['F'].append(box(118, 110, 131, 124))
    bodies['B'].append(box(122, 98, 132, 115))
    for t in data['tracks']:
        copper[t['side']].append((LineString([t['start'], t['end']]).buffer(t['width'] / 2), t['net'], 'track'))
    for v in data['vias']:
        for side in ['F', 'B']:
            copper[side].append((Point(v['pos']).buffer(v['diameter'] / 2), v['net'], 'via'))
    keepouts = [(Polygon(p), z) for z in json.loads((TRIAL / 'evidence/placement-extra.json').read_text())['keepouts'] for p in z['poly']]
    anchors = {
        'U10': (111, 102, 'F'), 'U11': (117, 102, 'F'), 'U12': (110, 114, 'B'),
        'C31': (111, 104, 'F'), 'C32': (117, 104, 'F'), 'C33': (110, 116, 'B'),
        'C34': (109, 102, 'F'), 'C35': (115, 102, 'F'), 'C36': (106, 120, 'B'),
        'R24': (109, 104, 'F'), 'R25': (109, 105, 'F'), 'R26': (115, 104, 'F'),
        'R27': (115, 105, 'F'), 'R28': (108, 116, 'B'),
        'R29': (110, 112, 'B'), 'R30': (112, 112, 'B')}
    order = ['U10', 'C31', 'C34', 'R24', 'R25', 'U11', 'C32', 'C35',
             'R26', 'R27', 'U12', 'C33', 'R28', 'R29', 'R30', 'C36']
    inside = box(98.4, 98.4, 137.6, 129.6)
    placements, searched, all_stubs, all_vias = {}, {}, [], []
    # These existing pins changed nets. Reserve their original-position exits
    # before moving new parts into any available space beside them.
    for ref, pins in []:
        f = data['footprints'][ref]
        moved_pads = [(poly(p['poly']), p['net']) for p in f['pads']]
        trees = {side: STRtree([c[0] for c in copper[side]]) for side in ['F', 'B']}
        diagnostics = {}
        exits = reserve(ref, f['side'], moved_pads, f['pads'], copper, trees, keepouts, selected_pins=pins, diagnostics=diagnostics)
        if exits is None:
            raise RuntimeError('Changed original pin has no reserved escape: ' + str(diagnostics))
        stubs, vias = exits
        for stub in stubs:
            copper[f['side']].append((LineString(stub['points']).buffer(stub['width'] / 2), stub['net'], 'track'))
        for via in vias:
            for side in ['F', 'B']:
                copper[side].append((Point(via['pos']).buffer(.3), via['net'], 'via'))
        all_stubs.extend(stubs)
        all_vias.extend(vias)
        print('fixed pin', ref, sorted(pins), 'reserved', flush=True)
    for ref in order:
        f = data['footprints'][ref]
        assert f['movable'] and f['side'] == 'F' and f['angle'] == 0
        ox, oy = f['pos']
        body = affinity.translate(poly(f['courtyards']), -ox, -oy)
        pads = [(affinity.translate(poly(p['poly']), -ox, -oy), p['net']) for p in f['pads']]
        ax, ay, preferred = anchors[ref]
        owner = {'C31':'U10','C34':'U10','R24':'U10','R25':'U10',
                 'C32':'U11','C35':'U11','R26':'U11','R27':'U11',
                 'C33':'U12','R28':'U12','R29':'U12','R30':'U12'}.get(ref)
        if owner in placements:
            ax, ay, _, preferred = placements[owner]
        variants = {}
        for side in ['F', 'B']:
            for angle in [0, 90, 180, 270]:
                def transform(p):
                    return affinity.rotate(affinity.scale(p, xfact=1, yfact=-1 if side == 'B' else 1, origin=(0, 0)), -angle, origin=(0, 0))
                variants[side, angle] = transform(body), [(transform(p), n) for p, n in pads]
        positions = sorted(((x / 4 - ax) ** 2 + (y / 4 - ay) ** 2 + (0 if side == preferred else 25), x / 4, y / 4, side)
                           for side in ['F', 'B'] for x in range(395, 549) for y in range(395, 517))
        body_union = {side: unary_union(bodies[side]) for side in ['F', 'B']}
        trees = {side: STRtree([c[0] for c in copper[side]]) for side in ['F', 'B']}
        count, selected = 0, None
        for _, x, y, side in positions:
            for angle in [0, 90, 180, 270]:
                count += 1
                local_body, local_pads = variants[side, angle]
                moved_body = affinity.translate(local_body, x, y)
                if not inside.covers(moved_body) or moved_body.buffer(.055).intersects(body_union[side]):
                    continue
                moved_pads = [(affinity.translate(p, x, y), n) for p, n in local_pads]
                if any((kind == 'via' or net != other) and pad.distance(shape) < .2005
                       for pad, net in moved_pads for idx in trees[side].query(pad.buffer(.205))
                       for shape, other, kind in [copper[side][idx]]):
                    continue
                exits = reserve(ref, side, moved_pads, f['pads'], copper, trees, keepouts)
                if exits is None:
                    continue
                stubs, vias = exits
                selected = [x, y, angle, side]
                placements[ref], searched[ref] = selected, count
                bodies[side].append(moved_body)
                copper[side].extend((p, n, 'pad') for p, n in moved_pads)
                for stub in stubs:
                    copper[side].append((LineString(stub['points']).buffer(stub['width'] / 2), stub['net'], 'track'))
                for via in vias:
                    for layer in ['F', 'B']:
                        copper[layer].append((Point(via['pos']).buffer(.3), via['net'], 'via'))
                all_stubs.extend(stubs)
                all_vias.extend(vias)
                print(ref, selected, 'candidates', count, 'pin exits', len(stubs), flush=True)
                break
            if selected:
                break
        if selected is None:
            raise RuntimeError('No full-pin placement for ' + ref + '; preserve source and review the failed constraints')
        # Partial evidence is recoverable if a later component needs a new search.
        report = {'source_sha256': data['source_sha256'], 'placement_input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                  'placements': placements, 'candidate_counts': searched, 'stubs': all_stubs, 'vias': all_vias,
                  'complete': len(placements) == len(order),
                  'scope': 'Full-pin escape reservation. Native DRC, routing, RF/assembly and populated fit remain pending.'}
        (TRIAL / 'evidence/placement-progress.json').write_text(json.dumps(report, indent=2) + '\n')
    target.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    run()
