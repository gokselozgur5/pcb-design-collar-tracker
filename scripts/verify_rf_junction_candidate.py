#!/usr/bin/env python3
"""Verify the bounded r05j change and two source-bound supplier records."""
import copy
import json
from pathlib import Path

from verify_power_pin_candidate import check_files, read, require, sha
from verify_routing_candidate import verify_supplier

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'experiments/power-r05i-rf-stack'
TRIAL = ROOT / 'experiments/power-r05j-rf-junctions'
EXPECTED_BASE = '0db809c4ecefbf577db1001164886709708f02ab6ba54f7a572e948583d726a1'


def close(a, b):
    return len(a) == len(b) and all(abs(x-y) < 1e-6 for x, y in zip(a, b))


def verify_geometry(trial=TRIAL):
    e = trial / 'evidence'
    source = sha(trial / 'hardware/collar-tracker.kicad_pcb')
    require(sha(BASE / 'hardware/collar-tracker.kicad_pcb') == EXPECTED_BASE, 'Baseline changed')
    for name in ['collar-tracker.kicad_sch', 'collar-tracker.kicad_dru', 'collar-tracker.kicad_pro', 'bom.csv']:
        require(sha(trial/'hardware'/name) == sha(BASE/'hardware'/name), 'Circuit, rules or BOM changed: '+name)
    a, b = [read(p/'evidence/route-geometry.json') for p in [BASE, trial]]
    require(a['source_sha256'] == EXPECTED_BASE and b['source_sha256'] == source, 'Stale geometry')
    for key in ['vias', 'mask_graphics', 'zones', 'copper_layers', 'board_bounds_mm']:
        require(a[key] == b[key], 'Unintended geometry change: '+key)
    expected_pads = copy.deepcopy(a['pads'])
    for p in expected_pads:
        if p['ref'] == 'R3':
            p['pos'][0] += .3
            for contour in p['poly']:
                for point in contour:
                    point[0] += .3
    require(len(expected_pads) == len(b['pads']) == 337, 'Pad inventory changed')
    for old, new in zip(expected_pads, b['pads']):
        require({k:v for k,v in old.items() if k not in {'pos','poly'}} ==
                {k:v for k,v in new.items() if k not in {'pos','poly'}}, 'Pad attributes changed')
        require(close(old['pos'], new['pos']) and len(old['poly']) == len(new['poly']) and
                all(len(c) == len(d) and all(close(x,y) for x,y in zip(c,d))
                    for c,d in zip(old['poly'],new['poly'])), 'Unintended pad movement')
    seed = read(trial/'initial-layout/evidence/rf-junction-seed.json')
    refinement = read(e/'r3-refinement.json')
    require(seed['baseline_sha256'] == EXPECTED_BASE and
            seed['source_sha256'] == refinement['before_sha256'] ==
            sha(trial/'initial-layout/hardware/collar-tracker.kicad_pcb') and
            refinement['source_sha256'] == source, 'Edit receipt chain differs')
    expected_tracks = {t['id']: copy.deepcopy(t) for t in a['tracks']}
    for change in seed['changes']:
        for uid in change['removed']:
            require(expected_tracks[uid]['net'] == change['net'], 'Removed track net differs')
            del expected_tracks[uid]
        for t in change['added_tracks']:
            expected_tracks[t['id']] = dict(id=t['id'], net=change['net'], start=t['start'],
                end=t['end'], layer='F.Cu', width=t['width_mm'])
    expected_tracks[refinement['extension_track']]['end'] = refinement['new_input_end_mm']
    for uid, a0, b0 in zip(refinement['output_tracks'], refinement['output_points_mm'],
                           refinement['output_points_mm'][1:]):
        expected_tracks[uid]['start'] = a0
        expected_tracks[uid]['end'] = b0
    require(expected_tracks == {t['id']:t for t in b['tracks']}, 'Unexpected routing change')
    native_before, native_after = [read(p/'evidence/components.native.json') for p in [BASE,trial]]
    require(native_before['board_size_mm'] == native_after['board_size_mm'] and
            native_after['source_sha256'] == source, 'Board dimensions or placement source changed')
    require([p for p in native_before['parts'] if p['ref'] != 'R3'] ==
            [p for p in native_after['parts'] if p['ref'] != 'R3'], 'Other component placement changed')
    old_r3 = next(p for p in native_before['parts'] if p['ref'] == 'R3')
    new_r3 = next(p for p in native_after['parts'] if p['ref'] == 'R3')
    require(new_r3['side'] == old_r3['side'] == 'top' and new_r3['native_angle_degrees'] == 0 and
            close(new_r3['native_position_mm'], [old_r3['native_position_mm'][0]+.3, old_r3['native_position_mm'][1]]),
            'Unexpected R3 pose')
    reports = {name:read(e/(name+'.json')) for name in [
        'layout-inventory','attachment-review','passive-copper-review','power-path-review','rf-review','thickness-fit']}
    require(all(r['source_sha256'] == source for r in reports.values()), 'Stale layout/fit review')
    inv = reports['layout-inventory']
    require((inv['footprints'], inv['ground_pads'], inv['ground_vias'], inv['non_ground_vias'],
             inv['rf_segments'], inv['returns_outside_2mm'], inv['ground_layer_tracks']) ==
            (71,97,110,128,27,0,0), 'Layout invariant differs')
    require(inv['planes'] == read(BASE/'evidence/layout-inventory.json')['planes'], 'Ground plane inventory changed')
    grounds = reports['attachment-review']['grounds']
    require(len(grounds) == 94 and all(g['via'] is not None and g['local_path_mm'] is not None for g in grounds),
            'Local GND connection missing')
    r3 = next(p for p in reports['passive-copper-review']['passives'] if p['ref'] == 'R3')
    require(all(1 <= x < 1.01 for x in r3['ratios'].values()), 'R3 contour balance regressed')
    entries = next(p for p in reports['attachment-review']['passives'] if p['ref'] == 'R3')
    require(all(len(p['attachments']) == 1 and p['total_exit_width_mm'] == .36 for p in entries['pads']),
            'R3 no longer has one equal-width entry per land')
    power = reports['power-path-review']
    require(len(power['paths']) == 12 and all(p['connected'] for p in power['paths']) and
            power['assumptions']['inner_copper_um'] == 15.2 and power['assumptions']['thickness_mm'] == .91,
            'Power-path check differs')
    rf = reports['rf-review']; geometry = read(e/'rf-geometry.json')
    require(geometry['source_sha256'] == source and rf['input_sha256'] == sha(e/'rf-geometry.json') and
            geometry['zones'] == read(BASE/'evidence/rf-geometry.json')['zones'], 'Reference plane changed')
    require(rf['native_contains_disagreements'] == 0 and rf['port_route_unbacked_copper_mm2'] < 1e-9 and
            rf['port_route_widths_mm'] == [.2,.28,.36] and rf['matching_route_widths_mm'] == [.2], 'RF coverage failed')
    fit = reports['thickness-fit']
    require(fit['all_pass'] and fit['original_carrier_rejected'] and
            [s['thickness_mm'] for s in fit['scenarios']] == [.71,.81,.84088,.91] and
            all(s['checked'] == 69 for s in fit['scenarios']), 'Populated fit failed')
    require(all(sha(ROOT/p) == h for p,h in fit['inputs'].items()), 'Fit inputs changed')
    return dict(source_sha256=source, r3_contour_ratios=r3['ratios'])


