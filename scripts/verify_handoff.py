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


def verify():
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
    return {'baseline_revision': '0.3.4', 'evidence_files': len(manifest['files']),
            'supplier_records': sorted(records), 'result': 'PASS',
            'scope': 'Saved baseline/evidence integrity only. No new KiCad/JLC run or r04/SMT/functional acceptance.'}


if __name__ == '__main__':
    try:
        print(json.dumps(verify(), indent=2))
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        sys.exit(1)
