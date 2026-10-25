"""Reserve r05l pin escapes at the unchanged 0.2 mm native clearance.

The numeric epsilon handles coordinates lying exactly on the rule boundary;
all accepted copper still requires native DRC. Historical planners are retained."""
import math
from shapely.geometry import LineString, Point, box
from power_ground_plan import paths

SIDES = ['F', 'B']
VIA_REGION = box(98.71, 98.71, 137.29, 129.29)


def reserve(ref, side, moved_pads, original_pads, copper, trees, keepouts, selected_pins=None, diagnostics=None):
    stubs, vias, added = [], [], {'F': [], 'B': []}
    existing = [(tuple(shape.centroid.coords[0]), net) for shape, net, kind in copper['F'] if kind == 'via']

    def obstacles(layer, shape, margin):
        for index in trees[layer].query(shape.buffer(margin)):
            yield copper[layer][index]
        yield from added[layer]

    def via_clear(end, net):
        point = Point(end)
        if not VIA_REGION.covers(point) or any(point.distance(pad) < .501 for pad, _ in moved_pads):
            return False
        for layer in SIDES:
            if any(point.distance(shape) < .501 for shape, other, kind in obstacles(layer, point, .51)
                   if not (kind == 'track' and other == net)):
                return False
        return not any(z['vias'] and point.distance(shape) < .501 for shape, z in keepouts)

    def line_clear(points, net, width):
        line = LineString(points)
        if not box(98.401 + width / 2, 98.401 + width / 2,
                   137.599 - width / 2, 129.599 - width / 2).covers(line):
            return False
        if any(other != net and line.distance(shape) < width / 2 + .2 - 1e-7 for shape, other in moved_pads):
            return False
        if any(z['tracks'] and z['layer'] == side + '.Cu'
               and line.distance(shape) < width / 2 + .2 - 1e-7 for shape, z in keepouts):
            return False
        for shape, other, kind in obstacles(side, line, width / 2 + .21):
            if other == net and kind != 'pad':
                continue
            if kind == 'pad' and other == net and any(n == net and shape.equals(p) for p, n in moved_pads):
                continue
            if line.distance(shape) < width / 2 + .2 - 1e-7:
                return False
        return True

    def add_via(pos, net, reason):
        vias.append({'pos': list(pos), 'net': net, 'reason': reason})
        for layer in SIDES:
            added[layer].append((Point(pos).buffer(.3), net, 'via'))

    # Ground and exposed pads first; every remaining signal must still escape.
    order = sorted(range(len(moved_pads)), key=lambda i: (moved_pads[i][1] != '/GND', -moved_pads[i][0].area))
    for index in order:
        pad, net = moved_pads[index]
        if selected_pins is not None and original_pads[index]['pin'] not in selected_pins:
            continue
        if not net or net.startswith('unconnected-'):
            continue
        start = tuple(pad.centroid.coords[0])
        power_decoupler = len(moved_pads) == 2 and any(n in {'/VDD_NRF', '/VSYS', '/VBAT', '/VIN_5V'} for _, n in moved_pads)
        width = min(.4 if power_decoupler else .2, pad.bounds[2] - pad.bounds[0], pad.bounds[3] - pad.bounds[1])
        current_vias = existing + [(tuple(v['pos']), v['net']) for v in vias]
        candidates = [(pos, True) for pos, other in current_vias if other == net and math.dist(start, pos) < 2.8]
        for radius in [.65, .8, 1, 1.2, 1.5, 1.8, 2.1, 2.4]:
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
                candidates.append(((round((start[0] + dx * radius) * 20) / 20,
                                    round((start[1] + dy * radius) * 20) / 20), False))
        if selected_pins is not None:
            # An existing control pin may need an offset via between retained
            # traces. This broader signal-only search does not relax GND limits.
            for dx in range(-14, 15):
                for dy in range(-14, 15):
                    if .6 <= math.hypot(dx / 4, dy / 4) <= 3.5:
                        candidates.append(((round((start[0] + dx / 4) * 20) / 20,
                                            round((start[1] + dy / 4) * 20) / 20), False))
        candidates.sort(key=lambda c: math.dist(start, c[0]) - (.1 if c[1] else 0))
        selected, clear_vias = None, 0
        for end, shared in candidates:
            if not shared and not via_clear(end, net):
                continue
            clear_vias += 1
            for points in paths(start, end):
                line = LineString(points)
                limit = 4.2 if selected_pins is not None and net != '/GND' else 2.2
                if line.difference(pad).length > limit or not line_clear(points, net, width):
                    continue
                selected = {'ref': ref, 'pin': original_pads[index]['pin'], 'net': net,
                            'layer': side + '.Cu', 'points': [list(p) for p in points],
                            'width': width, 'via': list(end), 'shared_via': shared,
                            'exposed_length': line.difference(pad).length}
                break
            if selected:
                break
        if selected is None:
            if diagnostics is not None:
                diagnostics.update(failed_pin=ref + '.' + original_pads[index]['pin'], clear_via_candidates=clear_vias)
            return None
        stubs.append(selected)
        added[side].append((LineString(selected['points']).buffer(width / 2), net, 'track'))
        if not selected['shared_via']:
            add_via(selected['via'], net, 'pin escape')

    # Reserve a plane-return via now if a signal transition lacks a nearby one.
    for via in list(vias):
        if via['net'] == '/GND':
            continue
        grounds = [pos for pos, net in existing if net == '/GND'] + [v['pos'] for v in vias if v['net'] == '/GND']
        if min((math.dist(via['pos'], p) for p in grounds), default=math.inf) <= 1.95:
            continue
        selected = None
        candidates = []
        for dx in range(-7, 8):
            for dy in range(-7, 8):
                if .81 <= math.hypot(dx / 4, dy / 4) <= 1.95:
                    candidates.append((round((via['pos'][0] + dx / 4) * 20) / 20,
                                       round((via['pos'][1] + dy / 4) * 20) / 20))
        for end in sorted(candidates, key=lambda p: math.dist(via['pos'], p)):
            if via_clear(end, '/GND'):
                selected = end
                break
        if selected is None:
            if diagnostics is not None:
                diagnostics.update(missing_return_for=via)
            return None
        add_via(selected, '/GND', 'local return screen')
    return stubs, vias
