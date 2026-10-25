# Swim-r02: populated board fit

The PCB and its two clean JLC analyses are unchanged. This revision replaces the
blanket component-height boxes with 49 component envelopes at the actual r04i
placements, two factory wire-termination requirements and two bare test-pad areas.
C11/C12 remain DNP. It does not approve the battery, antennas or physical assembly.

Open `review.pdf` for the updated overview and drawing. `populated.png` shows the
board and carrier. Gray blocks are conservative fit bounds, not detailed 3D part
models. Orange blocks include antenna and harness reservations.

## Changes from r01

| Finding | Change |
|---|---|
| D1's native body/land bounds plus the 0.20 mm XY allowance touch the carrier ledge | Extend the SIM-side relief to X=17.6 mm; retain the original case as a failing regression |
| The original M4 nut's full-rotation envelope has -0.041 mm floor clearance and only 0.059 mm to the board including warp allowance | Use an M3 × 0.5 rear thread, 3.5 mm long, with an HFN-M3-A2 thin-nut dimensional candidate; move the contact center from Z=5.8 to 5.5 mm |
| Contact backing hardware intersects the carrier's lower ledge | Add two 0.5 mm-deep underside reliefs; the remaining 1 mm bridge keeps the carrier connected |
| Bare U.FL receptacle height omits the cable plug | Reserve 2.50 mm maximum mated height and a 6 × 6 mm plug footprint requirement; actual antenna cable assemblies must meet both |

The housing remains 57.4 × 49.4 × 17.6 mm, 58.7 mm including the docking key.
The required boot remains 60.4 × 52.4 × 22.4 mm. Main/contact seal dimensions are
unchanged. The dock's pin bores follow the revised contact height automatically.
Use r02 body, carrier, contact and dock files together; do not mix them with r01.

## Evidence and limits

- `components.native.json`: read-only KiCad export of all 55 references, native
  sides/orientations and Fab/land bounds, tied to the tested PCB SHA256.
- `fit-profile.json`: manufacturer height sources, candidate MPNs, explicit
  reservations, carrier reliefs and contact-retention constraints. This is not a
  released AVL or purchasing BOM. Representative RC0402 family dimensions do not
  constitute exact-value electrical approval.
- `populated-fit.json`: all 53 non-DNP entries checked against the carrier,
  cavity, floor/lid, contact backing stack and existing pack/antenna reservations.
  The 0.20 mm XY allowance and 0.15 mm solder + 0.10 mm warp allowances are
  engineering assumptions, not measured factory process capability. Sourced
  dimensions improve Z screening; XY still uses conservative native outlines.
- The resulting maximum fitted envelopes are 2.75 mm above and 1.75 mm below the
  board. The narrowest component clearance is C10 to carrier, 0.24 mm, against a
  0.20 mm screen. J4 and J6 have 0.45 mm to the reserved battery volume.
- `mesh-checks.json`: eight exported closed, oriented, connected STL surfaces;
  an independent CAD intersection must be empty after adding 0.20 mm to component
  bounds. Restoring the old carrier must produce a nonempty interference solid.
- Six regressions cover D1, contact hardware, a taller J4 termination, missing
  profile entries and accidental RF tuning population. Thirty inherited shell
  and seal-envelope checks also pass. None of these are physical tests.

The contact stack must fit within Ø6.4 mm and a 1.0 mm maximum washer/lug thickness
plus the 1.8 mm maximum thin nut. This leaves 0.7 mm exposed M3 thread. The exact
lug, washer, torque, anti-loosening method, coating and strain relief remain open.
The displayed retention cylinder is the full-rotation space claim, not a
manufacturing drawing for a cylindrical nut.

The 1.50 mm J3/J4 termination limits are requirements for the factory harness.
A 2.10 mm J4 termination fails the battery clearance check. Cable routing, bend
radii and service slack are not included in the 53-entry fit pass.
Carrier fit does not prove positive board retention under shock or vibration.

## Next work

1. Resolve the [pack and antenna selection review](selection-review.md), then
   model their actual bodies, feeds, cables and near-metal requirements.
2. Finish factory harness, PCB retention, dock electronics/spring contacts,
   material grades, seal compounds, fastener drawings and torque requirements.
3. Review power/UVLO/VDD_GPIO sequencing and RF/assembly acceptance before release.
4. Build and qualify the final assembly. Swimming is the selected use case;
   2 m fresh water / 60 minutes and magnetic charging remain provisional choices.
   No physical IP6X/IPX8, powered, thermal, mechanical or RF result exists.

The [r01 manufacturing and acceptance notes](../swim-r01/README.md) still apply
except its M4 thread, contact height, carrier and blanket component-height model.
Factory assembly/programming/testing remains required; no end-user soldering.
No order, payment or supplier message has been made.

## Reproduce

From the repository root:

```sh
LC_ALL=C scripts/kicad-python scripts/export_populated_geometry.py \
  experiments/paul-nanosim-r04i-sim-access-40x32/hardware/collar-tracker.kicad_pcb \
  --output mechanical/swim-r02-fit/components.native.json
.venv-dfm/bin/python scripts/audit_populated_fit.py
.venv-dfm/bin/python -m unittest discover -s tests -p test_populated_fit.py -v
python3 scripts/export_populated_enclosure.py
python3 scripts/make_populated_review.py
python3 scripts/verify_handoff.py
```

Geometry checks require Shapely from `requirements-dfm.txt`. The exporter accepts
`COLLAR_GEOMETRY_PYTHON` and `COLLAR_OPENSCAD` overrides. Read-only handoff
verification requires only Python's standard library. STLs are millimeters,
1:1, for fit review; a printable closed mesh is not an ingress-qualified part.

Sources are attached to each height in `fit-profile.json`. The
[GCT D6 drawing](../../references/paul-nanosim-r04/SIM8051-drawing-D6.pdf) is preserved
with its hash. The contact nut dimensions come from the supplier's
[HFN-M3-A2 specification](https://www.accu.co.uk/thin-hexagon-nuts/73054-HFN-M3-A2).
Availability and supplier approval are not implied by selecting a dimensional
candidate.
