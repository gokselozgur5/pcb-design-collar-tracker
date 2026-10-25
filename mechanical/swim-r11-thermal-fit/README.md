# r11 — thermal-fit prototype

Four radial keys now locate the retaining frame on the carrier while leaving room
for differential expansion. The shell cavity, PCB guides and lid stops have more
clearance. The PCB and both all-green JLC reports remain unchanged.

[Dimensioned drawing](retention-sheet.pdf) · [Dimensions](retention.json) ·
[Thermal assumptions and sources](thermal.json) · [Calculated results](retention-checks.json)

This is a **conditional geometric prototype**, not a manufacturing release.
The pack is still an unapproved request. Physical thermal fit, load/tilt, connector
strain, materials, sealing and ingress have not been qualified.

## What changed

| Feature | r11 definition |
|---|---|
| Rigid enclosure | 57.4 x 49.4 x 21.0mm; docking key adds 1.3mm in X |
| Internal cavity | 42.4 x 34.7mm |
| Retainer | 41.8 x 34.3mm outside; 40.8 x 33.3mm aperture; 1.2mm thick |
| Locating keys | Four radial slots; the wider west key rejects 180-degree reversal |
| Carrier guide aperture | 40.4 x 32.4mm; component reliefs interrupt the rails |
| Guide / seated frame plane | Z=11.50mm |
| Lid stop | Z=13.00mm |
| SIM lane | Fully open guide span; the old bridge interfered with D1 at admitted lift |
| Charging contact | Smooth stem 7.50mm, shortened 0.20mm to match the wider cavity; seal land and M3 thread unchanged |

D1/U12 reliefs are larger, C10/R29/C33 have local clearance cuts, and two guide
segments clear C29/U12. One carrier leg moves to Y=9.4mm. No PCB drill is added.
The first enlarged-motion candidate and its failing checks are preserved in
[evidence/initial-motion](evidence/initial-motion/failure.json).

## Thermal model and its limits

The model uses -10 to +45°C, referenced to 23°C, with each rigid part allowed to
be at a different endpoint. This is the requested pack operating interval used
for a mechanical screen, not an approved product or storage rating.

[TECANAT natural PC](https://www.ensinger-online.com/modules/public/sheet/createsheet.php?FILENAME=TECANAT_natural_0.PDF&FL=0&SID=1346&ZOOM=1.2)
is the CNC prototype candidate for body, lid, carrier and retainer. Its 80ppm/K
longitudinal value is a guideline over 23–60°C, not a guaranteed cold-temperature
or transverse bound. The manufacturer also identifies stress-cracking sensitivity.

The assigned bounds are 60–100ppm/K for PC, 8–25 for PCB XY and 30–90 for PCB Z.
These are requirements for confirmation or measurement. The actual JLC laminate
has not been confirmed; neither an Isola comparison nor JLC's hosted S1000H sheet
selects a laminate for this order. Water mass uptake is not a dimensional strain.
Moisture swelling, creep, seal compression and chemical exposure remain open.

Under those same bounds the preserved r10 candidate gives negative clearances:
-0.105mm at the X guide/PCB interface and -0.094mm in the closing stack.
The [r10 comparison](r10-thermal-comparison.json) records all seven failures.
These are calculated sensitivities, not measured failed parts.

r11 has at least 0.058mm closing clearance in this model. Opposed keys constrain
frame/carrier translation and in-plane yaw; their calculated pointwise bound is
0.241mm and the component screen reserves 0.25mm. Assigned PCB/carrier and
PCB/body allowances are 0.40mm and 0.76mm; PCB top Z is 11.02–11.97mm.
The guide rotation allocation, parallel-board assumption and real load/tilt behavior
must be checked on parts. This calculation does not certify arbitrary movement.

The 0.05mm axial allocation applies separately to three assembled dimensions:
closed lid-stop height, seated guide height, and frame thickness. For each of the
first two chains, the **sum of absolute errors of its constituent machined lengths**
must be at most 0.05mm; two independent +/-0.05mm part errors are not allowed.
The same allocation applies to the assembled PCB support plane. Inspect these
chains on the actual parts. The model scales the complete error budget by the
largest expansion factor; it does not assume tolerance errors cancel thermally.

All 85 component envelopes clear the modeled solids by at least 0.205mm.
The four tabs overlap the guaranteed interior of the modeled board by at least
0.162mm² each. Contact area alone does not establish strength or retention force.

## Antenna cables

LTE and GNSS paths retain the provisional 98.5mm centerline requirement for nominal
100mm assemblies. LTE's first bend and rear crossing are moved; the GNSS crossing
is raised. Four lid-guide centers remain fixed across the 27 sampled PCB poses.

The pose search adjusts initial tangent length and in-plane plug azimuth. Selected
shapes use -30 to +30 degrees relative to the nominal exit. Minimum sampled
component gap is 0.235mm; bend radius stays at least 3mm and cable separation at
least 0.322mm. Component temperature allowances are included. Separate checks
cover retention solids, cavity/lid, antennas, self-clearance and bottom components.

An admissible curve is not proof that a supplied cable can assume it without
loading its connector. Plug orientation/force limits, actual cable length and
thermal behavior, guide tolerances, lid opening, continuous movement and flex life
remain unqualified. Do not use these samples as a mechanical or RF release.

## Assembly and continuation

Factory assembly/programming/test remains required. Insert the SIM with power off
and the PCB seated in the lifted carrier. Fit the four matching keys and inspect
the tabs, contact backing hardware and cable paths before closing without force.
No end-user soldering operation is introduced.

Next: define battery retention and the controlled harness/dock around the existing
pack request, reconcile the supplier response once sending is authorized, then
close cable/material/process requirements, firmware and factory/physical tests.
The target remains swimming/dust resistance; IP68 has not been demonstrated.

## Reproduce

Read-only saved verification needs standard Python:

```sh
python3 scripts/verify_thermal_assembly.py
```

Deliberate regeneration requires the geometry environment and OpenSCAD. Preserve
checked revisions; do not overwrite them merely to rerun a status check.

```sh
.venv-dfm/bin/python scripts/check_thermal_assembly.py
.venv-dfm/bin/python scripts/check_thermal_cables.py
.venv-dfm/bin/python -m unittest discover -s tests -p test_thermal_assembly.py -v
python3 scripts/export_thermal_enclosure.py
python3 scripts/make_thermal_sheet.py
```

The exporter checks nine actual meshes and eight positive/negative CAD controls,
including swept carrier/retainer clearance and the reversed key. It uses two
independent OpenSCAD jobs at a time. The final saved checkpoint binds source,
calculations, drawings and exports; saved verification does not rerun physical tests.
