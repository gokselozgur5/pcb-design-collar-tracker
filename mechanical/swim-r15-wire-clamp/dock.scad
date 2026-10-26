// r15 dry dock: independent padded wire clamp with mechanical hard stops.
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
module base_shell(){
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
module base_half(upper=false){intersection(){base_shell();translate([-1,-20,upper?dock_split_z:dock_bottom-1])
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
    x=clamp_first_splice_x;
    for(y=dock_pin_y){
        xcyl(motion_fixed_end_x,y,5.5,harness_wire_od_max,x-motion_fixed_end_x);
        xcyl(x,y,5.5,2.4,5);
    }
    xcyl(x+5,-6,5.5,4,7.5);
    xcyl(x+12.5,-6,5.5,2.4,5);
    xcyl(x+17.5,-6,5.5,1.2,harness_route_x[0]-x-17.5);
    xcyl(x+5,6,5.5,1.2,harness_route_x[0]-x-5);
    for(sign=[-1,1])splay(sign);
}
module stationary_screen(){
    stationary_harness();
    translate([harness_route_x[0]-.6,-6.6,4.9])cube([19.2,13.2,1.2]);
    translate([dock_wire_exit_x+1.775,3,6])cube([4.45,4.8,3.7]);
}
module harness(){
    color("#afbfca")stationary_harness();
    color("#bf3340")loop(-1);
    color("#202832")loop(1);
    color("#333c49")xcyl(dock_wire_exit_x,0,5.5,4.1,20);
}
// Clamp halves seat on columns, so tightening cannot reduce the specified gap.
clamp_lo=dock_pin_z-clamp_gap/2;
clamp_hi=dock_pin_z+clamp_gap/2;
module pad_rim(y,upper=false,extra=clamp_pad_pocket_extra){
    difference(){
        translate([clamp_pad_x[0]-.5,y-clamp_pad_width/2-.4,upper?clamp_hi-.6:clamp_lo-.01])
            cube([clamp_pad_x[1]-clamp_pad_x[0]+1,clamp_pad_width+.8,.61]);
        translate([clamp_pad_x[0],y-(clamp_pad_width+extra)/2,clamp_lo-.1])
            cube([clamp_pad_x[1]-clamp_pad_x[0]+extra,clamp_pad_width+extra,clamp_gap+.2]);
        // Open central slots retain pad edges without a hard lip on the wire.
        translate([clamp_pad_x[0]-.6,y-1.05,clamp_lo-.1])
            cube([clamp_pad_x[1]-clamp_pad_x[0]+1.2,2.1,clamp_gap+.2]);
    }
}
module clamp_bores(nuts=false){
    for(y=clamp_screw_y){
        translate([clamp_screw_x,y,dock_bottom-.1])cylinder(d=clamp_screw_hole_d,h=20);
        if(nuts)translate([clamp_screw_x,y,dock_bottom-eps])rotate([0,0,30])
            cylinder(d=(clamp_nut_af+.3)/cos(30),h=clamp_nut_ceiling_z-dock_bottom+eps,$fn=6);
    }
}
module foundation(){
    difference(){
        union(){
            translate([clamp_cap_x[0],-clamp_cap_half_width,1.9])
                cube([clamp_cap_x[1]-clamp_cap_x[0],2*clamp_cap_half_width,clamp_lo-1.9]);
            for(y=clamp_screw_y)translate([clamp_screw_x,y,1.9])cylinder(r=2.6,h=clamp_hi-1.9);
            for(y=dock_pin_y)pad_rim(y);
        }
        clamp_bores(true);
    }
}
module cap(extra=clamp_pad_pocket_extra){
    difference(){
        union(){
            translate([clamp_cap_x[0],-clamp_cap_half_width,clamp_hi])
                cube([clamp_cap_x[1]-clamp_cap_x[0],2*clamp_cap_half_width,clamp_cap_thickness]);
            for(y=dock_pin_y)pad_rim(y,true,extra);
        }
        clamp_bores();
    }
}
module cap_hardware(){
    for(y=clamp_screw_y){
        top=clamp_hi+clamp_cap_thickness;
        translate([clamp_screw_x,y,top-clamp_screw_length])cylinder(d=2,h=clamp_screw_length);
        translate([clamp_screw_x,y,top])cylinder(d=clamp_screw_head_d,h=clamp_screw_head_h);
    }
}
module pads(){
    // Illustrative compressed height only; real pad deformation is not modeled.
    t=(clamp_gap-harness_wire_od_max)/2;
    for(y=dock_pin_y)for(z=[clamp_lo,clamp_hi-t])
        translate([clamp_pad_x[0],y-clamp_pad_width/2,z])
            cube([clamp_pad_x[1]-clamp_pad_x[0],clamp_pad_width,t]);
}
module incoming_pads(inset=0){
    t=clamp_pad_thickness+clamp_pad_thickness_tolerance;
    w=clamp_pad_width+clamp_pad_dimension_tolerance;
    for(y=dock_pin_y)for(z=[clamp_lo,clamp_hi-t])
        translate([clamp_pad_x[0]+inset,y-w/2+inset,z+inset])
            cube([clamp_pad_x[1]-clamp_pad_x[0]+clamp_pad_dimension_tolerance-2*inset,w-2*inset,t-2*inset]);
}
module lower(){difference(){union(){base_half();foundation();}clamp_bores(true);}}
module upper(){
    difference(){
        base_half(true);
        translate([clamp_cap_x[0]-clamp_cap_fit_allowance,-clamp_cap_half_width-clamp_cap_fit_allowance,dock_split_z-eps])
            cube([clamp_cap_x[1]-clamp_cap_x[0]+2*clamp_cap_fit_allowance,
                  2*(clamp_cap_half_width+clamp_cap_fit_allowance),
                  clamp_hi+clamp_cap_thickness+clamp_screw_head_h+clamp_cap_fit_allowance-dock_split_z+eps]);
    }
}
module shell(){lower();upper();cap();}
module fixture_grooves(){
    p=wire_poses[0];
    for(sign=[-1,1]){
        // Open semicircular channels. Flange recess provides a visible end datum.
        translate([0,0,3-dock_pin_z]){
            xcyl(-2,sign*6,dock_pin_z,1.95,dock_flange_back_x-contact_flange_t+2);
            xcyl(dock_flange_back_x-contact_flange_t-.08,sign*6,dock_pin_z,2.25,contact_flange_t+.16);
            xcyl(dock_flange_back_x,sign*6,dock_pin_z,1.8,contact_crimp_length+.05);
        }
        // Flat-bottom open wire channel; keep its 2D outline in the XY plane.
        // This avoids a costly union of 160 overlapping 3D spherical cutters.
        translate([0,0,2.53])linear_extrude(height=1){
            for(i=[0:79])hull()for(j=[i,i+1])let(t=j/80)
                translate([p[0]+(p[1]-p[0])*t,sign*(6+p[2]*(1-cos(360*t))/2)])circle(d=1.15,$fn=16);
            translate([p[1]-.01,sign*6-.575])square([clamp_pad_x[1]+1-p[1],1.15]);
        }
    }
}
module fixture(){difference(){translate([-1,-16,0])cube([58,32,3]);fixture_grooves();}}
if(part=="lower")lower();
else if(part=="upper")upper();
else if(part=="cap")cap();
else if(part=="fixture")fixture();
else if(part=="wire_interference")intersection(){shell();wire_sweep();}
else if(part=="pin_interference")intersection(){shell();for(y=dock_pin_y)pin(y);}
else if(part=="collar_interference")intersection(){shell();collar();}
else if(part=="stationary_interference")union(){
    intersection(){shell();stationary_screen();}
    intersection(){difference(){shell();jacket_saddle();}xcyl(dock_wire_exit_x,0,5.5,4.1,20);}
}
else if(part=="cap_interference")intersection(){cap();union(){lower();upper();}}
else if(part=="cap_overlap_control")intersection(){translate([0,0,-.1])cap();lower();}
else if(part=="screw_interference")intersection(){shell();cap_hardware();}
else if(part=="pad_interference")intersection(){shell();incoming_pads();}
// Only this deliberately bad control probes pad interiors to avoid adding
// seating faces to its nonzero collision volume. Actual fit uses full pads.
else if(part=="old_pad_pocket_control")intersection(){cap(0);incoming_pads(.001);}
else if(part=="fixture_interference")intersection(){fixture();
    translate([0,0,3-dock_pin_z])union(){for(y=dock_pin_y)pin(y);for(sign=[-1,1])loop(sign,0);}}
else if(part=="old_upper_control")intersection(){import("../swim-r14-wire-motion/upper.stl");cap();}
else if(part=="pinch_control")intersection(){translate([0,0,-.8])cap();wire_sweep();}
else if(part=="key_reversed")intersection(){key();translate([earliest_contact_gap+.2,0,11])rotate([180,0,0])shell();}
else if(part=="review"){
    color("#afc6d9")lower();harness();color("#3a8073")pads();
    color("#dba15d")translate([0,0,8])cap();
    color([.3,.5,.7,.25])translate([0,0,20])upper();
}
else if(part=="clamp_detail"){
    intersection(){color("#afc6d9")lower();translate([47,-15,0])cube([11,30,8]);}
    color("#3a8073")pads();color("#dba15d")translate([0,0,4])cap();
    for(y=dock_pin_y)color("#803d46")xcyl(47,y,dock_pin_z,harness_wire_od_max,10);
}
else if(part=="fixture_review"){color("#bed1df")fixture();
    translate([0,0,3-dock_pin_z]){for(y=dock_pin_y)color("#aaaeb5")pin(y);for(sign=[-1,1])color("#c35655")loop(sign,0);}}
else{color("#afc6d9")lower();harness();color("#3a8073")pads();color("#dba15d")cap();}
