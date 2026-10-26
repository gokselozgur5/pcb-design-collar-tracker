// External adjustable collar attachment. Millimetres. Prototype CAD.
// The pressure boundary, PCB and internal assembly are preserved.
$fn=64;
part="mounted";
collar_width=25;
collar_thickness=3;
rope_diameter=8;
strap_length=160;
strap_w=10;
strap_t=1.4;
anchor_x=17.5;
body_w=57.4;
body_d=49.4;
body_h=21;
floor_z=-5.5;
pad_bottom=-7.8;
round_collar=false;
explode=0;

module rr(w,d,r){offset(r=r)square([w-2*r,d-2*r],center=true);}
module yz_extrude(x,w){multmatrix([[0,0,1,x],[1,0,0,0],[0,1,0,0],[0,0,0,1]])linear_extrude(w)children();}

module boot(){
 difference(){
  translate([0,0,floor_z])linear_extrude(27.3)rr(body_w+3.4,body_d+3.4,5.7);
  translate([0,0,0])linear_extrude(body_h+.2)rr(body_w+.5,body_d+.5,4.25);
  translate([0,0,body_h])linear_extrude(2)rr(body_w-1.2,body_d-1.2,3.4);
  // Charging targets and the asymmetric dock key remain accessible.
  translate([body_w/2-1.5,-18.5,.6])cube([8,37,14.2]);
  for(x=[-25.1,25.1],y=[-21.1,21.1])translate([x,y,-2])cylinder(d=3.2,h=2.1);
  for(x=[-anchor_x,anchor_x]){
   // Two downward entries joined by a tunnel above a 3mm load bar.
   translate([x-5.5,-7.1,-2.5])cube([11,14.2,2]);
   for(y=[-5.5,5.5])translate([x-5.5,y-1.6,-5.6])cube([11,3.2,5.1]);
  }
  // Blind pad-registration sockets never reach the rigid shell.
  for(x=[-6,6])translate([x,0,-5.6])cylinder(d=3.1,h=1.5);
 }
}

module pad_keys(){for(x=[-6,6])translate([x,0,-5.6])cylinder(d=2.8,h=1.4);}
module flat_pad(){
 union(){
  translate([0,0,-7.5])linear_extrude(2)rr(22,44,3);
  for(y=[-18:4:18])translate([-9,y,-7.5])rotate([0,90,0])cylinder(r=.3,h=18,$fn=20);
  pad_keys();
 }
}
module round_pad(){
 union(){
  difference(){
   translate([0,0,-12])linear_extrude(6.5)rr(22,22,3);
   yz_extrude(-12,24)polygon([[-12,-20],[12,-20],[12,-18.8],[0,-6.8],[-12,-18.8]]);
  }
  pad_keys();
 }
}

module strap_blank(){
 assert(strap_length>=90);
 difference(){
  union(){
   translate([0,strap_length/2,0])linear_extrude(strap_t)rr(strap_w,strap_length,4);
   translate([0,21.5,0])linear_extrude(strap_t)rr(14.6,9,2);
   // Two positive-lock buttons; the remaining tail passes through the keeper.
   for(y=[7,12]){
    translate([0,y,strap_t-.02])cylinder(d=2.2,h=2.05,$fn=32);
    translate([0,y,strap_t+1.5])cylinder(d1=2.2,d2=4,h=.6,$fn=32);
    translate([0,y,strap_t+2.1])cylinder(d1=4,d2=3.2,h=.5,$fn=32);
   }
   for(x=[-6.3,6.3])translate([x-1,19,0])cube([2,5,4.4]);
   translate([-7.3,19,3.2])cube([14.6,5,1.2]);
  }
  for(y=[32:5:strap_length-8])translate([0,y,-.1])cylinder(d=2.5,h=strap_t+.2,$fn=32);
 }
}

function round_path(r,zc)=[for(a=[0:10:350])[r*sin(a),zc+r*cos(a)]];
function flat_path(w,t)=[[-5.5,-1.5],[5.5,-1.5],[5.5,-6.5],
 [max(w/2+.9,6),pad_bottom+.8],[w/2+1.2,pad_bottom-t-.2],
 [w/2-.4,pad_bottom-t-1],[-w/2+.4,pad_bottom-t-1],
 [-w/2-1.2,pad_bottom-t-.2],[-max(w/2+.9,6),pad_bottom+.8],[-5.5,-6.5]];
function rope_path(d)=let(r=d/2+.9,zc=-6.8-d/2*sqrt(2))
 concat([[-5.5,-1.5],[5.5,-1.5],[5.5,-6.5]],
        [for(a=[35:10:325])[r*sin(a),zc+r*cos(a)]],[[-5.5,-6.5]]);
module installed_strap(x){
 // Installed centreline envelope; button/keeper/tail detail is in strap_blank.
 path=round_collar?rope_path(rope_diameter):flat_path(collar_width,collar_thickness);
 color([.08,.43,.41])yz_extrude(x-strap_w/2,strap_w)
 difference(){offset(r=strap_t/2)polygon(path);offset(delta=-strap_t/2)polygon(path);}
}
module collar(){
 if(round_collar)color([.50,.24,.07])translate([-58,0,-6.8-rope_diameter/2*sqrt(2)])rotate([0,90,0])cylinder(d=rope_diameter,h=116);
 else color([.53,.25,.09])translate([-58,-collar_width/2,pad_bottom-collar_thickness])cube([116,collar_width,collar_thickness]);
}

