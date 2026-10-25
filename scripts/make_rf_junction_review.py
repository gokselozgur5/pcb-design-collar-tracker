#!/usr/bin/env python3
"""Render native LTE copper and R3 review contours before and after r05j."""
import html
import json
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, box
from audit_rf_reference import copper
from verify_rf_junction_candidate import verify_geometry, BASE, TRIAL


def main():
    checked = verify_geometry()
    e = TRIAL/'evidence'
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1000" viewBox="0 0 1500 1000">',
           '<rect width="1500" height="1000" fill="#f5f7fa"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#182335}</style>']

    def text(x,y,s,size=22):
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}">{html.escape(s)}</text>')

    text(35,45,'Collar tracker — R3 and LTE tuning junctions',32)
    text(35,80,'r05j: one 0.36 mm entry per R3 land; the resistor moves 0.30 mm. Native DRC/ERC/parity: zero.',22)
    region = box(110.2,117.5,118.6,123.5)
    for index, (trial, title, color) in enumerate([
        (BASE,'Before — r05i','#d06c17'),(TRIAL,'After — r05j','#006adc')]):
        x0 = 35 + index*745
        route = json.loads((trial/'evidence/route-geometry.json').read_text())
        rf = json.loads((trial/'evidence/rf-geometry.json').read_text())
        text(x0,125,title,25)
        svg.append(f'<rect x="{x0}" y="145" width="705" height="510" fill="#edf0e9" rx="8"/>')
        svg.append(f'<svg x="{x0+10}" y="155" width="685" height="490" viewBox="110.2 117.5 8.4 6">')
        svg.append(copper(rf['zones'][0]['poly']).intersection(region).svg(fill_color='#c7d8c5',opacity=1,scale_factor=.001))
        for t in route['tracks']:
            if t['layer'] != 'F.Cu':continue
            shape = LineString([t['start'],t['end']]).buffer(t['width']/2).intersection(region)
            if shape.is_empty:continue
            c = color if t['net'] in {'/LTE_RF','/LTE_ANT'} else '#a0abad'
            svg.append(shape.svg(fill_color=c,opacity=1,scale_factor=.0005))
        for p in route['pads']:
            if 'F.Cu' not in p['layers']:continue
            for raw in p['poly']:
                shape=Polygon(raw).intersection(region)
                if shape.is_empty or shape.area == 0:continue
                c='#c9a85d' if p['ref'] in {'R3','C11','C12','J1'} else '#889698'
                svg.append(shape.svg(fill_color=c,opacity=1,scale_factor=.0005))
                if p['ref'] == 'R3':
                    for offset in [.05,.15,.30]:
                        points=' '.join(f'{x},{y}' for x,y in shape.buffer(offset,quad_segs=48).exterior.coords)
                        svg.append(f'<polyline points="{points}" fill="none" stroke="#b32738" stroke-width=".012"/>')
        for via in route['vias']:
            pos=Point(via['pos'])
            if not region.contains(pos):continue
            x,y=via['pos'];c='#476d4d' if via['net']=='/GND' else '#69798b'
            svg.append(f'<circle cx="{x}" cy="{y}" r=".3" fill="{c}"/><circle cx="{x}" cy="{y}" r=".1" fill="#f5f7fa"/>')
        for x,y,s in [(110.5,121.08,'C11 (DNP)'),(113.0,119.62,'R3'),(112.6,123.22,'C12 (DNP)'),(116.3,123.22,'LTE U.FL')]:
            svg.append(f'<text x="{x}" y="{y}" style="font-size:.23px">{s}</text>')
        svg.append('</svg>')
        ratio=next(p for p in json.loads((trial/'evidence/passive-copper-review.json').read_text())['passives'] if p['ref']=='R3')['ratios']
        text(x0,687,'R3 ratios: '+' / '.join(f'{ratio[k]:.3f}' for k in ['0.05','0.15','0.3']),24)
    lines=[
        'Red contours are 0.05 / 0.15 / 0.30 mm outside each land. Ratios compare unique trace-copper intersections.',
        'C11 branch: 1.31 → 0.42 mm centerline. C12 lies on the main path, eliminating its previous 2.84 mm branch.',
        'Tradeoff: combined LTE feed centerline grows from 5.89 to 8.91 mm, excluding the resistor body. RF loss is unmeasured.',
        'All vias, other component placements, inner copper, continuous GND planes, module escapes and stack stay unchanged.',
        '1,742 native reference probes agree; all RF trace copper projects onto In1.Cu GND. This is not an EM simulation.',
        '69 populated envelopes pass the modeled thickness range. Assembly, power, antenna/body and IP68 remain unqualified.',
    ]
    for n,line in enumerate(lines):text(35,737+n*36,line,20)
    text(35,980,'PCB SHA256 '+checked['source_sha256'],17)
    svg.append('</svg>')
    (e/'rf-junction-review.svg').write_text('\n'.join(svg)+'\n')


if __name__ == '__main__':
    main()
