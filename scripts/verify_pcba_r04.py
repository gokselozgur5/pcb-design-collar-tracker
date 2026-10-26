#!/usr/bin/env python3
"""Check saved datum-experiment evidence; never approve it for manufacture."""
import json
from pathlib import Path

from verify_pcba_r03 import csv_rows, require, sha

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assembly/pcba-r04'
OLD = ROOT / 'assembly/pcba-r03'


def verify():
    evidence = json.loads((OUT / 'comparison.json').read_text())
    require(evidence['decision'] == 'REJECTED' and not evidence['production_release'], 'Rejected datum status')
    require(evidence['selected_cpl'] == 'assembly/pcba-r03/cpl-jlc-review.csv', 'Selected CPL changed')
    require(sha(ROOT / 'experiments/pcba-r05m-rohm-q1/hardware/collar-tracker.kicad_pcb') == evidence['source_sha256'], 'Native source identity')
    require(sha(ROOT / 'experiments/power-r05l-charge-interlock/evidence/collar-tracker-05l-charge-final4-40x32-dfm.zip') == evidence['gerber_sha256'], 'Gerber identity')
    require((OUT / 'bom.csv').read_bytes() == (OLD / 'bom.csv').read_bytes(), 'BOM changed')
    for name, digest in evidence['input_sha256'].items():
        require(sha(ROOT / name) == digest, f'Input identity: {name}')
    before = csv_rows(OLD / 'cpl-jlc-review.csv', 'Designator')
    after = csv_rows(OUT / 'rejected-native-centres-cpl.csv', 'Designator')
    require(len(after) == 81 and set(before) == set(after), 'Part coverage')
    for ref, row in after.items():
        expected = dict(before[ref])
        if ref in ['J1', 'J2']:
            expected['Mid X'] = {'J1': '18.300000', 'J2': '28.300000'}[ref]
        require(row == expected, f'Unexpected datum edit: {ref}')
    bom = {ref: r['Comment'] for r in csv_rows(OUT / 'bom.csv', 'Designator').values()
           for ref in r['Designator'].split(',')}
    preview = json.loads((OUT / 'jlc-preview-positions.json').read_text())['rows']
    require(len(preview) == 81 and {p['reference'] for p in preview} == set(after), 'Read-back coverage')
    for p in preview:
        row = after[p['reference']]
        require(p['mpn'] == bom[p['reference']] and p['side'] == row['Layer'], 'Read-back MPN/side')
        require(all(abs(p[k] - float(row[v])) < 1e-6 for k, v in
                    [('x_mm', 'Mid X'), ('y_mm', 'Mid Y'), ('angle', 'Rotation')]), 'Read-back position')
    old = json.loads((OLD / 'smt-results.json').read_text())['actions'][0]
    new = json.loads((OUT / 'smt-results.json').read_text())
    require(not new['accepted'] and new['actions'][0]['categories'] == old['categories'], 'SMT rules/status')
    for action, key in [(old, 'overlap_before'), (new['actions'][0], 'overlap_diagnostic')]:
        n = next(i for i, c in enumerate(action['categories']) if c['name'] == 'weld2paste')
        measured = {}
        for layer in action['results']:
            for m in layer['meas']:
                if m['cat_num'] == n:
                    measured.setdefault(m['name1'], []).append(m['value'])
        require(measured == evidence[key], 'Overlap comparison changed')
    require(sha(OLD / 'jlc-rules.json') == evidence['rule_sha256'], 'Rule identity')
    for name, digest in json.loads((OUT / 'checkpoint.json').read_text())['files'].items():
        require(sha(ROOT / name) == digest, f'Frozen diagnostic evidence: {name}')
    return {'result': 'PASS', 'scope': 'Saved rejected-datum evidence integrity',
            'diagnostic_selected': False, 'placements_verified': len(preview),
            'unreturned_pin_edges': sum(v['unreturned'] for v in evidence['pin_edge_union'].values()),
            'pcba_order_ready': False}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
