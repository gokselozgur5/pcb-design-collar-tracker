#!/usr/bin/env python3
"""Create explicit stripped-wire meshes and an assembled CAD inspection scene."""
import json
import math
from pathlib import Path
import struct

import numpy as np
from shapely.geometry import Polygon

from check_internal_harness import ROOT, OUT, BASE
from internal_harness_geometry import evaluate
from inspect_enclosure_mesh import inspect


def mesh(control, wire, destination):
    curve=evaluate(control,601);arc=curve['arc_lower'];length=arc[-1]
    boundaries=[wire['terminal_strip_mm'],length-wire['pcb_strip_mm']]
    stations=sorted(set(arc.tolist()+boundaries))
    outside=wire['outside_diameter_nominal_mm']/2
    core=wire['conductor_diameter_nominal_mm']/2
    rings=[];previous=None
    count=24
    for s in stations:
        center=np.array([np.interp(s,arc,curve['xyz'][:,a]) for a in range(3)])
        tangent=np.array([np.interp(s,arc,curve['derivative'][:,a]) for a in range(3)])
        tangent/=np.linalg.norm(tangent)
        normal=np.cross(tangent,[0,0,1]) if previous is None else previous-tangent*np.dot(previous,tangent)
        normal/=np.linalg.norm(normal);previous=normal
        binormal=np.cross(tangent,normal)
        if s==boundaries[0]:radii=[core,outside]
        elif s==boundaries[1]:radii=[outside,core]
        else:radii=[core if s<boundaries[0] or s>boundaries[1] else outside]
        for radius in radii:
            rings.append([center+radius*(math.cos(2*math.pi*j/count)*normal+math.sin(2*math.pi*j/count)*binormal) for j in range(count)])
    rings=np.array(rings);triangles=[]
    for i in range(len(rings)-1):
        for j in range(count):
            k=(j+1)%count
            triangles.extend([[rings[i,j],rings[i,k],rings[i+1,k]],
                              [rings[i,j],rings[i+1,k],rings[i+1,j]]])
    for j in range(1,count-1):
        triangles.extend([[rings[0,0],rings[0,j+1],rings[0,j]],
                          [rings[-1,0],rings[-1,j],rings[-1,j+1]]])
    triangles=np.array(triangles)
    volume=np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6
    if volume<0:triangles=triangles[:,[0,2,1]]
    data=bytearray(b'Internal charge wire; nominal shape; factory qualification pending'.ljust(80,b' '))
    data+=struct.pack('<I',len(triangles))
    for tri in triangles:
        n=np.cross(tri[1]-tri[0],tri[2]-tri[0]);n/=np.linalg.norm(n)
        data+=struct.pack('<12fH',*n,*tri.ravel(),0)
    destination.write_bytes(data)
    return inspect(destination)


def main():
    spec=json.loads((OUT/'harness.json').read_text())
    meshes=[mesh(w['controls_mm'],spec['wire'],OUT/(w['colour']+'-wire.stl')) for w in spec['wires']]
    fit=json.loads((BASE/'antenna-fit.json').read_text())['scenarios'][2]
    boxes=[]
    for part in fit['parts']:
        if part['ref']=='J3':continue
        a,b,c,d=part['envelope_xy_bounds_mm'];lo,hi=part['envelope_z_mm']
        boxes.append([part['ref'],[a,b,lo],[c-a,d-b,hi-lo]])
    geom=json.loads((ROOT/'experiments/power-r05l-charge-interlock/evidence/route-geometry.json').read_text())
    pads=[]
    for pin in ['1','2']:
        pad=next(p for p in geom['pads'] if p['ref']=='J3' and p['pin']==pin)
        shape=Polygon([(x-118,114-y) for x,y in pad['poly'][0]]).buffer(-spec['joints']['pcb_pad_edge_margin_mm'])
        pads.append(list(shape.exterior.coords)[:-1])
    from thermal_cable_geometry import spline
    motion=json.loads((BASE/'retention-checks.json').read_text())
    rf=[spline(c['control_points_mm'],121)[0].tolist() for c in motion['cable_motion']['cases'][13]['cables']]
    scad='''// Nominal assembled wire prototype; geometry is not a production release.
part="review";
$fn=48;
module body(){import("../../mechanical/swim-r16-contact-retention/body.stl");}
module carrier(){translate([0,0,1.8])import("../../mechanical/swim-r12-pack-retention/carrier.stl");}
module retainer(){translate([0,0,10.6])import("../../mechanical/swim-r11-thermal-fit/retainer.stl");}
module wires(){import("red-wire.stl");import("black-wire.stl");}
module terminals(){translate([21.6,-6,2.35])import("../../mechanical/swim-r16-contact-retention/positive_terminal.stl");translate([21.6,6,2.35])import("../../mechanical/swim-r16-contact-retention/negative_terminal.stl");}
module pcb_fillet(i){translate([0,0,11.24088])linear_extrude(fillet_height)polygon(pad_shapes[i]);}
module terminal_fillet(i){translate([fillet_x[0],tail_ys[i],13.3])rotate([0,90,0])cylinder(r=fillet_radius,h=fillet_x[1]-fillet_x[0]);}
module joints(){for(i=[0:1]){pcb_fillet(i);terminal_fillet(i);}}
module components(){for(b=part_boxes)translate(b[1])cube(b[2]);}
module obstacles(){body();carrier();retainer();components();}
module collision(){intersection(){union(){wires();joints();}obstacles();}}
module metal_collision(){intersection(){wires();terminals();}}
module lowered_wire_control(){intersection(){translate([0,0,-1])import("black-wire.stl");components();}}
module rf_leads(){for(j=[0:1])color(j==0?[.9,.62,.2,.45]:[.15,.45,.85,.45])for(i=[0:len(rf_paths[j])-2])hull(){translate(rf_paths[j][i])sphere(r=.565,$fn=12);translate(rf_paths[j][i+1])sphere(r=.565,$fn=12);}}
module review(){
 color([.72,.76,.80,.2])body();
 color([.26,.62,.68,.25])carrier();
 color([.63,.3,.66,.35])retainer();
 color([.35,.42,.48,.5])components();
 color([.85,.7,.2])terminals();
 color([.75,.75,.78])joints();
 color([.9,.15,.12])import("red-wire.stl");
 color([.1,.12,.15])import("black-wire.stl");
 color([.15,.45,.25,.4])translate([-20,-16,10.4])cube([40,32,.84088]);
 rf_leads();
}
if(part=="collision")collision();
else if(part=="metal_collision")metal_collision();
else if(part=="lowered_wire_control")lowered_wire_control();
else review();
'''
    parameters=dict(part_boxes=boxes,pad_shapes=pads,rf_paths=rf,tail_ys=[-3.3,6],
                    fillet_height=spec['joints']['pcb_fillet_height_max_mm'],
                    fillet_x=[spec['joints']['terminal_fillet_front_x_mm'],spec['joints']['terminal_fillet_back_x_mm']],
                    fillet_radius=spec['joints']['terminal_fillet_radius_mm'])
    (OUT/'harness.scad').write_text('\n'.join(k+' = '+json.dumps(v)+';' for k,v in parameters.items())+'\n'+scad)
    (OUT/'wire-meshes.json').write_text(json.dumps(dict(meshes=meshes,physical_qualification=False),indent=2)+'\n')
    print(json.dumps(dict(closed_meshes=len(meshes),files=[m['file'] for m in meshes]),indent=2))


if __name__=='__main__':main()
