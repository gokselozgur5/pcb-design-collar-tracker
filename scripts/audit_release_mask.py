#!/usr/bin/env python3
"""Measure pad/mask/paste overlap in this release's actual Gerbers.

Deliberately limited to KiCad's mm/4.6, linear-region Gerbers with the
RoundRect macro and standard R/O/C apertures. Unsupported drawing operations
fail instead of silently producing a clean result. This is not JLCDFM.
Run with .venv-dfm/bin/python.
"""
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'release/collar-tracker-0.3-35x28-dfm'
OUTPUT = ROOT / 'evidence/jlc-dfm-20261024-r3/gerber-mask-audit.json'


def aperture(kind, params):
    v = [float(x) for x in params.split('X')]
    if kind == 'C':
        assert len(v) == 1
        return Point(0, 0).buffer(v[0] / 2, quad_segs=96)
    if kind == 'R':
        assert len(v) == 2
        return box(-v[0]/2, -v[1]/2, v[0]/2, v[1]/2)
    if kind == 'O':
        assert len(v) == 2
        w, h = v
        a = (max(0, w-h)/2, max(0, h-w)/2)
        return LineString([(-a[0], -a[1]), a]).buffer(min(w,h)/2, quad_segs=96)
    if kind == 'RoundRect':
        assert len(v) == 10 and v[-1] == 0, v
        return Polygon(list(zip(v[1:9:2], v[2:9:2]))).buffer(v[0], quad_segs=96)
    raise ValueError(f'Unsupported aperture {kind}')


def read_gerber(path, copper=False):
    text = path.read_text()
    assert '%MOMM*%' in text and '%FSLAX46Y46*%' in text
    assert not re.search(r'G0[23]|%LP[CR]|%SR|%L[MR]|%LS|%AB', text)
    macros = re.findall(r'%AM([^*]+)\*', text)
    assert set(macros) <= {'RoundRect'}, macros
    # Recognize KiCad's exact RoundRect construction, not an arbitrary macro
    # that merely has the same name.
    if macros:
        macro = re.search(r'%AMRoundRect\*(.*?)\*%', text, re.S).group(1)
        primitives = [x.strip() for x in macro.split('*') if x.strip() and not x.strip().startswith('0 ')]
        assert len(primitives) == 9
        assert primitives[0] == '4,1,4,$2,$3,$4,$5,$6,$7,$8,$9,$2,$3,0'
        assert sum(x.startswith('1,1,$1+$1,') for x in primitives) == 4
        assert sum(x.startswith('20,1,$1+$1,') for x in primitives) == 4
    definitions = {int(n): aperture(k, v) for n,k,v in re.findall(r'%ADD(\d+)([^,*]+),([^*]+)\*%', text)}
    dcode = None
    owner = None
    pin = None
    region = None
    shapes, pads = [], []
    for line in text.splitlines():
        if line.startswith('%TO.C,'):
            owner = line[len('%TO.C,'):-2]
        elif line.startswith('%TO.P,'):
            owner, pin = line[len('%TO.P,'):-2].split(',')[:2]
        elif line == '%TD*%':
            owner = pin = None
        elif re.fullmatch(r'D\d+\*', line):
            dcode = int(line[1:-1])
            assert dcode in definitions
        elif line == 'G36*':
            assert region is None
            region = []
        elif line == 'G37*':
            assert region is not None and len(region) >= 4
            # Copper pours may use bridged hole contours. They are not part of
            # this pad-flash-only audit and must not be reinterpreted as pads.
            if not copper:
                p = Polygon(region)
                assert p.is_valid
                shapes.append((owner, p))
            region = None
        elif line.startswith(('X', 'Y')):
            m = re.fullmatch(r'X(-?\d+)Y(-?\d+)D0([123])\*', line)
            assert m, f'Unsupported coordinate {line}'
            x, y, op = int(m[1])/1e6, int(m[2])/1e6, m[3]
            if region is not None:
                assert op in ['1', '2']
                assert not region or op == '1', 'Multiple contours need a general Gerber parser'
                region.append((x,y))
            elif op == '3':
                g = translate(definitions[dcode], x, y)
                shapes.append((owner, g))
                if pin is not None:
                    pads.append({'ref':owner, 'pin':pin, 'xy':[x,y], 'geometry':g})
            else:
                assert copper, f'Unexpected stroked aperture in {path.name}'
    assert region is None
    return shapes, pads


def main():
    archive = SOURCE.parent / (SOURCE.name + '.zip')
    report = {'release':str(SOURCE), 'scope':'Actual Gerber pad-flash coverage by mask apertures; JLC example locations are not supplied.',
              'coordinate_system':'Gerber mm, board bottom-left origin; Y upwards',
              'comparison_tolerance_mm':0.0001, 'hashes':{}, 'sides':{},
              'zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name in z.namelist():
            assert (SOURCE/name).read_bytes() == z.read(name), f'Extracted file differs: {name}'
    report['zip_and_extracted_files_identical'] = True
    for side, ce, me, pe in [('top','gtl','gts','gtp'), ('bottom','gbl','gbs','gbp')]:
        paths = [next(SOURCE.glob('*.'+x)) for x in [ce, me, pe]]
        for p in paths: report['hashes'][p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
        _, pads = read_gerber(paths[0], copper=True)
        masks, _ = read_gerber(paths[1])
        paste, _ = read_gerber(paths[2])
        mu = unary_union([g for _,g in masks])
        pu = unary_union([g for _,g in paste])
        assert pads and mu.is_valid and pu.is_valid
        incomplete = []
        coverage = []
        for p in pads:
            g = p['geometry']
            item = {k:v for k,v in p.items() if k != 'geometry'}
            diff = g.difference(mu.buffer(0.0001, quad_segs=96))
            item.update(copper_area_mm2=g.area, uncovered_copper_area_mm2=diff.area,
                        paste_copper_area_ratio=g.intersection(pu).area/g.area)
            if diff.area > 1e-7: incomplete.append(item)
            coverage.append(item)
        report['sides'][side] = {'pad_flashes':len(pads), 'fully_mask_exposed':len(pads)-len(incomplete),
                                 'partially_mask_covered':incomplete, 'pads':coverage}
    OUTPUT.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:{'pads':v['pad_flashes'],'fully_mask_exposed':v['fully_mask_exposed'],
                       'partially_mask_covered':v['partially_mask_covered']} for k,v in report['sides'].items()}, indent=2))


if __name__ == '__main__':
    if len(sys.argv)>1:
        assert len(sys.argv)==3, 'usage: audit_release_mask.py [release-directory report.json]'
        SOURCE=Path(sys.argv[1]).resolve()
        OUTPUT=Path(sys.argv[2]).resolve()
    main()
