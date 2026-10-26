# r15 — wire clamp and assembly fixture

r14 allocated space for a moving wire but had no part restraining its fixed end.
r15 adds a removable clamp cap, two hard-stop columns and four silicone pads.
A separate open-channel fixture locates both pigtails during factory assembly.
The external dry dock is **101.5 x 36 x 16mm**, excluding screw heads and cable.
The wearable, PCB, contact seats, key and seals are unchanged.

This is an implemented **prototype geometry**, not a qualified restraint or a
manufacturing release. The clamp relies on friction against PTFE insulation.
Its holding force cannot be obtained from the silicone durometer or this CAD.

## Assembly definition

| Item | Definition |
|---|---|
| Free pigtail | Preserved r14: 40.95 +/- 0.10mm at 23C, excluding strip/crimp/splice allowances |
| Fixed-end plane | X=49mm; position and slip together must stay within the inherited +/- 0.10mm feature budget |
| Pads | Four converted, unbacked HT-6210 candidates, each 6 x 3 x 0.7874mm |
| Sheet thickness | +/- 0.1016mm from the inspected manufacturer tolerance table |
| Converted pad outline | +/- 0.10mm engineering requirement, not the roll-width tolerance |
| Hard-face gap | 1.93 +/- 0.04mm; a separate +/- 0.015mm service allowance is assigned |
| Cap | 7 x 28.4 x 3mm, with pad-edge rims; columns set the closing position |
| Clamp screws | Two Accu SSCF-M2-10-A2 screws and HPN-M2-A2 nuts; incoming screw-length tolerance and torque remain open |
| Termination positions | First splices X=56..61, fuse X=61..68.5, rear positive splice X=68.5..73.5mm |
| USB tail/jacket | Splay X=75.5..93.5, jacket-retention bay X=93.5..100.5mm |

The pad pockets are 6.2 x 3.2mm, allowing the maximum converted outline.
The pads fit behind shallow edge rims; the central front/rear openings avoid a
hard edge against the wire. Their unloaded outlines are drawing dimensions,
not a four-piece STL set. The green pads in the preview show an illustrative
compressed height. They are not a deformation or contact-pressure simulation.

The cap and enclosure upper half are separate parts. The upper half has a local
recess for the installed cap and its screw heads. Remove that half before
adjusting the clamp. The cap screws pass through the base to underside hex nuts.
No adhesive or end-user soldering is specified.

## Evidence and its limit

`checks.json` repeats the 42 inherited wire/dock calculations and adds 19 clamp
checks. With independent sheet limits and the assigned service allowances, local
pad displacement at the wire center is **5.50 to 43.52%**. The 5..45% interval is
an engineering screening requirement, not a Rogers recommended clamp window.
It is not pressure, holding force, insulation strain or proof of a fixed end.

The assigned +/- 0.02mm pad service-thickness budget is **unqualified**. It is
not a derived guarantee for compression set, aging or temperature. A measurement
outside that allowance invalidates the squeeze result and requires new geometry
or controlled shimming. The same applies to the wire/gap service allowances.
The manufacturer sheet reports typical compression-set behavior under a specific
test; that value does not establish the life of this assembly.

Four meshes are exported: dock lower, upper, cap and the separate forming fixture.
Thirteen CAD checks cover rigid solids against the full r14 wire envelope,
stationary harness, pins, wearable, cap, screws, incoming pads and the nominal
fixture harness. Five intersections are empty. Three contain only the intended
cap/column, screw-head/cap or pad/support contact faces: every exported triangle
must lie on one specified plane and within its bearing or pad footprint. OpenSCAD warns that these
zero-thickness contact surfaces are not solid meshes; they are not delivered as
parts. No contact band is removed to hide an overlap. A cap shifted down 0.1mm
must instead produce a positive interference volume. The four deliverable part
meshes must remain closed and free of CAD warnings.

The other negative controls restore the old upper half and nominal-only pad
pocket, lower the cap into the wire, and reverse the key. The bad-pad-pocket
control uses a 0.001mm inset interior probe to separate its positive collision
volume from its seating faces; actual pad acceptance checks the complete pads.
The fixture
supports one nominal assembly pose; it does **not** force a wire to follow the
calculated family during cycling. The ten regression tests reject excessive
or missing squeeze, short/long screws, an undersized pad pocket, a shifted endpoint, the old splice
location and the old narrow wire compartment.

## Factory sequence and acceptance still to perform

1. Confirm HT-6210 sheet/batch thickness and die-cut dimensions against
   `sources.json` and `dock.json`. Do not substitute adhesive-backed sheet.
2. Approve the Mill-Max crimp and fuse/splice/insulation processes. Determine
   total wire cut length from actual insertion and overlap; 40.95mm is only the
   free insulated span. Extend the USB fanout as defined by the harness drawing.
3. Use the separate fixture with the contacts rear-seated at the marked flange
   recess. Form each free span in its open channel. Transfer the harness into
   the lower dock half without stretching it. The fixture is an assembly aid,
   not a precision wire-length measurement or a cyclic-flex test.
4. Install two lower pads, wires and two upper pads. Seat the cap on both columns.
   Establish screw torque on representative parts; do not infer it from M2 size.
   Confirm the upper housing closes without moving the cap or pinching a wire.
5. Measure the actual fixed-end planes at X=49.00 +/- 0.10mm. The position error
   **and** later slip share that budget; each cannot independently consume 0.10mm.
   Reject pad extrusion, exposed conductor, damaged PTFE or excessive motion.
6. Prototype acceptance target: load each stationary wire at 5N for 60 seconds
   in both axial directions with the contact isolated from this pull. Repeat
   after temperature dwell and a defined docking-cycle test. This is an assigned
   test load, not a demonstrated strength or a published Mill-Max requirement.
   Record before/after endpoint position, insulation condition, resistance and
   pad condition. Define the cycle count and retention life before release.

Actual pad friction/creep, cap stiffness and incoming screw-length tolerance are unqualified.
Dock-to-collar holding, internal contact lugs/J3 wiring, a protected-pack response,
firmware and powered/RF/ingress acceptance remain open. The supplier enquiry is
still unsent. The rejected quarter-turn catalogue research is not a selected latch.
The preserved r05l PCB remains all-green in its two recorded JLC PCB runs;
that result does not cover the assembled charger or IP68.

## Reproduce

```sh
python3 scripts/check_dock_wire_clamp.py
python3 -m unittest discover -s tests -p test_dock_wire_clamp.py -v
python3 scripts/export_dock_wire_clamp.py
python3 scripts/make_dock_clamp_sheet.py
python3 scripts/verify_dock_wire_clamp.py
```

Saved verification needs standard Python. Deliberate regeneration needs OpenSCAD
and rsvg-convert. All dock parts share the installed r13/r14 coordinate frame.
The fixture uses its own Z=0 base and Z=3 wire-center plane; it never goes in the
product. Earlier source and evidence remain preserved.
