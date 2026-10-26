#!/usr/bin/env python3
"""Freeze the ROHM Q1 screen and the actual, non-passing JLC SMT run."""
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import zipfile

from prepare_pcba_r03 import BASE, DEST, OUT, OLD, NEW, OLD_URL, NEW_URL

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / '.runtime/pcba-r03'
CAPTURE = RAW / 'q1-candidate'
GERBER = BASE.parent / 'evidence/collar-tracker-05l-charge-final4-40x32-dfm.zip'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + '\n')


def read_csv(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def review():
    manifest = json.loads((OUT / 'preparation.json').read_text())
    for name, digest in manifest['native_files'].items():
        current = DEST / name
        assert sha(current) == digest, name
        restored = current.read_text().replace(NEW_URL, OLD_URL).replace(
            NEW + 'TCN', OLD + '-7').replace(NEW, OLD)
        assert restored == (BASE / name).read_text(), name
    drc = json.loads((DEST.parent / 'evidence/native-drc.json').read_text())
    erc = json.loads((DEST.parent / 'evidence/native-erc.json').read_text())
    assert not any(drc[k] for k in ('violations', 'unconnected_items', 'schematic_parity'))
    assert all(not s['violations'] for s in erc['sheets'])
    with zipfile.ZipFile(GERBER) as archive:
        assert all(OLD.encode() not in archive.read(n) for n in archive.namelist())
    write('native-checks.json', {
        'result': 'PASS', 'scope': 'MPN-only revision; exact inverse substitutions recover all base native files',
        'native_sources': manifest['native_files'],
        'reports': {n: sha(DEST.parent / 'evidence' / n) for n in ('native-drc.json', 'native-erc.json')},
        'kicad_version': drc['kicad_version'],
        'inherited_ignored_drc': drc['ignored_checks'], 'inherited_ignored_erc': erc['ignored_checks'],
        'gerber_path': str(GERBER.relative_to(ROOT)), 'gerber_sha256': sha(GERBER),
        'gerber_reused_byte_for_byte': True, 'new_pcb_dfm_claimed': False,
    })

    numbers = json.loads((RAW / 'rohm-library-number.json').read_text())['result']
    packages = json.loads((RAW / 'rohm-library-package.json').read_text())['result']
    number = next(n for n in numbers if n['number'] == 'C510056')
    package = next(p['dataStr'] for p in packages if p['uuid'] == number['puuid'])
    head = package['head']
    pads = [s.split('~') for s in package['shape'] if s.startswith('PAD~')]
    library = {s[8]: [(float(s[2]) - float(head['x'])) * .254,
                      -(float(s[3]) - float(head['y'])) * .254] for s in pads}
    native = {p['pin']: p for p in read_csv(ROOT / 'assembly/pcba-r01/fitted-pads.csv')
              if p['reference'] == 'Q1'}
    cpl = {p['Designator']: p for p in read_csv(OUT / 'cpl-jlc-review.csv')}
    centre = [float(cpl['Q1'][k]) for k in ('Mid X', 'Mid Y')]
    target = {pin: [float(p['x_mm']) - centre[0], float(p['y_mm']) - centre[1]]
              for pin, p in native.items()}
    expected_nets = {'1': '/GND', '2': '/POWER_FAULT', '3': '/VIO_ENABLE',
                     '4': '/GND', '5': '/POWER_FAULT', '6': '/VIO_DISCHARGE'}
    assert {p: n['net'] for p, n in native.items()} == expected_nets
    assert set(library) == set(native)
    angles = []
    for angle in (0, 90, 180, 270):
        a = math.radians(angle)
        errors = [math.dist([x * math.cos(a) - y * math.sin(a),
                            x * math.sin(a) + y * math.cos(a)], target[pin])
                  for pin, (x, y) in library.items()]
        angles.append({'angle': angle, 'max_mm': max(errors),
                       'rms_mm': math.sqrt(sum(e * e for e in errors) / len(errors))})
    best = min(angles, key=lambda r: r['rms_mm'])
    assert best['angle'] == float(cpl['Q1']['Rotation']) == 270 and best['max_mm'] < .051
    # Tolerance and TCR act independently; worst temperature delta from 25 C is 65 C.
    resistance_scale = .99 * (1 - 100e-6 * 65)
    r21_min, r20_min = 22 * resistance_scale, 10000 * resistance_scale
    discharge_power = 1.9 ** 2 / (4 * r21_min)
    enable_power = 5.5 ** 2 / (4 * r20_min)
    write('q1-review.json', {
        'reference': 'Q1', 'mpn': 'UM6K34NTCN', 'jlc_code': 'C510056',
        'decision': 'Selected for the next assembled prototype; powered qualification remains open',
        'old_mpn': 'DMN62D2UDW-7', 'native_copper_nets_lands_unchanged': True,
        'datasheet': {'publisher': 'ROHM', 'url': NEW_URL, 'revision': '20160629 Rev.001',
                      'sha256': sha(RAW / 'um6k34n.pdf'), 'pages_inspected': [1, 2, 3, 10]},
        'stock_observation': {'observed_at_utc': '2026-10-26T09:12:24.780Z',
                              'source': 'https://jlcdfm.com/bomMatch', 'jlcpcb_stock': 828,
                              'reserved': False, 'proof': 'previews/q1-stock.png'},
        'pin_functions': {'1': 'S1', '2': 'G1', '3': 'D2', '4': 'S2', '5': 'G2', '6': 'D1'},
        'pin_nets': expected_nets,
        'prior_report_correction': 'r02 q1-review.json reversed D1/D2 names on 3/6. Native symbol already names 3 D2 / 6 D1. Both sources and gates are common; no circuit change.',
        'package_mm': {'pitch': .65, 'body_length_max': 2.1, 'body_width_max': 1.35,
                       'lead_span_max': 2.2, 'height_max': 1, 'lead_width_min_max': [.15, .30],
                       'existing_pad_width_length': [.42, .60], 'existing_row_centres': 1.9},
        'package_limit': 'ROHM page 10 terminal-position areas are not a recommended solder-land drawing; standard UMT6-compatible native lands retained.',
        'ratings_25C': {'vds_max_V': 50, 'vgs_abs_max_V': 8, 'id_continuous_mA': 200,
                        'power_total_mW': 150, 'power_element_mW': 120,
                        'theta_ja_total_C_W': 833, 'theta_ja_element_C_W': 1042,
                        'rds_max_at_1v5_200mA_ohm': 2.8, 'rds_max_at_1v2_100mA_ohm': 3.3,
                        'gate_leak_at_8V_uA': 10},
        'circuit_screen': {'role': 'U4 enable pull-down and external 1.8 V rail discharge; not the modem power switch',
                           'max_rail_V': 5.5, 'vio_initial_max_V': 1.9, 'vio_cap_max_uF': 12,
                           'temperature_C': [-40, 85], 'r21_min_ohm': r21_min,
                           'r20_min_ohm': r20_min,
                           'initial_current_bound_mA': 1000 * 1.9 / r21_min,
                           'stored_energy_uJ': .5 * 12 * 1.9 ** 2,
                           'discharge_fet_power_bound_mW': discharge_power * 1000,
                           'enable_fet_power_bound_mW': enable_power * 1000,
                           'combined_fet_power_bound_mW': (discharge_power + enable_power) * 1000,
                           'power_bound_method': 'For any nonnegative channel resistance R, V^2 R/(Rs+R)^2 <= V^2/(4Rs)',
                           'reference_land_element_limit_at_85C_mW': 1000 * (150 - 85) / 1042,
                           'reference_land_total_limit_at_85C_mW': 1000 * (150 - 85) / 833,
                           'pulse_800mA_rating_used': False,
                           'limits': 'Reference-land thermal comparison, not actual-board thermal proof. 800 mA applies only <=10 us/1% duty. Hot RDS, startup/falling rail, resistor pulse behavior and 12 uF domain remain prototype acceptance items.'},
        'gate_drive_screen': {'source': 'https://www.ti.com/lit/ds/symlink/sn74lvc1g14.pdf',
                              'revision': 'SCES218AA, October 2025, table 5.5',
                              'minimum_supply_V': 1.65, 'minimum_high_at_100uA_V': 1.55,
                              'maximum_low_at_100uA_V': .1,
                              'two_gate_leaks_plus_1M_pull_down_at_5v5_uA': 25.5,
                              'limits': 'Static load screen using ROHM 25 C leakage; hot leakage, transients and collapse below 1.65 V are not guaranteed here.'},
        'library': {'attribution': 'JLCEDA / EasyEDA Official Library',
                    'url': 'https://easyeda.com/', 'package_uuid': number['puuid'],
                    'number_response_sha256': sha(RAW / 'rohm-library-number.json'),
                    'package_response_sha256': sha(RAW / 'rohm-library-package.json'),
                    'pin_centres_mm': library, 'native_relative_pin_centres_mm': target,
                    'angle_candidates': angles, 'selected_supplier_angle': 270,
                    'native_angle_unchanged': 90,
                    'limit': '0.05 mm library/native row-centre difference is not a pad displacement edit or solder-process qualification.'},
        'production_release': False,
    })

    for local, remote in [('bom.csv', '014-downloadByFileAccessId.bin'),
                          ('cpl-jlc-review.csv', '015-downloadByFileAccessId.bin')]:
        assert (OUT / local).read_bytes() == (CAPTURE / remote).read_bytes()
    with zipfile.ZipFile(CAPTURE / '012-downloadByFileAccessId.bin') as z:
        preview = json.loads(json.loads(z.read('bom_merge.json'))['data'])
    bom = {ref: r['Comment'] for r in read_csv(OUT / 'bom.csv') for ref in r['Designator'].split(',')}
    rows = []
    for board in preview['designator_info']:
        for key, side in [('top', 'Top'), ('bottom', 'Bottom')]:
            for part in board[key]:
                p = part['ec'] or part['oc']
                ref, code = part['des'], part['lc_code']
                assert part['is_mount'] and side == cpl[ref]['Layer']
                assert bom[ref] == preview['comp_info'][code]['lc_model']
                for a, b in [('x', 'Mid X'), ('y', 'Mid Y'), ('ang', 'Rotation')]:
                    assert abs(float(p[a]) - float(cpl[ref][b])) < 1e-6
                rows.append({'reference': ref, 'side': side, 'part_code': code, 'mpn': bom[ref],
                             'x_mm': float(p['x']), 'y_mm': float(p['y']), 'angle': float(p['ang'])})
    assert len(rows) == 81 and {p['reference'] for p in rows} == set(bom) == set(cpl)
    write('jlc-preview-positions.json', {
        'observed_at_utc': '2026-10-26T09:22:00Z', 'source': 'https://jlcdfm.com/bomMatch',
        'pcb_record': '637366801595977730', 'method': 'Actual reupload, reload and downloaded placement/MPN comparison; supplier BOM/CPL downloads equal local bytes',
        'input_sha256': {n: sha(OUT / n) for n in ('bom.csv', 'cpl-jlc-review.csv')},
        'raw_response_sha256': sha(CAPTURE / '012-downloadByFileAccessId.bin'),
        'matched_mpns': len(preview['comp_info']), 'counts': preview['check_info'],
        'missing_references': [], 'rows': sorted(rows, key=lambda r: r['reference']),
        'j6_visual_model': 'Placeholder; backend SMT reports J6 body spacing but no explicit J6 pin-overlap evidence',
        'dfm_save_and_close_submitted': True, 'factory_placement_accepted': False,
    })
    with zipfile.ZipFile(CAPTURE / '017-downloadByFileAccessId.bin') as z:
        result = json.loads(z.read('dfm.json'))
    smt = next(a for a in result['actions'] if a['name'] == 'jlc_analysis_smt')
    assert smt['results']
    # Remove account/order identifiers and keep actual category/measurement data intact.
    write('smt-results.json', {'pcb_record': '637366801595977730',
                             'raw_zip_sha256': sha(CAPTURE / '017-downloadByFileAccessId.bin'),
                             'actions': [smt], 'accepted': False,
                             'note': 'Returned measurements are capped at 50 per layer/category; truncate.orig_num preserves actual totals.'})
    (OUT / 'previews').mkdir(exist_ok=True)
    for source, target_name in [('um6k34n-live-stock.png', 'q1-stock.png'),
                                ('r03-top.png', 'top.png'), ('r03-bottom.png', 'bottom.png'),
                                ('r03-smt-initial.png', 'smt-initial.png'),
                                ('r03-smt-lead-overlap.png', 'smt-lead-overlap.png'),
                                ('r03-smt-board-edge.png', 'smt-board-edge.png')]:
        shutil.copy2(CAPTURE / source, OUT / 'previews' / target_name)
    shutil.copy2(CAPTURE / '003-downloadByFileAccessId.bin', OUT / 'jlc-rules.json')
    shutil.copy2(CAPTURE / 'DFM analysis report_JLCDFM_collar-tracker-05l-charge-final4-40x32-dfm.zip.pdf', OUT / 'smt-report.pdf')
    assert sha(OUT / 'jlc-rules.json') == 'f1bebb3b2b5ac2ba0579f882fc0605d169c1d6a3a852a07beb8652b719e0a725'
    drawing = (ROOT / 'assembly/pcba-r02/placement-reference.svg').read_text()
    for old, new in [
        ('r05l / PCBA r02', 'r05m / PCBA r03'),
        ('Original DMN62D2UDW-7 remains mandatory; candidate not selected.', 'Selected ROHM UM6K34NTCN; supplier CPL angle 270 degrees.'),
        ('1 S1 / 2 G1 / 3 D1 / 4 S2 / 5 G2 / 6 D2', '1 S1 / 2 G1 / 3 D2 / 4 S2 / 5 G2 / 6 D1'),
        ('D1: VIO_ENABLE; D2: VIO_DISCHARGE', 'D2: VIO_ENABLE; D1: VIO_DISCHARGE'),
        ('GCT SIM8051 D6; Diodes SOT363.', 'GCT SIM8051 D6; ROHM UMT6.')]:
        assert old in drawing
        drawing = drawing.replace(old, new)
    (OUT / 'placement-reference.svg').write_text(drawing)
    print(json.dumps({'native': 'PASS', 'bom_matches': 44, 'placements_verified': len(rows),
                      'smt': 'ACTUALLY_RUN_NOT_ACCEPTED', 'production_release': False}))


if __name__ == '__main__':
    review()
