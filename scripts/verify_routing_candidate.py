#!/usr/bin/env python3
"""Verify a saved WIP routing checkpoint without treating it as manufacturing approval."""
import json
import math
from pathlib import Path
import re
import zipfile

from verify_power_pin_candidate import check_files, read, require, sha

ROOT = Path(__file__).resolve().parents[1]
RULES_SHA = 'f1bebb3b2b5ac2ba0579f882fc0605d169c1d6a3a852a07beb8652b719e0a725'


def verify_supplier(trial, manifest, source, copper_layers):
    """Require two complete, independent supplier records for the same final bytes."""
    package = (ROOT / manifest['package']).resolve()
    require(package.is_relative_to(trial), 'Package escapes trial')
    require(sha(package) == manifest['zip_sha256'], 'Supplier package changed')
    exported = read(package.with_suffix('') / 'manifest.json')
    require(exported['source_sha256'] == source and exported['zip_sha256'] == sha(package),
            'Supplier package belongs to another source')
    require(exported['copper_layers'] == copper_layers, 'Export layer order differs')
    require(all(sha(trial / 'hardware' / n) == digest
                for n, digest in exported['native_input_sha256'].items()), 'Export inputs changed')
    with zipfile.ZipFile(package) as z:
        require(z.testzip() is None and len(z.namelist()) == len(copper_layers) + 10,
                'Invalid supplier archive')
        require(set(z.namelist()) == {row['name'] for row in exported['files']}, 'Archive file set differs')
        for row in exported['files']:
            path = package.with_suffix('') / 'gerbers' / row['name']
            require(Path(row['name']).name == row['name'] and sha(path) == row['sha256']
                    and z.read(row['name']) == path.read_bytes(), 'Gerber differs: ' + row['name'])
    records = set()
    folders = manifest['supplier_evidence']
    require(len(folders) == 2 and len(set(folders)) == 2, 'Two supplier folders required')
    for name in folders:
        folder = (trial / name).resolve()
        require(folder.is_relative_to(trial), 'Supplier evidence escapes trial')
        receipt = read(folder / 'receipt.json'); records.add(receipt['record_id'])
        require(receipt['zip_sha256'] == manifest['zip_sha256'], 'Wrong supplier input')
        require(sha(folder / 'rules.json') == RULES_SHA, 'Supplier rules changed')
        rows = re.findall(r'([^\n]+)\t(\d+),\s*(\d+),\s*(\d+)\tDetails', (folder / 'rows.txt').read_text())
        require(len(rows) == 29 and all(int(d) == int(w) == 0 for _, d, w, _ in rows),
                'Supplier rows incomplete or not green')
        count = 0
        for action in read(folder / 'dfm.json')['actions']:
            if action['name'] == 'jlc_analysis_smt':
                require(not action['results'], 'Unexpected SMT scope'); continue
            require(action['results'], 'Unanalyzed supplier action')
            for layer in action['results']:
                for m in layer.get('meas') or []:
                    c, s = action['categories'][m['cat_num']], m['meas_shape']
                    require(c['type'] == 'CGT_LINE_SEGMENT' and len(s) == 5 and s[2] == 'L',
                            'Unknown supplier measurement')
                    require(math.hypot(s[3]-s[0], s[4]-s[1]) >= c['range'][1], 'Supplier measurement not green')
                    count += 1
        require(count == sum(int(g) for _, _, _, g in rows), 'Supplier raw/UI totals differ')
        summary = read(folder / 'summary.json')
        require(summary['counts'] == {'danger': 0, 'warning': 0, 'good': count}
                and summary['record_id'] == receipt['record_id'] and not summary['smt_analyzed'],
                'Supplier summary differs')
        require((folder / 'report.pdf').read_bytes().startswith(b'%PDF'), 'Missing supplier PDF')
    require(len(records) == 2 and records == set(manifest['supplier_records']), 'Supplier records differ')
    return sorted(records)


def verify(trial):
    trial = Path(trial).resolve()
    evidence = trial / 'evidence'
    manifest = read(evidence / 'routing-checkpoint.json')
    count = check_files(trial, manifest)
    pcb = trial / 'hardware/collar-tracker.kicad_pcb'
    source = sha(pcb)
    require(source == manifest['source_sha256'], 'Candidate PCB differs from checkpoint')
    require(manifest['manufacturing_release'] is False and manifest['electrical_acceptance'] == 'HOLD',
            'Saved layout evidence cannot establish electrical or manufacturing release')
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
    require(inv['footprints'] == 71 and inv['ground_pads'] == 97
            and inv['rf_segments'] == 24 and inv['rf_segments_preserved'], 'Critical layout invariant failed')
    if inv.get('copper_layers', 4) == 6:
        require(trial.name == 'power-r05h-six-layer' and inv['ground_layer_tracks'] == 0
                and inv['inner_tracks'] > 0
                and set(inv['track_layers']) <= {'F.Cu', 'In2.Cu', 'In3.Cu', 'B.Cu'},
                'Six-layer signal/ground allocation changed')
        planes = {'In1.Cu', 'In4.Cu'}
        copper_layers = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']
    else:
        require(inv.get('copper_layers', 4) == 4 and inv['inner_tracks'] == 0,
                'Four-layer ground-only inner allocation changed')
        planes = {'In1.Cu', 'In2.Cu'}
        copper_layers = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
    require(set(inv['planes']) == planes and all(
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
    records = []
    if manifest['supplier_records']:
        require(not any(drc[k] for k in ['violations', 'unconnected_items', 'schematic_parity'])
                and inv['returns_outside_2mm'] == 0, 'Final layout checks are incomplete')
        records = verify_supplier(trial, manifest, source, copper_layers)
    return {'revision': trial.name, 'source_sha256': source, 'verified_files': count,
            'native_drc': manifest['native_drc'], 'returns_outside_2mm': inv['returns_outside_2mm'],
            'supplier_records': records,
            'result': 'SAVED EVIDENCE VERIFIED', 'electrical_acceptance': 'HOLD',
            'manufacturing_release': False}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trial', type=Path)
    print(json.dumps(verify(parser.parse_args().trial), indent=2))
