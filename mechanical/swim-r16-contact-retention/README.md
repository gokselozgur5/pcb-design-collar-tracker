# r16 contact rear retention

The old 6.4mm circular backing reservation was smaller than the 7.34mm contact
bore. It provided no defined rear bearing. r16 adds two custom terminal plates
whose lateral ears bear on recessed faces inside the shell. The front head,
radial seals, external contact positions and outside dimensions remain unchanged.

**Geometric prototype, not a complete charging harness or an ordering release.**
The unchanged r05l PCB/Gerber still owns the two actual 0/0/455 JLC PCB results.
PCB DFM does not validate these machined parts or the assembled enclosure.

## Parts and load path

| Part | Current definition |
|---|---|
| Body | r13 body with two dry-side pockets; bearing faces at X=22.6mm |
| Turned contact | r11 head/gland; 5.9mm stem and 4.8mm M3 x 0.5 thread |
| Positive terminal | CT-CHG-TERMINAL-P-A; canted tail at Y=-3.3, Z=13.3mm |
| Ground terminal | CT-CHG-TERMINAL-N-A; tail at Y=+6, Z=13.3mm |
| Terminal stock | 1mm CuZn30 R480 candidate; tail milled to 0.5mm; matte tin finish |
| Washer / nut | Accu HRDW-M3-A2 / HFN-M3-A2 candidates |

The nut loads the washer, terminal plate and body bearing face against the
external head. The contact shoulder remains recessed, so it does not stop the
nut before the plate bears on the shell. The plate's two ears bridge the bore;
the 6mm washer only spreads the nut load onto the plate. These plates are custom
machined parts, **not Keystone 4004 lugs** and not printable plastic parts.

Contact Y=-6 connects to J3.1 `/VIN_5V` through the red lead. Contact Y=+6
connects to J3.2 `/GND` through the black lead. This follows the native netlist
and r13 harness. Do not use the opposite polarity text in the obsolete r01 study.

## Evidence and limits

The calculation checks the axial stack, minimum seal-wall ligaments, two rear
bearing areas per contact, the complete 85-part swept envelope and the requested
pack/cradle. Actual CAD intersections check the existing carrier/retainer and
the body. Exact planar bearing is expected; every exported contact vertex must
lie on the specified plane. The unmodified body must fail the control.

The first positive-terminal mesh failed the unchanged topology check at the
thickness step. Its source and mesh are preserved under `evidence/initial-step/`.
The final source mills the step from one blank, avoiding overlapping cut
extrusions. CAD diagnostics alone are not sufficient to accept an STL.

Plate position +/-0.10mm and its additional 0.05mm thermal allowance are assigned
assembly requirements, not measured production capability. The pocket, contact
and terminal dimensions have separate tolerances in `contact.json`. Geometry
does not establish clamp load, plastic creep, pull strength, vibration resistance,
contact resistance, plating life or leakage. No installation torque is released.
The thin tail and its wire joint also require pull/flex qualification.

The internal red/black wire routes, joint insulation, strain relief and assembly
insertion motion are still **HOLD**. The investigated cubic routes conflict with
an RF lead, adjacent components or each other. Do not cut a production harness
from those drafts. Complete the route and factory process before powered tests.
Factory preparation/assembly is required; no end-user soldering is intended.

All prior sources remain intact. Current wearable parts: r16 body, contacts and
terminals; r12 carrier/cap; r11 lid, retainer, boot, contact seals and magnet plugs.
The r15 dry dock remains unchanged. Contact/lid seal geometry is retained, but
its earlier conditional calculations do not constitute an IP68 result for r16.

## Reproduce

```sh
.venv-dfm/bin/python scripts/check_contact_retention.py
.venv-dfm/bin/python -m unittest discover -s tests -p test_contact_retention.py -v
python3 scripts/export_contact_retention.py
python3 scripts/make_contact_retention_sheet.py
python3 scripts/verify_contact_retention.py
```

The exporter needs OpenSCAD. Saved handoff verification uses standard Python.
Use `contacts.scad` for assembly coordinates. The terminal STLs are translated
to local frames: add `[21.6,-6,2.35]` for positive and `[21.6,+6,2.35]` for ground.
The contact STL retains its local shaft axis; rotate +90 degrees about Y and
translate to `[28.7,+/-6,5.5]`. Body STL uses the enclosure assembly frame.

Next: finish the internal harness and dock holding, obtain the approved pack/lead
exit, then implement firmware and factory acceptance. The battery enquiry is
still unsent. Supplier messages, orders and physical acceptance remain separate.
