#!/usr/bin/env python3
"""Read-only checks for the r05m Q1 revision and actual SMT evidence."""
import csv
import hashlib
import json
from pathlib import Path
import zipfile

from prepare_pcba_r03 import BASE, DEST, OUT, OLD, NEW, OLD_URL, NEW_URL

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def csv_rows(path, key):
    with path.open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    result = {r[key]: r for r in rows}
    require(len(result) == len(rows), f'Duplicate {key}: {path}')
    return result


def verify():
    native = json.loads((OUT / 'native-checks.json').read_text())
    for name, digest in native['native_sources'].items():
        p = DEST / name
        require(sha(p) == digest, f'Native identity: {name}')
        restored = p.read_text().replace(NEW_URL, OLD_URL).replace(NEW + 'TCN', OLD + '-7').replace(NEW, OLD)
        require(restored == (BASE / name).read_text(), f'Unexpected geometry/net/source edit: {name}')
    require(sha(ROOT / native['gerber_path']) == native['gerber_sha256'], 'Reused Gerber identity')
    for name, digest in native['reports'].items():
        require(sha(DEST.parent / 'evidence' / name) == digest, f'Native report identity: {name}')
    drc = json.loads((DEST.parent / 'evidence/native-drc.json').read_text())
    erc = json.loads((DEST.parent / 'evidence/native-erc.json').read_text())
    require(not any(drc[k] for k in ('violations', 'unconnected_items', 'schematic_parity')), 'Native DRC/parity')
    require(all(not s['violations'] for s in erc['sheets']), 'Native ERC')
    old_bom = csv_rows(ROOT / 'assembly/pcba-r01/bom.csv', 'Designator')
    bom = csv_rows(OUT / 'bom.csv', 'Designator')
    require(set(bom) == set(old_bom) and len(bom) == 44, 'BOM coverage')
    for ref, row in bom.items():
        expected = dict(old_bom[ref])
        if ref == 'Q1':
            expected.update(Comment='UM6K34NTCN', Description='UM6K34NTCN')
        require(row == expected, f'Unreviewed part substitution: {ref}')
    old_cpl = csv_rows(ROOT / 'assembly/pcba-r02/cpl-jlc-review.csv', 'Designator')
    cpl = csv_rows(OUT / 'cpl-jlc-review.csv', 'Designator')
    require(set(cpl) == set(old_cpl) and len(cpl) == 81, 'CPL coverage')
    for ref, row in cpl.items():
        expected = dict(old_cpl[ref])
        if ref == 'Q1':
            expected['Rotation'] = '270.000000'
        require(row == expected, f'Unreviewed position/side/angle: {ref}')
    readback = json.loads((OUT / 'jlc-preview-positions.json').read_text())
    for name, digest in readback['input_sha256'].items():
        require(sha(OUT / name) == digest, f'Supplier input identity: {name}')
    expected_mpns = {ref: r['Comment'] for r in bom.values() for ref in r['Designator'].split(',')}
    require(len(readback['rows']) == 81 and not readback['missing_references'], 'Supplier omitted references')
    require({r['reference'] for r in readback['rows']} == set(cpl) == set(expected_mpns), 'Reference sets')
    for p in readback['rows']:
        cp = cpl[p['reference']]
        require(p['mpn'] == expected_mpns[p['reference']] and p['side'] == cp['Layer'], 'Supplier MPN/side')
        require(all(abs(p[k] - float(cp[v])) < 1e-6 for k, v in
                    [('x_mm', 'Mid X'), ('y_mm', 'Mid Y'), ('angle', 'Rotation')]), 'Supplier coordinate/angle')
    q = json.loads((OUT / 'q1-review.json').read_text())
    require(q['mpn'] == 'UM6K34NTCN' and q['pin_functions']['3'] == 'D2' and q['pin_functions']['6'] == 'D1', 'Q1 identity/pins')
    require(min(q['library']['angle_candidates'], key=lambda r: r['rms_mm'])['angle'] == 270, 'Q1 angle screen')
    require(not q['production_release'] and not readback['factory_placement_accepted'], 'Acceptance overclaim')
    smt = json.loads((OUT / 'smt-results.json').read_text())
    require(not smt['accepted'] and smt['actions'][0]['results'], 'SMT failure missing or overstated')
    require(any(m['cat_num'] == 17 for r in smt['actions'][0]['results'] for m in r['meas']), 'Overlap findings omitted')
    require(sha(OUT / 'jlc-rules.json') == 'f1bebb3b2b5ac2ba0579f882fc0605d169c1d6a3a852a07beb8652b719e0a725', 'DFM rules changed')
    checkpoint = json.loads((OUT / 'checkpoint.json').read_text())
    for name, digest in checkpoint['files'].items():
        require(sha(ROOT / name) == digest, f'Frozen r03 evidence changed: {name}')
    manifest = json.loads((ROOT / 'release/collar-tracker-r05m-pcba-r03-review.json').read_text())
    package = ROOT / manifest['package']
    require(not manifest['production_release'] and sha(package) == manifest['sha256'], 'Package identity/status')
    with zipfile.ZipFile(package) as archive:
        require(archive.testzip() is None and set(archive.namelist()) == set(manifest['members']), 'ZIP contents')
        for name, digest in manifest['members'].items():
            require(hashlib.sha256(archive.read(name)).hexdigest() == digest, f'ZIP member: {name}')
    return {'result': 'PASS', 'scope': 'Saved source/assembly evidence integrity; not SMT acceptance',
            'mpns': 44, 'verified_placements': 81, 'q1': 'UM6K34NTCN',
            'smt': 'ACTUAL_RUN_WITH_UNRESOLVED_FINDINGS', 'pcba_order_ready': False}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
