#!/usr/bin/env python3
"""Compare native numbered IC lands with the supplier's public library geometry."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'assembly/pcba-r01'
RUNTIME = ROOT/'.runtime/manufacturing-r01'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def review():
    match = json.loads((OUT/'jlc-library-match.json').read_text())
    numbers = json.loads((RUNTIME/'library-numbers.json').read_text())
    packages = json.loads((RUNTIME/'library-packages.json').read_text())
    assert numbers['success'] and packages['success']
    numbers = {r['number']: r for r in numbers['result']}
    packages = {r['uuid']: r['dataStr'] for r in packages['result']}
    cpl = {r['Designator']: r for r in csv.DictReader((OUT/'cpl.csv').open())}
    native = {}
    for p in csv.DictReader((OUT/'fitted-pads.csv').open()):
        # Unnumbered native paste apertures are not electrical terminals.
        if not p['pin']:
            continue
        native.setdefault(p['reference'], {})[p['pin']] = p
    results = []
    for row in match['rows']:
        for ref in filter(None, (row['top']+','+row['bottom']).split(',')):
            # Connector numbering/origins need a separate manufacturer review.
            if not ref.startswith(('U', 'D')):
                continue
            code = row['part_code']
            package_id = numbers[code]['puuid']
            package = packages[package_id]
            head = package['head']
            pads = [s.split('~') for s in package['shape'] if s.startswith('PAD~')]
            library = {s[8]: ((float(s[2])-float(head['x']))*.254,
                              -(float(s[3])-float(head['y']))*.254) for s in pads}
            assert set(library) == set(native[ref]), ref
            cp = cpl[ref]
            target = {pin: (float(p['x_mm'])-float(cp['Mid X']),
                            float(p['y_mm'])-float(cp['Mid Y'])) for pin, p in native[ref].items()}
            alternatives = []
            for angle in (0, 90, 180, 270):
                a = math.radians(angle)
                errors = []
                for pin, (x, y) in library.items():
                    xx, yy = x*math.cos(a)-y*math.sin(a), x*math.sin(a)+y*math.cos(a)
                    # JLC bottom rendering reflects X after applying CPL rotation.
                    if cp['Layer'] == 'Bottom':
                        xx = -xx
                    errors.append(math.hypot(xx-target[pin][0], yy-target[pin][1]))
                alternatives.append(dict(angle=angle, rms_mm=math.sqrt(sum(e*e for e in errors)/len(errors)),
                                         max_mm=max(errors)))
            alternatives.sort(key=lambda p: p['rms_mm'])
            best = alternatives[0]
            results.append(dict(reference=ref, side=cp['Layer'], code=code, mpn=row['requested_mpn'],
                                package_uuid=package_id, pad_count=len(library),
                                native_angle=float(cp['Rotation']), proposed_angle=best['angle'],
                                library_pin1_mm=library['1'], native_pin1_mm=target['1'],
                                candidates=alternatives))
    assert len(results) == 14
    data = dict(scope='Supplier model orientation screening; land geometry, solder process and production acceptance remain open',
                source='JLCEDA/EasyEDA Official Library',
                source_urls=['https://lceda.cn/', 'https://easyeda.com/',
                             'https://docs.easyeda.com/en/API/2-Coordinate-System-and-Unit/'],
                library_response_sha256={p.name: sha(p) for p in [RUNTIME/'library-numbers.json', RUNTIME/'library-packages.json']},
                inputs={str(p.relative_to(ROOT)):sha(p) for p in [OUT/'cpl.csv', OUT/'fitted-pads.csv', OUT/'jlc-library-match.json', Path(__file__).resolve()]},
                changed_references=sum(p['native_angle'] != p['proposed_angle'] for p in results),
                rows=results,
                open_references={'Q1':'No exact BOM match/model', 'J6':'Exact BOM match but no library footprint/model returned',
                                 'J1,J2':'Library pin numbering/origin and land arrangement differ; manual manufacturer/package review required'},
                supplier_rotation_qualified=False, smt_accepted=False, production_release=False)
    (OUT/'orientation-review.json').write_text(json.dumps(data, indent=2)+'\n')
    with (OUT/'cpl-jlc-review.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(next(iter(cpl.values()))))
        writer.writeheader()
        changes = {p['reference']:p['proposed_angle'] for p in results}
        for ref, p in cpl.items():
            writer.writerow({**p, 'Rotation':f"{changes.get(ref,float(p['Rotation'])):.6f}"})
    print(json.dumps({'reviewed':len(results), 'changed':data['changed_references'],
                      'open':data['open_references'], 'production_release':False}, indent=2))


if __name__ == '__main__':
    review()
