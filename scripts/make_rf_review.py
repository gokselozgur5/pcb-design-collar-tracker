#!/usr/bin/env python3
"""Draw the actual before/after RF copper over its saved reference plane."""
import html
import json
from pathlib import Path

from shapely.geometry import LineString, Polygon, box
from audit_rf_reference import copper, PORT_NETS, MATCHING_NETS

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05i-rf-stack'
BASE = ROOT / 'experiments/power-r05h-six-layer'


def main():
    e = TRIAL/'evidence'
    before, after = [json.loads((e/n).read_text()) for n in ['baseline-rf-geometry.json','rf-geometry.json']]
    route_before = json.loads((BASE/'evidence/route-geometry.json').read_text())
    route_after = json.loads((e/'route-geometry.json').read_text())
    report = json.loads((e/'rf-review.json').read_text())
    summaries = [json.loads((e/f'jlc-check{n}/summary.json').read_text()) for n in [1,2]]
    assert all(s['counts']['danger'] == s['counts']['warning'] == 0 for s in summaries)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1040" viewBox="0 0 1500 1040">',
           '<rect width="1500" height="1040" fill="#f5f7fa"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#182335}.small{font-size:18px}.body{font-size:22px}</style>']

    def text(x,y,s,size=22,color='#182335'):
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{html.escape(s)}</text>')

    text(40,48,'Collar tracker — RF geometry revision r05i',32)
    text(40,82,'Native checks and two JLC PCB analyses pass. Electrical / RF / assembly / IP68: HOLD.',22)
    region = box(110.6,110.5,128.2,123.5)
    for panel, (native, route, title, color) in enumerate([
        (before,route_before,'r05h — original 0.20 mm routes','#e36c18'),
        (after,route_after,'r05i — 0.36 mm main routes','#006adc'),
    ]):
        x0=40+panel*740
        text(x0,125,title,23)
        svg.append(f'<rect x="{x0}" y="145" width="700" height="530" rx="8" fill="#edf0e9" stroke="#bac5cd"/>')
        svg.append(f'<svg x="{x0+10}" y="155" width="680" height="510" viewBox="110.6 110.5 17.6 13.2">')
        plane = copper(native['zones'][0]['poly']).intersection(region)
        svg.append(plane.svg(fill_color='#c7d8c5',opacity=1,scale_factor=.002))
        for t in route['tracks']:
            if t['layer']!='F.Cu':continue
            shape=LineString([t['start'],t['end']]).buffer(t['width']/2).intersection(region)
            if shape.is_empty:continue
            c=color if t['net'] in PORT_NETS else '#9453b4' if t['net'] in MATCHING_NETS else '#a5aeb5'
            svg.append(shape.svg(fill_color=c,opacity=1,scale_factor=.001))
        for p in route['pads']:
            if 'F.Cu' not in p['layers']:continue
            for raw in p['poly']:
                shape=Polygon(raw).intersection(region)
                if not shape.is_empty and shape.area > 0:
                    svg.append(shape.svg(fill_color='#c9a85d' if p['net'] in PORT_NETS|MATCHING_NETS else '#889698',opacity=1,scale_factor=.001))
        for v in route['vias']:
            x,y=v['pos']
            if region.contains(box(x-.3,y-.3,x+.3,y+.3)):
                c='#476d4d' if v['net']=='/GND' else '#69798b'
                svg.append(f'<circle cx="{x}" cy="{y}" r=".3" fill="{c}"/><circle cx="{x}" cy="{y}" r=".1" fill="#f5f7fa"/>')
        # Native coordinates, not illustrative component placement.
        for x,y,s in [(111.0,119.6,'C11 DNP'),(113.0,119.6,'R3'),(113.2,123.35,'C12 DNP'),
                      (116.5,123.35,'LTE'),(126.0,111.1,'GNSS'),(121.4,114.6,'SKY65943')]:
            svg.append(f'<text x="{x}" y="{y}" style="font-size:.35px;fill:#142236">{s}</text>')
        svg.append('</svg>')
    lines = [
        'Changed: six port nets, two bounded module escapes, GNSS elbow, explicit candidate stack. Pads/vias/digital copper unchanged.',
        'Reference: 1,761 native Contains probes agree; all revised RF trace copper projects onto In1.Cu GND.',
        'Candidate: JLC06081H-7628; F.Cu → In1.Cu gap 0.2104 mm. Calculator: 0.3586 mm for nominal 50 Ω.',
        'Limits: live calculator and guide disagree on Er / etch / mask; supplier confirmation and RF measurement remain open.',
        'Module-pad GND retained: VBAT runs underneath on In2.Cu. Opening it without rerouting would expose the RF pads.',
        '0.20/0.28 mm escapes, DNP matching stubs and FEM matching remain discontinuities requiring RF review.',
        'Fit: 69 populated envelopes pass at 0.71 / 0.81 / 0.84088 / 0.91 mm. Original carrier interference is still detected.',
        'No physical powered, antenna/body, factory-assembly or water/dust acceptance. Heart-rate hardware is not implemented.',
    ]
    for n,line in enumerate(lines):text(40,715+n*36,line,20)
    text(40,1018,'PCB SHA256 '+report['source_sha256'],17)
    svg.append('</svg>')
    (e/'rf-review.svg').write_text('\n'.join(svg)+'\n')


if __name__=='__main__':
    main()