module housing(){color([.84,.87,.90])import("../swim-r16-contact-retention/body.stl");}
module lid(){color([.90,.92,.94])translate([0,0,18.5])import("../swim-r11-thermal-fit/lid.stl");}
module carrier(){color([.25,.59,.63])translate([0,0,1.8])import("../swim-r12-pack-retention/carrier.stl");}
module retainer(){color([.27,.35,.41])translate([0,0,10.6])import("../swim-r18-charge-clearance/retainer.stl");}
module battery(){
 color([.25,.30,.34])translate([-16,-15.25,1.8])cube([32,30.5,5.3]);
 color([.92,.55,.16])translate([-13,-2.05,7.25])cube([26,4.1,.5]);
 color([.65,.5,.12])translate([-14,-3.05,7.75])cube([28,6.1,.1]);
}
module pcb(){
 color([.05,.35,.20])translate([-20,-16,10.4])cube([40,32,.84088]);
 include <components.scad>
}
module contacts(){
 for(y=[-6,6])color([.82,.65,.23])translate([28.7,y,5.5])rotate([0,90,0])import("../swim-r16-contact-retention/contact.stl");
}
module ring2(w,d,r,width){difference(){rr(w+width,d+width,r+width/2);rr(w-width,d-width,r-width/2);}}
module gasket(){
 stretch=169.6991118430775/(PI*(50.52+1.78));
 width=1.78*1.78/(stretch*1.34);
 color([.08,.10,.12])translate([0,0,18.5-1.34/2])
 for(i=[0:39])let(z=-1.34/2+(i+.5)*1.34/40,w=width*sqrt(max(0,1-pow(2*z/1.34,2))))
 translate([0,0,z])linear_extrude(1.34/40+.001)ring2(49,41,6,w);
}
module antennas(){
 color([.78,.48,.12])translate([-30.7/2,-7-15.7/2,18.1])cube([30.7,15.7,.4]);
 color([.79,.62,.20])translate([-40.7/2,10.3-10.7/2,18.1])cube([40.7,10.7,.4]);
}
module charge_wires(){
 color([.8,.08,.06])import("../swim-r18-charge-clearance/red-wire.stl");
 color([.06,.07,.08])import("../swim-r18-charge-clearance/black-wire.stl");
}
module terminals(){
 color([.73,.58,.18]){
 translate([21.6,-6,2.35])import("../swim-r16-contact-retention/positive_terminal.stl");
 translate([21.6,6,2.35])import("../swim-r16-contact-retention/negative_terminal.stl");
 }
}
module rf_leads(){include <rf-paths.scad>}
module fasteners(){
 for(x=[-25.1,25.1],y=[-21.1,21.1])color([.44,.48,.52]){
  translate([x,y,-.5])cylinder(d=2,h=20);
  translate([x,y,19.5])difference(){cylinder(d=3.8,h=1.3);translate([-.35,-2,.8])cube([.7,4,1]);}
 }
}
module assembly(){housing();lid();contacts();fasteners();}
module exploded(){
 color([.10,.18,.22])translate([0,0,-18])boot();
 color([.19,.49,.45])translate([0,0,-21])flat_pad();
 housing();
 translate([0,0,8]){carrier();battery();}
 translate([0,0,22])pcb();
 translate([0,0,30])retainer();
 translate([0,0,37])antennas();
 translate([0,0,43])gasket();
 translate([0,0,46])lid();
 contacts();terminals();
}
module mounted(){
 collar();for(x=[-anchor_x,anchor_x])installed_strap(x);
 color([.10,.18,.22])boot();
 color([.19,.49,.45])if(round_collar)round_pad();else flat_pad();
 assembly();
}
if(part=="boot")translate([0,0,5.5])boot();
else if(part=="flat_pad")translate([0,0,7.8])flat_pad();
else if(part=="round_pad")translate([0,0,12])round_pad();
else if(part=="strap")strap_blank();
else if(part=="pcb")pcb();
else if(part=="pcb_substrate")translate([-20,-16,10.4])cube([40,32,.84088]);
else if(part=="pcb_components"){include <components.scad>}
else if(part=="body")housing();
else if(part=="lid")lid();
else if(part=="carrier")carrier();
else if(part=="retainer")retainer();
else if(part=="battery")battery();
else if(part=="contacts")contacts();
else if(part=="gasket")gasket();
else if(part=="antennas")antennas();
else if(part=="rf")rf_leads();
else if(part=="terminals")terminals();
else if(part=="charge_wires")charge_wires();
else if(part=="fasteners")fasteners();
else if(part=="staking")import("../../assembly/internal-charge-r03/staking-envelopes.stl");
else if(part=="collar")collar();
else if(part=="installed_straps")for(x=[-anchor_x,anchor_x])installed_strap(x);
else if(part=="exploded")exploded();
else if(part=="assembly")assembly();
else if(part=="mount_section")intersection(){mounted();translate([-70,-60,-45])cube([88,120,100]);}
else if(part=="boot_shell_collision")intersection(){boot();union(){housing();lid();}}
else if(part=="strap_boot_collision")intersection(){boot();union()for(x=[-anchor_x,anchor_x])installed_strap(x);}
else if(part=="strap_collar_collision")intersection(){collar();union()for(x=[-anchor_x,anchor_x])installed_strap(x);}
else if(part=="pad_strap_collision")intersection(){if(round_collar)round_pad();else flat_pad();union()for(x=[-anchor_x,anchor_x])installed_strap(x);}
else if(part=="pad_collar_collision")intersection(){collar();if(round_collar)round_pad();else flat_pad();}
else mounted();
