// Swim enclosure r01. Millimeters. Prototype geometry, not an IP rating.
// Generate parameters.scad with scripts/build_swim_enclosure.py.
include <parameters.scad>
$fn=96;
part="assembly"; // body, lid, carrier, contact, gasket, contact_seal, dock, assembly, exploded, section
show_reservations=true;
collar_width=20;
eps=0.01;

module rr(w,d,r) {
    offset(r=r) square([w-2*r,d-2*r],center=true);
}
module ring2(w,d,r,width) {
    difference() {rr(w+width,d+width,r+width/2);rr(w-width,d-width,r-width/2);}
}
module groove() {
    // Analytic rounded-bottom section sampled in 20 Z slices for the STL.
    translate([0,0,body_h-gland_depth+gland_bottom_r])
        linear_extrude(gland_depth-gland_bottom_r+eps)
            ring2(gland_w,gland_d,gland_r,gland_width);
    for(i=[0:19]) let(z=gland_bottom_r*i/20, dz=gland_bottom_r/20,
      width=gland_width-2*gland_bottom_r+2*sqrt(gland_bottom_r*gland_bottom_r-pow(gland_bottom_r-z,2)))
        translate([0,0,body_h-gland_depth+z])
            linear_extrude(dz+eps/10)ring2(gland_w,gland_d,gland_r,width);
}
module body() {
    difference() {
        union() {
            linear_extrude(body_h)rr(body_w,body_d,body_r);
            // Asymmetric docking key stays entirely outside the dry cavity.
            translate([body_w/2-eps,-1.5,10.8])cube([1.3+eps,3,2.4]);
        }
        translate([0,0,floor_t])linear_extrude(body_h+1)rr(cavity_w,cavity_d,cavity_r);
        groove();
        for(p=screw_centers) {
            translate([p[0],p[1],-eps])cylinder(d=screw_hole,h=body_h+2*eps);
            translate([p[0],p[1],-eps])rotate([0,0,30])cylinder(d=nut_af/cos(30),h=nut_depth+eps,$fn=6);
        }
        for(y=contact_y)translate([body_w/2-contact_length-eps,y,contact_z])rotate([0,90,0])cylinder(d=contact_bore,h=contact_length+2*eps);
        // External blind slots, machined from the bottom. They never enter the
        // electronics cavity or the lid gland. Potting and the boot retain plugs.
        for(y=magnet_y)translate([body_w/2-magnet_wall-magnet_t/2,y,-eps])
            linear_extrude(magnet_z+magnet_d/2+.05+eps)rr(magnet_t+.1,magnet_d+.1,.5);
    }
}
module lid() {
    difference() {
        linear_extrude(lid_t)rr(body_w,body_d,body_r);
        for(p=screw_centers) {
            translate([p[0],p[1],-eps])cylinder(d=screw_hole,h=lid_t+2*eps);
            translate([p[0],p[1],lid_t-head_depth])cylinder(d=head_d,h=head_depth+eps);
        }
    }
}
module carrier() {
    // Lift-out frame supports the 0.4 mm board-edge strip.
    // Board edge clearance is 0.4 mm; no board drill holes are added.
    difference() {
        linear_extrude(1.5)rr(41.6,33.6,1.8);
        translate([0,0,-eps])linear_extrude(1.5+2*eps)rr(39.2,31.2,.6);
        // Preserve the card-entry lane; insert/remove SIM with the tray lifted out.
        translate([3.8,14.8,-eps])cube([10.6,4,2]);
    }
    for(s=[-1,1],y=[-12,12])translate([s*20.4-.3,y-1,0])cube([.6,2,2.7]);
    // Four legs bear on the floor, outside the battery reservation.
    for(s=[-1,1],y=[-12,12])translate([s*19.8-.5,y-1,-(pcb_z-1.5-floor_t)])cube([1,2,pcb_z-1.5-floor_t]);
}
module contact() {
    difference() {
        union() {
            cylinder(d=contact_head_d,h=contact_head_t);
            translate([0,0,-contact_length])cylinder(d=contact_shaft,h=contact_length);
            // Smooth major-diameter envelope; drawing specifies M4 thread.
            translate([0,0,-contact_length-contact_thread_length])cylinder(d=contact_thread_d,h=contact_thread_length);
        }
        translate([0,0,-contact_groove_center-contact_groove_w/2])difference() {
            cylinder(d=contact_shaft+1,h=contact_groove_w);
            translate([0,0,-eps])cylinder(d=contact_root,h=contact_groove_w+2*eps);
        }
    }
}
module contact_seal() {
    R=(contact_bore+contact_root)/4;
    radial=(contact_bore-contact_root)/4;
    V=PI*pow(contact_oring_cs,2)/4*PI*(contact_oring_id+contact_oring_cs);
    axial=V/(2*PI*R*PI*radial);
    rotate_extrude()translate([R,0])scale([radial,axial])circle(1);
}
module gasket() {
    // Display the compressed closed loop; buy the specified round O-ring.
    stretch=gasket_perimeter/(PI*(gasket_id+gasket_cs));
    width=pow(gasket_cs,2)/(stretch*gland_depth);
    for(i=[0:39])let(z=-gland_depth/2+(i+.5)*gland_depth/40,
      w=width*sqrt(max(0,1-pow(2*z/gland_depth,2))))
        translate([0,0,z])linear_extrude(gland_depth/40+eps/10)ring2(gland_w,gland_d,gland_r,w);
}
module dock() {
    // Alignment shell only. Spring contacts, USB power wiring and fuse are not selected.
    difference() {
        translate([0,-18,-1])cube([6,36,16]);
        for(y=contact_y)translate([-eps,y,contact_z])rotate([0,90,0])cylinder(d=contact_head_d+.4,h=2);
        translate([-eps,-1.7,10.6])cube([1.7,3.4,2.8]);
        // Back-entry bores allow magnet insertion; the front wall stays closed.
        for(y=magnet_y)translate([1.5,y,magnet_z])rotate([0,90,0])cylinder(d=magnet_pocket_d,h=4.5+eps);
        for(y=contact_y)translate([-eps,y,contact_z])rotate([0,90,0])cylinder(d=2.0,h=6+2*eps);
    }
}
module boot() {
    // Optional flexible retention boot; all collar loads remain outside the seal.
    // Full-height walls and a 0.7 mm overlapping lip retain the rigid shell.
    assert(collar_width>=12 && collar_width<=25,"Review a new boot outside the 12-25 mm collar range");
    difference() {
        translate([0,0,-4])linear_extrude(body_h+lid_t+4.8)rr(body_w+3,body_d+3,body_r+1.5);
        translate([0,0,0])linear_extrude(body_h+lid_t+eps)rr(body_w+.4,body_d+.4,body_r+.2);
        translate([0,0,body_h+lid_t])linear_extrude(2)rr(body_w-1,body_d-1,body_r-.5);
        translate([-body_w,-(collar_width+.6)/2,-3.2])cube([2*body_w,collar_width+.6,2.5]);
        translate([body_w/2-1,-18,.8])cube([4,36,12.6]);
    }
}
module magnet_plug() {
    linear_extrude(magnet_z-magnet_d/2-.05)rr(magnet_t+.05,magnet_d+.05,.45);
}
module contents() {
    color([.1,.52,.31])translate([-pcb_size[0]/2,-pcb_size[1]/2,pcb_z])cube(pcb_size);
    color([.85,.65,.17,.8])translate([-battery_size[0]/2,-battery_size[1]/2,battery_z])cube(battery_size);
    if(show_reservations) {
        color([.5,.55,.6,.15])translate([-20,-16,pcb_z+pcb_size[2]])cube([40,32,top_budget]);
        color([.5,.55,.6,.15])translate([-20,-16,pcb_z-bottom_budget])cube([40,32,bottom_budget]);
        for(i=[0:len(antenna_centers)-1])color([.95,.35,.1,.8])translate(antenna_centers[i])cube(antenna_sizes[i],center=true);
    }
}
module hardware() {
    for(y=contact_y)translate([body_w/2,y,contact_z])rotate([0,90,0]) {
        color([.8,.65,.2])contact();
        color([.1,.1,.1])translate([0,0,-contact_groove_center])contact_seal();
    }
    for(y=magnet_y)color([.6,.6,.65])translate([body_w/2-magnet_wall-magnet_t,y,magnet_z])rotate([0,90,0])cylinder(d=magnet_d,h=magnet_t);
    for(y=magnet_y)color([.3,.35,.4])translate([body_w/2-magnet_wall-magnet_t/2,y,0])magnet_plug();
}
module assembly(explode=0) {
    color([.15,.22,.28,.78])body();
    color([.55,.6,.65])translate([0,0,pcb_z-1.5+explode/3])carrier();
    translate([0,0,explode/3])contents();
    hardware();
    color([.08,.08,.08])translate([0,0,body_h-gland_depth/2+explode/2])gasket();
    color([.18,.25,.31,.85])translate([0,0,body_h+explode])lid();
}
if(part=="body")body();
else if(part=="lid")lid();
else if(part=="carrier")translate([0,0,pcb_z-1.5-floor_t])carrier();
else if(part=="contact")contact();
else if(part=="contact_seal")contact_seal();
else if(part=="gasket")translate([0,0,gland_depth/2])gasket();
else if(part=="dock")dock();
else if(part=="boot")translate([0,0,4])boot();
else if(part=="magnet_plug")magnet_plug();
else if(part=="mounted"){assembly();color([.25,.3,.36,.8])boot();}
else if(part=="exploded")assembly(18);
else if(part=="section")difference(){assembly();translate([-40,-40,-1])cube([80,40,70]);}
else assembly();
