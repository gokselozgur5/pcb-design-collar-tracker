// Requested pack and NTC stack. No approved supplier part.
module pack_request_stack_r09() {
  color([.65,.68,.72])translate([-16.0,-15.25,2.1])cube([32, 30.5, 5.3]);
  color([.95,.55,.1])translate([-13.0,-2.05,7.550000000000001])cube([26,4.1,0.5]);
  color([.85,.7,.2,.4])translate([-14.0,-3.05,8.05])cube([28,6.1,0.1]);
}

module pack_request_stack(){translate([0,0,-0.30000000000000004])pack_request_stack_r09();}
