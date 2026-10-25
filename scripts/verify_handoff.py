#!/usr/bin/env python3
"""Read-only integrity check for the portable checkpoint, not new PCB acceptance."""
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PCB = 'experiments/35x28-clearance-r034/hardware/collar-tracker.kicad_pcb'
ZIP = 'release/collar-tracker-0.3.4-35x28-dfm.zip'
ANCHORS = {
    PCB: '597ebdee59550b6d07eb104274eabee57b038ea6c87da2dec38c1201f78c89b2',
    ZIP: '735ff8506629eb931cdd4a1847796e0eae2ec24deebb4f579f7441bb2182c990',
}
RULES_SHA = 'f1bebb3b2b5ac2ba0579f882fc0605d169c1d6a3a852a07beb8652b719e0a725'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(relative):
    return json.loads((ROOT / relative).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_current():
    trial=ROOT/'experiments/paul-nanosim-r04i-sim-access-40x32'
    evidence=trial/'evidence'
    checkpoint=json.loads((evidence/'routing-checkpoint.json').read_text())
    for item in checkpoint['files']:
        path=(trial/item['path']).resolve()
        require(path.is_relative_to(trial),'Current evidence path escapes trial')
        require(path.stat().st_size==item['bytes'] and sha(path)==item['sha256'],f'Current evidence changed: {item["path"]}')
    source=sha(trial/'hardware/collar-tracker.kicad_pcb')
    require(source==checkpoint['source_sha256'],'Current PCB identity mismatch')
    package=ROOT/checkpoint['package']
    require(sha(package)==checkpoint['zip_sha256'],'Current ZIP identity mismatch')
    exported=json.loads((package.with_suffix('')/'manifest.json').read_text())
    require(exported['source_sha256']==source and exported['zip_sha256']==checkpoint['zip_sha256'],'Export does not match current PCB/ZIP')
    require(all(sha(trial/'hardware'/n)==digest for n,digest in exported['native_input_sha256'].items()),'Export inputs differ from current native project')
    with zipfile.ZipFile(package) as z:
        require(z.testzip() is None and len(z.namelist())==14,'Invalid current ZIP')
        for name in z.namelist():
            require(Path(name).name==name,'Unexpected current ZIP path')
            require(z.read(name)==(package.with_suffix('')/'gerbers'/name).read_bytes(),f'Current package mismatch: {name}')
    drc=json.loads((evidence/'native-drc.json').read_text())
    require(not any(drc[k] for k in ['violations','unconnected_items','schematic_parity']),'Current saved DRC failed')
    erc=json.loads((evidence/'native-erc.json').read_text())
    require(all(not s['violations'] for s in erc['sheets']),'Current saved ERC failed')
    reports={name:json.loads((evidence/(name+'.json')).read_text()) for name in ['layout-inventory','contact-components','esd-paths','card-insertion-review','attachment-review','passive-copper-review','power-path-review','route-geometry']}
    require(all(d['source_sha256']==source for d in reports.values()),'Stale current geometry report')
    inv=reports['layout-inventory']
    require(inv['returns_outside_2mm']==inv['inner_tracks']==0 and inv['rf_segments_preserved'],'Current layout screen failed')
    require(all(p['filled_outline_count']==1 and p['zone_nets']==['/GND'] and not p['ground_vias_outside'] for p in inv['planes'].values()),'Current inner GND fill failed')
    require(not reports['contact-components']['ground_pads_without_track_path_to_via'],'Missing local GND path')
    paths=reports['esd-paths']['paths']
    require(len(paths)==4 and all(not p['bypasses_esd_land'] and p['connector_to_esd'] and p['esd_to_modem'] for p in paths),'Current SIM protection topology failed')
    require(reports['card-insertion-review']['pcb_entry_projection_clear'],'Current card-entry projection failed')
    records=set()
    for n in [1,2]:
        folder=evidence/f'jlc-check{n}'
        receipt=json.loads((folder/'receipt.json').read_text());records.add(receipt['record_id'])
        require(receipt['zip_sha256']==checkpoint['zip_sha256'],'Wrong current supplier input')
        require(sha(folder/'rules.json')==RULES_SHA,'Current supplier rules changed')
        rows=re.findall(r'([^\n]+)\t(\d+),\s*(\d+),\s*(\d+)\tDetails',(folder/'rows.txt').read_text())
        require(len(rows)==29 and all(int(d)==int(w)==0 for _,d,w,_ in rows),'Current JLC rows not green')
        report=json.loads((folder/'dfm.json').read_text())
        for action in report['actions']:
            if action['name']=='jlc_analysis_smt':
                require(not action['results'],'Current SMT scope changed');continue
            require(action['results'],f'Current unanalyzed action: {action["name"]}')
            for layer in action['results']:
                for m in layer.get('meas') or []:
                    c=action['categories'][m['cat_num']];s=m['meas_shape']
                    require(c['type']=='CGT_LINE_SEGMENT' and len(s)==5 and s[2]=='L','Unknown current supplier geometry')
                    require(math.hypot(s[3]-s[0],s[4]-s[1])>=c['range'][1],'Current supplier measurement not green')
    require(len(records)==2 and records==set(checkpoint['supplier_records']),'Wrong current supplier records')
    return {'revision':'r04i','files':len(checkpoint['files']),'source_sha256':source,'supplier_records':sorted(records),'result':'PASS'}


def verify_mechanical(pcb_sha):
    folder = ROOT / 'mechanical/swim-r01'
    parameters = json.loads((folder / 'parameters.json').read_text())
    checks = json.loads((folder / 'checks.json').read_text())
    meshes = json.loads((folder / 'mesh-checks.json').read_text())
    require(checks['source_sha256'] == meshes['pcb_sha256'] == pcb_sha,
            'Mechanical evidence references another PCB')
    require(checks['parameter_sha256'] == sha(folder / 'parameters.json'),
            'Stale mechanical parameter checks')
    require(checks['checker_sha256'] == sha(ROOT / 'scripts/build_swim_enclosure.py'),
            'Mechanical checker changed since saved results')
    require(checks['all_declared_geometry_checks_pass'] and len(checks['checks']) == 30
            and all(c['pass_'] for c in checks['checks']), 'Mechanical geometry screen failed')
    require(not parameters['target']['qualified'], 'Prototype unexpectedly claims qualification')
    require(set(meshes['cad_input_sha256']) == {'parameters.json', 'parameters.scad', 'enclosure.scad'},
            'Incomplete mechanical CAD identity')
    for name, digest in meshes['cad_input_sha256'].items():
        require(sha(folder / name) == digest, f'CAD changed since mesh export: {name}')
    expected = {n + '.stl' for n in ['body', 'lid', 'carrier', 'contact', 'contact_seal',
                                    'magnet_plug', 'dock', 'boot']}
    require(len(meshes['meshes']) == 8 and {m['file'] for m in meshes['meshes']} == expected,
            'Incomplete exported mesh set')
    for mesh in meshes['meshes']:
        require(sha(folder / mesh['file']) == mesh['sha256'], f'Mesh changed: {mesh["file"]}')
        require(mesh['closed_oriented_manifold'] and mesh['connected_surfaces'] == 1
                and mesh['bad_edge_count'] == mesh['collapsed_faces_at_1e_5mm'] == 0,
                f'Exported mesh failed: {mesh["file"]}')
    require(set(meshes['previews']) == {'exploded.png', 'section.png', 'mounted.png'},
            'Incomplete mechanical preview set')
    for name, digest in meshes['previews'].items():
        require(sha(folder / name) == digest, f'Mechanical preview changed: {name}')
    return {'revision': 'swim-r01', 'analytical_checks': 30, 'closed_meshes': 8,
            'result': 'PASS', 'ingress_qualified': False}


def verify_populated_fit(pcb_sha):
    folder = ROOT / 'mechanical/swim-r02-fit'
    native = json.loads((folder / 'components.native.json').read_text())
    profile = json.loads((folder / 'fit-profile.json').read_text())
    fit = json.loads((folder / 'populated-fit.json').read_text())
    shell = json.loads((folder / 'checks.json').read_text())
    meshes = json.loads((folder / 'mesh-checks.json').read_text())
    require(native['source_sha256'] == fit['pcb_sha256'] == shell['source_sha256']
            == meshes['pcb_sha256'] == pcb_sha, 'Populated fit references another PCB')
    require(sha(ROOT / native['source']) == pcb_sha, 'Populated native input changed')
    require(native['exporter_sha256'] == sha(ROOT / 'scripts/export_populated_geometry.py'),
            'Populated exporter changed; regenerate geometry')
    require(fit['checker_sha256'] == sha(ROOT / 'scripts/audit_populated_fit.py'),
            'Populated checker changed; regenerate fit report')
    require(len(native['parts']) == len(profile['parts']) == 55,
            'Incomplete populated footprint/profile count')
    require(fit['checked'] == 53 and fit['checked_geometry_pass'] and not fit['violations']
            and all(c['pass_'] for c in fit['hardware_checks']), 'Populated geometry screen failed')
    require(not fit['production_assembly_complete'] and fit['open_items'],
            'Fit prototype unexpectedly claims complete assembly')
    require(any(v['ref'] == 'D1' and v['obstacle'] == 'carrier ledge'
                for v in fit['original_carrier_violations']), 'Missing original carrier regression')
    for name, digest in fit['input_sha256'].items():
        require(sha(folder / name) == digest, f'Populated fit input changed: {name}')
    require(shell['parameter_sha256'] == sha(folder / 'parameters.json')
            and shell['checker_sha256'] == sha(ROOT / 'scripts/build_swim_enclosure.py')
            and len(shell['checks']) == 30 and all(c['pass_'] for c in shell['checks']),
            'Populated shell checks stale or failed')
    for name, digest in meshes['cad_input_sha256'].items():
        require(sha(folder / name) == digest, f'Populated CAD input changed: {name}')
    require(meshes['exporter_sha256'] == sha(ROOT / 'scripts/export_populated_enclosure.py'),
            'Populated mesh exporter changed')
    require(len(meshes['meshes']) == 8 and len(meshes['previews']) == 4,
            'Incomplete populated mesh/preview set')
    for mesh in meshes['meshes']:
        require(sha(folder / mesh['file']) == mesh['sha256'] and mesh['closed_oriented_manifold']
                and mesh['connected_surfaces'] == 1 and mesh['bad_edge_count'] == 0,
                f'Populated mesh failed or changed: {mesh["file"]}')
    for name, digest in meshes['previews'].items():
        require(sha(folder / name) == digest, f'Populated preview changed: {name}')
    controls = {c['case']: c for c in meshes['intersection_controls']}
    require(set(controls) == {'current-carrier', 'original-carrier'}, 'Incomplete CAD controls')
    require(controls['current-carrier']['source_sha256'] == sha(folder / 'enclosure.scad')
            and controls['current-carrier']['empty'] and controls['current-carrier']['returncode'] == 1
            and controls['current-carrier']['interference_volume_mm3'] == 0,
            'Current CAD interference control failed')
    require(not controls['original-carrier']['empty'] and controls['original-carrier']['returncode'] == 0
            and controls['original-carrier']['interference_volume_mm3'] > 0,
            'Original CAD interference control did not detect the defect')
    return {'revision': 'swim-r02-fit', 'checked_entries': 53, 'closed_meshes': 8,
            'result': 'PASS', 'ingress_qualified': False, 'production_assembly_complete': False}


def verify_review_bundle(sidecar_path='release/collar-tracker-r04i-swim-r01-review.json'):
    sidecar = read_json(sidecar_path)
    path = ROOT / sidecar['package']
    require(path.is_relative_to(ROOT / 'release') and sha(path) == sidecar['zip_sha256'],
            'Review bundle identity mismatch')
    with zipfile.ZipFile(path) as z:
        require(z.testzip() is None, 'Corrupt review bundle')
        manifest = json.loads(z.read('manifest.json'))
        require(manifest == {k: v for k, v in sidecar.items() if k not in {'package', 'zip_sha256'}},
                'Review bundle manifest differs from sidecar')
        names = [f['archive_path'] for f in manifest['files']]
        require(len(names) == len(set(names)) and set(z.namelist()) == set(names) | {'manifest.json'},
                'Unexpected or duplicate review bundle entries')
        for item in manifest['files']:
            data = z.read(item['archive_path'])
            require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'],
                    f'Review bundle entry changed: {item["archive_path"]}')
            if item.get('source_path'):
                source = (ROOT / item['source_path']).resolve()
                require(source.is_relative_to(ROOT) and sha(source) == item['sha256'],
                        f'Review bundle is stale: {item["source_path"]}')
            if item.get('derived_from'):
                source = (ROOT / item['derived_from']).resolve()
                require(source.is_relative_to(ROOT) and sha(source) == item['derived_from_sha256'],
                        f'Derived review input is stale: {item["derived_from"]}')
    return {'files': len(names), 'zip_sha256': sidecar['zip_sha256'], 'result': 'PASS'}


