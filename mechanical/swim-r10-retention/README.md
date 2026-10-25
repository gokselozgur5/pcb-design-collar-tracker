# r10 — captive PCB prototype

The PCB now has a separate retaining frame, four inward tabs and lid stops.
Carrier side rails and four shell locating ribs bound lateral movement. A keyed
projection rejects a reversed retaining frame. This is a **geometric prototype**;
retention force, vibration, wear, material expansion and ingress are unqualified.

[Dimensioned review drawing](retention-sheet.pdf) · [Controlled dimensions](retention.json)

The r05l PCB, its two actual all-green JLC results, CT-BAT-001-A battery request
and every earlier CAD revision remain unchanged. The rigid enclosure is still
57.4 x 49.4 x 21.0mm, excluding its 1.3mm key; boot 60.4 x 52.4 x 25.8mm.
The battery is still an unapproved request and is not retained by this PCB frame.

## Retention and assembly datums

| Feature | Nominal definition |
|---|---|
| Retainer | 41.8 x 33.8mm outer; 40.7 x 32.7mm aperture; 1.2mm frame thickness |
| Inward tabs | Four asymmetric edge contacts; minimum calculated contact area is recorded in the checks |
| Orientation key | Left side, Y=4.2–5.8mm; mates with the carrier slot |
| PCB support plane | Z=10.40mm; candidate PCB thicknesses 0.71–0.91mm |
| Carrier guide aperture | 40.20 x 32.20mm; 0.10mm nominal gap per board edge before tolerances |
| Carrier guide tops / seated retainer bottom | Z=11.50mm |
| Lid stop plane | Z=12.85mm |
| SIM bridge underside | Z=10.70mm; at least 0.20mm above the seated-board underside at assigned axial limits |

[retention.json](retention.json) owns dimensions and manufacturing requirements.
The size tolerances are assigned inspection requirements, not demonstrated printer
or supplier capability. The model includes a minimum zero closing gap at the
worst rigid stack; a part outside those limits must be rejected or reworked before
closing the lid. Do not use the lid screws to force an interfering assembly shut.

The inherited `carrier()` comment mentioning 0.4mm describes the lower support
strip width. Its wording about edge clearance is stale; use the 0.10mm nominal
guide gap above and the controlled tolerance/movement bounds below.

This frame makes the PCB captive; it does not claim zero free play. The worst
modeled top-plane interval is Z=11.06–11.75mm. Carrier-relative XY allowance is
0.20mm and whole-board XY allowance is 0.30mm. Four-tab overlap is also checked
at relative offsets up to 0.45mm and sampled yaw angles of -0.6, 0 and +0.6 degrees.
The frame's stiffness, impact deflection and any anti-rattle treatment still need
physical qualification. Do not present the drawing as a shock or vibration rating.

## Clearance changes

Adding a stop alone was insufficient. Raising the PCB by 0.2mm in the r09 route
reduced GNSS-to-J1 clearance below 0.2mm. One GNSS spline control is raised 1mm;
the actual cable curve moves by less than that. The initial LTE bend is adjusted
0.2mm in X. Both nominal cable lengths are fitted to the existing 98.5mm centerline
requirement, which still depends on unqualified connector/feed datums.

The new checks include 27 endpoint poses with an adjusted initial tangent handle
to preserve cable length. All guide centers remain unchanged across those endpoint
poses. This samples possible cable deformation; it does not prove every continuous
motion or cyclic life. The separate nominal screen still covers four PCB thicknesses.
An additional source-bound check covers the moving paths against the new retention
parts, cavity/lid, both antennas, nonlocal self clearance and the full bottom-side
thickness bound. The existing intentional feed-joint exclusion remains explicit.

The bounded board movement also needs C10/R29 carrier reliefs, larger D1/U12 reliefs
and a 0.3mm support-leg move. The initial U12 clearance failure is preserved under
[evidence/initial-clearance](evidence/initial-clearance/failure.json). Component
swept volumes and retainer movement are checked separately from cable pose samples.
The retainer acts on board edges, not component bodies; no PCB drill hole is added.

The first carrier STL failed its mesh check: 64 triangles collapsed at 0.00001mm,
with 75 invalid oriented edges. [The failed export](evidence/initial-mesh/failure.json)
is preserved. Carrier rails now share the carrier's clipped outer contour and
local Z datum, with internal leg/frame overlap. The mesh acceptance rule is
unchanged; the exporter checks solids before spending time on preview renders.

## Factory sequence and service

1. Complete PCBA assembly, programming and electrical checks before enclosing it.
2. With power disconnected, seat the PCB in the lifted carrier and insert the SIM.
   The bridge clears the card path with the PCB seated. Remove the retainer and
   hold the PCB seated before later SIM service; insertion with a lifted PCB is
   outside this check.
3. Install the controlled pack and factory harness once their definitions are
   approved. Their routing, strain relief and pack retention are still open.
4. Locate the carrier on the shell ribs. Fit the retainer with its key in the
   matching slot. Inspect each tab and the wire paths before bringing down the lid.
5. Fit the antenna cables to their guides, close without pinching a cable or forcing
   the stack, then perform the specified mechanical and sealed-assembly tests.

These are factory operations. This change adds no end-user soldering operation.
The retainer is assembled after reflow, not subjected to the PCBA reflow profile.

## Material and remaining acceptance

Unfilled insulating POM-C, such as
[Ensinger TECAFORM AH natural](https://www.ensinger-online.com/modules/public/sheet/createsheet.php?FILENAME=TECAFORM_AH_natural_18.PDF&FL=18&SID=1344&ZOOM=1.0),
is a prototype retainer candidate. The manufacturer sheet identifies machining
and insulation properties but explicitly treats its values as guidelines. It
does not establish this thin frame's strength or manufacturing capability.
The assigned dimensions are an ambient assembly study. Material selection and
thermal expansion over the operating range must be resolved before ordering;
no thermal fit approval is inferred from room-temperature clearance.

Physical PCB/pack retention, harness/dock, material/seal/fastener acceptance,
firmware, RF/operator tests and powered/water/dust qualification remain open.
IP68 is a design target, not a result of these geometry checks.

## Reproduce

```sh
.venv-dfm/bin/python scripts/check_retention_assembly.py
.venv-dfm/bin/python scripts/check_retention_cables.py
.venv-dfm/bin/python -m unittest discover -s tests -p test_retention_assembly.py -v
python3 scripts/export_retention_enclosure.py
python3 scripts/verify_retention_assembly.py
```

The export verifies actual meshes, cable channels, populated clearances and the
orientation key with failing controls. Read-only checkpoint verification needs
only standard Python; deliberate CAD regeneration needs the geometry venv and
OpenSCAD. Preserve checked revisions and regenerate the source-bound checkpoint
after reviewing a deliberate change.
