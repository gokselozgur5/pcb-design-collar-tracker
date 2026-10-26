#!/usr/bin/env python3
"""Export three staking envelopes and two removable, open-top forming nests."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
from importlib.metadata import version
import subprocess

import numpy as np
import manifold3d as m

from internal_harness_geometry import evaluate
from inspect_enclosure_mesh import inspect
from charge_fixture_csg import fixture as make_fixture, read_stl, write_stl, collision

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'assembly/internal-charge-r03'
RUNTIME = ROOT/'.runtime/internal-restraint-r19/cad'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def tube(control, radius, path, shift):
    """Closed full-radius witness, independent of the open-channel CAD generator."""
    cv = evaluate(control,1201)
    vertices=[]; previous=None; sides=32
    for xyz, derivative in zip(cv['xyz'],cv['derivative'],strict=True):
        tangent=derivative/np.linalg.norm(derivative)
        normal=np.cross(tangent,[0,0,1]) if previous is None else previous-tangent*np.dot(previous,tangent)
        normal/=np.linalg.norm(normal);previous=normal
        binormal=np.cross(tangent,normal)
        vertices.append([xyz+shift+radius*(normal*math.cos(2*math.pi*j/sides)+binormal*math.sin(2*math.pi*j/sides))
                         for j in range(sides)])
    vertices=np.array(vertices); faces=[]
    for i in range(len(vertices)-1):
        for j in range(sides):
            k=(j+1)%sides
            faces += [[vertices[i,j],vertices[i,k],vertices[i+1,k]],
                      [vertices[i,j],vertices[i+1,k],vertices[i+1,j]]]
    for j in range(1,sides-1):
        faces += [[vertices[0,0],vertices[0,j+1],vertices[0,j]],
                  [vertices[-1,0],vertices[-1,j],vertices[-1,j+1]]]
    triangles=np.array(faces)
    if np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()<0:
        triangles=triangles[:,[0,2,1]]
    data=bytearray(b'R19 tool fit witness; not a production wire'.ljust(80,b' '))
    data+=struct.pack('<I',len(triangles))
    for triangle in triangles:
        normal=np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0]);normal/=np.linalg.norm(normal)
        data+=struct.pack('<12fH',*normal,*triangle.ravel(),0)
    path.write_bytes(data)
    return inspect(path)


def main():
    exe=os.environ.get('COLLAR_OPENSCAD') or shutil.which('openscad')
    if not exe:
        raise ValueError('OpenSCAD is required')
    RUNTIME.mkdir(parents=True,exist_ok=True)
    if version('manifold3d')!='3.5.4':raise ValueError('Use the pinned Manifold version')
    initial_names=[OUT/'restraint.json',Path(__file__),ROOT/'scripts/internal_harness_geometry.py',ROOT/'scripts/inspect_enclosure_mesh.py',ROOT/'assembly/internal-charge-r02/harness.json',ROOT/'mechanical/swim-r18-charge-clearance/routing.json',ROOT/'scripts/charge_fixture_csg.py',OUT/'requirements.txt']
    initial_hashes={str(path.relative_to(ROOT)):sha(path) for path in initial_names}
    spec=json.loads((OUT/'restraint.json').read_text())
    model=json.loads((ROOT/spec['route_source']).read_text())
    wire=json.loads((ROOT/'assembly/internal-charge-r02/harness.json').read_text())['wire']
    inputs=[OUT/'restraint.json',ROOT/spec['route_source'],Path(__file__),
            ROOT/'scripts/internal_harness_geometry.py',ROOT/'scripts/inspect_enclosure_mesh.py',
            ROOT/'assembly/internal-charge-r02/harness.json',
            ROOT/'mechanical/swim-r18-charge-clearance/harness.scad']
    text=(ROOT/'mechanical/swim-r18-charge-clearance/harness.scad').read_text()
    def imports(match):
        actual=(ROOT/'mechanical/swim-r18-charge-clearance'/match[1]).resolve()
        inputs.append(actual)
        return 'import("'+os.path.relpath(actual,OUT)+'")'
    text=re.sub(r'import\("([^"]+)"\)',imports,text)
    text=text[:text.index('if(part=="gnss_guide_collision")')]
    patches=[[v['low_mm'],(np.array(v['high_mm'])-v['low_mm']).tolist()] for v in spec['patches']]
    text+='\npatches='+json.dumps(patches)+';\n'+'''
module staking(){for(v=patches)translate(v[0])cube(v[1]);}
module unexpected(){intersection(){staking();union(){obstacles();translate([0,0,18.5])import("../../mechanical/swim-r11-thermal-fit/lid.stl");}}}
module displaced_control(){intersection(){translate([1,0,0])staking();components();}}
if(part=="envelopes")staking();
else if(part=="unexpected")unexpected();
else if(part=="displaced_control")displaced_control();
else {review();color([0.2,0.85,0.75,0.7])staking();}
'''
    scene=OUT/'restraint.scad';scene.write_text(text)
    inputs.append(ROOT/'mechanical/swim-r11-thermal-fit/lid.stl')
    inputs.append(scene)
    meshes=[]; controls=[]; tools=[]
    def preview(scene,dest):
        proc=subprocess.run([exe,'-o',str(dest),'--imgsize','1500,1000','--projection','o',
                             '--viewall','--autocenter','--camera','0,0,0,30,0,30,120',
                             '--colorscheme','Tomorrow','-D','part="review"',str(scene)],capture_output=True,text=True)
        if proc.returncode or re.search('WARNING|ERROR',proc.stderr):
            raise ValueError(proc.stderr)
    staker=m.Manifold.batch_boolean([m.Manifold.cube(size).translate(low) for low,size in patches],m.OpType.Add)
    write_stl(staker,OUT/'staking-envelopes.stl')
    meshes.append(inspect(OUT/'staking-envelopes.stl',allow_separate=True))
    obstacles=[read_stl(ROOT/'mechanical/swim-r16-contact-retention/body.stl'),
               read_stl(ROOT/'mechanical/swim-r12-pack-retention/carrier.stl').translate([0,0,1.8]),
               read_stl(ROOT/'mechanical/swim-r18-charge-clearance/retainer.stl').translate([0,0,10.6]),
               read_stl(ROOT/'mechanical/swim-r11-thermal-fit/lid.stl').translate([0,0,18.5])]
    component_line=next(line for line in text.splitlines() if line.startswith('part_boxes = '))
    components=[m.Manifold.cube(size).translate(low) for _,low,size in json.loads(component_line.split('=',1)[1].strip().rstrip(';'))]
    actual=m.Manifold.batch_boolean(obstacles+components,m.OpType.Add)
    controls.append(collision(staker,actual,'staking-collision',True))
    controls.append(collision(staker.translate([1,0,0]),m.Manifold.batch_boolean(components,m.OpType.Add),'displaced-staking-control',False))
    print('staking CAD PASS',flush=True)
    preview(scene,OUT/'restraint-preview.png')
    for index,colour in enumerate(['red','black']):
        f=spec['fixture'];control=model['poses'][f['nominal_pose_index']]['charge_controls'][index]
        cv=evaluate(control,f['curve_sampling_count']);xyz=cv['xyz']
        radius=wire['outside_diameter_max_mm']/2+f['groove_extra_radius_mm']
        shift=np.array([f['base_margin_mm']-xyz[:,0].min(),
                        f['base_margin_mm']-xyz[:,1].min(),
                        f['minimum_floor_mm']+radius-xyz[:,2].min()])
        points=xyz+shift
        size=[float(np.ptp(xyz[:,0])+2*f['base_margin_mm']),
              float(np.ptp(xyz[:,1])+2*f['base_margin_mm']),f['base_height_mm']]
        # Each Bezier cell is inside its control hull. Its maximum distance
        # from its endpoint chord bounds deviation from the CAD path segment.
        cells=cv['cells'];v=cells[:,3]-cells[:,0];vv=(v*v).sum(axis=1)
        fraction=np.clip(np.einsum('ijk,ik->ij',cells-cells[:,0,None,:],v)/vv[:,None],0,1)
        chord_error=float(np.linalg.norm(cells-(cells[:,0,None,:]+fraction[:,:,None]*v[:,None,:]),axis=2).max())
        tool_error=f['dimensional_tolerance_mm'];minimum=f['minimum_radial_clearance_mm']
        cylinder_sides=24
        clearance_bound=radius*math.cos(math.pi/cylinder_sides)-wire['outside_diameter_max_mm']/2-tool_error-chord_error
        if clearance_bound<minimum:
            raise ValueError('Insufficient continuous fixture clearance')
        if points[:,2].max()+radius>=size[2]:
            raise ValueError('Fixture wall is too low')
        # Account explicitly for inscribed polygon facets in the clearance bound.
        # Overlapping hulls make every channel section vertically open.
        first=points[0,:2]-points[1,:2];last=points[-1,:2]-points[-2,:2]
        # Horizontal lead-outs retain the full minimum floor at the wire ends.
        cut_points=np.vstack([points[0]+np.r_[first*.8/np.linalg.norm(first),0],
                              points,points[-1]+np.r_[last*.8/np.linalg.norm(last),0]])
        floor=float(cut_points[:,2].min()-radius)
        if floor<f['minimum_floor_mm']-1e-8:raise ValueError('Tool floor is too thin')
        tool_text='path='+json.dumps(cut_points.tolist())+';\nsize='+json.dumps(size)+';\nradius='+str(radius)+';\n'+'''
part="fixture";
module slot(r){for(i=[0:len(path)-2])hull(){
 for(j=[i:i+1])translate([path[j][0],path[j][1],path[j][2]-r])cylinder(r=r,h=size[2]+2-path[j][2]+r,$fn=24);
}}
module label(){translate([3,1,size[2]-.3])linear_extrude(.31)text("'''+colour.upper()+''' R19",size=2);}
module fixture(r=radius){difference(){cube(size);slot(r);label();}}
if(part=="label")label();
else if(part=="fixture")fixture();
else if(part=="collision")intersection(){import("'''+colour+'''-fixture.stl");import("'''+colour+'''-fixture-witness.stl");}
else if(part=="raised_floor_control")intersection(){translate([0,0,.30])import("'''+colour+'''-fixture.stl");import("'''+colour+'''-fixture-witness.stl");}
else {color([.65,.67,.72])import("'''+colour+'''-fixture.stl");color('''+('[.95,.15,.1]' if index==0 else '[.08,.09,.12]')+''')import("'''+colour+'''-fixture-wire.stl");}
'''
        tool_path=OUT/(colour+'-fixture.scad');tool_path.write_text(tool_text)
        # The witness includes machining error, required clearance, wire max OD,
        # polygon circumscription and the finer spline-to-mesh chord deviation.
        fine=evaluate(control,1201);fine_cells=fine['cells'];u=fine_cells[:,3]-fine_cells[:,0]
        frac=np.clip(np.einsum('ijk,ik->ij',fine_cells-fine_cells[:,0,None,:],u)/(u*u).sum(axis=1)[:,None],0,1)
        fine_error=float(np.linalg.norm(fine_cells-(fine_cells[:,0,None,:]+frac[:,:,None]*u[:,None,:]),axis=2).max())
        witness_radius=(wire['outside_diameter_max_mm']/2+tool_error+minimum+fine_error)/math.cos(math.pi/32)
        meshes.append(tube(control,witness_radius,OUT/(colour+'-fixture-witness.stl'),shift))
        meshes.append(tube(control,wire['outside_diameter_nominal_mm']/2,OUT/(colour+'-fixture-wire.stl'),shift))
        label_path=RUNTIME/(colour+'-label.stl')
        proc=subprocess.run([exe,'-o',str(label_path),'--export-format','binstl','-D','part="label"',str(tool_path)],capture_output=True,text=True)
        if proc.returncode or re.search('WARNING|ERROR',proc.stderr):raise ValueError(proc.stderr)
        solid=make_fixture(cut_points,size,radius,read_stl(label_path))
        fixture_path=OUT/(colour+'-fixture.stl');write_stl(solid,fixture_path)
        meshes.append(inspect(fixture_path))
        witness_solid=read_stl(OUT/(colour+'-fixture-witness.stl'))
        delivered=read_stl(fixture_path)
        controls.append(collision(delivered,witness_solid,colour+'-fixture-collision',True))
        controls.append(collision(delivered.translate([0,0,.30]),witness_solid,colour+'-raised-floor-control',False))
        print(fixture_path.name,'PASS',floor,flush=True)
        preview(tool_path,OUT/(colour+'-fixture-preview.png'))
        inputs.append(tool_path)
        inputs += [ROOT/'scripts/charge_fixture_csg.py',OUT/'requirements.txt']
        tools.append(dict(colour=colour,case_to_fixture_translation_mm=shift.tolist(),size_mm=size,
                          continuous_chord_error_bound_mm=chord_error,
                          minimum_clearance_bound_mm=clearance_bound,minimum_floor_mm=floor,
                          witness_radius_mm=witness_radius,vertical_removal_open=True,
                          wire_length_mm=model['wire_target_lengths_mm'][index],
                          length_tolerance_qualified=False))
    if any(sha(ROOT/name)!=digest for name,digest in initial_hashes.items()):
        raise ValueError('Source changed during CAD generation')
    hashes={str(path.relative_to(ROOT)):sha(path) for path in inputs}
    report=dict(inputs=hashes,meshes=meshes,controls=controls,forming_tools=tools,
                previews={path.name:sha(path) for path in OUT.glob('*-preview.png')},
                physical_qualification=False,manufacturing_release=False,
                scope='Nominal CAD and continuous tool-path clearance only. No adhesion, springback, fatigue, factory tolerance or movement qualification.')
    (OUT/'cad-checks.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    main()