def verify_power_candidate():
    """Verify the unfinished successor without treating its saved state as acceptance."""
    trial = ROOT / 'experiments/power-r05-supervised'
    checkpoint = json.loads((trial / 'evidence/routing-checkpoint.json').read_text())
    names = [item['path'] for item in checkpoint['files']]
    require(len(names) == len(set(names)), 'Duplicate r05 evidence paths')
    for item in checkpoint['files']:
        path = (trial / item['path']).resolve()
        require(path.is_relative_to(trial), 'r05 evidence escapes trial')
        require(path.stat().st_size == item['bytes'] and sha(path) == item['sha256'],
                f'r05 checkpoint changed: {item["path"]}')
    source = sha(trial / 'hardware/collar-tracker.kicad_pcb')
    require(source == checkpoint['source_sha256'], 'r05 PCB identity mismatch')
    drc = json.loads((trial / 'evidence/native-drc.json').read_text())
    counts = {key: len(drc[key]) for key in ['violations', 'unconnected_items', 'schematic_parity']}
    require(counts == checkpoint['native_drc'], 'r05 native counts differ from handoff')
    require(not drc['violations'] and not drc['schematic_parity'], 'r05 saved geometry/parity failed')
    require(drc['unconnected_items'], 'Routed successor needs an explicitly reviewed checkpoint')
    baseline = ROOT / 'experiments/paul-nanosim-r04i-sim-access-40x32/hardware'
    old = json.loads((baseline / 'collar-tracker.kicad_pro').read_text())
    new = json.loads((trial / 'hardware/collar-tracker.kicad_pro').read_text())
    require(old['board']['design_settings'] == new['board']['design_settings']
            and old['net_settings'] == new['net_settings'], 'r05 inherited rules changed')
    require(sha(baseline / 'collar-tracker.kicad_dru') == sha(trial / 'hardware/collar-tracker.kicad_dru'),
            'r05 custom rules changed')
    reports = {name: json.loads((trial / f'evidence/{name}.json').read_text())
               for name in ['route-geometry', 'layout-inventory', 'attachment-review', 'esd-paths']}
    require(all(report['source_sha256'] == source for report in reports.values()), 'Stale r05 geometry report')
    inventory = reports['layout-inventory']
    require(inventory['footprints'] == 71 and inventory['ground_pads'] == 97
            and inventory['ground_vias'] == 100 and inventory['inner_tracks'] == 0
            and inventory['rf_segments_preserved'], 'r05 layout invariants changed')
    require(all(p['filled_outline_count'] == 1 and p['zone_nets'] == ['/GND']
                and not p['ground_vias_outside'] for p in inventory['planes'].values()),
            'r05 inner ground fill changed')
    require(all(g['via'] is not None and g['local_path_mm'] is not None
                for g in reports['attachment-review']['grounds']), 'r05 local ground attachment is missing')
    require(len(reports['esd-paths']['paths']) == 4 and all(
        p['connector_to_esd'] and p['esd_to_modem'] and not p['bypasses_esd_land']
        for p in reports['esd-paths']['paths']), 'r05 SIM clamp topology changed')
    require(not checkpoint['manufacturing_release'] and checkpoint['supplier_records'] == [],
            'Unfinished r05 unexpectedly claims supplier/manufacturing acceptance')
    from check_power_r05 import verify as verify_power
    power = verify_power()
    require(power['electrical_acceptance'] == 'HOLD' and not power['physical_test'],
            'Unqualified circuit unexpectedly claims electrical acceptance')
    return {'revision': 'r05-supervised', 'result': 'EVIDENCE_PASS', 'complete': False,
            'source_sha256': source, 'files': len(names), 'native_drc': counts,
            'return_screen_gaps': inventory['returns_outside_2mm'],
            'electrical_acceptance': 'HOLD', 'supplier_runs': 0}


