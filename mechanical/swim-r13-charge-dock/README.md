# r13 charging dock prototype

Replaces the old 6mm-deep alignment block with a split housing for two real
Mill-Max 0962 crimp contacts, a USB harness, fuse and cable-retention bay.
The external dock is 60 x 36 x 16mm, excluding cable and screw heads.
The wearable's shell/PCB/pack/seals remain the r12 geometry except for its
external key: 4.0mm projection and Z=7.7–13.2mm. The shell including key is
61.4 x 49.4 x 21.0mm; the unchanged boot remains 60.4 x 52.4 x 25.8mm.

**Conditional geometric prototype. No magnetic holding, power, crimp, production
assembly or IP68 acceptance is established.** The harness definition lists the
remaining [process and power gates](../../assembly/charge-harness-r01/README.md).

The old key is too short to block the earliest possible reverse contact after
allowing pin movement inside its housing. It also sits too high to hit the reversed
front nose. The new taller key blocks the aligned 180-degree reversed approach
before conductive contact. Off-axis/skewed approaches, loads and damage still need
physical evaluation. These controls do not establish an unconditional polarity barrier.

The spring flange seats on the rear shoulder under mating force. A front shoulder
around the smaller barrel retains it when disconnected. The front shoulder is
deliberately ahead of the larger steps, avoiding an implausibly tight moulded fit
between the almost equal barb/flange diameters. Unloaded movement is conservatively
bounded from the flange alone; the earlier barb stop can reduce actual movement.

## Saved checks

- 29 analytic checks, including 64 stroke/tolerance combinations, positive flange
  capture, head landing, boot/key clearances, continuous wire-bend bound and native
  J3/J4 pinout. General manufacturer tolerances are used, not assumed tighter fits.
- Operating compression 0.2391–1.1079mm; remaining travel at least 0.4161mm,
  **while the mating faces are held within the assigned 0.05mm gap**.
- Earliest possible contact at a face gap of 3.25mm after conservatively allowing
  2.1421mm unloaded forward movement. The assigned new-key margin is 0.55mm.
- Two actual dock-half meshes and the changed shell mesh are checked for closed,
  oriented, connected topology. CAD checks exercise pins, harness and the actual
  existing body/boot; reverse-key and undersized-bore controls must interfere.
  The shortened key must miss the early block, reproducing the unsafe geometry.
  The jacket's intended saddle bearing is separated from the clearance screen;
  its exit/diameter/position are checked analytically. Pin/wire paths still have
  full-shell collision checks. This is nominal harness fit, not a full pin-motion
  or slack qualification.
- Seven regression tests reject the old shallow dock/high key, lost contact,
  spring bottoming, lost flange capture and excessive wire curvature.

The first boot intersection used its print frame; it was corrected by restoring
the source's assembly transform. A nominal jacket/saddle bearing line is an
intentional contact and is screened separately. A tangent head pocket caused a
CGAL manifold warning despite a passing exported-STL edge check; the lower relief
removes that zero-thickness edge. All three rejected checks are preserved under
`evidence/`. Final mesh export requires both a clean CAD diagnostic and STL topology.

PC/plastic dimensional errors of ±0.05mm, 0.03mm differential axial thermal
movement, key/boot placement and individual USB lead bounds are assigned
requirements. Manufacturer process capability is not confirmed. The collar's
existing r11 thermal screen is preserved; this external dock has not been qualified
over that full temperature/tilt/load domain. Physical stroke, force, material
creep, screw torque, wire retention and contamination remain open.

## Reproduce

```sh
python3 scripts/check_charge_dock.py
python3 -m unittest discover -s tests -p test_charge_dock.py -v
python3 scripts/export_charge_dock.py
python3 scripts/make_charge_dock_sheet.py
python3 scripts/verify_charge_dock.py
```

The exporter needs OpenSCAD and takes several minutes. Read-only verification
needs standard Python and the saved artifacts. Preserve r12 and the all-green
r05l board/Gerber; this revision does not change PCB copper or manufacture files.
Source values, evidence and remaining qualification flags are explicit in
`dock.json`, `checks.json` and `mesh-checks.json`.
