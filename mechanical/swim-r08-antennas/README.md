# r08 — prototype antennas, cable routes and lid guides

This revision replaces the two 30 × 5 mm antenna placeholders with CAPH and ZETA
prototype candidates. The r05l PCB, native project, Gerber and two real JLC passes
remain byte-identical. The [selection review](../../assembly/pack-antenna-r02/README.md)
records the manufacturer sources and outstanding limits.

The shell keeps its 57.4 × 49.4 mm footprint. Body plus lid height increases from
17.6 to **20.6 mm** to accommodate two standard-length cables at separate heights.
The boot is **60.4 × 52.4 × 25.4 mm**. The docking key adds 1.3 mm on positive X.
No new exterior opening is added; main/contact seal dimensions remain unchanged.
There is no physical water/dust test or IP68 acceptance.

Both FPCs mount under the lid. Four internal slotted guides retain the nominal
cable paths in the gap between them. Cable routing ends at the actual J1/J2
positions. Lift/service motion with the leads connected has not been qualified:
the exploded drawing shows separated parts, not a validated opening sequence.

The longer shell uses a 20 mm M2 screw candidate. Blind 3 mm diameter, 1.7 mm deep
pockets in the boot clear its protruding tips, outside the collar lane. The
conditional length/stack screen leaves at least 0.3 mm tip clearance and 2.3 mm
boot floor. Head, nut, torque and production tolerances still need approval.

## Evidence and limits

- All 85 populated envelopes pass at 0.71, 0.81, 0.84088 and 0.91 mm PCB thickness.
- Two smooth centerlines are approximately 98.5 mm; the provisional connector
  datum allowance makes the assembly length 100 mm. This is a nominal case, not
  a qualified fit of every supplied cable tolerance.
- Cable radius includes 0.15 mm position allowance. Sample spacing is bounded;
  clearance calculations deduct half-step bounds. The 3 mm bend screen is an
  engineering constraint, not a sourced limit for the exact supplied coax.
- The factory feed cable is part of its FPC assembly. The final 20 mm near its
  own FPC is excluded from a free-air separation check; the detailed feed bond
  remains unqualified. Lid, other antenna, board and other cable checks remain active.
- An independent CAD intersection found 0.031656 mm³ at the initial GNSS exit
  guide. A 2.0 mm straight channel still interfered by 0.013088 mm³. The final
  exit uses a curved 2.0 mm channel in a 4.8 mm wide body, while
  the other channels stay 1.8 mm. The failed geometry is retained in
  [evidence/initial-guide](evidence/initial-guide/failure.json).
- The final inflated cable/guide intersection is empty, as is the populated
  component/body/lid/carrier intersection. All eight exported meshes are closed,
  oriented and connected. All 34 shell/seal/fastener screens pass conditionally.
  The exploded, section, mounted, populated and routing previews were inspected.
- Restoring the old carrier produces 1.234334 mm³ interference; deliberately
  narrowing the cable channels to 1.0 mm produces 4.399098 mm³. These controls
  show that the actual CAD checks reject intersecting geometry.
- Clip strength, assembly forces, cable length variation, opening/service motion,
  actual RF performance, pack/NTC, positive PCB retention and physical ingress
  remain open. The battery block is still an unselected reservation.

The meshes represent prototype geometry, not a watertight printing process.
The unchanged seal tolerance calculation does not establish surface finish,
material compatibility, compression under load or a finished IP rating.

## Reproduce

Use the geometry environment and OpenSCAD from [RESUME](../../docs/RESUME.md).
Do not run a PCB generator or upload another unchanged Gerber to DFM.
Use a separate checkout for regeneration so the saved evidence and delivered
archive remain intact. `verify_antenna_candidate.py` alone is read-only.

```sh
python3 scripts/build_swim_r08_geometry.py
.venv-dfm/bin/python scripts/check_antenna_assembly.py
.venv-dfm/bin/python -m unittest discover -s tests -p test_antenna_assembly.py -v
python3 scripts/export_antenna_enclosure.py
python3 scripts/verify_antenna_candidate.py
```

The four regressions reject the old lid height, coincident cable paths, a cable
lowered into the populated board and collision with the other antenna despite
the intentional own-feed joint. Source hashes bind the reports to the actual
PCB, parameters, routing controls, checker and generated CAD.
