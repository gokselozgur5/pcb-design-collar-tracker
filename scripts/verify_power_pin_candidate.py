#!/usr/bin/env python3
"""Read-only r05b checkpoint verification; unfinished routing is not acceptance."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def check_files(folder, manifest):
    names = [item['path'] for item in manifest['files']]
    require(len(names) == len(set(names)), 'Duplicate checkpoint paths')
    for item in manifest['files']:
        path = (folder / item['path']).resolve()
        require(path.is_relative_to(folder.resolve()), 'Checkpoint path escapes its directory')
        require(path.stat().st_size == item['bytes'] and sha(path) == item['sha256'],
                f'Checkpoint file changed: {path.relative_to(ROOT)}')
    return len(names)


def verify():
    trial = ROOT / 'experiments/power-r05b-pin-exits'
    evidence = trial / 'evidence'
    checkpoint = read(evidence / 'routing-checkpoint.json')
    files = check_files(trial, checkpoint)
    source = sha(trial / 'hardware/collar-tracker.kicad_pcb')
    require(source == checkpoint['source_sha256'], 'r05b PCB identity changed')
    require(not checkpoint['manufacturing_release'] and checkpoint['supplier_records'] == [],
            'Unfinished r05b cannot claim manufacturing or supplier acceptance')
    drc = read(evidence / 'native-drc.json')
    counts = {k: len(drc[k]) for k in ['violations', 'unconnected_items', 'schematic_parity']}
    require(counts == checkpoint['native_drc'] ==
            dict(violations=27, unconnected_items=14, schematic_parity=0),
            'r05b saved DRC differs; review a successor explicitly')
    require(Counter((v['type'], v['severity']) for v in drc['violations']) ==
            Counter({('via_dangling', 'warning'): 27}), 'Unexpected r05b DRC violation')
    previous_evidence = ROOT / 'experiments/power-r05-supervised/evidence'
    require(drc['ignored_checks'] == read(previous_evidence / 'native-drc.json')['ignored_checks'],
            'r05b DRC disabled-check configuration changed')
    require(all('/GND' not in str(v) for v in drc['unconnected_items']), 'Open ground in r05b')
    old = ROOT / 'experiments/power-r05-supervised/hardware'
    current = trial / 'hardware'
    require(sha(old / 'collar-tracker.kicad_sch') == sha(current / 'collar-tracker.kicad_sch'),
            'r05b circuit changed; repeat circuit qualification')
    a, b = read(old / 'collar-tracker.kicad_pro'), read(current / 'collar-tracker.kicad_pro')
    require(a['board']['design_settings'] == b['board']['design_settings']
            and a['net_settings'] == b['net_settings']
            and sha(old / 'collar-tracker.kicad_dru') == sha(current / 'collar-tracker.kicad_dru'),
            'r05b inherited native rules changed')
    erc = read(evidence / 'erc.json')
    require(erc['ignored_checks'] == read(previous_evidence / 'erc.json')['ignored_checks']
            and all(not s['violations'] for s in erc['sheets']),
            'r05b ERC has violations or changed disabled checks')
    reports = {name: read(evidence / (name + '.json')) for name in
               ['route-geometry', 'layout-inventory', 'attachment-review', 'passive-copper-review',
                'esd-paths', 'card-insertion-review', 'power-path-review']}
    require(all(r['source_sha256'] == source for r in reports.values()), 'Stale r05b report')
    inv = reports['layout-inventory']
    require((inv['footprints'], inv['ground_pads'], inv['ground_vias'], inv['non_ground_vias'],
             inv['inner_tracks'], inv['rf_segments'], inv['returns_outside_2mm']) ==
            (71, 97, 113, 143, 0, 24, 2) and inv['rf_segments_preserved'],
            'r05b layout inventory changed')
    require(set(inv['planes']) == {'In1.Cu', 'In2.Cu'} and all(
        p['zone_nets'] == ['/GND'] and p['filled_outline_count'] == 1
        and not p['ground_vias_outside'] for p in inv['planes'].values()),
        'r05b inner ground plane continuity changed')
    grounds = reports['attachment-review']['grounds']
    require(len(grounds) == 94 and all(g['via'] is not None and g['local_path_mm'] is not None
                                     for g in grounds), 'r05b local ground attachment missing')
    paths = reports['esd-paths']['paths']
    require(len(paths) == 4 and all(p['connector_to_esd'] and p['esd_to_modem']
                                  and not p['bypasses_esd_land'] for p in paths),
            'r05b SIM clamp path changed')
    access = reports['card-insertion-review']
    require(access['pcb_entry_projection_clear'] and not access['overlap_candidates']
            and len(access['parts']) == 19, 'r05b SIM entry blocked')
    power = reports['power-path-review']['paths']
    require(len(power) == 12 and all(p['connected'] for p in power), 'Original power backbone opened')

    # Only the explicitly reviewed leaf removals may differ from protected geometry.
    before = read(evidence / 'placement-checks/route-geometry.json')
    after = reports['route-geometry']
    old_items = {x['id']: x for k in ['tracks', 'vias'] for x in before[k]}
    new_items = {x['id']: x for k in ['tracks', 'vias'] for x in after[k]}
    protected = set(read(evidence / 'protected-fanout.json'))
    removed = set()
    for i in range(1, 17):
        receipt = read(evidence / f'local1-trim{i}.json')
        require(receipt['pad_islands_preserved'], 'Missing native pruning invariant')
        for item in receipt['removed']:
            require(item['net'] in {'/VSYS', '/VBAT', '/NRF_ENABLE', '/POWER_GOOD', '/VIO_DISCHARGE'},
                    'Unreviewed pruned net')
            require(item['id'] not in removed, 'Duplicate pruned item')
            removed.add(item['id'])
    require(len(removed) == 21 and len(removed & protected) == 19
            and not (removed & new_items.keys()), 'Pruning receipt mismatch')
    require(len(protected) == 1369 and all(old_items[u] == new_items.get(u)
                                         for u in protected - removed),
            'Protected copper changed beyond recorded leaf removal')
    fit = verify_fit(source)
    return dict(revision='r05b-pin-exits', result='EVIDENCE_PASS', complete=False,
                source_sha256=source, files=files, native_drc=counts,
                return_screen_gaps=2, protected_items_retained=1350,
                electrical_acceptance='HOLD', supplier_runs=0, preliminary_fit=fit)


def verify_fit(source):
    folder = ROOT / 'mechanical/swim-r03-r05b-fit'
    checkpoint = read(folder / 'checkpoint.json')
    files = check_files(folder, checkpoint)
    native, profile, fit, shell = [read(folder / name) for name in
                                  ['components.native.json', 'fit-profile.json',
                                   'populated-fit.json', 'checks.json']]
    require(checkpoint['source_sha256'] == native['source_sha256'] == fit['pcb_sha256']
            == shell['source_sha256'] == source, 'r05b mechanical source changed')
    require(sha(ROOT / native['source']) == source
            and native['exporter_sha256'] == sha(ROOT / 'scripts/export_populated_geometry.py')
            and fit['checker_sha256'] == sha(ROOT / 'scripts/audit_populated_fit.py'),
            'r05b native/fit tool or source changed')
    require(len(native['parts']) == len(profile['parts']) == 71 and fit['checked'] == 69
            and fit['checked_geometry_pass'] and not fit['violations']
            and all(c['pass_'] for c in fit['hardware_checks']), 'r05b fit screen failed')
    require(sum(p['status'] == 'component_envelope_requirement' for p in profile['parts']) == 9,
            'Review resistor qualification explicitly before changing fit assumptions')
    require(not fit['production_assembly_complete'] and fit['open_items']
            and not checkpoint['physical_ingress_test'] and not checkpoint['mesh_acceptance'],
            'Preliminary r05b fit unexpectedly claims complete assembly')
    require(any(v['ref'] == 'D1' and v['obstacle'] == 'carrier ledge'
                for v in fit['original_carrier_violations']), 'Missing original carrier control')
    for name, digest in fit['input_sha256'].items():
        require(sha(folder / name) == digest, f'Stale r05b fit input: {name}')
    require(shell['parameter_sha256'] == sha(folder / 'parameters.json')
            and shell['checker_sha256'] == sha(ROOT / 'scripts/build_swim_enclosure.py')
            and len(shell['checks']) == 30 and all(c['pass_'] for c in shell['checks']),
            'r05b shell checks failed or changed')
    return dict(revision='swim-r03-r05b-fit', result='PRELIMINARY_GEOMETRY_PASS', files=files,
                checked_entries=69, unresolved_component_envelopes=9,
                ingress_qualified=False, production_assembly_complete=False)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
