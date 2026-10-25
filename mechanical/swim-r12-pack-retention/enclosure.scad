// Swim enclosure r12 pack-retention prototype. Millimeters. Prototype geometry, not an IP rating.
// Generate parameters.scad with scripts/build_swim_r08_geometry.py.
include <../swim-r11-thermal-fit/parameters.scad>
include <../swim-r11-thermal-fit/populated.scad>
include <../swim-r11-thermal-fit/cables.scad>
include <pack.scad>
include <../swim-r11-thermal-fit/retention.scad>
include <pack-retention.scad>
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
module body_shell() {
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
module body_base(){union(){body_shell();body_locators();}}
module lid_shell() {
    difference() {
        linear_extrude(lid_t)rr(body_w,body_d,body_r);
        for(p=screw_centers) {
            translate([p[0],p[1],-eps])cylinder(d=screw_hole,h=lid_t+2*eps);
            translate([p[0],p[1],lid_t-head_depth])cylinder(d=head_d,h=head_depth+eps);
        }
    }
}
module align_axis(v) {
    axis=[-v[1],v[0],0];
    if(norm(axis)<0.00001)children();
    else rotate(a=acos(v[2]/norm(v)),v=axis)children();
}
module cable_guide_solids(bore_override=0) {
    // Four lid-mounted prototype clips, wholly inside the dry cavity.
    // The slot and material strain need physical qualification.
    difference() {
        union()for(c=cable_clips)translate(c[2])cube(c[3]-c[2]+[0,0,.1]);
        for(i=[0:len(cable_clips)-1])let(c=cable_clips[i]) {
            if(i==3)intersection() {
                cable_tube(cable_paths[1],(bore_override>0?bore_override:c[4])/2,true);
                translate(c[2]-[.1,.1,.1])cube(c[3]-c[2]+[.2,.2,.2]);
            }
            else translate(c[0])align_axis(c[1])cylinder(d=bore_override>0?bore_override:c[4],h=12,center=true,$fn=48);
            translate([c[0][0]-c[5]/2,c[2][1]-.1,c[2][2]-.1])
                cube([c[5],c[3][1]-c[2][1]+.2,c[0][2]-c[2][2]+.1]);
        }
    }
}
module lid() {
    union(){lid_shell();translate([0,0,-body_h]){cable_guide_solids();retention_posts();}}
}
module cable_tube(path,r=cable_radius,local_only=false) {
    for(i=[0:len(path)-2])
        if(!local_only || min(path[i][1],path[i+1][1])<6 && max(path[i][1],path[i+1][1])>-.4)
            hull(){translate(path[i])sphere(r=r/pow(cos(15),2),$fn=12);translate(path[i+1])sphere(r=r/pow(cos(15),2),$fn=12);}
}
module rf_cables() {
    for(i=[0:len(cable_paths)-1])color(i==0?[.95,.45,.12]:[.15,.5,.95])cable_tube(cable_paths[i]);
}
module rf_antennas() {
    for(i=[0:len(antenna_centers)-1])color(i==0?[.95,.65,.15,.65]:[.25,.65,.9,.65])
        translate(antenna_centers[i])cube(antenna_sizes[i],center=true);
}
module cable_guide_interference(bore_override=0) {
    intersection(){cable_guide_solids(bore_override);union()for(p=cable_paths)cable_tube(p,cable_radius+.165,true);}
}
module carrier_base() {
    // Lift-out frame supports the 0.4 mm board-edge strip.
    // The 0.4 mm lower support strip is separate from the guide aperture; no PCB holes are added.
    difference() {
        linear_extrude(1.5)rr(41.6,33.6,1.8);
        translate([0,0,-eps])linear_extrude(1.5+2*eps)rr(39.2,31.2,.6);
        // Preserve the card-entry lane; insert/remove SIM with the tray lifted out.
        for(b=carrier_reliefs)translate([b[0],b[1],-eps])cube([b[2]-b[0],b[3]-b[1],b[4]+eps]);
    }
    guide_rail_solids(-(pcb_z-1.5));
    // Four legs bear on the floor, outside the battery reservation.
    for(p=carrier_leg_centers)translate([p[0]-.5,p[1]-1,-(pcb_z-1.5-floor_t)])cube([1,2,pcb_z-1.5-floor_t+eps]);
}
module contact() {
    difference() {
        union() {
            cylinder(d=contact_head_d,h=contact_head_t);
            translate([0,0,-contact_length])cylinder(d=contact_shaft,h=contact_length);
            // Smooth major-diameter envelope; drawing specifies M3 x 0.5 thread.
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
    // Required flexible retention boot; all collar loads remain outside the seal.
    // Full-height walls and a 0.7 mm overlapping lip retain the rigid shell.
    assert(collar_width>=12 && collar_width<=25,"Review a new boot outside the 12-25 mm collar range");
    difference() {
        translate([0,0,-4])linear_extrude(body_h+lid_t+4.8)rr(body_w+3,body_d+3,body_r+1.5);
        translate([0,0,0])linear_extrude(body_h+lid_t+eps)rr(body_w+.4,body_d+.4,body_r+.2);
        translate([0,0,body_h+lid_t])linear_extrude(2)rr(body_w-1,body_d-1,body_r-.5);
        translate([-body_w,-(collar_width+.6)/2,-3.2])cube([2*body_w,collar_width+.6,2.5]);
        translate([body_w/2-1,-18,.8])cube([4,36,12.6]);
        // M2 x 20 tips protrude below the shell; local blind pockets keep them
        // clear of the boot. Pockets remain outside the collar strap lane.
        for(p=screw_centers)translate([p[0],p[1],-boot_tip_depth])cylinder(d=boot_tip_d,h=boot_tip_depth+eps);
    }
}
module magnet_plug() {
    linear_extrude(magnet_z-magnet_d/2-.05)rr(magnet_t+.05,magnet_d+.05,.45);
}
module fit_envelopes(clearance=0) {
    for(p=fit_boxes)translate(p[1]-[clearance,clearance,clearance])
        cube(p[2]+[2*clearance,2*clearance,2*clearance]);
}
module fit_interference() {
    // A second check using the actual CAD boolean solids, not only 2D bounds.
    intersection() {
        fit_envelopes(.2);
        union(){body();translate([0,0,body_h])lid();translate([0,0,pcb_z-1.5])carrier();}
    }
}
module contents() {
    color([.1,.52,.31])translate([-pcb_size[0]/2,-pcb_size[1]/2,pcb_z])cube(pcb_size);
    pack_request_stack();
    if(show_reservations) {
        // Sourced maximum-height envelopes at actual r05l placements.
        // Orange boxes are unapproved harness requirements; grey boxes are fit bounds.
        for(p=fit_boxes) color(p[3]=="harness_reservation" ? [.95,.45,.12,.8] : [.5,.55,.6,.85])
            translate(p[1])cube(p[2]);

    }
}
module contact_retention() {
    // Full-rotation envelope includes the selected thin nut and a <=1 mm
    // washer/lug stack requirement. Detailed termination is not yet approved.
    for(y=contact_y) color([.6,.65,.7])
        translate([body_w/2-contact_length-retention_stack,y,contact_z])rotate([0,90,0])
            difference(){cylinder(d=retention_d,h=retention_stack);translate([0,0,-eps])cylinder(d=contact_thread_d,h=retention_stack+2*eps);}
}
module fastener_envelopes() {
    bearing=body_h+lid_t-head_depth;
    for(p=screw_centers)color([.65,.68,.7]) {
        translate([p[0],p[1],bearing-fastener_length])cylinder(d=2,h=fastener_length);
        translate([p[0],p[1],bearing])cylinder(d=3.8,h=1.3);
        translate([p[0],p[1],.1])rotate([0,0,30])cylinder(d=4/cos(30),h=1.6,$fn=6);
    }
}
module hardware() {
    contact_retention();
    fastener_envelopes();
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
    color([.65,.24,.65])translate([0,0,explode/2])retainer();
    hardware();
    translate([0,0,explode])rf_antennas();
    if(explode==0)rf_cables();
    color([.08,.08,.08])translate([0,0,body_h-gland_depth/2+explode/2])gasket();
    color([.18,.25,.31,.85])translate([0,0,body_h+explode])lid();
}
if(part=="pack_components")pack_component_interference();
else if(part=="pack_components_control")pack_component_interference(false);
else if(part=="pack_hardware")pack_hardware_interference();
else if(part=="pack_ntc")pack_ntc_interference();
else if(part=="pack_ntc_control")pack_ntc_interference(false);
else if(part=="pack_cradle")pack_cradle_interference();
else if(part=="pack_cradle_control")pack_cradle_interference([31,29.5]);
else if(part=="pack_review")pack_review();
else if(part=="pack_exploded")pack_exploded();
else if(part=="pack_section")difference(){pack_review();translate([-40,-40,-1])cube([80,40,70]);}
else if(part=="body")body();
else if(part=="lid")lid();
else if(part=="retainer")translate([0,0,-key_z])retainer();
else if(part=="carrier")translate([0,0,pcb_z-1.5-floor_t])carrier();
else if(part=="contact")contact();
else if(part=="interference")fit_interference();
else if(part=="guide_interference")cable_guide_interference();
else if(part=="guide_control")cable_guide_interference(1.0);
else if(part=="routing"){contents();rf_cables();rf_antennas();color([.6,.6,.6,.5])cable_guide_solids();}
else if(part=="contact_seal")contact_seal();
else if(part=="gasket")translate([0,0,gland_depth/2])gasket();
else if(part=="dock")dock();
else if(part=="boot")translate([0,0,4])boot();
else if(part=="magnet_plug")magnet_plug();
else if(part=="mounted"){assembly();color([.25,.3,.36,.8])boot();}
else if(part=="exploded")assembly(18);
else if(part=="populated"){contents();color([.2,.4,.7,.8])translate([0,0,pcb_z-1.5])carrier();hardware();rf_cables();rf_antennas();color([.65,.24,.65,.8])retainer();}
else if(part=="section")difference(){assembly();translate([-40,-40,-1])cube([80,40,70]);}

else if(part=="retention_interference")retention_interference();
else if(part=="carrier_motion_interference")intersection(){moving_components(carrier_motion_boxes,.2);translate([0,0,pcb_z-1.5])carrier();}
else if(part=="key_interference")intersection(){retainer();translate([0,0,pcb_z-1.5])carrier();}
else if(part=="key_wrong_orientation")intersection(){rotate([0,0,180])retainer();translate([0,0,pcb_z-1.5])carrier();}
else assembly();
