// Conditional pack retention. Body-integral cradle and carrier-integral cap.
include <pack-retention-parameters.scad>
module pack_cradle(inner=pack_cradle_inner) {
    translate([0,0,floor_t-eps])linear_extrude(pack_platform_z-floor_t+eps)
        rr(pack_cradle_outer[0],pack_cradle_outer[1],pack_cradle_r);
    translate([0,0,pack_platform_z-eps])linear_extrude(pack_wall_z-pack_platform_z+eps)
        difference(){
            rr(pack_cradle_outer[0],pack_cradle_outer[1],pack_cradle_r);
            rr(inner[0],inner[1],pack_cradle_r);
        }
}
module pack_cap_plan(reliefs=true,ntc=true) {
    difference(){
        union(){
            difference(){
                rr(pack_cap_outer[0],pack_cap_outer[1],pack_cap_r);
                square(pack_cap_inner,center=true);
                if(ntc)square(pack_cap_ntc,center=true);
            }
            for(b=pack_cap_tongues)translate([b[0],b[1]])square([b[2]-b[0],b[3]-b[1]]);
        }
        if(reliefs)for(b=pack_cap_reliefs)translate([b[0],b[1]])square([b[2]-b[0],b[3]-b[1]]);
    }
}
module pack_cap(reliefs=true,ntc=true) {
    translate([0,0,pack_cap_z])linear_extrude(pack_cap_top-pack_cap_z)pack_cap_plan(reliefs,ntc);
    for(b=pack_bridges)translate([b[0],b[1],pack_cap_z])cube([b[2]-b[0],b[3]-b[1],pack_bridge_top-pack_cap_z]);
}
module body(){union(){body_base();pack_cradle();}}
module carrier(){union(){carrier_base();translate([0,0,-(pcb_z-1.5)])pack_cap();}}
// The collision screen expands added solids by the same feature and thermal
// bounds used in the analytic model. These envelopes are not manufactured parts.
module pack_cap_envelope(reliefs=true){
    translate([0,0,pack_cap_z-.13])linear_extrude(pack_cap_top-pack_cap_z+.26)
        offset(delta=.05)pack_cap_plan(reliefs);
    for(b=pack_bridges)translate([b[0]-.05,b[1]-.05,pack_cap_z-.13])
        cube([b[2]-b[0]+.1,b[3]-b[1]+.1,pack_bridge_top-pack_cap_z+.26]);
}
module pack_component_interference(reliefs=true){
    intersection(){moving_components(motion_boxes,.2);pack_cradle();}
    intersection(){moving_components(carrier_motion_boxes,.2);pack_cap_envelope(reliefs);}
}
module pack_hardware_interference(){
    intersection(){union(){pack_cradle();pack_cap();}hardware();}
}
module pack_ntc(){translate([-14,-3.05,pack_body_z+5.45])cube([28,6.1,.6]);}
module pack_ntc_interference(ntc=true){intersection(){pack_cap(true,ntc);pack_ntc();}}
module pack_max_body(){translate([-16,-15.25,pack_body_z])cube([32,30.5,5.3]);}
module pack_cradle_interference(inner=pack_cradle_inner){
    // Exclude intentional floor bearing; test wall interference.
    intersection(){
        difference(){pack_cradle(inner);translate([-30,-30,-1])cube([60,60,pack_platform_z+1]);}
        pack_max_body();
    }
}
module pack_review(){
    color([.20,.37,.52,.5])body();
    pack_request_stack();
    color([.82,.58,.18])translate([0,0,pcb_z-1.5])carrier();
    color([.55,.6,.65])contact_retention();
}
module pack_exploded(){
    color([.20,.37,.52,.7])body();
    translate([0,0,5])pack_request_stack();
    color([.82,.58,.18])translate([0,0,pcb_z-1.5+15])carrier();
}