def verify():
    e = TRIAL/'evidence'
    manifest = read(e/'rf-junction-checkpoint.json')
    count = check_files(TRIAL, manifest)
    geometry = verify_geometry()
    source = geometry['source_sha256']
    require(source == manifest['source_sha256'] and not manifest['manufacturing_release'] and
            manifest['electrical_acceptance'] == manifest['rf_acceptance'] == 'HOLD', 'Release state differs')
    folder = (ROOT/manifest['package']).with_suffix('')
    exported = read(folder/'manifest.json'); drc = read(folder/'drc.json'); erc = read(folder/'erc.json')
    require(not any(drc[k] for k in ['violations','unconnected_items','schematic_parity']) and
            all(not s['violations'] for s in erc['sheets']), 'Native checks failed')
    old_folder = BASE/'evidence/collar-tracker-05i-rf-40x32-dfm'
    require(drc['ignored_checks'] == read(old_folder/'drc.json')['ignored_checks'] and
            erc['ignored_checks'] == read(old_folder/'erc.json')['ignored_checks'], 'Disabled checks changed')
    records = verify_supplier(TRIAL, manifest, source, exported['copper_layers'])
    return dict(revision='r05j RF junction candidate', result='PASS', files=count,
        **geometry, zip_sha256=manifest['zip_sha256'], supplier_records=records,
        native_drc={k:len(drc[k]) for k in ['violations','unconnected_items','schematic_parity']},
        electrical_acceptance='HOLD', rf_acceptance='HOLD', manufacturing_release=False)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
