# r07 carrier for the charge-interlock PCB

This enclosure candidate uses the actual r05l placements and sourced maximum
heights for 85 populated envelopes. All pass at 0.71, 0.81, 0.84088 and 0.91mm board
thickness. The previous carrier collides with U12 and remains a negative control.

U12 needs a ledge relief at `[-19.8, 11.025, -16.7, 14.975]` mm, through the 1.5mm
ledge. A 1mm outer bridge remains. The adjacent support leg moves from
`[-19.8, 12]` to `[-19.8, 10]`; its 1 × 2mm section and connection to the rail remain.
The guide posts, shell, seal gland and charging-contact geometry are unchanged.

`check_charge_fit.py` checks the final source and four thickness cases.
`export_charge_enclosure.py` exports the actual CAD meshes and previews, checks
closed/oriented connected surfaces, and performs a CAD intersection with 0.20mm
component clearance. Restoring the previous ledge and leg provides the nonempty
control. Reports identify their exact source hashes; do not reuse old revision
mesh acceptance for this model.

Rigid body plus lid: 57.4 × 49.4 × 17.6mm, excluding the local docking key.
The boot envelope is 60.4 × 52.4 × 22.4mm. Battery and antenna boxes remain
reservations; this is not a finalized selected-component assembly.

IP68 swimming/dust resistance remains a target. The provisional immersion case
is 2m fresh water for 60 minutes. Material/seal grades, fasteners/torque, positive
PCB retention, selected pack/antennas, harness/dock and physical qualification
remain open. CAD geometry does not establish ingress protection or carrier strength.
