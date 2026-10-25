#!/usr/bin/env python3
"""Package the unchanged all-green PCB and the explicit battery charging HOLD."""
import argparse
import base64
import hashlib
import html
import io
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05k-selected-parts'
OUT = ROOT / 'release/r05k-review'
PACKAGE = ROOT / 'release/collar-tracker-r05k-pcb-review.zip'
RECEIPT = PACKAGE.with_suffix('.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_bundle():
    receipt = json.loads(RECEIPT.read_text())
    assert sha(PACKAGE) == receipt['zip_sha256'], 'Review ZIP changed'
    with zipfile.ZipFile(PACKAGE) as archive:
        assert len(archive.namelist()) == len(set(archive.namelist())), 'Duplicate ZIP members'
        assert set(archive.namelist()) == {x['archive_path'] for x in receipt['files']} | {'manifest.json'}
        assert json.loads(archive.read('manifest.json')) == {k:v for k,v in receipt.items() if k != 'zip_sha256'}
        for entry in receipt['files']:
            actual = archive.read(entry['archive_path'])
            assert len(actual) == entry['bytes']
            assert hashlib.sha256(actual).hexdigest() == entry['sha256']
            assert sha(ROOT / entry['repo_path']) == entry['sha256'], entry['repo_path']
    assert receipt['production_release'] is False and receipt['physical_ingress_test'] is False
    return dict(package=str(PACKAGE), files=len(receipt['files']), sha256=receipt['zip_sha256'], result='PASS')


def build():
    from verify_handoff import verify
    checked = verify()
    assert checked['pack_charge_review']['charge_window_implemented'] is False
    checkpoint = json.loads((TRIAL / 'evidence/parts-checkpoint.json').read_text())
    source = checkpoint['source_sha256']
    assert sha(TRIAL / 'hardware/collar-tracker.kicad_pcb') == source
    plots = json.loads((OUT / 'plot-receipt.json').read_text())
    assert plots['pcb_sha256'] == source and plots['native_exit_codes'] == [0, 0]
    assert all(sha(OUT / name) == digest for name, digest in plots['files'].items()), 'Stale PCB preview'
    records = [json.loads((TRIAL / f'evidence/jlc-check{i}/summary.json').read_text()) for i in (1, 2)]
    assert all(r['counts'] == dict(danger=0, warning=0, good=450) and r['analyzed_rows'] == 29 for r in records)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200" font-family="Arial, sans-serif">']

    def rect(x, y, w, h, fill):
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')

    def text(x, y, value, size=23, color='#253442', bold=False):
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{"bold" if bold else "normal"}">{html.escape(str(value))}</text>')

    def image(name, x, y):
        data = base64.b64encode((OUT / name).read_bytes()).decode()
        svg.append(f'<image x="{x}" y="{y}" width="700" height="510" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{data}"/>')

    rect(0, 0, 1600, 1200, '#f4f6f8'); rect(0, 0, 1600, 120, '#183145')
    text(40, 55, 'COLLAR TRACKER / r05k PCB REVIEW', 36, 'white', True)
    text(40, 95, 'Two clean PCB DFM reports. Working-device release remains on hold.', 24, '#e3ebf0')
    for x, name, title in [(40, 'top.png', 'TOP / copper and silkscreen'), (820, 'bottom.png', 'BOTTOM / mirrored component view')]:
        rect(x, 145, 740, 585, 'white'); text(x + 20, 185, title, 25, bold=True)
        image(name, x + 20, 205)
    rect(40, 750, 740, 360, '#e4f0e8'); text(60, 793, 'VERIFIED PCB', 25, '#18603c', True)
    for i, line in enumerate([
        '40 × 32 mm / six Cu layers / 71 footprints',
        'Native DRC, ERC, connectivity and parity: zero findings',
        'JLC: 0 Danger / 0 Warning / 450 Good in both runs',
        'Same ZIP, same rules, all 29 rows analyzed; SMT off',
        '65 fitted references / 38 exact candidate MPNs',
        'BOM, CPL, native KiCad and both reports included',
        'Two GND planes; inherited local return checks pass']):
        text(60, 835 + i * 36, line, 21)
    rect(820, 750, 740, 360, '#fff1e8'); text(840, 793, 'REQUIRED BEFORE WORKING DELIVERY', 25, '#8d351f', True)
    for i, line in enumerate([
        'Charging: direct 10k/B3435 NTC permits 50°C charging.',
        'Reviewed pack maximum: 45°C. /CE is tied to GND.',
        'A cell-temperature charge interlock is not implemented.',
        'Protected pack, antennas, harness and retention: open.',
        'Firmware, factory programming and powered tests: open.',
        'Swimming/IP68: target only; no physical ingress test.',
        'This is a PCB review package, not an order release.']):
        text(840, 835 + i * 36, line, 20)
    text(40, 1144, 'PCB SHA256: ' + source, 17)
    text(40, 1178, 'JLC records: ' + ' / '.join(r['record_id'] for r in records) + ' | 2026-10-25', 18)
    svg.append('</svg>')
    (OUT / 'review.svg').write_text('\n'.join(svg) + '\n')
    for suffix in ('png', 'pdf'):
        subprocess.run(['rsvg-convert', '-f', suffix, '-o', str(OUT / ('review.' + suffix)), str(OUT / 'review.svg')], check=True)
    (OUT / 'START-HERE.txt').write_text(
        'COLLAR TRACKER r05k — PCB REVIEW, NOT A WORKING-DEVICE ORDER RELEASE\n\n'
        'Open review.pdf first. Upload only gerber.zip to a PCB DFM analyzer.\n'
        'The outer review ZIP also contains CAD, BOM/CPL and reports; do not upload it as Gerbers.\n\n'
        'Two actual same-byte JLC analyses: 0 Danger / 0 Warning / 450 Good each.\n'
        'All 29 PCB categories analyzed with unchanged rules; SMT was off.\n'
        'Native connectivity, DRC, ERC and schematic parity have zero findings.\n\n'
        'CHARGING HOLD: the direct 10k/B3435 NTC allows charging at 50 C,\n'
        'above the reviewed candidate pack 45 C limit. CE is grounded.\n'
        'The charge interlock is not implemented. See pack-charge/README.md.\n'
        'Pack/antennas, sealed assembly, firmware and factory tests are incomplete.\n'
        'No IP68, physical ingress, powered, RF or working-PCBA acceptance is claimed.\n\n'
        'pcb/native contains the editable KiCad project with local libraries.\n'
        'assembly contains candidate BOM/CPL; rotations, purchasing and SMT remain unapproved.\n'
        'manifest.json binds every file to the repository source and SHA256.\n'
        'Full engineering history and continuation:\n'
        'https://github.com/gokselozgur5/pcb-design-collar-tracker\n')
    payload, entries = {}, []

    def add(name, path):
        assert name not in payload
        data = path.read_bytes(); payload[name] = data
        entries.append(dict(archive_path=name, repo_path=str(path.relative_to(ROOT)),
                            sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))

    for name in ('START-HERE.txt', 'review.pdf', 'review.png', 'top.svg', 'bottom.svg'):
        add(name, OUT / name)
    add('gerber.zip', TRIAL / 'evidence/collar-tracker-05k-parts-40x32-dfm.zip')
    for entry in checkpoint['files']:
        name = entry['path']
        if name.startswith('hardware/'):
            add('pcb/native/' + name.removeprefix('hardware/'), TRIAL / name)
    for name in ('candidate-bom.csv', 'candidate-cpl.csv', 'assembly-check.json'):
        add('assembly/' + name, TRIAL / 'assembly' / name)
    for run in ('jlc-check1', 'jlc-check2'):
        for name in ('report.pdf', 'receipt.json', 'summary.json', 'dfm.json', 'rules.json', 'rows.txt', 'screen.png'):
            add(run + '/' + name, TRIAL / 'evidence' / run / name)
    for name in ('inputs.json', 'check.json', 'README.md'):
        add('pack-charge/' + name, ROOT / 'assembly/pack-charge-r01' / name)
    manifest = dict(pcb_sha256=source, gerber_zip_sha256=checkpoint['zip_sha256'],
                    supplier_records=[r['record_id'] for r in records], production_release=False,
                    physical_ingress_test=False, files=sorted(entries, key=lambda v: v['archive_path']))
    payload['manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 25, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    data = buffer.getvalue()
    assert not PACKAGE.exists() or PACKAGE.read_bytes() == data, 'Preserve the earlier package; use a new revision'
    PACKAGE.write_bytes(data)
    RECEIPT.write_text(json.dumps({**manifest, 'zip_sha256': hashlib.sha256(data).hexdigest()}, indent=2) + '\n')
    return verify_bundle()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    print(json.dumps(verify_bundle() if args.verify else build(), indent=2))
