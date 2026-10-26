#!/usr/bin/env python3
"""Generate and inspect r15 clamp meshes and discriminating CAD controls."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

from inspect_enclosure_mesh import inspect
from check_dock_wire_clamp import validate_contact_faces

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/swim-r15-wire-clamp'
RUNTIME = ROOT / '.runtime/dock-clamp-r15'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    exe = os.environ.get('COLLAR_OPENSCAD') or shutil.which('openscad')
    assert exe, 'Install OpenSCAD or set COLLAR_OPENSCAD'
    RUNTIME.mkdir(parents=True, exist_ok=True)
    r = json.loads((OUT / 'checks.json').read_text())
    assert r['result'] == 'CLAMP_GEOMETRY_PASS'
    inputs = dict(r['inputs'])
    for p in [OUT / 'parameters.scad', OUT / 'dock.scad', Path(__file__),
              ROOT / 'scripts/inspect_enclosure_mesh.py',
              ROOT / 'mechanical/swim-r11-thermal-fit/boot.stl',
              ROOT / 'mechanical/swim-r13-charge-dock/body.stl',
              ROOT / 'mechanical/swim-r14-wire-motion/upper.stl']:
        inputs[str(p.relative_to(ROOT))] = sha(p)
    assert all(sha(ROOT / n) == digest for n, digest in inputs.items())

    diagnostics = {}

    def mesh(name):
        path = OUT / (name + '.stl')
        with (RUNTIME / (name + '.log')).open('w') as log:
            subprocess.run([exe, '-o', str(path), '--export-format', 'binstl',
                            '-D', f'part="{name}"', str(OUT / 'dock.scad')],
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        diagnostic = (RUNTIME / (name + '.log')).read_text()
        assert not re.search(r'WARNING|ERROR', diagnostic), (name, diagnostic)
        assert re.search(r'Simple:\s+yes', diagnostic), (name, diagnostic)
        diagnostics[name] = diagnostic
        result = inspect(path)
        print('Closed mesh:', name, flush=True)
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        meshes = list(pool.map(mesh, ['lower', 'upper', 'cap', 'fixture']))

    def control(case):
        name, expected_empty = case
        bearing = name in {'cap_interference', 'screw_interference', 'pad_interference'}
        with tempfile.TemporaryDirectory(prefix=name, dir=RUNTIME) as temp:
            path = Path(temp) / 'intersection.stl'
            result = subprocess.run([exe, '-o', str(path), '--export-format', 'binstl',
                                     '-D', f'part="{name}"', str(OUT / 'dock.scad')], capture_output=True, text=True)
            (RUNTIME / (name + '.log')).write_text(result.stderr)
            empty = 'Current top level object is empty.' in result.stderr
            points = []
            if bearing:
                # Exact bearing contact produces a zero-thickness surface, not
                # a valid solid STL. Validate every exported vertex against the
                # intended plane and annulus; never discard an overlap band.
                assert result.returncode == 0 and path.exists() and not empty
                spec = json.loads((OUT/'dock.json').read_text())
                # Binary float32 keeps more precision than OpenSCAD's ASCII
                # coordinate output at X=52mm (whose rounding exceeds 1e-5mm).
                data = path.read_bytes()
                count = struct.unpack_from('<I', data, 80)[0]
                assert len(data) == 84+50*count
                points = [list(struct.unpack_from('<3f', data, 84+50*i+12+12*j))
                          for i in range(count) for j in range(3)]
                validate_contact_faces(name, points, spec)
                warning_lines = [line for line in result.stderr.splitlines() if re.search(r'WARNING|ERROR', line)]
                allowed = {'WARNING: Object may not be a valid 2-manifold and may need repair!',
                           'EXPORT-WARNING: Exported object may not be a valid 2-manifold and may need repair'}
                assert all(line in allowed for line in warning_lines), (name, warning_lines)
                volume = 0
            elif expected_empty:
                assert not re.search(r'WARNING|ERROR', result.stderr), (name, result.stderr)
                assert result.returncode == 1 and empty and not path.exists(), (name, result.stderr)
                volume = 0
            else:
                assert not re.search(r'WARNING|ERROR', result.stderr), (name, result.stderr)
                assert result.returncode == 0 and path.exists() and not empty, (name, result.stderr)
                volume = inspect(path, allow_separate=True)['signed_volume_mm3']
                assert volume > 0
            print('CAD control:', name, 'intended planar bearing' if bearing else ('empty' if empty else volume), flush=True)
            return dict(case=name, expected_empty=expected_empty, empty=empty,
                        returncode=result.returncode, interference_volume_mm3=volume,
                        diagnostic=result.stderr, planar_bearing=bearing, contact_vertices=points)

    cases = [('pin_interference', True), ('collar_interference', True),
             ('wire_interference', True), ('stationary_interference', True),
             ('cap_interference', False), ('screw_interference', False),
             ('fixture_interference', True), ('pad_interference', False),
             ('old_pad_pocket_control', False), ('key_reversed', False),
             ('old_upper_control', False), ('pinch_control', False), ('cap_overlap_control', False)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        controls = list(pool.map(control, cases))
    previews = {}
    for name in ['review', 'clamp_detail', 'fixture_review']:
        path = OUT / (name + '.png')
        with (RUNTIME / (name + '.log')).open('w') as log:
            subprocess.run([exe, '-o', str(path), '--imgsize', '1600,1100', '--projection', 'o',
                            '--viewall', '--autocenter', '--camera', '0,0,0,55,0,40,180',
                            '--colorscheme', 'Tomorrow', '-D', f'part="{name}"', str(OUT / 'dock.scad')],
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        previews[path.name] = sha(path)
        print('Rendered:', name, flush=True)
    assert all(sha(ROOT / n) == digest for n, digest in inputs.items()), 'Source changed during export'
    (OUT / 'mesh-checks.json').write_text(json.dumps(dict(inputs=inputs, meshes=meshes, diagnostics=diagnostics,
        controls=controls, previews=previews, physical_qualification=False), indent=2) + '\n')


if __name__ == '__main__':
    main()
