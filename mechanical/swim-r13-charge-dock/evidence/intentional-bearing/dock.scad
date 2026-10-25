// r13 external charging dock. Prototype; no holding-force or ingress qualification.
include <parameters.scad>
$fn=64;
part="assembly";
eps=.01;

module xcyl(x,y,z,d,h) {translate([x,y,z])rotate([0,90,0])cylinder(d=d,h=h);}
module new_key(length=key_length) {
    translate([-.01,key_y_min,key_z_min])cube([length+.01,key_y_max-key_y_min,key_z_max-key_z_min]);
}
module body() {
    union() {
        import("../swim-r12-pack-retention/body.stl");
        translate([28.7,0,0])new_key();
    }
}
module shell_cut() {
    difference() {
        union() {
            translate([0,-dock_nose_width/2,dock_nose_bottom])
                cube([dock_nose_depth,dock_nose_width,dock_nose_top-dock_nose_bottom]);
            translate([dock_rear_start,-dock_width/2,dock_bottom])
                cube([dock_depth-dock_rear_start,dock_width,dock_top-dock_bottom]);
        }
        for(y=dock_pin_y) {
            xcyl(-eps,y,dock_pin_z,dock_head_pocket_d,dock_head_pocket_depth+eps);
            xcyl(-eps,y,dock_pin_z,dock_upper_bore_d,dock_front_stop_x+eps);
            xcyl(dock_front_stop_x,y,dock_pin_z,dock_flange_pocket_d,dock_flange_back_x-dock_front_stop_x);
            xcyl(dock_flange_back_x-eps,y,dock_pin_z,dock_tail_bore_d,dock_wire_pocket_x[0]-dock_flange_back_x+2*eps);
        }
        translate([-eps,key_slot_y_min,key_slot_z_min])
            cube([key_slot_depth+eps,key_slot_y_max-key_slot_y_min,key_slot_z_max-key_slot_z_min]);
        translate([dock_wire_pocket_x[0],dock_wire_pocket_y[0],dock_wire_pocket_z[0]])
            cube([dock_wire_pocket_x[1]-dock_wire_pocket_x[0],dock_wire_pocket_y[1]-dock_wire_pocket_y[0],dock_wire_pocket_z[1]-dock_wire_pocket_z[0]]);
        // Jacket retention bay with two 2.5mm cable-tie feed-throughs.
        translate([52,-10,2])cube([7,20,8.5]);
        xcyl(dock_wire_exit_x-eps,0,dock_pin_z,dock_wire_exit_d,dock_depth-dock_wire_exit_x+2*eps);
        for(y=[-4,4])translate([54.5,y-.8,dock_bottom-eps])cube([2.9,1.6,7]);
        translate([54.5,-4.8,dock_bottom-eps])cube([2.9,9.6,1.11]);
        // Captive nuts in the lower half. Four M2 x 16 screws enter from above.
        for(p=dock_screw_xy) {
            translate([p[0],p[1],dock_bottom-eps])cylinder(d=dock_screw_hole_d,h=dock_top-dock_bottom+2*eps);
            translate([p[0],p[1],dock_bottom-eps])rotate([0,0,30])
                cylinder(d=dock_nut_af/cos(30),h=dock_nut_depth+eps,$fn=6);
        }
        // Preserved 3mm magnet candidates. Holding force is explicitly unqualified.
        for(y=[-13,13])xcyl(1.5,y,5.8,3.1,1.1);
    }
}
module shell() {
    union() {
        shell_cut();
        // Flat jacket support: a tie presses the jacket here, not onto loose wires.
        // 3.8..4.4mm cable OD gives center Z=5.35..5.65 before feature allowances.
        translate([52,-3,1.9])cube([7,6,1.55]);
    }
}
module half(upper=false) {
    intersection() {
        shell();
        translate([-1,-20,upper?dock_split_z:dock_bottom-1])
            cube([dock_depth+2,40,upper?dock_top-dock_split_z+1:dock_split_z-dock_bottom+1]);
    }
}
module pin(y,compression=.6985,forward=0) {
    back=dock_flange_back_x-forward;
    tip=back-contact_full_stroke_to_flange_back-contact_stroke+compression;
    // Conservative diameter envelope of the sourced stepped barrel; not a STEP model.
    xcyl(tip,y,dock_pin_z,contact_tip_d,back-contact_full_stroke_to_flange_back-tip+eps);
    xcyl(back-contact_full_stroke_to_flange_back,y,dock_pin_z,contact_barrel_d,
        contact_full_stroke_to_flange_back-contact_upper_step_to_flange_back+eps);
    xcyl(back-contact_upper_step_to_flange_back,y,dock_pin_z,contact_upper_d,
        contact_upper_step_to_flange_back-contact_flange_t+eps);
    xcyl(back-contact_flange_t,y,dock_pin_z,contact_flange_d,contact_flange_t);
    xcyl(back-eps,y,dock_pin_z,contact_crimp_d,contact_crimp_length+eps);
}
module wire_curve(sign=1) {
    for(i=[0:39])hull()for(j=[i,i+1])let(t=j/40,x=harness_route_x[0]+t*(harness_route_x[1]-harness_route_x[0]),
      y=sign*(harness_route_y[0]+(harness_route_y[1]-harness_route_y[0])*(3*t*t-2*t*t*t)))
        translate([x,y,dock_pin_z])sphere(d=harness_usb_tail_d_requirement,$fn=16);
}
module harness() {
    color("#a9a9a9")for(y=dock_pin_y)pin(y);
    color("#b83038") {
        xcyl(dock_flange_back_x+contact_crimp_length,-6,dock_pin_z,harness_wire_od_max,8.45);
        wire_curve(-1);
    }
    color("#333333") {
        xcyl(dock_flange_back_x+contact_crimp_length,6,dock_pin_z,harness_wire_od_max,34-dock_flange_back_x-contact_crimp_length);
        wire_curve(1);
        xcyl(52,0,dock_pin_z,harness_usb_cable_d_nom,20);
    }
    color("#dfcb69")xcyl(harness_fuse_center[0]-harness_fuse_body_length_requirement/2,-6,dock_pin_z,
                         harness_fuse_insulated_d_requirement,harness_fuse_body_length_requirement);
    color("#b83038")xcyl(27.25,-6,dock_pin_z,1.2,6.75);
    color("#878787")for(p=[[17.5,-6],[29.5,-6],[29.5,6]])xcyl(p[0]-2,p[1],dock_pin_z,2.4,4);
}
module harness_screen() {
    // Bounding solids for the wire/sleeve paths; pin geometry remains explicit.
    for(y=dock_pin_y)pin(y);
    for(y=dock_pin_y)xcyl(dock_flange_back_x+contact_crimp_length,y,dock_pin_z,
                         harness_wire_od_max,34-dock_flange_back_x-contact_crimp_length);
    xcyl(19.75,-6,dock_pin_z,4,7.5);
    for(p=[[17.5,-6],[29.5,-6],[29.5,6]])xcyl(p[0]-2,p[1],dock_pin_z,2.4,4);
    // Contains both complete nominal splay paths, including their insulation.
    translate([33.4,-6.6,4.9])cube([19.2,13.2,1.2]);
    xcyl(52,0,dock_pin_z,harness_usb_cable_d_nom,20);
    // Installed head orientation: 4.45 along X, 4.8 along Y, 3.7 along Z.
    translate([53.775,3,6])cube([4.45,4.8,3.7]);
}
module local_collar_envelope() {
    translate([-28.7,0,0])import("../swim-r12-pack-retention/body.stl");
    new_key();
    for(y=dock_pin_y)xcyl(0,y,dock_pin_z,8.5,.8);
    // The boot STL is translated +4 for printing; restore its assembly frame.
    translate([-28.7,0,-4])import("../swim-r11-thermal-fit/boot.stl");
}
module inverted_dock(gap) {translate([gap,0,2*dock_pin_z])rotate([180,0,0])shell();}
if(part=="body")body();
else if(part=="lower")half();
else if(part=="upper")half(true);
else if(part=="pin_interference")intersection(){shell();for(y=dock_pin_y)pin(y);}
else if(part=="collar_interference")intersection(){shell();local_collar_envelope();}
else if(part=="harness_interference")intersection(){shell();harness_screen();}
else if(part=="key_reversed")intersection(){new_key();inverted_dock(earliest_contact_gap+.2);}
else if(part=="key_short_control")intersection(){new_key(1.3);inverted_dock(earliest_contact_gap+.2);}
else if(part=="small_bore_control")intersection(){for(y=dock_pin_y)pin(y);difference(){
    translate([1.5,-10,2])cube([3.5,20,7]);for(y=dock_pin_y)xcyl(1,y,dock_pin_z,1.5,5);}}
else if(part=="review") {
    color("#c7d7e7")half();harness();
    color([.35,.5,.65,.2])translate([0,0,15])half(true);
}
else if(part=="mounted") {
    color("#54718c")translate([-28.7,0,0])body();
    color("#a6b7c5")shell();harness();
}
else {color("#9badbd")half();harness();color([.35,.5,.65,.3])half(true);}
