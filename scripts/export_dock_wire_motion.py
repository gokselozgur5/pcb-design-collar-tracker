#!/usr/bin/env python3
"""Generate and inspect r14 meshes and discriminating CAD controls."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from inspect_enclosure_mesh import inspect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/swim-r14-wire-motion'
RUNTIME = ROOT / '.runtime/dock-wire-r14'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    exe = os.environ.get('COLLAR_OPENSCAD') or shutil.which('openscad')
    assert exe, 'Install OpenSCAD or set COLLAR_OPENSCAD'
    RUNTIME.mkdir(parents=True, exist_ok=True)
    r = json.loads((OUT / 'checks.json').read_text())
    assert r['result'] == 'CONDITIONAL_WIRE_GEOMETRY_PASS'
    inputs = dict(r['inputs'])
    for p in [OUT / 'parameters.scad', OUT / 'dock.scad', Path(__file__),
              ROOT / 'scripts/inspect_enclosure_mesh.py',
              ROOT / 'mechanical/swim-r11-thermal-fit/boot.stl',
              ROOT / 'mechanical/swim-r13-charge-dock/body.stl',
              ROOT / 'mechanical/swim-r13-charge-dock/lower.stl',
              ROOT / 'mechanical/swim-r13-charge-dock/upper.stl']:
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
        meshes = list(pool.map(mesh, ['lower', 'upper']))

    def control(case):
        name, expected_empty = case
        with tempfile.TemporaryDirectory(prefix=name, dir=RUNTIME) as temp:
            path = Path(temp) / 'intersection.stl'
            result = subprocess.run([exe, '-o', str(path), '--export-format', 'binstl',
                                     '-D', f'part="{name}"', str(OUT / 'dock.scad')], capture_output=True, text=True)
            (RUNTIME / (name + '.log')).write_text(result.stderr)
            empty = 'Current top level object is empty.' in result.stderr
            if expected_empty:
                assert result.returncode == 1 and empty and not path.exists(), (name, result.stderr)
                volume = 0
            else:
                assert result.returncode == 0 and path.exists() and not empty, (name, result.stderr)
                volume = inspect(path, allow_separate=True)['signed_volume_mm3']
                assert volume > 0
            print('CAD control:', name, 'empty' if empty else volume, flush=True)
            return dict(case=name, expected_empty=expected_empty, empty=empty,
                        returncode=result.returncode, interference_volume_mm3=volume)

    cases = [('pin_interference', True), ('collar_interference', True),
             ('wire_interference', True), ('stationary_interference', True),
             ('key_reversed', False), ('old_housing_control', False)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        controls = list(pool.map(control, cases))
    previews = {}
    for name in ['review', 'motion', 'mounted']:
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
