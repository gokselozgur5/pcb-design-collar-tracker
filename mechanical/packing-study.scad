// Collar tracker / packaging study 0.1 / dimensions in mm.
// This is a volume allocation, not a routed PCB or a proven antenna design.
// The health head, antenna shapes and all circuit blocks except nRF9151 are
// reservations. No sealed enclosure, fastening or strain relief is designed.
// Open in OpenSCAD and change variant/view_mode. Render before exporting.

variant = "compact_250"; // [compact_250,reference_500]
view_mode = "exploded"; // [exploded,section,assembled,mockup]
$fn = 48;

compact = variant == "compact_250";
body = compact ? [38,30,14] : [44,36,14];
wall = 1.2;
corner = 4;
lid_z = body[2]-wall;
// EEMB 250mAh pack example: supplier listings differ by 1mm; use 32mm length.
// 500mAh reference: Adafruit 1578. Both are mechanical examples, not selected.
cell = compact ? [32,20.5,5.3] : [36,29,4.75];
cell_y = compact ? -0.5 : -0.5;
cell_z = 3;
pcb = [30,22,0.8];
pcb_z = 8.9;
antenna_y = body[1]/2-wall-1.2;
lift = view_mode == "exploded" ? 1 : 0;

module rounded_prism(size, radius) {
    linear_extrude(height=size[2])
        offset(r=radius)
            square([size[0]-2*radius,size[1]-2*radius],center=true);
}

module base() {
    difference() {
        rounded_prism([body[0],body[1],lid_z],corner);
        translate([0,0,wall])
            rounded_prism([body[0]-2*wall,body[1]-2*wall,body[2]],corner-wall);
        // Placeholder contact-window opening. Optical material and sealing TBD.
        translate([0,0,-1]) cylinder(d=8,h=wall+2);
    }
}

module lid() {
    translate([0,0,lid_z]) rounded_prism([body[0],body[1],wall],corner);
}

module block(size, position, tint) {
    color(tint) translate(position)
        translate([-size[0]/2,-size[1]/2,0]) cube(size);
}

module internals() {
    // Pink = provisional health head; sensor/optics/electrodes not selected.
    block([10,10,1.3],[0,0,1.4+lift*1.2],[0.87,0.30,0.55]);
    color([0.87,0.30,0.55]) translate([0,0,-0.6+lift*1.2]) cylinder(d=8,h=1.8);
    // Gold = battery. Allowance around the block is not a cell swelling spec.
    block(cell,[0,cell_y,cell_z+lift*7],[0.88,0.68,0.22]);
    // Green = board envelope; actual PCB not placed or routed.
    block(pcb,[1,0,pcb_z+lift*16],[0.16,0.53,0.39]);
    // Only this package has an individually verified component body dimension.
    block([12.1,11.1,1.2],[-6,0,pcb_z+pcb[2]+lift*16],[0.28,0.33,0.40]);
    // Combined circuit budget: power, eSIM, passives, protection and connectors.
    block([12,8,2.5],[8,-5,pcb_z+pcb[2]+lift*16],[0.45,0.48,0.53]);
    block([6,4,1.2],[9,5,pcb_z+pcb[2]+lift*16],[0.45,0.48,0.53]);
    // Amber = requested antenna volume, NOT a selected or simulated antenna.
    block([30,1,7],[0,antenna_y,3.3+lift*16],[0.98,0.40,0.12]);
    block([14,5,1],[6,antenna_y-2.1,11+lift*16],[0.98,0.40,0.12]);
}

module assembly() {
    color([0.72,0.77,0.83]) base();
    internals();
    color([0.78,0.83,0.89,0.65]) translate([0,0,lift*30]) lid();
}

if (view_mode == "mockup") {
    // Solid sizing dummy only; not the functional enclosure.
    union() {
        rounded_prism(body,corner);
        translate([0,0,-0.6]) cylinder(d=8,h=0.7);
    }
} else if (view_mode == "section") {
    difference() {
        assembly();
        // Cut away front half to expose the height stack.
        translate([-50,-50,-5]) cube([100,50,90]);
    }
} else {
    assembly();
}
