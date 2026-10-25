#!/usr/bin/env python3
"""Package only reviewed PCB/mechanical artifacts; never replace different bytes."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
from verify_handoff import verify

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--name', default='collar-tracker-r04i-swim-r01-review')
args = parser.parse_args()
assert re.fullmatch(r'[a-zA-Z0-9_-]+', args.name), 'Use a plain package name'
verification = verify(include_review_bundle=False)
trial = ROOT / 'experiments/paul-nanosim-r04i-sim-access-40x32'
mechanical = ROOT / 'mechanical/swim-r01'
checkpoint = json.loads((trial / 'evidence/routing-checkpoint.json').read_text())
payload = {}
entries = []


def add(name, source=None, text=None):
    assert name not in payload and not name.startswith('/') and '..' not in Path(name).parts
    data = source.read_bytes() if source else text.encode('utf-8')
    payload[name] = data
    entries.append({'archive_path': name,
                    'source_path': str(source.relative_to(ROOT)) if source else None,
                    'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})


add('START-HERE.txt', text='''COLLAR TRACKER: r04i PCB + swim-r01 enclosure review

Open review.pdf first. All dimensions are millimeters. STLs are 1:1.

PCB: 40 x 32 x 0.8 mm, four copper layers. The exact PCB/DFM.zip passed
two actual JLC PCB analyses at 0 Danger / 0 Warning with unchanged rules.
PCB/jlc-check1 and jlc-check2 contain both full reports and raw evidence.
PCB/native contains the editable KiCad project and its local libraries.
These results do not establish SMT assembly, powered operation or RF performance.

ENCLOSURE: engineering prototype, not a completed production design.
Rigid body 57.4 x 49.4 x 17.6 mm; 58.7 mm including the docking key.
With collar boot: 60.4 x 52.4 x 22.4 mm. Read mechanical/README.md.
Swimming/IP68 is the owner's design target. 2 m fresh water / 60 min and
magnetic charging are provisional engineering assumptions, not user approvals.
The CAD and exported meshes passed their declared geometry/integrity checks.
No dust, immersion, physical fit, powered or RF qualification has occurred.
Battery/antenna/component-height reservations, final contact/dock/harness parts,
seal compounds, material process and assembly torque remain to be resolved.

DFM UPLOAD: upload only PCB/DFM.zip, not this complete review bundle.
No manufacturing order, payment or factory acceptance is included.

manifest.json binds every file to its SHA256. The source repository contains
the complete review history, regeneration scripts and continuation instructions:
https://github.com/gokselozgur5/pcb-design-collar-tracker
''')
add('review.pdf', mechanical / 'review.pdf')
add('PCB/DFM.zip', ROOT / checkpoint['package'])
for item in checkpoint['files']:
    if item['path'].startswith('hardware/'):
        add('PCB/native/' + item['path'].removeprefix('hardware/'), trial / item['path'])
for name in ['native-drc.json', 'native-erc.json', 'layout-inventory.json',
             'contact-components.json', 'esd-paths.json', 'card-insertion-review.json',
             'attachment-review.json', 'passive-copper-review.json', 'power-path-review.json',
             'front.png', 'back.png']:
    add('PCB/' + name, trial / 'evidence' / name)
for run in ['jlc-check1', 'jlc-check2']:
    for name in ['receipt.json', 'rows.txt', 'dfm.json', 'rules.json', 'report.pdf',
                 'screen.png', 'summary.json']:
        add(f'PCB/{run}/{name}', trial / 'evidence' / run / name)
for name in ['README.md', 'parameters.json', 'parameters.scad', 'enclosure.scad',
             'checks.json', 'mesh-checks.json', 'mechanical-bom.csv',
             'body.stl', 'lid.stl', 'carrier.stl', 'contact.stl', 'contact_seal.stl',
             'magnet_plug.stl', 'dock.stl', 'boot.stl',
             'exploded.png', 'section.png', 'mounted.png',
             'overview.svg', 'overview.png', 'overview.pdf',
             'drawing.svg', 'drawing.png', 'drawing.pdf']:
    add('mechanical/' + name, mechanical / name)
manifest = {'pcb_sha256': verification['current']['source_sha256'],
            'dfm_zip_sha256': checkpoint['zip_sha256'],
            'supplier_records': checkpoint['supplier_records'],
            'mechanical_revision': 'swim-r01', 'ingress_qualified': False,
            'files': sorted(entries, key=lambda x: x['archive_path'])}
payload['manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for name, data in sorted(payload.items()):
        info = zipfile.ZipInfo(name, date_time=(2026, 10, 25, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, data)
data = buffer.getvalue()
out = ROOT / 'release' / (args.name + '.zip')
sidecar = out.with_suffix('.json')
metadata = {**manifest, 'package': str(out.relative_to(ROOT)),
            'zip_sha256': hashlib.sha256(data).hexdigest()}
metadata_bytes = (json.dumps(metadata, indent=2) + '\n').encode()
for path, content in [(out, data), (sidecar, metadata_bytes)]:
    assert not path.exists() or path.read_bytes() == content, f'Preserve existing package; choose a new --name: {path}'
for path, content in [(out, data), (sidecar, metadata_bytes)]:
    path.write_bytes(content)
print(json.dumps({'package': str(out), 'files': len(entries),
                  'bytes': len(data), 'sha256': metadata['zip_sha256']}, indent=2))
