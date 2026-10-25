"""Reserve short GND connections during placement, before later parts can block them."""
import math
from shapely.geometry import LineString, Point, box


def paths(start, end):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = min(abs(dx), abs(dy))
    sx, sy = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
    for middle in [(start[0] + sx * length, start[1] + sy * length),
                   (end[0] - sx * length, end[1] - sy * length)]:
        points = [start]
        for p in [middle, end]:
            if math.dist(points[-1], p) > 1e-8:
                points.append(p)
        if len(points) > 1:
            yield points


def reserve(ref, side, moved_pads, original_pads, copper, trees, keepouts):
    stubs, added_vias = [], []
    existing = [tuple(shape.centroid.coords[0]) for shape, net, kind in copper['F']
                if kind == 'via' and net == '/GND']
    for index, (shape, net) in enumerate(moved_pads):
        if net != '/GND':
            continue
        start = tuple(shape.centroid.coords[0])
        # Balance simple power decouplers; use the pad's physical width bound.
        power = len(moved_pads) == 2 and any(n in ['/VDD_NRF', '/VSYS', '/VBAT', '/VIN_5V'] for _, n in moved_pads)
        width = min(.4 if power else .2, shape.bounds[2] - shape.bounds[0], shape.bounds[3] - shape.bounds[1])
        candidates = [(v, True) for v in existing + added_vias if math.dist(start, v) < 2.8]
        for radius in [.65, .8, 1, 1.2, 1.5, 1.8, 2.1, 2.4]:
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
                candidates.append(((round((start[0] + dx * radius) * 20) / 20,
                                    round((start[1] + dy * radius) * 20) / 20), False))
        candidates.sort(key=lambda c: math.dist(start, c[0]) - (.12 if c[1] else 0))
        selected = None
        for end, shared in candidates:
            point = Point(end)
            if not box(98.71, 98.71, 137.29, 129.29).covers(point):
                continue
            if not shared:
                if any(point.distance(p) < .501 for p, _ in moved_pads):
                    continue
                if any(math.dist(end, v) < .801 for v in added_vias):
                    continue
                blocked = False
                for layer in ['F', 'B']:
                    for j in trees[layer].query(point.buffer(.51)):
                        obstacle, other_net, kind = copper[layer][j]
                        if kind == 'track' and other_net == '/GND':
                            continue
                        if point.distance(obstacle) < .501:
                            blocked = True
                            break
                    if blocked:
                        break
                if blocked or any(z['vias'] and point.distance(p) < .501 for p, z in keepouts):
                    continue
            for points in paths(start, end):
                line = LineString(points)
                if line.difference(shape).length > 2.2:
                    continue
                if not box(98.4 + width / 2, 98.4 + width / 2,
                           137.6 - width / 2, 129.6 - width / 2).covers(line):
                    continue
                if any(n != '/GND' and line.distance(p) < width / 2 + .201 for p, n in moved_pads):
                    continue
                if any(z['tracks'] and z['layer'] == side + '.Cu' and
                       line.distance(p) < width / 2 + .201 for p, z in keepouts):
                    continue
                blocked = False
                for j in trees[side].query(line.buffer(width / 2 + .21)):
                    obstacle, other_net, kind = copper[side][j]
                    # GND tracks/vias are connections. Other component pads are
                    # not used as intermediate nodes, even on the same net.
                    if other_net == '/GND' and kind != 'pad':
                        continue
                    if line.distance(obstacle) < width / 2 + .201:
                        blocked = True
                        break
                if not blocked:
                    selected = {'ref': ref, 'pin': original_pads[index]['pin'],
                                'layer': side + '.Cu', 'points': [list(p) for p in points],
                                'width': width, 'length': line.length,
                                'exposed_length': line.difference(shape).length,
                                'shared_via': shared, 'via': list(end)}
                    break
            if selected:
                break
        if selected is None:
            return None
        stubs.append(selected)
        if not selected['shared_via']:
            added_vias.append(tuple(selected['via']))
    return stubs, added_vias
