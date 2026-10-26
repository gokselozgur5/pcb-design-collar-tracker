#!/usr/bin/env python3
"""Prepare the Q1 sourcing revision without changing copper, lands or nets."""
import csv
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'experiments/power-r05l-charge-interlock/hardware'
DEST = ROOT / 'experiments/pcba-r05m-rohm-q1/hardware'
OUT = ROOT / 'assembly/pcba-r03'
OLD = 'DMN62D2UDW'
NEW = 'UM6K34N'
OLD_URL = 'https://www.diodes.com/datasheet/download/DMN62D2UDW.pdf'
NEW_URL = 'https://fscdn.rohm.com/en/products/databook/datasheet/discrete/transistor/mosfet/um6k34ntcn-e.pdf'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def convert(text):
    return text.replace(OLD_URL, NEW_URL).replace(OLD + '-7', NEW + 'TCN').replace(OLD, NEW)


def prepare():
    if DEST.exists() or OUT.exists():
        raise SystemExit('Revision already exists; preserve it and review before regenerating.')
    DEST.mkdir(parents=True)
    OUT.mkdir(parents=True)
    (DEST.parent / 'evidence').mkdir()
    selected = []
    for path in sorted(BASE.iterdir()):
        if path.is_dir() and path.name.endswith('.pretty'):
            shutil.copytree(path, DEST / path.name)
            selected.extend(p for p in path.rglob('*') if p.is_file())
        elif path.is_file() and (path.suffix in {'.kicad_pcb', '.kicad_sch', '.kicad_pro',
                                                '.kicad_dru', '.kicad_sym'} or
                                path.name in {'fp-lib-table', 'sym-lib-table', 'design.json',
                                              'bom.csv', 'library-provenance.json'}):
            shutil.copy2(path, DEST / path.name)
            selected.append(path)
    changes = []
    for source in selected:
        target = DEST / source.relative_to(BASE)
        before = source.read_text()
        after = convert(before)
        if before != after:
            target.write_text(after)
            # Exact reversible token replacements: no geometric or net edit.
            restored = after.replace(NEW_URL, OLD_URL).replace(NEW + 'TCN', OLD + '-7').replace(NEW, OLD)
            assert restored == before, target
            changes.append(str(target.relative_to(DEST)))
    with (ROOT / 'assembly/pcba-r01/bom.csv').open(newline='') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    row = next(r for r in rows if r['Designator'] == 'Q1')
    assert row['Comment'] == OLD + '-7'
    row['Comment'] = NEW + 'TCN'
    row['Description'] = NEW + 'TCN'
    with (OUT / 'bom.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fields)
        writer.writeheader()
        writer.writerows(rows)
    with (ROOT / 'assembly/pcba-r02/cpl-jlc-review.csv').open(newline='') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    row = next(r for r in rows if r['Designator'] == 'Q1')
    assert float(row['Rotation']) == 90
    row['Rotation'] = '270.000000'
    with (OUT / 'cpl-jlc-review.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fields)
        writer.writeheader()
        writer.writerows(rows)
    report = {
        'revision': 'r05m', 'base': str(BASE.relative_to(ROOT)),
        'change': 'Q1 MPN/symbol/datasheet only; supplier Q1 CPL rotation 90 to 270',
        'old_mpn': OLD + '-7', 'new_mpn': NEW + 'TCN', 'jlc_code': 'C510056',
        'native_geometry_and_net_changes': False, 'changed_native_files': changes,
        'native_files': {str(p.relative_to(DEST)): digest(p) for p in sorted(DEST.rglob('*')) if p.is_file()},
        'assembly_files': {p.name: digest(p) for p in sorted(OUT.glob('*.csv'))},
        'production_release': False,
    }
    (OUT / 'preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'changed_native_files': changes, 'copper_changed': False,
                      'new_mpn': report['new_mpn']}, indent=2))


if __name__ == '__main__':
    prepare()
