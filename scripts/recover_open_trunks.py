#!/usr/bin/env python3
"""Recover clear original trunk pieces only on still-open nets of a joint trial.

Plan with geometry Python, then apply with KiCad Python. Source hashes guard
both stages. Neither stage establishes native DRC or supplier acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def plan(args):
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import unary_union
    from shapely.strtree import STRtree
    current = json.loads((args.trial / 'evidence/route-geometry.json').read_text())
    original = json.loads((args.reference / 'evidence/route-geometry.json').read_text())
    assert current['source_sha256'] == sha(args.trial / 'hardware/collar-tracker.kicad_pcb')
    assert original['source_sha256'] == sha(args.reference / 'hardware/collar-tracker.kicad_pcb')
    drc = json.loads(args.drc.read_text())
    nets = {re.search(r'\[([^]]+)\]', x['items'][0]['description'])[1] for x in drc['unconnected_items']}
    assert '/GND' not in nets
    removed = {r['id'] for r in json.loads((args.trial / 'evidence/trunk-removal.json').read_text())['removed']}
    keepouts = json.loads((args.trial / 'evidence/placement-extra.json').read_text())['keepouts']

    def shape(kind, x):
        if kind == 'pad':
            return unary_union([Polygon(p) for p in x['poly']])
        if kind == 'track':
            return LineString([x['start'], x['end']]).buffer(x['width'] / 2, quad_segs=32)
        return Point(x['pos']).buffer(x['diameter'] / 2, quad_segs=64)

    objects = [(kind, x, shape(kind, x)) for kind, field in [('pad', 'pads'), ('track', 'tracks'), ('via', 'vias')]
               for x in current[field]]
    trees = {}
    for layer in ['F.Cu', 'B.Cu']:
        rows = [(kind, x, s) for kind, x, s in objects if layer in x.get('layers', [x.get('layer')])]
        trees[layer] = (rows, STRtree([s for _, _, s in rows]))
    present = {x['id'] for _, x, _ in objects}
    accepted, rejected = [], []
    for kind, field in [('track', 'tracks'), ('via', 'vias')]:
        for item in original[field]:
            if item['id'] not in removed or item['id'] in present or item['net'] not in nets:
                continue
            s = shape(kind, item)
            layers = ['F.Cu', 'B.Cu'] if kind == 'via' else [item['layer']]
            conflicts = set()
            for layer in layers:
                rows, tree = trees[layer]
                for i in tree.query(s.buffer(.201)):
                    other_kind, other, copper = rows[int(i)]
                    same = other['net'] == item['net']
                    # Preserve a real annular gap to all existing holes/pads,
                    # including same-net ones; do not create duplicate drills.
                    if same and not (kind == 'via' and other_kind in {'via', 'pad'}):
                        continue
                    if s.distance(copper) < .19999:
                        conflicts.add(other['id'])
                for zone in keepouts:
                    if zone['layer'] != layer or not zone['vias' if kind == 'via' else 'tracks']:
                        continue
                    if s.intersects(unary_union([Polygon(p) for p in zone['poly']])):
                        conflicts.add('native-keepout')
            if conflicts:
                rejected.append({'id': item['id'], 'net': item['net'], 'conflicts': sorted(conflicts)})
            else:
                accepted.append(dict(item, kind=kind))
    out = {'before_sha256': current['source_sha256'], 'reference_sha256': original['source_sha256'],
           'reference': str(args.reference), 'drc_sha256': sha(args.drc), 'open_nets': sorted(nets),
           'accepted': accepted, 'rejected': rejected,
           'scope': 'Existing geometry proposal only. Native DRC and connectivity remain required.'}
    assert not args.output.exists(), 'Preserve earlier recovery evidence'
    args.output.write_text(json.dumps(out, indent=2) + '\n')
    print('Recoverable original pieces:', len(accepted), '; conflicting pieces:', len(rejected))


def apply(args):
    import pcbnew as k
    from trim_power_r05_tails import islands
    data = json.loads(args.output.read_text())
    out = args.output.with_name(args.output.stem + '-applied.json')
    assert not out.exists(), 'Preserve earlier recovery evidence'
    pcb = args.trial / 'hardware/collar-tracker.kicad_pcb'
    assert sha(pcb) == data['before_sha256'], 'Stale recovery proposal'
    assert sha(args.reference / 'hardware/collar-tracker.kicad_pcb') == data['reference_sha256']
    board = k.LoadBoard(str(pcb))
    ground = islands(board, {'/GND'})
    existing = {t.m_Uuid.AsString() for t in board.GetTracks()}
    vector = lambda p: k.VECTOR2I(*(round(v * 1e6) for v in p))
    for item in data['accepted']:
        assert item['id'] not in existing and item['net'] != '/GND'
        if item['kind'] == 'via':
            t = k.PCB_VIA(board)
            t.SetPosition(vector(item['pos'])); t.SetWidth(round(item['diameter'] * 1e6))
            t.SetDrill(round(item['drill'] * 1e6)); t.SetLayerPair(k.F_Cu, k.B_Cu)
            t.SetFrontTentingMode(k.TENTING_MODE_TENTED); t.SetBackTentingMode(k.TENTING_MODE_TENTED)
        else:
            t = k.PCB_TRACK(board)
            t.SetStart(vector(item['start'])); t.SetEnd(vector(item['end']))
            t.SetLayer(board.GetLayerID(item['layer'])); t.SetWidth(round(item['width'] * 1e6))
        t.SetNet(board.FindNet(item['net'])); t.SetLocked(True)
        t.SetUuid(k.KIID(item['id'])); board.Add(t)
    assert islands(board, {'/GND'}) == ground
    k.ZONE_FILLER(board).Fill(board.Zones())
    assert k.SaveBoard(str(pcb), board)
    out.write_text(json.dumps({'before_sha256': data['before_sha256'], 'source_sha256': sha(pcb),
                   'plan_sha256': sha(args.output), 'added_ids': [x['id'] for x in data['accepted']],
                   'scope': 'Native import only. Fresh DRC required.'}, indent=2) + '\n')
    print('Restored:', len(data['accepted']))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('trial', type=Path)
    p.add_argument('reference', type=Path)
    p.add_argument('--drc', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--apply', action='store_true')
    args = p.parse_args()
    if args.apply:
        apply(args)
    else:
        assert args.drc is not None
        plan(args)
