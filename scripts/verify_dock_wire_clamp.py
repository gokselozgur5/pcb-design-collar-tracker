#!/usr/bin/env python3
"""Read-only r15 evidence verification, with no physical release inference."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from check_dock_wire_clamp import evaluate, validate_contact_faces
from inspect_enclosure_mesh import inspect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'mechanical/swim-r15-wire-clamp'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def evidence():
    spec = json.loads((OUT/'dock.json').read_text())
    saved = json.loads((OUT/'checks.json').read_text())
    current = evaluate(spec)
    require(all(saved[k] == v for k, v in current.items()), 'Clamping calculation differs from source')
    require(current['result'] == 'CLAMP_GEOMETRY_PASS', 'Clamp calculation failed')
    require(not spec['production_release'] and not current['physical_retention_qualified'] and
            not spec['clamp']['physical_retention_qualified'] and
            not spec['clamp']['insulation_compression_qualified'], 'Unexpected physical acceptance')
    mesh = json.loads((OUT/'mesh-checks.json').read_text())
    for report in [saved, mesh]:
        for name, digest in report['inputs'].items():
            require(sha(ROOT/name) == digest, 'Changed clamp input: '+name)
    names = {'lower.stl', 'upper.stl', 'cap.stl', 'fixture.stl'}
    require({m['file'] for m in mesh['meshes']} == names, 'Missing clamp mesh')
    for row in mesh['meshes']:
        require(inspect(OUT/row['file']) == row, 'Changed clamp mesh: '+row['file'])
    require(set(mesh['diagnostics']) == {Path(n).stem for n in names}, 'Missing CAD diagnostics')
    for name, diagnostic in mesh['diagnostics'].items():
        require(not re.search(r'WARNING|ERROR', diagnostic) and re.search(r'Simple:\s+yes', diagnostic),
                'CAD warning or invalid solid: '+name)
    expected = {'pin_interference': True, 'collar_interference': True, 'wire_interference': True,
                'stationary_interference': True, 'cap_interference': False, 'screw_interference': False,
                'fixture_interference': True, 'pad_interference': False, 'old_pad_pocket_control': False,
                'key_reversed': False, 'old_upper_control': False,
                'pinch_control': False, 'cap_overlap_control': False}
    require({c['case'] for c in mesh['controls']} == set(expected), 'Missing clamp CAD control')
    for c in mesh['controls']:
        empty = expected[c['case']]
        bearing = c['case'] in {'cap_interference', 'screw_interference', 'pad_interference'}
        require(c['planar_bearing'] == bearing, 'Wrong bearing scope')
        if bearing:
            validate_contact_faces(c['case'], c['contact_vertices'], spec)
            require(c['returncode']==0 and not c['empty'] and not c['expected_empty'] and
                    c['interference_volume_mm3']==0, 'Wrong bearing result')
            allowed = {'WARNING: Object may not be a valid 2-manifold and may need repair!',
                       'EXPORT-WARNING: Exported object may not be a valid 2-manifold and may need repair'}
            require(all(line in allowed for line in c['diagnostic'].splitlines()
                        if re.search(r'WARNING|ERROR', line)), 'Unexpected bearing diagnostic')
            continue
        require(not re.search(r'WARNING|ERROR', c['diagnostic']), 'CAD control warning: '+c['case'])
        require(c['empty'] == empty and c['expected_empty'] == empty and
                c['returncode'] == (1 if empty else 0) and
                (c['interference_volume_mm3'] == 0 if empty else c['interference_volume_mm3'] > 0),
                'Failed clamp CAD control: '+c['case'])
    require(set(mesh['previews']) == {'review.png', 'clamp_detail.png', 'fixture_review.png'}, 'Missing preview')
    for name, digest in mesh['previews'].items():
        require(sha(OUT/name) == digest, 'Changed clamp preview: '+name)
    require(not mesh['physical_qualification'], 'Unexpected physical CAD acceptance')
    return current


def record():
    evidence()
    names = ['README.md', 'sources.json', 'dock.json', 'dock.scad', 'checks.json', 'parameters.scad',
             'lower.stl', 'upper.stl', 'cap.stl', 'fixture.stl', 'mesh-checks.json',
             'review.png', 'clamp_detail.png', 'fixture_review.png',
             'wire-clamp-sheet.svg', 'wire-clamp-sheet.pdf', 'wire-clamp-sheet.png']
    files = [OUT/name for name in names]
    files += [ROOT/'scripts'/name for name in ['check_dock_wire_clamp.py', 'export_dock_wire_clamp.py',
                                             'make_dock_clamp_sheet.py', 'verify_dock_wire_clamp.py']]
    files += [ROOT/'tests/test_dock_wire_clamp.py']
    cp = dict(revision='r15', production_release=False, physical_qualification=False,
              files={str(p.relative_to(ROOT)): sha(p) for p in files})
    path = OUT/'checkpoint.json'
    if path.exists():
        require(json.loads(path.read_text()) == cp, 'Preserve recorded clamp checkpoint; use a successor')
    else:
        path.write_text(json.dumps(cp, indent=2)+'\n')


def verify(check_baseline=True):
    if check_baseline:
        from verify_dock_wire_motion import verify as verify_previous
        verify_previous()
    result = evidence()
    cp = json.loads((OUT/'checkpoint.json').read_text())
    require(cp['revision'] == 'r15' and not cp['production_release'] and not cp['physical_qualification'],
            'Wrong clamp scope')
    for name, digest in cp['files'].items():
        p = (ROOT/name).resolve()
        require(p.is_relative_to(ROOT) and sha(p) == digest, 'Changed clamp artifact: '+name)
    return dict(revision='r15', result='SAVED_CLAMP_GEOMETRY_VERIFIED', checks=len(result['checks']),
                inherited_checks=len(result['wire']['checks']), closed_meshes=4, cad_controls=13,
                files=len(cp['files']), physical_qualification=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', action='store_true')
    args = parser.parse_args()
    if args.record:
        record()
    print(json.dumps(verify(), indent=2))
