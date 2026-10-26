#!/usr/bin/env python3
"""Verify saved assembly-review identities and completeness, not factory acceptance."""
import csv
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'assembly/pcba-r01'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(name):
    return json.loads((OUT/name).read_text())


def verify():
    checkpoint = read('checkpoint.json')
    for name, digest in checkpoint['files'].items():
        p = (ROOT/name).resolve()
        require(p.is_relative_to(ROOT) and sha(p) == digest, f'PCBA review identity changed: {name}')
    checks = read('file-checks.json')
    for name, digest in checks['inputs'].items():
        require(sha(ROOT/name) == digest, f'PCBA input changed: {name}')
    for name, digest in checks['outputs'].items():
        require(sha(OUT/name) == digest, f'PCBA output changed: {name}')
    contacts = read('contact-export.json')
    require(contacts['source_sha256'] == checks['pcb_sha256'], 'PCBA contact PCB changed')
    require(sha(ROOT/'scripts/export_pcba_contacts.py') == contacts['exporter_sha256'], 'Contact exporter changed')
    for name, digest in contacts['outputs'].items():
        require(sha(OUT/name) == digest, f'Contact export changed: {name}')
    source = ROOT/'experiments/power-r05l-charge-interlock'
    netlist = json.loads((source/'evidence/native-netlist.json').read_text())
    old = json.loads((source/'assembly/assembly-check.json').read_text())
    require(sha(source/'evidence/native-netlist.json') == old['inputs'][str((source/'evidence/native-netlist.json').relative_to(ROOT))], 'Native netlist changed')
    for name in ['interface-pads.csv', 'pin-one.csv', 'fitted-pads.csv']:
        for p in csv.DictReader((OUT/name).open()):
            if p['pin']:
                require(f"{p['reference']}.{p['pin']}" in netlist['nets'].get(p['net'], []), f'Wrong interface net: {p}')
    bom = list(csv.DictReader((OUT/'bom.csv').open()))
    by_mpn = {r['Comment']:set(r['Designator'].split(',')) for r in bom}
    refs = [ref for r in bom for ref in r['Designator'].split(',')]
    require(len(by_mpn) == 44 and len(refs) == len(set(refs)) == 81, 'Incomplete or duplicate BOM')
    require(all(int(r['Quantity']) == len(r['Designator'].split(',')) for r in bom), 'BOM quantity mismatch')
    native = {r['Designator']:r for r in csv.DictReader((OUT/'cpl.csv').open())}
    reviewed = {r['Designator']:r for r in csv.DictReader((OUT/'cpl-jlc-review.csv').open())}
    require(set(native) == set(reviewed) == set(refs), 'BOM/CPL references differ')
    changed = set()
    for ref in refs:
        require(all(native[ref][k] == reviewed[ref][k] for k in ['Mid X','Mid Y','Layer']), f'Placement moved: {ref}')
        if float(native[ref]['Rotation']) != float(reviewed[ref]['Rotation']):
            changed.add(ref)
    orientation = read('orientation-review.json')
    require(len(orientation['rows']) == 14 and len(changed) == 13, 'Orientation review coverage changed')
    for r in orientation['rows']:
        require(float(reviewed[r['reference']]['Rotation']) == r['proposed_angle'], 'Wrong supplier angle')
    for name in ['jlc-library-match.json','jlc-reviewed-match.json']:
        match = read(name)
        for filename, digest in match['input_sha256'].items():
            require(sha(OUT/filename) == digest, 'Supplier evidence refers to another upload')
        require(len(match['rows']) == 44, 'Incomplete supplier matching evidence')
        for r in match['rows']:
            require(set(filter(None,(r['top']+','+r['bottom']).split(','))) == by_mpn[r['requested_mpn']], 'Supplier reference group differs')
            if r['part_code']:
                require(r['matched_mpn'] == r['requested_mpn'], 'Unapproved supplier substitution')
            else:
                require(r['top'] == 'Q1' and not r['bottom'] and r['matched_mpn'] is None, 'Unexpected unmatched part')
        require(sum(bool(r['part_code']) for r in match['rows']) == 43, 'Supplier match count changed')
        require(not any(match[k] for k in ['procurement_accepted','rotations_accepted','smt_accepted']), 'Unexpected acceptance claim')
    preview = read('jlc-preview-positions.json')
    require(preview['input_cpl_sha256'] == sha(OUT/'cpl-jlc-review.csv'), 'Stale placement preview')
    require(len(preview['placements']) == 80 and preview['missing'] == ['Q1'], 'Partial preview coverage changed')
    require({r['reference'] for r in preview['placements']} == set(refs)-{'Q1'}, 'Preview references differ')
    for r in preview['placements']:
        p = reviewed[r['reference']]
        require((r['x_mm'],r['y_mm'],r['angle'],r['side']) == (float(p['Mid X']),float(p['Mid Y']),float(p['Rotation']),p['Layer'].lower()), 'Supplier placement differs')
    require(not preview['complete_assembly_accepted'] and not preview['smt_accepted'], 'Incomplete preview promoted to acceptance')
    release = json.loads((ROOT/'release/collar-tracker-r05l-pcba-r01-review.json').read_text())
    require(sha(ROOT/release['package']) == release['sha256'], 'PCBA review ZIP changed')
    with zipfile.ZipFile(ROOT/release['package']) as z:
        require(z.testzip() is None and set(z.namelist()) == set(release['members']), 'Invalid PCBA ZIP')
        for name, digest in release['members'].items():
            require(hashlib.sha256(z.read(name)).hexdigest() == digest, 'PCBA archive member changed')
    return dict(result='PASS', scope='Saved file identities, native nets and supplier read-back only',
                fitted_references=81, matched_mpns=43, required_mpns=44,
                corrected_rotations=13, preview_references=80, missing_preview=['Q1'],
                smt_accepted=False, production_release=False)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
