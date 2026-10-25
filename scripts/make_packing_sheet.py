#!/usr/bin/env python3
"""Build a self-contained engineering review sheet from the packing study."""
import base64
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
report = json.loads((ROOT / 'mechanical/packing-checks.json').read_text())
compact = report['variants'][0]
length, width, height = compact['body_mm']
png = base64.b64encode((ROOT / 'previews/compact-250-exploded.png').read_bytes()).decode()

# Measure exported binary STL geometry, not the source dimensions.
stls = {}
for variant, stem in zip(report['variants'], ['compact-250', 'reference-500']):
    path = ROOT / 'mechanical' / (stem + '-sizing-dummy.stl')
    raw = path.read_bytes()
    count, = struct.unpack_from('<I', raw, 80)
    assert len(raw) == 84 + count * 50
    vertices = []
    for n in range(count):
        for v in range(3):
            vertices.append(struct.unpack_from('<fff', raw, 84 + n * 50 + 12 + v * 12))
    bounds = [[min(p[a] for p in vertices), max(p[a] for p in vertices)] for a in range(3)]
    actual = [hi - lo for lo, hi in bounds]
    expected = variant['body_mm'][:2] + [variant['total_height_with_contact_reservation_mm']]
    assert all(abs(a - b) < 0.001 for a, b in zip(actual, expected)), (path.name, actual, expected)
    stls[path.name] = dict(triangles=count, bounds_mm=bounds, size_mm=actual,
                           expected_mm=expected, tolerance_mm=0.001, result='PASS')
(ROOT / 'mechanical/stl-bounds.json').write_text(json.dumps(stls, indent=2) + '\n')

legend = [
    ('#2a8763', 'PCB volume', '30 × 22 × 0.8 mm; no component layout'),
    ('#475466', 'nRF9151', '12.1 × 11.1 × 1.2 mm package'),
    ('#dfad38', '250 mAh example cell', '32 × 20.5 × 5.3 mm; not selected'),
    ('#fa661e', 'LTE / GNSS volumes', 'No antennas selected; assumed volumes'),
    ('#de4d8c', 'Heart-rate contact', 'Bottom side; method/sensor unselected'),
    ('#737b87', 'Other electronics', 'Aggregate component volume budget'),
    ('#b8c4d3', 'Body and lid', 'Assembly and sealing not designed'),
]
rows = []
for i, (color, name, detail) in enumerate(legend):
    y = 535 + i * 55
    rows.append(f'<rect x="1080" y="{y-14}" width="15" height="15" rx="3" fill="{color}"/>'
                f'<text x="1110" y="{y}" class="label">{name}</text>'
                f'<text x="1110" y="{y+21}" class="small">{detail}</text>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1600" height="1120" viewBox="0 0 1600 1120">
<defs><marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 10 5 L 0 0 L 0 10 Z" fill="#516171"/></marker></defs>
<style>text{{font-family:Arial,sans-serif;fill:#192d3c}} .small{{font-size:17px;fill:#526471}} .label{{font-size:19px;font-weight:bold}} .dim{{stroke:#516171;stroke-width:1.5;fill:none}}</style>
<rect width="1600" height="1120" fill="#f8fafb"/>
<text x="60" y="53" font-size="17" letter-spacing="2">COLLAR TRACKER · PACKING STUDY 0.1</text>
<text x="60" y="110" font-size="42" font-weight="bold">{length} × {width} × {height} mm target body</text>
<text x="60" y="143" font-size="20" fill="#526471">250 mAh example · 14.6 mm with assumed contact protrusion · Collar mount excluded</text>
<line x1="60" x2="1540" y1="169" y2="169" stroke="#d8e0e5"/>
<image x="15" y="184" width="1020" height="802" xlink:href="data:image/png;base64,{png}"/>
<text x="60" y="986" class="small">Exploded view: layers separated for clarity. Image is not to scale.</text>
<text x="1080" y="210" font-size="17" letter-spacing="1">TOP VIEW · BODY / PCB VOLUME</text>
<rect x="1150" y="265" width="304" height="240" rx="32" fill="#e7ecf0" stroke="#718495" stroke-width="2"/>
<rect x="1190" y="297" width="240" height="176" rx="3" fill="#d6e8e0" stroke="#2a8763" stroke-width="2" stroke-dasharray="6 4"/>
<text x="1310" y="382" text-anchor="middle" font-size="22">PCB volume</text>
<text x="1310" y="411" text-anchor="middle" font-size="19">30 × 22 mm</text>
<path d="M 1150 255 V 234 M 1454 255 V 234 M 1150 242 H 1454" class="dim"/>
<line x1="1154" x2="1450" y1="242" y2="242" class="dim" marker-start="url(#arrow)" marker-end="url(#arrow)"/>
<rect x="1261" y="227" width="82" height="25" fill="#f8fafb"/>
<text x="1302" y="247" text-anchor="middle" font-size="18">38 mm</text>
<path d="M 1464 265 H 1490 M 1464 505 H 1490" class="dim"/>
<line x1="1480" x2="1480" y1="269" y2="501" class="dim" marker-start="url(#arrow)" marker-end="url(#arrow)"/>
<text x="1504" y="385" transform="rotate(-90 1504 385)" text-anchor="middle" font-size="18">30 mm</text>
{''.join(rows)}
<rect x="60" y="1011" width="1480" height="83" rx="8" fill="#e9eff3"/>
<text x="82" y="1043" font-size="19" font-weight="bold">Checks: reserved volumes do not overlap; solid dummy STL dimensions verified.</text>
<text x="82" y="1074" font-size="18">Open: actual PCB layout, RF / antennas, sensor contact, runtime and mechanical assembly.</text>
</svg>'''
(ROOT / 'previews/compact-250-review.svg').write_text(svg)
print(json.dumps(dict(sheet='previews/compact-250-review.svg', exported_stl_bounds=stls)))
