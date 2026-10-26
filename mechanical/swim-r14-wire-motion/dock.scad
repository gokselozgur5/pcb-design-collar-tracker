// r14 dry dock: full conservative contact-movement wire envelopes.
include <parameters.scad>
$fn=48;
part="assembly";
pose=0;
eps=.01;
module xcyl(x,y,z,d,h){translate([x,y,z])rotate([0,90,0])cylinder(d=d,h=h);}
module key(length=key_length){translate([-.01,key_y_min,key_z_min])cube([length+.01,key_y_max-key_y_min,key_z_max-key_z_min]);}
module collar(){
    translate([-28.7,0,0])import("../swim-r13-charge-dock/body.stl");
    for(y=dock_pin_y)xcyl(0,y,dock_pin_z,8.5,.8);
    translate([-28.7,0,-4])import("../swim-r11-thermal-fit/boot.stl");
}
module jacket_saddle(){translate([dock_wire_exit_x,-3,1.9])cube([7,6,1.55]);}
module shell(){
    union(){
        difference(){
            union(){
                translate([0,-dock_nose_width/2,dock_nose_bottom])cube([dock_nose_depth,dock_nose_width,dock_nose_top-dock_nose_bottom]);
                translate([dock_rear_start,-dock_width/2,dock_bottom])cube([dock_depth-dock_rear_start,dock_width,dock_top-dock_bottom]);
            }
            for(y=dock_pin_y){
                xcyl(-eps,y,dock_pin_z,dock_head_pocket_d,dock_head_pocket_depth+eps);
                translate([-eps,y-.6,dock_nose_bottom-.1])cube([dock_head_pocket_depth+eps,1.2,.5]);
                xcyl(-eps,y,dock_pin_z,dock_upper_bore_d,dock_front_stop_x+eps);
                xcyl(dock_front_stop_x,y,dock_pin_z,dock_flange_pocket_d,dock_flange_back_x-dock_front_stop_x);
                xcyl(dock_flange_back_x-eps,y,dock_pin_z,dock_tail_bore_d,dock_wire_pocket_x[0]-dock_flange_back_x+2*eps);
            }
            // Rear relief leaves the load-bearing flange shoulder intact.
            for(sign=[-1,1])scale([1,sign,1])
                translate([motion_rear_relief_start_x,motion_rear_relief_inner_y,motion_rear_relief_z[0]])
                cube([motion_rear_relief_end_x-motion_rear_relief_start_x,motion_rear_relief_outer_y-motion_rear_relief_inner_y,
                    motion_rear_relief_z[1]-motion_rear_relief_z[0]]);
            translate([-eps,key_slot_y_min,key_slot_z_min])cube([key_slot_depth+eps,key_slot_y_max-key_slot_y_min,key_slot_z_max-key_slot_z_min]);
            translate([dock_wire_pocket_x[0],dock_wire_pocket_y[0],dock_wire_pocket_z[0]])
                cube([dock_wire_pocket_x[1]-dock_wire_pocket_x[0],dock_wire_pocket_y[1]-dock_wire_pocket_y[0],dock_wire_pocket_z[1]-dock_wire_pocket_z[0]]);
            translate([dock_wire_exit_x,-10,2])cube([7,20,8.5]);
            xcyl(dock_wire_exit_x-eps,0,dock_pin_z,dock_wire_exit_d,dock_depth-dock_wire_exit_x+2*eps);
            for(y=[-4,4])translate([dock_wire_exit_x+2.5,y-.8,dock_bottom-eps])cube([2.9,1.6,7]);
            translate([dock_wire_exit_x+2.5,-4.8,dock_bottom-eps])cube([2.9,9.6,1.11]);
            for(p=dock_screw_xy){
                translate([p[0],p[1],dock_bottom-eps])cylinder(d=dock_screw_hole_d,h=dock_top-dock_bottom+2*eps);
                translate([p[0],p[1],dock_bottom-eps])rotate([0,0,30])cylinder(d=dock_nut_af/cos(30),h=dock_nut_depth+eps,$fn=6);
            }
            for(y=[-13,13])xcyl(1.5,y,5.8,3.1,1.1);
        }
        jacket_saddle();
    }
}
module half(upper=false){intersection(){shell();translate([-1,-20,upper?dock_split_z:dock_bottom-1])
    cube([dock_depth+2,40,upper?dock_top-dock_split_z+1:dock_split_z-dock_bottom+1]);}}
