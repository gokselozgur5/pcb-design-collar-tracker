// r16 internal contact retention. Nominal millimetres; prototype, not an IP rating.
include <parameters.scad>
$fn=72;
part="review";

// Use the already inspected r13 assembly frame. Its STL has Z=0 at the body base.
module old_body(){import("../swim-r13-charge-dock/body.stl");}
module yz_prism(x,t){multmatrix([[0,0,1,x],[1,0,0,0],[0,1,0,0],[0,0,0,1]])linear_extrude(t)children();}
module base_plan(y,w,zs){translate([y,(zs[0]+zs[1])/2])offset(r=.3)square([w-.6,zs[1]-zs[0]-.6],center=true);}
module tail_plan(i,r){hull(){translate([contact_ys[i],tail_root_z])circle(r=r);translate(tail_yz[i])circle(r=r);}}
module terminal_plan(i){union(){base_plan(contact_ys[i],terminal_w,terminal_z);tail_plan(i,terminal_r);}}
module pockets(){for(i=[0:1])yz_prism(20.9,bearing_x-20.9){
    base_plan(contact_ys[i],pocket_w,pocket_z);
    intersection(){tail_plan(i,pocket_r);translate([-20,0])square([40,pocket_top]);}
}}
module body(){difference(){old_body();pockets();}}
module terminal(i){difference(){
    union(){
        yz_prism(bearing_x-terminal_t,terminal_t)intersection(){terminal_plan(i);translate([-20,0])square([40,transition_z]);}
        yz_prism(bearing_x-tail_t,tail_t)intersection(){terminal_plan(i);translate([-20,transition_z-.01])square([40,20]);}
    }
    yz_prism(bearing_x-terminal_t-.01,terminal_t+.02){
        translate([contact_ys[i],contact_z])circle(d=terminal_hole);
        translate(tail_yz[i])circle(d=wire_hole);
    }
}}
module contact_r16(){difference(){union(){
    cylinder(d=8.5,h=.8);
    translate([0,0,-stem_l])cylinder(d=7.28,h=stem_l);
    translate([0,0,-stem_l-thread_l])cylinder(d=3,h=thread_l);
  }
  translate([0,0,-3.85-2.8/2])difference(){cylinder(d=8.28,h=2.8);translate([0,0,-.01])cylinder(d=4.64,h=2.82);}
}}
module contacts(){for(y=contact_ys)translate([28.7,y,contact_z])rotate([0,90,0])contact_r16();}
module washers(){for(y=contact_ys)yz_prism(bearing_x-terminal_t-.5,.5)difference(){translate([y,contact_z])circle(d=6);translate([y,contact_z])circle(d=3.2);}}
module nuts(){for(y=contact_ys)yz_prism(bearing_x-terminal_t-.5-1.8,1.8)difference(){translate([y,contact_z])circle(d=5.5/cos(30),$fn=6);translate([y,contact_z])circle(d=3);}}
module metal(){contacts();for(i=[0:1])terminal(i);washers();nuts();}
module existing_carrier(){translate([0,0,1.8])import("../swim-r12-pack-retention/carrier.stl");}
module existing_retainer(){translate([0,0,10.6])import("../swim-r11-thermal-fit/retainer.stl");}
module retention_collision(){intersection(){union(){for(i=[0:1])terminal(i);washers();nuts();}union(){existing_carrier();existing_retainer();}}}
// Exact bearing planes are deliberate contact. The exporter verifies every
// vertex of a zero-volume intersection instead of discarding an overlap band.
module terminal_body_collision(){intersection(){body();for(i=[0:1])terminal(i);}}
module old_body_control(){intersection(){old_body();for(i=[0:1])terminal(i);}}
module review(){
    color([.72,.76,.80,.38])body();
    color([.82,.64,.20])contacts();
    color([.75,.75,.78]){washers();nuts();}
    color([.90,.24,.18])terminal(0);
    color([.16,.18,.23])terminal(1);
    color([.25,.62,.70,.35])existing_carrier();
    color([.65,.28,.65,.4])existing_retainer();
}
if(part=="body")body();
else if(part=="contact")contact_r16();
else if(part=="positive_terminal")translate([-bearing_x+terminal_t,6,-terminal_z[0]])terminal(0);
else if(part=="negative_terminal")translate([-bearing_x+terminal_t,-6,-terminal_z[0]])terminal(1);
else if(part=="retention_collision")retention_collision();
else if(part=="body_collision")terminal_body_collision();
else if(part=="old_body_control")old_body_control();
else if(part=="section")intersection(){review();translate([17,-17,0])cube([17,34,21]);}
else review();
