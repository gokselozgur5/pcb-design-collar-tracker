# Internal charge harness — HOLD

The electrical mapping is fixed: case Y=-6 is red to J3.1 `/VIN_5V`; Y=+6 is
black to J3.2 `/GND`. The current contact/terminal geometry is
[r16](../../mechanical/swim-r16-contact-retention/README.md). The PCB is unchanged.

The wire candidate is the existing Alpha 2843/7 stranded 26 AWG PTFE wire:
0.8382mm maximum outside diameter and 8.382mm minimum bend radius. Manufacturer
source identity is preserved in
[the external harness sources](../charge-harness-r01/sources.json).

`route-study.json` preserves **failed draft control points**, not approved wire
paths or cut lengths. A red-only route can clear components and RF cables but
does not leave sufficient space at the ground termination. The simultaneous
two-wire route has not passed. Do not include these drafts in manufacturing CAD
or describe the completed terminal bearing as a completed harness.

Next: route both leads together from the r16 terminal exits to the native J3
pads, with actual stripped-end and solder-joint envelopes. Check RF lead
separation, bend radius and the closed lid. Implement fixing/strain relief and
check board insertion/service movement before freezing wire cut lengths.
The eventual factory process must prepare, join and inspect the assembly;
end-user soldering is not part of the product flow. Process temperature/time,
flux cleaning, joint insulation, pull and contact resistance remain unqualified.

The r16 washer/terminal combination also changes the contact's complete
electrical path. Measure it after torquing; do not infer low resistance from
the mechanical fit or bare-material conductivity.
