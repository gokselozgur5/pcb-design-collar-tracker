#!/usr/bin/env python3
"""Read-only native/manufacturer, supplier-origin and r02 artifact checks."""
import csv
import hashlib
import json
import math
from pathlib import Path
import zipfile

from review_pcba_connectors import native_lands

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assembly/pcba-r02'
BASE = ROOT / 'assembly/pcba-r01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify():
    r = json.loads((OUT / 'connector-review.json').read_text())
    require(not r['production_release'] and not r['smt_accepted'], 'False release claim')
    for name, digest in r['input_sha256'].items():
        require(sha(ROOT / name) == digest, f'Changed input: {name}')
    native_cpl, native = native_lands()
    require(native == r['native_lands'], 'Native pad export changed')

    def land(ref, pin, x, y, width, height, net):
        candidates = [p for p in native[ref] if p['pin'] == str(pin) and p['net'] == net]
        expected = (x, y, width, height)
        require(any(all(abs(p[k] - v) < 1e-6 for k, v in zip(
            ('x_mm', 'y_mm', 'width_mm', 'height_mm'), expected)) for p in candidates),
            f'{ref}.{pin}: manufacturer land or electrical function differs')

    d = r['ufl']['manufacturer_dimensions_mm']
    for ref, net in [('J1', '/LTE_ANT'), ('J2', '/GNSS_ANT')]:
        land(ref, 1, -(d['signal_inner_edge'] + d['signal_length'] / 2), 0,
             d['signal_length'], d['signal_width'], net)
        for sign in (-1, 1):
            land(ref, 2, 0, sign * (d['ground_outer_span'] + d['ground_inner_gap']) / 4,
                 d['ground_length'], (d['ground_outer_span'] - d['ground_inner_gap']) / 2, '/GND')
        require(len(native[ref]) == 3, f'Unexpected {ref} pad count')
    sim_nets = {1: '/SIM_1V8', 2: '/SIM_RST', 3: '/SIM_CLK', 5: '/GND',
                6: 'unconnected-(J6-C6_VPP_UNUSED-Pad6)', 7: '/SIM_IO'}
    for row, y in [((1, 2, 3), 5.9), ((5, 6, 7), -5.9)]:
        for pin, x in zip(row, (2.54, 0, -2.54)):
            land('J6', pin, x, y, 1, 1.1, sim_nets[pin])
    for x in (-5.3, 5.3):
        land('J6', 8, x, 0, 1, 3, '/GND')
    require(len(native['J6']) == 8, 'SIM pad count')
    require(not r['sim']['library_model_returned'] and not r['sim']['supplier_placement_accepted'], 'SIM acceptance overclaim')
    for pin, x, y, net in [(1, -.65, -.95, '/GND'), (2, 0, -.95, '/POWER_FAULT'),
                           (3, .65, -.95, '/VIO_ENABLE'), (4, .65, .95, '/GND'),
                           (5, 0, .95, '/POWER_FAULT'), (6, -.65, .95, '/VIO_DISCHARGE')]:
        land('Q1', pin, x, y, .42, .6, net)
    require(len(native['Q1']) == 6, 'Q1 pad count')

    old = {p['Designator']: p for p in csv.DictReader((BASE / 'cpl-jlc-review.csv').open())}
    new = {p['Designator']: p for p in csv.DictReader((OUT / 'cpl-jlc-review.csv').open())}
    require(set(old) == set(new) and len(new) == 81, 'CPL reference set')
    offset = r['ufl']['model_offset_mm']
    require(math.dist(offset, [.6320028, 0]) < 1e-8, 'Unexpected dated model offset')
    old_failures, corrected_errors = [], []
    for ref in old:
        if ref not in ('J1', 'J2'):
            require(old[ref] == new[ref], f'Unexpected CPL edit: {ref}')
            continue
        for k in ('Designator', 'Rotation', 'Layer'):
            require(old[ref][k] == new[ref][k], f'Unexpected {ref} {k} edit')
        target = [float(native_cpl[ref][k]) for k in ('Mid X', 'Mid Y')]
        previous = [float(old[ref][k]) + offset[i] for i, k in enumerate(('Mid X', 'Mid Y'))]
        corrected = [float(new[ref][k]) + offset[i] for i, k in enumerate(('Mid X', 'Mid Y'))]
        old_failures.append(math.dist(previous, target) > .01)
        corrected_errors.append(math.dist(corrected, target))
    require(all(old_failures) and max(corrected_errors) < 1e-6, 'U.FL origin regression did not distinguish old/new CPL')

    q = json.loads((OUT / 'q1-review.json').read_text())
    require(q['original_mpn'] == 'DMN62D2UDW-7' and not q['bom_changed'] and not q['substitution_approved'], 'Q1 candidate was silently selected')
    require(q['availability_observation']['jlcpcb_stock'] == 1 and not q['availability_observation']['reserved'], 'Stock observation changed')
    a = q['circuit_screen']
    require(abs(a['initial_current_bound_mA_zero_fet_resistance'] - 1000 * a['vio_initial_max_V'] /
                (a['discharge_resistor_ohm_nominal'] * (1 - a['discharge_resistor_initial_tolerance_fraction']))) < .01,
            'Q1 declared current screen')
    require(abs(a['stored_capacitor_energy_uJ'] - .5 * a['vio_cap_max_uF'] * a['vio_initial_max_V'] ** 2) < .01,
            'Q1 declared energy screen')
    require(not a['hot_rds_assumption_qualified'], 'Unqualified hot RDS represented as a guarantee')

    readback = json.loads((OUT / 'jlc-preview-positions.json').read_text())
    require(readback['input_sha256']['cpl-jlc-review.csv'] == sha(OUT / 'cpl-jlc-review.csv'), 'Preview belongs to another CPL')
    require(readback['input_sha256']['bom.csv'] == sha(BASE / 'bom.csv'), 'Preview belongs to another BOM')
    require(readback['missing_references'] == ['Q1'], 'Unexpected missing preview references')
    require(len(readback['rows']) == 80 and {p['reference'] for p in readback['rows']} == set(new) - {'Q1'}, 'Preview completeness')
    for p in readback['rows']:
        cp = new[p['reference']]
        require(p['side'] == cp['Layer'], f"Preview side: {p['reference']}")
        require(all(abs(p[k] - float(cp[v])) < 1e-8 for k, v in [('x_mm', 'Mid X'), ('y_mm', 'Mid Y'), ('angle', 'Rotation')]),
                f"Preview placement: {p['reference']}")
    require(not readback['smt_accepted'] and not readback['placement_approved'], 'Preview overstated')
    for source in json.loads((OUT / 'sources.json').read_text())['sources']:
        if 'local_path' in source:
            require(sha(ROOT / source['local_path']) == source['sha256'], 'Local manufacturer drawing changed')
    checkpoint = json.loads((OUT / 'checkpoint.json').read_text())
    for name, digest in checkpoint['files'].items():
        require(sha(ROOT / name) == digest, f'Changed r02 evidence: {name}')
    manifest_path = ROOT / 'release/collar-tracker-r05l-pcba-r02-review.json'
    manifest = json.loads(manifest_path.read_text())
    package = ROOT / manifest['package']
    require(sha(package) == manifest['sha256'] and not manifest['production_release'], 'Review package identity')
    with zipfile.ZipFile(package) as z:
        require(set(z.namelist()) == set(manifest['members']), 'Review package members')
        for name, digest in manifest['members'].items():
            require(hashlib.sha256(z.read(name)).hexdigest() == digest, f'Review package member: {name}')
    return {'result': 'PASS', 'native_manufacturer_references_checked': ['J1', 'J2', 'J6', 'Q1'],
            'old_ufl_model_centre_failures': sum(old_failures), 'corrected_model_centre_max_error_mm': max(corrected_errors),
            'supplier_preview_references': 80, 'missing_reference': 'Q1', 'sim_model_missing': True,
            'q1_substitution_approved': False, 'smt_accepted': False, 'production_release': False}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
