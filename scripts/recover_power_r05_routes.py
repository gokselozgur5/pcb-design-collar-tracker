#!/usr/bin/env python3
"""Recover still-clear r04i rail geometry in the isolated r05 ground-stage PCB.

Plan with geometry Python; apply that exact plan with KiCad Python and --apply.
The seed removed whole power nets. Recover only their source-identical items
that clear the changed pin nets, new lands and new ground exits. This avoids
ripping up already working signal pin escapes. Native DRC remains mandatory.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05-supervised'
BASE = ROOT / 'experiments/paul-nanosim-r04i-sim-access-40x32'
PCB = TRIAL / 'hardware/collar-tracker.kicad_pcb'
PLAN = TRIAL / 'evidence/recovered-rail-plan.json'
BASE_SHA = 'f4be0288708733aaa6092a703ffa1bfebb3dc059fd21112a8cfed94028acc3b0'
GROUND_SHA = '350c81e9d6a66e44cf395255874fd0be04e6365c9a10f233b186e4e6ff2a9b20'
NETS = {'/VBAT', '/VSYS', '/VDD_NRF', '/NRF_ENABLE'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan():
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import unary_union
    assert not PLAN.exists(), 'Preserve earlier evidence'
    assert sha(PCB) == GROUND_SHA, 'Use the reviewed ground-stage checkpoint'
    assert sha(BASE / 'hardware/collar-tracker.kicad_pcb') == BASE_SHA
    current = json.loads((TRIAL / 'evidence/route-geometry.json').read_text())
    original = json.loads((BASE / 'evidence/route-geometry.json').read_text())
    assert current['source_sha256'] == GROUND_SHA
    assert original['source_sha256'] == BASE_SHA
    removed = {r['uuid'] for r in json.loads((TRIAL / 'evidence/pcb-seed.json').read_text())['removed_tracks']}

    def shape(item, kind):
        if kind == 'pad':
            return unary_union([Polygon(p) for p in item['poly']])
        if kind == 'via':
            return Point(item['pos']).buffer(item['diameter'] / 2, quad_segs=64)
        return LineString([item['start'], item['end']]).buffer(item['width'] / 2, quad_segs=64)

    def objects(geometry):
        return [dict(item, kind=kind, shape=shape(item, kind),
                     sides=set(item.get('layers', [item.get('layer')])) & {'F.Cu', 'B.Cu'})
                for kind, field in [('pad', 'pads'), ('via', 'vias'), ('track', 'tracks')]
                for item in geometry[field]]

    obstacles = objects(current)
    accepted, rejected = [], []
    for item in objects(original):
        if item['kind'] == 'pad' or item['id'] not in removed or item['net'] not in NETS:
            continue
        conflicts = []
        for other in obstacles:
            if not item['sides'] & other['sides']:
                continue
            # Retain the same no-via-in-pad screen used for the original board.
            if item['net'] == other['net'] and not (item['kind'] == 'via' and other['kind'] in ['pad', 'via']):
                continue
            distance = item['shape'].distance(other['shape'])
            if distance < .199999:
                conflicts.append({'id': other['id'], 'ref': other.get('ref'),
                                  'net': other['net'], 'kind': other['kind'],
                                  'copper_distance_mm': distance})
        if conflicts:
            rejected.append({'id': item['id'], 'net': item['net'], 'conflicts': conflicts})
        else:
            accepted.append({k: v for k, v in item.items() if k not in {'shape', 'sides'}})
            obstacles.append(item)
    report = {'source_sha256': GROUND_SHA, 'baseline_sha256': BASE_SHA,
              'accepted': accepted, 'rejected': rejected,
              'scope': 'Recovery proposal only; native DRC, dangling tails and new connections need review.'}
    PLAN.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'recovered_items_planned': len(accepted), 'rejected_items': len(rejected)}))


def apply():
    import pcbnew as k
    report = json.loads(PLAN.read_text())
    assert sha(PCB) == report['source_sha256'] == GROUND_SHA
    assert sha(BASE / 'hardware/collar-tracker.kicad_pcb') == report['baseline_sha256'] == BASE_SHA
    project = PCB.with_suffix('.kicad_pro')
    rules_before = json.loads(project.read_text())
    board = k.LoadBoard(str(PCB))
    existing = {t.m_Uuid.AsString() for t in board.GetTracks()}
    vector = lambda point: k.VECTOR2I(*(round(v * 1e6) for v in point))
    restored_ids = {}
    for item in report['accepted']:
        assert item['id'] not in existing
        if item['kind'] == 'via':
            track = k.PCB_VIA(board)
            track.SetPosition(vector(item['pos']))
            track.SetWidth(round(item['diameter'] * 1e6))
            track.SetDrill(round(item['drill'] * 1e6))
            track.SetViaType(k.VIATYPE_THROUGH)
            track.SetLayerPair(k.F_Cu, k.B_Cu)
            track.SetFrontTentingMode(k.TENTING_MODE_TENTED)
            track.SetBackTentingMode(k.TENTING_MODE_TENTED)
        else:
            track = k.PCB_TRACK(board)
            track.SetStart(vector(item['start']))
            track.SetEnd(vector(item['end']))
            track.SetWidth(round(item['width'] * 1e6))
            track.SetLayer(board.GetLayerID(item['layer']))
        track.SetNet(board.FindNet(item['net']))
        track.SetLocked(True)
        board.Add(track)
        restored_ids[item['id']] = track.m_Uuid.AsString()
    board.BuildConnectivity()
    k.ZONE_FILLER(board).Fill(board.Zones())
    assert k.SaveBoard(str(PCB), board)
    rules_after = json.loads(project.read_text())
    assert rules_before['board']['design_settings'] == rules_after['board']['design_settings']
    assert rules_before['net_settings'] == rules_after['net_settings']
    (TRIAL / 'evidence/recovered-rail-apply.json').write_text(json.dumps({
        'before_sha256': GROUND_SHA, 'source_sha256': sha(PCB),
        'plan_sha256': sha(PLAN), 'recovered_items': len(report['accepted']),
        'original_to_restored_ids': restored_ids,
        'scope': 'Native DRC and unfinished routing still require verification.'}, indent=2) + '\n')
    print('Recovered', len(report['accepted']), 'source-identical rail items')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    apply() if args.apply else plan()
