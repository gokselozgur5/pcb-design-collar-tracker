#!/usr/bin/env python3
"""Verify a saved WIP routing checkpoint without treating it as manufacturing approval."""
import json
from pathlib import Path

from verify_power_pin_candidate import check_files, read, require, sha

ROOT = Path(__file__).resolve().parents[1]


def verify(trial):
    trial = Path(trial).resolve()
    evidence = trial / 'evidence'
    manifest = read(evidence / 'routing-checkpoint.json')
    count = check_files(trial, manifest)
    pcb = trial / 'hardware/collar-tracker.kicad_pcb'
    source = sha(pcb)
    require(source == manifest['source_sha256'], 'Candidate PCB differs from checkpoint')
    require(manifest['manufacturing_release'] is False and not manifest['supplier_records'],
            'This verifier only accepts explicit WIP checkpoints without supplier approval')
    old = ROOT / 'experiments/power-r05-supervised'
    current = trial / 'hardware'
    require(sha(current / 'collar-tracker.kicad_sch') == sha(old / 'hardware/collar-tracker.kicad_sch'),
            'Circuit changed; a new electrical review is required')
    a, b = read(current / 'collar-tracker.kicad_pro'), read(old / 'hardware/collar-tracker.kicad_pro')
    require(a['board']['design_settings'] == b['board']['design_settings']
            and a['net_settings'] == b['net_settings']
            and sha(current / 'collar-tracker.kicad_dru') == sha(old / 'hardware/collar-tracker.kicad_dru'),
            'Inherited design rules changed')
    drc = read(evidence / 'native-drc.json')
    require({name: len(drc[name]) for name in ['violations', 'unconnected_items', 'schematic_parity']}
            == manifest['native_drc'], 'Saved DRC totals differ')
    require(drc['ignored_checks'] == read(old / 'evidence/native-drc.json')['ignored_checks'],
            'Disabled-check configuration changed')
    require(not drc['schematic_parity'], 'Schematic parity mismatch')
    erc = read(evidence / 'erc.json')
    require(erc['ignored_checks'] == read(old / 'evidence/erc.json')['ignored_checks']
            and all(not s['violations'] for s in erc['sheets']), 'ERC state differs')
    require(all(v['type'] in {'track_dangling', 'via_dangling'} and v['severity'] == 'warning'
                for v in drc['violations']), 'Unexpected geometry violation')
    require(all('/GND' not in str(x) for x in drc['unconnected_items']), 'Ground connection open')
    reports = {name: read(evidence / (name + '.json')) for name in [
        'route-geometry', 'layout-inventory', 'attachment-review', 'passive-copper-review',
        'esd-paths', 'card-insertion-review', 'power-path-review', 'placement-input', 'placement-extra']}
    require(all(r['source_sha256'] == source for r in reports.values()), 'Stale layout report')
    inv = reports['layout-inventory']
    for key, expected in manifest['inventory'].items():
        require(inv[key] == expected, 'Inventory differs: ' + key)
    require(inv['footprints'] == 71 and inv['ground_pads'] == 97 and inv['inner_tracks'] == 0
            and inv['rf_segments'] == 24 and inv['rf_segments_preserved'], 'Critical layout invariant failed')
    require(set(inv['planes']) == {'In1.Cu', 'In2.Cu'} and all(
        p['zone_nets'] == ['/GND'] and p['filled_outline_count'] == 1 and not p['ground_vias_outside']
        for p in inv['planes'].values()), 'Ground plane continuity changed')
    grounds = reports['attachment-review']['grounds']
    require(len(grounds) == 94 and all(g['via'] is not None and g['local_path_mm'] is not None
                                     for g in grounds), 'Local ground attachment missing')
    paths = reports['esd-paths']['paths']
    require(len(paths) == 4 and all(p['connector_to_esd'] and p['esd_to_modem']
                                  and not p['bypasses_esd_land'] for p in paths), 'SIM protection path changed')
    require(reports['card-insertion-review']['pcb_entry_projection_clear']
            and not reports['card-insertion-review']['overlap_candidates'], 'SIM entry is blocked')
    power = reports['power-path-review']['paths']
    require(len(power) == 12 and all(p['connected'] for p in power), 'Original power backbone open')
    poses = read(trial / 'build/placement.json')
    for ref, f in reports['placement-input']['footprints'].items():
        require(poses[ref] == f['pos'] + [f['angle'], f['side']], 'Stale placement: ' + ref)
    if manifest.get('fit_checkpoint'):
        fit_path = (ROOT / manifest['fit_checkpoint']).resolve()
        require(fit_path.is_relative_to(ROOT), 'Fit path escapes the checkout')
        checkpoint = read(fit_path)
        check_files(fit_path.parent, checkpoint)
        fit = read(fit_path.parent / 'populated-fit.json')
        native = read(fit_path.parent / 'components.native.json')
        require(checkpoint['source_sha256'] == native['source_sha256'] == fit['pcb_sha256'] == source,
                'Fit belongs to another PCB')
        require(fit['checked'] == 69 and fit['checked_geometry_pass'] and not fit['violations'],
                'Populated fit does not pass its declared screen')
        require(not checkpoint['physical_ingress_test'] and not checkpoint['manufacturing_release'],
                'Preliminary fit cannot claim physical acceptance')
    return {'revision': trial.name, 'source_sha256': source, 'verified_files': count,
            'native_drc': manifest['native_drc'], 'returns_outside_2mm': inv['returns_outside_2mm'],
            'result': 'SAVED EVIDENCE VERIFIED', 'electrical_acceptance': 'HOLD',
            'manufacturing_release': False}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trial', type=Path)
    print(json.dumps(verify(parser.parse_args().trial), indent=2))