def verify(include_review_bundle=True):
    for rel, expected in ANCHORS.items():
        require(sha(ROOT / rel) == expected, f'Baseline changed: {rel}')
    manifest = read_json('evidence/release-034/manifest.json')
    for item in manifest['files']:
        path = (ROOT / item['path']).resolve()
        require(path.is_relative_to(ROOT), 'Manifest path escapes checkout')
        require(path.stat().st_size == item['bytes'] and sha(path) == item['sha256'],
                f'Evidence changed: {item["path"]}')
    with zipfile.ZipFile(ROOT / ZIP) as archive:
        require(archive.testzip() is None and len(archive.namelist()) == 14, 'Bad baseline ZIP')
        for name in archive.namelist():
            require(Path(name).name == name, 'Unexpected ZIP path')
            require(archive.read(name) == (ROOT / Path(PCB).parents[1] / 'evidence/gerbers' / name).read_bytes(),
                    f'Gerber differs: {name}')
    records = set()
    for n in (1, 2):
        folder = f'evidence/release-034/check{n}'
        receipt = read_json(f'{folder}/receipt.json')
        require(receipt['zip_sha256'] == ANCHORS[ZIP], 'Wrong upload hash')
        records.add(receipt['record_id'])
        require(sha(ROOT / folder / 'rules.json') == RULES_SHA, 'DFM rules changed')
        rows = re.findall(r'([^\n]+)\t(\d+),\s*(\d+),\s*(\d+)\tDetails',
                          (ROOT / folder / 'rows.txt').read_text())
        require(len(rows) == 29 and all(int(d) == int(w) == 0 for _, d, w, _ in rows),
                'Historical JLC UI is not all green')
        report = read_json(f'{folder}/dfm.json')
        for action in report['actions']:
            if action['name'] == 'jlc_analysis_smt':
                require(not action['results'], 'SMT scope unexpectedly changed')
                continue
            require(action['results'], f'Unanalyzed: {action["name"]}')
            for layer in action['results']:
                for measure in layer.get('meas') or []:
                    category = action['categories'][measure['cat_num']]
                    shape = measure['meas_shape']
                    require(category['type'] == 'CGT_LINE_SEGMENT' and len(shape) == 5 and shape[2] == 'L',
                            'Unknown supplier measurement')
                    require(math.hypot(shape[3] - shape[0], shape[4] - shape[1]) >= category['range'][1],
                            f'Non-green supplier measurement: {category["name"]}')
    require(len(records) == 2, 'Expected two distinct JLC records')
    for rel in ['experiments/35x28-clearance-r034/evidence/drc.json',
                'evidence/order-readiness-20261025-r034/drc.json']:
        drc = read_json(rel)
        require(not any(drc[key] for key in ['violations', 'unconnected_items', 'schematic_parity']),
                f'Saved native check failed: {rel}')
    erc = read_json('evidence/order-readiness-20261025-r034/erc.json')
    require(all(not s['violations'] for s in erc['sheets']), 'Saved ERC failed')
    for item in read_json('references/paul-nanosim-r04/sources.json')['files']:
        require(sha(ROOT / 'references/paul-nanosim-r04' / item['file']) == item['sha256'],
                f'Manufacturer reference changed: {item["file"]}')
    for name in ['AGENTS.md', 'CLAUDE.md', 'docs/STATUS.md', 'docs/RESUME.md', 'docs/paul-nanosim.md']:
        require((ROOT / name).is_file(), f'Missing entry file: {name}')
    imports = re.findall(r'^@([^\s]+)$', (ROOT / 'CLAUDE.md').read_text(), re.M)
    require(imports == ['AGENTS.md', 'docs/STATUS.md'], 'Claude entry imports changed; review the resume chain')
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    forbidden = {'browser-profile', 'browser-tmp', 'st-browser', 'node_modules', '.venv-dfm', '.runtime', '.continuity'}
    for name in filter(None, tracked):
        path = Path(name)
        require(not forbidden.intersection(path.parts) and path.name not in {'.env', 'CLAUDE.local.md'},
                f'Local/private runtime tracked: {name}')
    current=verify_current()
    mechanical=verify_mechanical(current['source_sha256'])
    populated_fit=verify_populated_fit(current['source_sha256'])
    from audit_power_architecture import verify_saved
    power_review = verify_saved()
    power_candidate = verify_power_candidate()
    from verify_power_pin_candidate import verify as verify_power_pins
    power_pin_candidate = verify_power_pins()
    from verify_routing_candidate import verify as verify_routing
    routing_candidate = verify_routing(ROOT / 'experiments/power-r05h-six-layer')
    from verify_rf_candidate import verify as verify_rf
    rf_candidate = verify_rf()
    routing_alternatives = [verify_routing(ROOT / 'experiments' / name) for name in [
        'power-r05c-return-corridors', 'power-r05d-joint-routing', 'power-r05e-native-joint',
        'power-r05f-return-reset', 'power-r05g-local-crossings']]
    return {'baseline_revision': '0.3.4', 'evidence_files': len(manifest['files']),
            'supplier_records': sorted(records), 'result': 'PASS',
            'current':current, 'mechanical':mechanical, 'populated_fit':populated_fit,
            'power_review': power_review,
            'power_candidate': power_candidate,
            'power_pin_candidate': power_pin_candidate,
            'routing_candidate': routing_candidate,
            'rf_candidate': rf_candidate,
            'routing_alternatives': routing_alternatives,
            'review_bundle':verify_review_bundle() if include_review_bundle else 'Rebuild in progress',
            'populated_review_bundle':verify_review_bundle('release/collar-tracker-r04i-swim-r02-fit-review.json') if include_review_bundle else 'Rebuild in progress',
            'scope': 'Saved PCB evidence, declared mechanical checks and artifact integrity. No new KiCad/JLC run or PCBA, powered, RF or ingress acceptance.'}


if __name__ == '__main__':
    try:
        print(json.dumps(verify(), indent=2))
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        sys.exit(1)