module pin(y,compression=.6985){
    back=dock_flange_back_x;
    tip=back-contact_full_stroke_to_flange_back-contact_stroke+compression;
    xcyl(tip,y,dock_pin_z,contact_tip_d,back-contact_full_stroke_to_flange_back-tip+eps);
    xcyl(back-contact_full_stroke_to_flange_back,y,dock_pin_z,contact_barrel_d,contact_full_stroke_to_flange_back-contact_upper_step_to_flange_back+eps);
    xcyl(back-contact_upper_step_to_flange_back,y,dock_pin_z,contact_upper_d,contact_upper_step_to_flange_back-contact_flange_t+eps);
    xcyl(back-contact_flange_t,y,dock_pin_z,contact_flange_d,contact_flange_t);
    xcyl(back-eps,y,dock_pin_z,contact_crimp_d,contact_crimp_length+eps);
}
module loop(sign=1,selected=pose){
    p=wire_poses[selected];
    for(i=[0:31])hull()for(j=[i,i+1])let(t=j/32)
        translate([p[0]+(p[1]-p[0])*t,sign*(6+p[2]*(1-cos(360*t))/2),dock_pin_z])sphere(d=harness_wire_od_max,$fn=12);
}
module wire_sweep(){
    for(sign=[-1,1])scale([1,sign,1])for(b=wire_swept_cells){
        // Interval center line + circular YZ insulation envelope. Circumscribe
        // the circle so tessellation cannot understate the continuous bound.
        // Flat X end planes also enclose the full spherical end extension.
        if(b[0]<motion_rear_relief_end_x)
            hull()for(yy=[6,b[4]-wire_envelope_radius])
                xcyl(b[0],yy,dock_pin_z,2*wire_envelope_radius/cos(180/$fn),b[3]-b[0]);
        else translate([b[0],b[1],b[2]])cube([b[3]-b[0],b[4]-b[1],b[5]-b[2]]);
    }
}
module splay(sign=1){
    for(i=[0:39])hull()for(j=[i,i+1])let(t=j/40)
        translate([harness_route_x[0]+(harness_route_x[1]-harness_route_x[0])*t,
            sign*(6+(.8-6)*(3*t*t-2*t*t*t)),dock_pin_z])sphere(d=1.2,$fn=12);
}
module stationary_harness(){
    for(y=dock_pin_y)pin(y);
    for(y=[-6,6])xcyl(48.5,y,5.5,2.4,5);
    xcyl(53.5,-6,5.5,4,7.5);
    xcyl(61,-6,5.5,2.4,5);
    xcyl(66,-6,5.5,1.2,2);
    xcyl(53.5,6,5.5,1.2,14.5);
    for(sign=[-1,1])splay(sign);
}
module stationary_screen(){
    stationary_harness();
    translate([67.4,-6.6,4.9])cube([19.2,13.2,1.2]);
    translate([dock_wire_exit_x+1.775,3,6])cube([4.45,4.8,3.7]);
}
module harness(){
    color("#afbfca")stationary_harness();
    color("#bf3340")loop(-1);
    color("#202832")loop(1);
    color("#333c49")xcyl(dock_wire_exit_x,0,5.5,4.1,20);
}
if(part=="lower")half();
else if(part=="upper")half(true);
else if(part=="wire_interference")intersection(){shell();wire_sweep();}
else if(part=="pin_interference")intersection(){shell();for(y=dock_pin_y)pin(y);}
else if(part=="collar_interference")intersection(){shell();collar();}
else if(part=="stationary_interference")union(){
    intersection(){shell();stationary_screen();}
    intersection(){difference(){shell();jacket_saddle();}xcyl(dock_wire_exit_x,0,5.5,4.1,20);}
}
else if(part=="old_housing_control")intersection(){
    union(){import("../swim-r13-charge-dock/lower.stl");import("../swim-r13-charge-dock/upper.stl");}
    wire_sweep();
}
else if(part=="key_reversed")intersection(){key();translate([earliest_contact_gap+.2,0,11])rotate([180,0,0])shell();}
else if(part=="review"){
    color("#afc6d9")half();harness();
    color([.3,.5,.7,.3])translate([0,0,15])half(true);
}
else if(part=="motion"){
    color([.7,.8,.9,.3])half();
    // Three illustrative poses; the complete family is checked by interval boxes.
    for(i=[0,4,8])color([i/(len(wire_poses)-1),.3,1-i/(len(wire_poses)-1),.7])for(sign=[-1,1])loop(sign,i);
}
else if(part=="mounted"){
    color("#6688a6")collar();color("#b3c9db")shell();harness();
}
else{color("#b3c9db")half();harness();}
