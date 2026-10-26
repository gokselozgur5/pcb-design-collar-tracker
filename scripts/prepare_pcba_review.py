#!/usr/bin/env python3
"""Prepare BOM/CPL for assembly review from the frozen r05l source exports."""
import csv
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'experiments/power-r05l-charge-interlock'
OUT = ROOT/'assembly/pcba-r01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def package(name):
    # Remove per-reference library-copy prefixes, not physical package details.
    name = re.sub(r'^(?:C|R|L|U|Q|D|FB|J)\d+_', '', name.split(':')[-1])
    match = re.fullmatch(r'[CRL]_(0201|0402|0603|0805)_\d+Metric', name)
    return match.group(1) if match else name


def prepare():
    saved = json.loads((SOURCE/'assembly/assembly-check.json').read_text())
    assert sha(SOURCE/'hardware/collar-tracker.kicad_pcb') == saved['source_sha256']
    assert sha(SOURCE/'hardware/collar-tracker.kicad_sch') == saved['schematic_sha256']
    for name, expected in saved['inputs'].items():
        assert sha(ROOT/name) == expected, name
    inventory = rows(SOURCE/'hardware/bom.csv')
    fitted = {p['ref']: p for p in inventory if p['mpn'] and p['dnp'] == 'False'}
    positions = {p['Ref']: p for p in rows(SOURCE/'assembly/native-positions.csv') if p['Ref'] in fitted}
    native = json.loads((SOURCE/'evidence/components.native.json').read_text())
    parts = {p['ref']: p for p in native['parts']}
    assert len(inventory) == 87 and len(fitted) == 81 and set(fitted) == set(positions)
    groups = {}
    for ref, part in fitted.items():
        assert not parts[ref]['dnp'] and part['value'] == positions[ref]['Val']
        assert positions[ref]['Side'] == parts[ref]['side']
        assert abs(float(positions[ref]['PosX']) - (parts[ref]['native_position_mm'][0]-100)) < 1e-6
        assert abs(float(positions[ref]['PosY']) - (128-parts[ref]['native_position_mm'][1])) < 1e-6
        assert abs((float(positions[ref]['Rot'])-parts[ref]['native_angle_degrees']) % 360) < 1e-6
        groups.setdefault(part['mpn'], []).append(ref)
    assert len(groups) == 44
    gerber = SOURCE/'evidence/collar-tracker-05l-charge-final4-40x32-dfm.zip'
    with zipfile.ZipFile(gerber) as archive:
        assert archive.testzip() is None
        edge = archive.read(next(n for n in archive.namelist() if 'Edge_Cuts' in n)).decode()
    assert '%FSLAX46Y46*%' in edge and '%MOMM*%' in edge
    vertices = {(int(x)/1e6, int(y)/1e6) for x, y in re.findall(r'X(-?\d+)Y(-?\d+)D0[12]\*', edge)}
    assert vertices == {(-2, -2), (-2, 30), (38, -2), (38, 30)}
    assert all(-2 <= float(p['PosX']) <= 38 and -2 <= float(p['PosY']) <= 30 for p in positions.values())
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT/'bom.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['Comment', 'Designator', 'Footprint', 'Quantity', 'Description'])
        for mpn, refs in sorted(groups.items()):
            packages = {package(fitted[r]['footprint']) for r in refs}
            assert len(packages) == 1, (mpn, packages)
            writer.writerow([mpn, ','.join(sorted(refs)), packages.pop(), len(refs),
                             '; '.join(sorted({fitted[r]['value'] for r in refs}))])
    with (OUT/'cpl.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['Designator', 'Mid X', 'Mid Y', 'Rotation', 'Layer'])
        for ref, p in sorted(positions.items()):
            writer.writerow([ref, p['PosX'], p['PosY'], f"{float(p['Rot'])%360:.6f}", p['Side'].title()])
    output = rows(OUT/'bom.csv')
    refs = [r for p in output for r in p['Designator'].split(',')]
    assert len(refs) == len(set(refs)) == 81 and set(refs) == set(fitted)
    assert {p['Designator'] for p in rows(OUT/'cpl.csv')} == set(refs)
    report = dict(result='PASS', scope='File/identity/coordinate consistency for assembly review only',
                  pcb_sha256=saved['source_sha256'], gerber_sha256=sha(gerber),
                  fitted_references=81, exact_mpns=44,
                  sides={s: sum(p['Side'] == s for p in positions.values()) for s in ['top', 'bottom']},
                  origin_native_mm=[100, 128], gerber_bounds_mm=[-2, -2, 38, 30],
                  coordinates='Millimetres, X right and Y up; both sides share Gerber origin; no bottom mirroring',
                  rotations='Native KiCad angles modulo 360; supplier package rotations unqualified',
                  dnp=['C11', 'C12'], unplaced_interfaces=['J3', 'J4', 'J5', 'J7'],
                  supplier_part_codes_verified=False, supplier_rotation_qualified=False,
                  smt_dfm_accepted=False, procurement_accepted=False, production_release=False,
                  inputs={str(p.relative_to(ROOT)): sha(p) for p in [
                      SOURCE/'hardware/bom.csv', SOURCE/'assembly/native-positions.csv',
                      SOURCE/'assembly/assembly-check.json', SOURCE/'evidence/components.native.json',
                      SOURCE/'hardware/collar-tracker.kicad_pcb', SOURCE/'hardware/collar-tracker.kicad_sch',
                      gerber, Path(__file__).resolve()]},
                  outputs={p.name: sha(p) for p in [OUT/'bom.csv', OUT/'cpl.csv']})
    (OUT/'file-checks.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    print(json.dumps(prepare(), indent=2))
