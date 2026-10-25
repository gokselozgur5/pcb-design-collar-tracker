#!/usr/bin/env python3
"""Verify the bounded r05i change without claiming controlled-impedance approval."""
import copy
import json
from pathlib import Path

from verify_power_pin_candidate import check_files, read, require, sha
from verify_routing_candidate import verify_supplier

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'experiments/power-r05h-six-layer'
RF = {'/LTE_RF', '/LTE_ANT', '/GPS_RF', '/GNSS_ANT', '/GNSS_FEM_IN', '/GNSS_FEM_OUT'}
EXPECTED_BASE = 'aecb8e431819fa2aa23dfecc98ff1f6a064b5ae81afe7679a6e317f3571c3171'


def verify(trial=None):
    trial = Path(trial or ROOT / 'experiments/power-r05i-rf-stack').resolve()
    e = trial / 'evidence'
    manifest = read(e / 'rf-checkpoint.json')
    count = check_files(trial, manifest)
    source = sha(trial / 'hardware/collar-tracker.kicad_pcb')
    require(source == manifest['source_sha256'], 'RF PCB differs from checkpoint')
    require(sha(BASE / 'hardware/collar-tracker.kicad_pcb') == EXPECTED_BASE, 'RF baseline changed')
    require(manifest['manufacturing_release'] is False and manifest['electrical_acceptance'] ==
            manifest['rf_acceptance'] == 'HOLD', 'Geometry is not electrical/RF/manufacturing acceptance')
    for name in ['collar-tracker.kicad_sch', 'collar-tracker.kicad_dru']:
        require(sha(trial / 'hardware' / name) == sha(BASE / 'hardware' / name), 'Circuit/rules changed')
    old = read(BASE / 'hardware/collar-tracker.kicad_pro')
    new = read(trial / 'hardware/collar-tracker.kicad_pro')
    expected = copy.deepcopy(old)
    next(c for c in expected['net_settings']['classes'] if c['name'] == 'RF')['track_width'] = .36
    for p in expected['net_settings']['netclass_patterns']:
        if p['pattern'] in ['/FILT_OUT', '/AMP_IN']:
            p['netclass'] = 'Default'
    require(new == expected, 'Unexpected project/rule change')
    a, b = read(BASE / 'evidence/route-geometry.json'), read(e / 'route-geometry.json')
    require(a['source_sha256'] == EXPECTED_BASE and b['source_sha256'] == source, 'Stale geometry')
    for key in ['pads', 'vias', 'mask_graphics', 'zones', 'copper_layers', 'board_bounds_mm']:
        require(a[key] == b[key], 'Non-RF physical geometry changed: '+key)
    require([t for t in a['tracks'] if t['net'] not in RF] ==
            [t for t in b['tracks'] if t['net'] not in RF], 'Non-port routing changed')
    seed = read(e / 'rf-seed.json')
    require(seed['source_sha256'] == source and seed['baseline_sha256'] == EXPECTED_BASE, 'Stale RF edit receipt')
    originals = {r['id'] for r in seed['changed_original_tracks']}
    escapes = {r['id']: r for r in seed['added_escapes']}
    require(len(originals) == 18 and len(escapes) == 4, 'RF change scope differs')
    port_tracks = [t for t in b['tracks'] if t['net'] in RF]
    require({t['id'] for t in port_tracks} == originals | set(escapes), 'RF track set differs')
    for t in port_tracks:
        require(t['layer'] == 'F.Cu', 'RF layer transition introduced')
        if t['id'] in escapes:
            r = escapes[t['id']]
            require(t['width'] == r['width_mm'] and t['start'] == r['start'] and t['end'] == r['end'],
                    'Bounded module escape changed')
        else:
            require(t['width'] == .36, 'Port-route width changed')
    inventory = read(e / 'layout-inventory.json')
    require(inventory['source_sha256'] == source and inventory['footprints'] == 71 and
            inventory['ground_pads'] == 97 and inventory['ground_vias'] == 110 and
            inventory['non_ground_vias'] == 128 and inventory['returns_outside_2mm'] == 0 and
            inventory['ground_layer_tracks'] == 0 and inventory['rf_segments'] == 28 and
            inventory['rf_segments_preserved'] is False, 'Layout inventory differs')
    require(set(inventory['planes']) == {'In1.Cu', 'In4.Cu'} and all(
        p['zone_nets'] == ['/GND'] and p['filled_outline_count'] == 1 and not p['ground_vias_outside']
        for p in inventory['planes'].values()), 'Dedicated ground plane changed')
    attachments = read(e / 'attachment-review.json')
    require(attachments['source_sha256'] == source and len(attachments['grounds']) == 94 and
            all(g['via'] is not None and g['local_path_mm'] is not None for g in attachments['grounds']),
            'Local ground path missing')
    power = read(e / 'power-path-review.json')
    require(power['source_sha256'] == source and len(power['paths']) == 12 and
            all(p['connected'] for p in power['paths']) and
            power['assumptions']['inner_copper_um'] == 15.2 and
            power['assumptions']['thickness_mm'] == .91, 'Power-path assumptions changed')
    require(read(e / 'passive-copper-review.json')['source_sha256'] == source,
            'Stale passive review')
    for name, expected_source in [('rf', source), ('baseline-rf', EXPECTED_BASE)]:
        geometry = read(e / (name+'-geometry.json')); review = read(e / (name+'-review.json'))
        require(geometry['source_sha256'] == review['source_sha256'] == expected_source and
                review['input_sha256'] == sha(e / (name+'-geometry.json')), 'Stale RF reference review')
        require(review['rf_acceptance'] == 'HOLD' and review['native_contains_disagreements'] == 0,
                'RF scope/interpretation changed')
    review = read(e / 'rf-review.json')
    require(review['port_route_unbacked_copper_mm2'] < 1e-9 and review['port_route_widths_mm'] == [.2,.28,.36]
            and review['matching_route_widths_mm'] == [.2], 'RF geometry screen failed')
    fit = read(e / 'thickness-fit.json')
    require(fit['source_sha256'] == source and fit['all_pass'] and fit['original_carrier_rejected'] and
            [s['thickness_mm'] for s in fit['scenarios']] == [.71,.81,.84088,.91], 'Thickness fit failed')
    require(all(sha(ROOT/path) == digest for path,digest in fit['inputs'].items()), 'Fit input changed')
    exported = read((ROOT / manifest['package']).with_suffix('') / 'manifest.json')
    folder = (ROOT / manifest['package']).with_suffix('')
    drc, erc = read(folder / 'drc.json'), read(folder / 'erc.json')
    require(not any(drc[key] for key in ['violations','unconnected_items','schematic_parity']) and
            not any(s['violations'] for s in erc['sheets']), 'Native checks not clean')
    require(drc['ignored_checks'] == read(BASE/'evidence/native-drc.json')['ignored_checks'] and
            erc['ignored_checks'] == read(BASE/'evidence/erc.json')['ignored_checks'], 'Ignored checks changed')
    records = verify_supplier(trial, manifest, source, exported['copper_layers'])
    return dict(revision='r05i RF geometry candidate', result='PASS', files=count,
                source_sha256=source, zip_sha256=manifest['zip_sha256'], supplier_records=records,
                native_drc={k:len(drc[k]) for k in ['violations','unconnected_items','schematic_parity']},
                electrical_acceptance='HOLD', rf_acceptance='HOLD', manufacturing_release=False)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
