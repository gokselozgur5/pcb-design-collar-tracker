#!/usr/bin/env python3
"""Freeze the r02 assembly review; use the verifier for normal resume."""
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assembly/pcba-r02'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def package():
    files = sorted(p for p in OUT.rglob('*') if p.is_file() and p.name != 'checkpoint.json')
    files += [ROOT / 'scripts' / n for n in ('review_pcba_connectors.py',
              'verify_pcba_connectors.py', 'package_pcba_connectors.py')]
    checkpoint = {'revision': 'pcba-r02', 'production_release': False,
                  'files': {str(p.relative_to(ROOT)): sha(p) for p in files}}
    (OUT / 'checkpoint.json').write_text(json.dumps(checkpoint, indent=2) + '\n')
    members = {}
    for folder in [OUT, ROOT / 'assembly/pcba-r01']:
        members.update({str(p.relative_to(ROOT)): p for p in folder.rglob('*') if p.is_file()})
    source = ROOT / 'experiments/power-r05l-charge-interlock'
    for name in ['collar-tracker.kicad_pcb', 'collar-tracker.kicad_sch',
                 'collar-tracker.kicad_pro', 'collar-tracker.kicad_dru']:
        p = source / 'hardware' / name
        members[str(p.relative_to(ROOT))] = p
    for relative in ['evidence/collar-tracker-05l-charge-final4-40x32-dfm.zip',
                     'evidence/jlc-check1/report.pdf', 'evidence/jlc-check2/report.pdf']:
        p = source / relative
        members[str(p.relative_to(ROOT))] = p
    members['docs/pcba-delivery.md'] = ROOT / 'docs/pcba-delivery.md'
    members['START-HERE.txt'] = OUT / 'package-readme.txt'
    dest = ROOT / 'release/collar-tracker-r05l-pcba-r02-review.zip'
    digests = {}
    with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, p in sorted(members.items()):
            content = p.read_bytes()
            if p.suffix == '.md':
                def link(match):
                    target = match.group(1)
                    if target.startswith(('http:', 'https:', '#')):
                        return match.group(0)
                    path, _, anchor = target.partition('#')
                    resolved = (p.parent / path).resolve()
                    if not resolved.is_file():
                        raise ValueError(f'Missing link: {target}')
                    relative = str(resolved.relative_to(ROOT))
                    if relative in members:
                        return match.group(0)
                    return '](https://github.com/gokselozgur5/pcb-design-collar-tracker/blob/main/' + relative + ('#' + anchor if anchor else '') + ')'
                content = re.sub(r'\]\(([^)]+)\)', link, content.decode()).encode()
            info = zipfile.ZipInfo(name, (2026, 10, 26, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, content)
            digests[name] = hashlib.sha256(content).hexdigest()
    report = {'package': str(dest.relative_to(ROOT)), 'sha256': sha(dest),
              'production_release': False, 'members': digests}
    dest.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'package': str(dest), 'sha256': report['sha256'], 'members': len(members)}, indent=2))


if __name__ == '__main__':
    package()
