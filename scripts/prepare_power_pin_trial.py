#!/usr/bin/env python3
"""Prepare an isolated r05b placement trial while preserving working legacy copper.

Plan with geometry Python, then apply with KiCad Python and --apply. The plan
removes only new r05 route geometry, stages the 20 changed footprints outside the
outline, and recovers original rail geometry clear of changed existing pad nets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'experiments/power-r05-supervised'
BASE = ROOT / 'experiments/paul-nanosim-r04i-sim-access-40x32'
TRIAL = ROOT / 'experiments/power-r05b-pin-exits'
SOURCE_SHA = '78df6a520fc978e08451c94e6c6f475877f401867b55c0218802ee3434d193a2'
BASE_SHA = 'f4be0288708733aaa6092a703ffa1bfebb3dc059fd21112a8cfed94028acc3b0'
PCB = TRIAL / 'hardware/collar-tracker.kicad_pcb'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(item, kind):
    point = lambda p: tuple(round(v, 6) for v in p)
    if kind == 'via':
        return kind, item['net'], point(item['pos']), item['diameter'], item['drill']
    return kind, item['net'], tuple(sorted([point(item['start']), point(item['end'])])), item['layer'], item['width']


def plan():
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import unary_union
    assert not TRIAL.exists(), 'Preserve existing trials'
    assert sha(SOURCE / 'hardware/collar-tracker.kicad_pcb') == SOURCE_SHA
    assert sha(BASE / 'hardware/collar-tracker.kicad_pcb') == BASE_SHA
    current = json.loads((SOURCE / 'evidence/route-geometry.json').read_text())
    original = json.loads((BASE / 'evidence/route-geometry.json').read_text())
    assert current['source_sha256'] == SOURCE_SHA and original['source_sha256'] == BASE_SHA
    moving = set(json.loads((SOURCE / 'evidence/pcb-seed.json').read_text())['changed_parts'])
    assert len(moving) == 20
    original_items = [(kind, item) for kind, field in [('track', 'tracks'), ('via', 'vias')]
                      for item in original[field]]
    current_items = [(kind, item) for kind, field in [('track', 'tracks'), ('via', 'vias')]
                     for item in current[field]]
    old_geometry = {signature(item, kind) for kind, item in original_items}
    retained = [(kind, item) for kind, item in current_items if signature(item, kind) in old_geometry]
    retained_geometry = {signature(item, kind) for kind, item in retained}
    fixed_pads = [(p, unary_union([Polygon(poly) for poly in p['poly']]))
                  for p in current['pads'] if p['ref'] not in moving]
    restored, rejected = [], []
    for kind, item in original_items:
        if item['net'] not in {'/VBAT', '/VSYS', '/VDD_NRF', '/NRF_ENABLE'} or signature(item, kind) in retained_geometry:
            continue
        sides = {'F.Cu', 'B.Cu'} if kind == 'via' else {item['layer']}
        shape = (Point(item['pos']).buffer(item['diameter'] / 2, quad_segs=64) if kind == 'via'
                 else LineString([item['start'], item['end']]).buffer(item['width'] / 2, quad_segs=64))
        conflicts = [p['ref'] + '.' + p['pin'] for p, pad in fixed_pads
                     if sides.intersection(p['layers']) and (kind == 'via' or p['net'] != item['net'])
                     and shape.distance(pad) < .199999]
        if conflicts:
            rejected.append({'id': item['id'], 'net': item['net'], 'pads': conflicts})
        else:
            restored.append(dict(item, kind=kind))
    (TRIAL / 'evidence').mkdir(parents=True)
    (TRIAL / 'build').mkdir()
    (TRIAL / 'previews').mkdir()
    shutil.copytree(SOURCE / 'hardware', TRIAL / 'hardware',
                    ignore=shutil.ignore_patterns('*.kicad_prl', '*.local-routing.json', '*.detour-proposal.json'))
    (TRIAL / 'evidence/preparation-plan.json').write_text(json.dumps({
        'source_sha256': SOURCE_SHA, 'baseline_sha256': BASE_SHA, 'moving': sorted(moving),
        'retained_ids': sorted(item['id'] for _, item in retained),
        'removed_ids': sorted(item['id'] for kind, item in current_items if signature(item, kind) not in old_geometry),
        'restored': restored, 'rejected': rejected,
        'scope': 'Preparation plan only. No placed/routed/DFM acceptance.'}, indent=2) + '\n')
    print(json.dumps({'retained': len(retained), 'restored': len(restored), 'rejected': len(rejected), 'moving': len(moving)}))


def apply():
    import pcbnew as k
    from seed_power_r05_pcb import export_placement
    plan_path = TRIAL / 'evidence/preparation-plan.json'
    data = json.loads(plan_path.read_text())
    assert sha(PCB) == SOURCE_SHA
    project = PCB.with_suffix('.kicad_pro')
    before_project = json.loads(project.read_text())
    board = k.LoadBoard(str(PCB))
    keep = set(data['retained_ids'])
    for track in list(board.GetTracks()):
        if track.m_Uuid.AsString() not in keep:
            board.Delete(track)
        else:
            track.SetLocked(True)
    vector = lambda p: k.VECTOR2I(*(round(v * 1e6) for v in p))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    for index, ref in enumerate(data['moving']):
        f = fps[ref]
        if f.IsFlipped():
            f.SetLayerAndFlip(k.F_Cu)
        f.SetOrientationDegrees(0)
        f.SetPosition(vector([150 + (index % 5) * 5, 100 + (index // 5) * 5]))
    restored_ids = {}
    for item in data['restored']:
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
    board.GetTitleBlock().SetRevision('0.5b-pin-exits-WIP')
    assert k.SaveBoard(str(PCB), board)
    after_project = json.loads(project.read_text())
    assert before_project['board']['design_settings'] == after_project['board']['design_settings']
    assert before_project['net_settings'] == after_project['net_settings']
    export_placement(board, set(data['moving']), output=PCB, trial=TRIAL)
    def polygons(poly):
        return [[[poly.COutline(i).CPoint(j).x / 1e6, poly.COutline(i).CPoint(j).y / 1e6]
                 for j in range(poly.COutline(i).PointCount())] for i in range(poly.OutlineCount())]
    keepouts = [{'layer': board.GetLayerName(z.GetLayer()), 'tracks': z.GetDoNotAllowTracks(),
                 'vias': z.GetDoNotAllowVias(), 'poly': polygons(z.Outline())}
                for z in [*board.Zones(), *(z for f in board.GetFootprints() for z in f.Zones())]
                if z.GetIsRuleArea()]
    (TRIAL / 'evidence/placement-extra.json').write_text(json.dumps({'keepouts': keepouts}, indent=2) + '\n')
    (TRIAL / 'evidence/preparation.json').write_text(json.dumps({
        'before_sha256': SOURCE_SHA, 'source_sha256': sha(PCB), 'plan_sha256': sha(plan_path),
        'restored_ids': restored_ids, 'scope': 'Unplaced candidate; native geometry/routing checks pending.'}, indent=2) + '\n')
    protected = sorted(t.m_Uuid.AsString() for t in board.GetTracks())
    (TRIAL / 'evidence/protected-legacy.json').write_text(json.dumps(protected, indent=2) + '\n')
    shutil.copy2(PCB, TRIAL / 'build/seed-before-placement.kicad_pcb')
    print(json.dumps({'protected_legacy_items': len(protected), 'seed_sha256': sha(PCB)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    apply() if args.apply else plan()
