#!/usr/bin/env python3
"""Freeze the r03 review, retaining the actual non-passing SMT report."""
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assembly/pcba-r03'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package():
    files = sorted(p for p in OUT.rglob('*') if p.is_file() and p.name != 'checkpoint.json')
    files += sorted(p for p in (ROOT / 'experiments/pcba-r05m-rohm-q1').rglob('*') if p.is_file())
    files += [ROOT / 'scripts' / n for n in ('prepare_pcba_r03.py', 'review_pcba_r03.py',
                                           'verify_pcba_r03.py', 'package_pcba_r03.py')]
    (OUT / 'checkpoint.json').write_text(json.dumps({
        'revision': 'pcba-r03', 'production_release': False,
        'files': {str(p.relative_to(ROOT)): sha(p) for p in files}}, indent=2) + '\n')
    members = {str(p.relative_to(ROOT)): p for p in files if 'scripts' not in p.parts}
    members['assembly/pcba-r03/checkpoint.json'] = OUT / 'checkpoint.json'
    source = ROOT / 'experiments/power-r05l-charge-interlock'
    for relative in ['evidence/collar-tracker-05l-charge-final4-40x32-dfm.zip',
                     'evidence/jlc-check1/report.pdf', 'evidence/jlc-check2/report.pdf']:
        path = source / relative
        members[str(path.relative_to(ROOT))] = path
    for relative in ['assembly/pcba-r01/cpl.csv', 'assembly/pcba-r01/interface-pads.csv',
                     'assembly/pcba-r02/connector-review.json', 'assembly/pcba-r02/sources.json',
                     'docs/pcba-delivery.md']:
        members[relative] = ROOT / relative
    members['START-HERE.txt'] = OUT / 'package-readme.txt'
    dest = ROOT / 'release/collar-tracker-r05m-pcba-r03-review.zip'
    digests = {}
    with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, path in sorted(members.items()):
            content = path.read_bytes()
            if path.suffix == '.md':
                def link(match):
                    target = match.group(1)
                    if target.startswith(('http:', 'https:', '#')):
                        return match.group(0)
                    relative, _, anchor = target.partition('#')
                    resolved = (path.parent / relative).resolve()
                    if not resolved.is_file():
                        raise ValueError(f'Missing link: {target}')
                    relative = str(resolved.relative_to(ROOT))
                    if relative in members:
                        return match.group(0)
                    return '](https://github.com/gokselozgur5/pcb-design-collar-tracker/blob/main/' + relative + ('#' + anchor if anchor else '') + ')'
                content = re.sub(r'\]\(([^)]+)\)', link, content.decode()).encode()
            info = zipfile.ZipInfo(name, (2026, 10, 26, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)
            digests[name] = hashlib.sha256(content).hexdigest()
    manifest = {'package': str(dest.relative_to(ROOT)), 'sha256': sha(dest),
                'production_release': False, 'members': digests}
    dest.with_suffix('.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'package': str(dest), 'sha256': manifest['sha256'],
                      'bytes': dest.stat().st_size, 'members': len(members)}, indent=2))


if __name__ == '__main__':
    package()
