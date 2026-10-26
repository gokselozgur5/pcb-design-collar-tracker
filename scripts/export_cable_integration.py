#!/usr/bin/env python3
"""Render the four-cable assembly and check RF passage through the existing lid.

CAD witnesses use the nominal 1.13 mm RF diameter. Position/travel allowances
are covered separately by check_cable_integration.py, not by these mesh tests.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

import numpy as np

from internal_harness_geometry import evaluate
from check_internal_harness import point_box_distance
from inspect_enclosure_mesh import inspect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/swim-r17-cable-integration'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def witness(control,clips,destination):
    curve=evaluate(control)
    xyz=curve['xyz']
    nearby=np.zeros(len(xyz),dtype=bool)
    for clip in clips:
        nearby |= point_box_distance(xyz,np.array(clip['low']),np.array(clip['high']))<2
    indices=np.flatnonzero(nearby)
    groups=np.split(indices,np.flatnonzero(np.diff(indices)>1)+1)
    triangles=[]
    for group in groups:
        if len(group)<3:
            raise ValueError('Insufficient guide witness geometry')
        rings=[];previous=None;count=24
        for i in group:
            tangent=curve['derivative'][i]/np.linalg.norm(curve['derivative'][i])
            normal=np.cross(tangent,[0,0,1]) if previous is None else previous-tangent*np.dot(previous,tangent)
            normal/=np.linalg.norm(normal);previous=normal
            binormal=np.cross(tangent,normal)
            rings.append([xyz[i]+.565*(math.cos(2*math.pi*j/count)*normal+math.sin(2*math.pi*j/count)*binormal) for j in range(count)])
        rings=np.array(rings);piece=[]
        for i in range(len(rings)-1):
            for j in range(count):
                k=(j+1)%count
                piece.extend([[rings[i,j],rings[i,k],rings[i+1,k]],[rings[i,j],rings[i+1,k],rings[i+1,j]]])
        for j in range(1,count-1):
            piece.extend([[rings[0,0],rings[0,j+1],rings[0,j]],[rings[-1,0],rings[-1,j],rings[-1,j+1]]])
        piece=np.array(piece)
        if np.einsum('ij,ij->i',piece[:,0],np.cross(piece[:,1],piece[:,2])).sum()<0:
            piece=piece[:,[0,2,1]]
        triangles.extend(piece)
    data=bytearray(b'Nominal RF guide witness; positional allowance is checked analytically'.ljust(80,b' '))
    data+=struct.pack('<I',len(triangles))
    for tri in triangles:
        normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);normal/=np.linalg.norm(normal)
        data+=struct.pack('<12fH',*normal,*np.array(tri).ravel(),0)
    destination.write_bytes(data)
    return inspect(destination,allow_separate=True)


def main():
    exe=os.environ.get('COLLAR_OPENSCAD') or shutil.which('openscad')
    if not exe:raise ValueError('OpenSCAD is required')
    model=json.loads((OUT/'routing.json').read_text());nominal=model['poses'][13]
    inputs=[OUT/'routing.json',Path(__file__),ROOT/'scripts/internal_harness_geometry.py',
            ROOT/'scripts/check_internal_harness.py',ROOT/'scripts/inspect_enclosure_mesh.py',
            ROOT/'mechanical/swim-r11-thermal-fit/lid.stl',ROOT/'mechanical/swim-r11-thermal-fit/retainer.stl',
            ROOT/'mechanical/swim-r16-contact-retention/body.stl',ROOT/'mechanical/swim-r12-pack-retention/carrier.stl',
            ROOT/'assembly/internal-charge-r02/red-wire.stl',ROOT/'assembly/internal-charge-r02/black-wire.stl',
            ROOT/'mechanical/swim-r11-thermal-fit/antenna-fit.json']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in inputs}
    meshes=[witness(c['control_points_mm'],model['clips'],OUT/(c['name'].lower()+'-guide-witness.stl')) for c in nominal['cables']]
    paths=[evaluate(c['control_points_mm'],241)['xyz'].tolist() for c in nominal['cables']]
    fit=json.loads((ROOT/'mechanical/swim-r11-thermal-fit/antenna-fit.json').read_text())['scenarios'][2]
    boxes=[]
    for part in fit['parts']:
        if part['ref']=='J3':continue
        a,b,c,d=part['envelope_xy_bounds_mm'];lo,hi=part['envelope_z_mm']
        boxes.append([[a,b,lo],[c-a,d-b,hi-lo]])
    scad='rf_paths='+json.dumps(paths)+';\npart_boxes='+json.dumps(boxes)+';\n'
    scad+='''// Four-cable nominal assembly. Physical qualification remains open.
part="review";
module lid(){translate([0,0,18.5])import("../swim-r11-thermal-fit/lid.stl");}
module witnesses(){import("lte-guide-witness.stl");import("gnss-guide-witness.stl");}
module guide_collision(){intersection(){lid();witnesses();}}
// A 0.3 mm cube is wholly inside the existing LTE guide wall. This gives an
// exact positive-volume Boolean control without tangential cable slivers.
module guide_wall_control(){intersection(){lid();translate([-16.75,2.45,17.95])cube([.3,.3,.3]);}}
module rf(){for(j=[0:1])color(j==0?[.95,.55,.12]:[.15,.48,.9])for(i=[0:len(rf_paths[j])-2])hull(){translate(rf_paths[j][i])sphere(r=.565,$fn=10);translate(rf_paths[j][i+1])sphere(r=.565,$fn=10);}}
module review(){
 color([.72,.76,.80,.18])import("../swim-r16-contact-retention/body.stl");
 color([.26,.62,.68,.18])translate([0,0,1.8])import("../swim-r12-pack-retention/carrier.stl");
 color([.63,.3,.66,.22])translate([0,0,10.6])import("../swim-r11-thermal-fit/retainer.stl");
 color([.35,.42,.48,.22])for(b=part_boxes)translate(b[0])cube(b[1]);
 color([.15,.45,.25,.25])translate([-20,-16,10.4])cube([40,32,.84088]);
 color([.9,.12,.12])import("../../assembly/internal-charge-r02/red-wire.stl");
 color([.12,.12,.14])import("../../assembly/internal-charge-r02/black-wire.stl");
 rf();
}
if(part=="guide_collision")guide_collision();
else if(part=="guide_wall_control")guide_wall_control();
else review();
'''
    scene=OUT/'routing.scad';scene.write_text(scad)
    hashes[str(scene.relative_to(ROOT))]=sha(scene)
    for m in meshes:hashes[str((OUT/m['file']).relative_to(ROOT))]=m['sha256']
    runtime=ROOT/'.runtime/cable-integration-r17/cad';runtime.mkdir(parents=True,exist_ok=True)
    controls=[]
    for name in ['guide_collision','guide_wall_control']:
        with tempfile.TemporaryDirectory(dir=runtime,prefix=name) as temp:
            result_path=Path(temp)/'intersection.stl'
            proc=subprocess.run([exe,'-o',str(result_path),'--export-format','binstl','-D',f'part="{name}"',str(scene)],capture_output=True,text=True)
            (runtime/(name+'.log')).write_text(proc.stderr)
            if re.search('WARNING|ERROR',proc.stderr):raise ValueError(proc.stderr)
            empty='Current top level object is empty.' in proc.stderr
            if name=='guide_collision':
                if not(empty and proc.returncode==1 and not result_path.exists()):raise ValueError('RF witness intersects existing lid: '+proc.stderr)
                volume=0
            else:
                if proc.returncode or empty:raise ValueError('Deliberate guide interference was missed: '+proc.stderr)
                volume=inspect(result_path,allow_separate=True)['signed_volume_mm3']
                if abs(volume-.027)>1e-6:raise ValueError('Guide-wall control did not return the complete known cube')
            controls.append(dict(name=name,empty=empty,volume_mm3=volume,returncode=proc.returncode,diagnostic=proc.stderr))
            print('CAD',name,'empty' if empty else volume,flush=True)
    preview=OUT/'review.png'
    proc=subprocess.run([exe,'-o',str(preview),'--imgsize','1600,1100','--projection','o','--viewall','--autocenter','--camera','0,0,0,55,0,40,150','--colorscheme','Tomorrow',str(scene)],capture_output=True,text=True)
    if proc.returncode or re.search('WARNING|ERROR',proc.stderr):raise ValueError(proc.stderr)
    if any(sha(ROOT/n)!=v for n,v in hashes.items()):raise ValueError('CAD input changed during export')
    report=dict(inputs=hashes,meshes=meshes,controls=controls,preview_sha256=sha(preview),physical_qualification=False,
                scope='Nominal RF witness meshes through unchanged actual lid bores. Continuous position/travel allowances are checked analytically. No force, flex or physical assembly acceptance.')
    (OUT/'cad-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Exported four-cable review',flush=True)


if __name__=='__main__':main()
