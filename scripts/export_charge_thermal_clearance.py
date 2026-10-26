#!/usr/bin/env python3
"""Export the relieved retainer and changed nominal charge wires; no physical release."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from export_internal_harness import mesh
from export_cable_integration import witness
from internal_harness_geometry import evaluate
from inspect_enclosure_mesh import inspect
from check_charge_thermal_clearance import validate_reliefs

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'mechanical/swim-r18-charge-clearance'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    exe = os.environ.get('COLLAR_OPENSCAD') or shutil.which('openscad')
    if not exe:
        raise ValueError('OpenSCAD is required')
    model = json.loads((OUT/'routing.json').read_text())
    nominal = dict(pose=model['poses'][13], clips=model['clips'])
    # CAD covers this exact nominal pose. Other pose calculations are separate;
    # their source identity is bound by the analytical report, not this mesh.
    nominal_path = OUT/'nominal-routing.json'
    nominal_path.write_text(json.dumps(nominal, indent=2)+'\n')
    paths = [nominal_path, OUT/'retainer-reliefs.json', Path(__file__)]
    paths += [ROOT/name for name in [
        'scripts/export_internal_harness.py', 'scripts/export_cable_integration.py',
        'scripts/internal_harness_geometry.py',
        'scripts/inspect_enclosure_mesh.py', 'scripts/check_charge_thermal_clearance.py',
        'assembly/internal-charge-r02/harness.json', 'assembly/internal-charge-r02/harness.scad',
        'mechanical/swim-r11-thermal-fit/retainer.stl',
        'mechanical/swim-r11-thermal-fit/lid.stl',
        'mechanical/swim-r16-contact-retention/body.stl',
        'mechanical/swim-r16-contact-retention/positive_terminal.stl',
        'mechanical/swim-r16-contact-retention/negative_terminal.stl',
        'mechanical/swim-r12-pack-retention/carrier.stl']]
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    reliefs = json.loads((OUT/'retainer-reliefs.json').read_text())
    validate_reliefs(reliefs)
    spec = json.loads((ROOT/'assembly/internal-charge-r02/harness.json').read_text())
    meshes = [mesh(control, spec['wire'], OUT/(colour+'-wire.stl'))
              for colour, control in zip(['red', 'black'], model['poses'][13]['charge_controls'])]
    meshes.append(witness(model['poses'][13]['cables'][1]['control_points_mm'], model['clips'],
                          OUT/'gnss-guide-witness.stl'))
    cuts = []
    expected_volume = 0.
    for c in reliefs['cuts']:
        x, y, u, v = c['xy_mm']
        cuts.append([[x, y, c['bottom_z_mm']-10.6], [u-x, v-y, 3]])
        expected_volume += .5*(v-y)*(12.7-c['bottom_z_mm'])
    retainer_scad = 'cuts='+json.dumps(cuts)+';\n'+'''
part="retainer";
module old(){import("../swim-r11-thermal-fit/retainer.stl");}
module revised(){difference(){old();for(c=cuts)translate(c[0])cube(c[1]);}}
if(part=="added_material")difference(){revised();old();}
else if(part=="removed_material")difference(){old();revised();}
else revised();
'''
    (OUT/'retainer.scad').write_text(retainer_scad)
    runtime = ROOT/'.runtime/internal-restraint-r18/cad'
    runtime.mkdir(parents=True, exist_ok=True)

    def render(scene, name, dest):
        proc = subprocess.run([exe, '-o', str(dest), '--export-format', 'binstl',
                               '-D', 'part="'+name+'"', str(OUT/scene)],
                              capture_output=True, text=True)
        (runtime/(name+'.log')).write_text(proc.stderr)
        if re.search('WARNING|ERROR', proc.stderr):
            raise ValueError(proc.stderr)
        return proc

    proc = render('retainer.scad', 'retainer', OUT/'retainer.stl')
    if proc.returncode:
        raise ValueError(proc.stderr)
    meshes.append(inspect(OUT/'retainer.stl'))
    text = (ROOT/'assembly/internal-charge-r02/harness.scad').read_text()
    rf = [evaluate(c['control_points_mm'], 121)['xyz'].tolist() for c in model['poses'][13]['cables']]
    text = re.sub(r'^rf_paths = .*?;$', 'rf_paths = '+json.dumps(rf)+';', text, flags=re.M)
    text = text.replace('../../mechanical/swim-r11-thermal-fit/retainer.stl', 'retainer.stl')
    text = text.replace('Nominal assembled wire prototype;', 'r18 thermal-clearance nominal assembly;')
    text = text.replace('if(part=="collision")collision();', '''module gnss_guide_collision(){intersection(){
 translate([0,0,18.5])import("../swim-r11-thermal-fit/lid.stl");
 import("gnss-guide-witness.stl");
}}
if(part=="gnss_guide_collision")gnss_guide_collision();
else if(part=="collision")collision();''')
    (OUT/'harness.scad').write_text(text)
    controls = []
    for scene, name, expected in [('retainer.scad', 'added_material', 0),
                                   ('retainer.scad', 'removed_material', expected_volume),
                                   ('harness.scad', 'collision', 0),
                                   ('harness.scad', 'metal_collision', 0),
                                   ('harness.scad', 'gnss_guide_collision', 0)]:
        with tempfile.TemporaryDirectory(dir=runtime, prefix=name) as temp:
            dest = Path(temp)/'result.stl'
            proc = render(scene, name, dest)
            empty = 'Current top level object is empty.' in proc.stderr
            if expected == 0:
                if not (empty and proc.returncode == 1 and not dest.exists()):
                    raise ValueError(name+' has unexpected material: '+proc.stderr)
                volume = 0.
            else:
                if proc.returncode or empty:
                    raise ValueError(name+' control failed: '+proc.stderr)
                volume = inspect(dest, allow_separate=True)['signed_volume_mm3']
                if abs(volume-expected) > 1e-4:
                    raise ValueError('Removed retainer volume differs from both designed slots')
            controls.append(dict(name=name, expected_volume_mm3=expected, volume_mm3=volume,
                                 empty=empty, returncode=proc.returncode, diagnostic=proc.stderr))
            print('CAD', name, volume, flush=True)
    preview = OUT/'review.png'
    proc = subprocess.run([exe, '-o', str(preview), '--imgsize', '1600,1100',
                           '--projection', 'o', '--viewall', '--autocenter',
                           '--camera', '0,0,0,55,0,40,150', '--colorscheme', 'Tomorrow',
                           str(OUT/'harness.scad')], capture_output=True, text=True)
    if proc.returncode or re.search('WARNING|ERROR', proc.stderr):
        raise ValueError(proc.stderr)
    if any(sha(ROOT/name) != digest for name, digest in hashes.items()):
        raise ValueError('CAD input changed during export')
    current = json.loads((OUT/'routing.json').read_text())
    if nominal != dict(pose=current['poses'][13], clips=current['clips']):
        raise ValueError('Nominal routing changed during export')
    for name in ['retainer.scad', 'harness.scad']:
        hashes[str((OUT/name).relative_to(ROOT))] = sha(OUT/name)
    report = dict(inputs=hashes, meshes=meshes, controls=controls,
                  preview_sha256=sha(preview), physical_qualification=False,
                  scope='Nominal CAD only; expanded tolerance geometry is checked separately. Frame strength and actual wire motion remain unqualified.')
    (OUT/'cad-checks.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
