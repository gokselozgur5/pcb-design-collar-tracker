# r19 — internal charge-wire support and forming tools

The r18 routes had no defined support at their soldered ends. This prototype adds
three controlled insulating staking volumes: one for both J3 leads and one at
each metal terminal. Two separate open-top nests form the nominal red and black
wires. The PCB, shell, r18 retainer, lid guides and wire routes stay as recorded.

**This is a prototype assembly definition. Holding force, manufacturing and the
working device remain HOLD.** A CAD fit does not establish adhesion or wire life.

## What the factory receives

- [Dimensioned review](restraint-sheet.pdf), [assembly preview](restraint-preview.png)
  and [controlled dimensions/process](restraint.json).
- [Red forming nest](red-fixture.stl) and [black forming nest](black-fixture.stl).
  These are removable bench tools, not parts inside the collar.
- [Staking envelope](staking-envelopes.stl): a dispensing/reference volume,
  **not** a part to print or an instruction to fill the enclosure.
- [Static checks](checks.json) and [CAD evidence](cad-checks.json).

The shared PCB block intentionally contacts both bare leads and the red PTFE
insulation passing above J3. The original conductor-to-conductor clearance remains
mandatory. Bonding to PTFE is not part of the load path. The terminals have their
own separate blocks; the r18 frame reliefs remain necessary.

Each nominal boundary has a combined 0.05mm placement/service allowance. The
minimum filled volume is inset by that allowance; the maximum occupied volume is
expanded. Manufacturing variation, cure shrinkage and temperature/aging changes
must share this budget. No material test yet demonstrates that they do.
The substrate fixes the PCB block's bottom face. Both bounds are engineering
requirements for an incoming process, not demonstrated material or dispensing capability.
The short covered bare sections are 0.7..1.2mm from each PCB tip and 0.9..1.25mm
from each terminal tip. The 0.15mm wire-position allowance is retained.

## Material and factory sequence

DOWSIL 3145 Gray is a candidate. Its manufacturer describes moisture curing
and cautions that adhesion depends on the actual substrates; untreated PTFE is
not a reliable bonding surface. Use representative solder mask, solder finish,
silver-plated copper and tinned terminal coupons. A data-sheet tensile number
does not establish this joint's pull strength. See the
[inspected Dow sheet](https://www.dow.com/documents/11/11-1832-01-dowsil-3145-rtv-mil-a-46146-adhesive-gray.pdf),
pages 2–3, and [source identities](../../references/charge-restraint-r19/sources.json).

1. Inspect wire and terminal dimensions. Use Alpha 2841/7; retain r02's 1.8mm
   terminal strip and 2.4mm PCB strip, both +/-0.1mm. The CAD centerline lengths
   are 43.7658mm red and 54.9209mm black. These are reference lengths, **not a
   qualified cutting tolerance**. Establish cut/strip capability on samples.
2. Form each wire in its labelled nest without pulling it tight. Lift it straight
   out of the open channel. Inspect the released shape and insulation; the nest
   does not compensate automatically for springback or impose the final route.
3. Install and join the wires to the recorded native J3 pads and r16 terminal
   holes. Inspect solder, polarity, resistance and spacing before covering them.
   The solder must solidify without fixture spring force on the joint. Supplier
   joining and cleaning processes require approval; no end-user soldering is specified.
4. With the battery absent, dispense only into the three documented volumes.
   Inspect complete wetting around the specified bare sections and attachment to
   the owning board/terminal. Keep the free spans, components, connectors, seal
   glands and fasteners clear. The outer envelopes include all squeeze-out.
5. Leave the lid open for cure. Plan a minimum 168-hour hold at 21..25C and
   40..60% RH, with representative cure/adhesion witnesses. This is an assigned
   trial process, **not a Dow guarantee of full cure**. Release requires passing
   witnesses and substrate tests, not elapsed time or a tack-free surface.
6. On qualification samples, apply the engineering handling target of 0.5N for
   60 seconds to each lead with its owning substrate restrained. Measure anchor
   displacement (target <=0.03mm), resistance and insulation before/after. This is
   below the wire's 3.914N published maximum pull, but neither number proves a
   solder-pad, plating or adhesive bond. Establish cycling/temperature/creep tests
   and actual installation motion before release.

The [historical NASA workmanship reference](https://s3vi.ndc.nasa.gov/ssri-kb/static/resources/nasa-std-8739.1b.pdf),
section 9, supports documenting intended staking contacts and keepouts. It is not
a certification claim or a claim that this assembly meets a current NASA standard.

## Evidence and limits

All 27 static poses pass 52 added checks each. The narrowest added component gap
is 0.22mm at R6, against 0.20mm. Six regressions reject the earlier oversized
block, the left corner approaching the retainer, underfill, omitted r18 reliefs,
missing conductor ownership and assumed PTFE/physical approval.

Each tool channel is open vertically and its nominal path uses the exact r18
curve. The clearance bound includes the maximum wire diameter, 0.05mm tool
tolerance, polygon facets and a continuous Bezier-to-chord bound. Separate CAD
controls check inflated wire witnesses and deliberately raised channel floors.
The tool is an assembly aid; it does not qualify the inherited +/-0.001mm
**numerical** route-length screen as a shop tolerance.

The imposed captured-curve change reaches 0.426mm for the black PCB lead across
the independent r18 poses. The silicone has not been shown to accommodate that
motion. These are compatible occupied volumes, not a validated elastic motion
solution, retention force or fatigue test. The nest also does not prove transfer
through the open shell or lid closure without disturbing the wires.

Next: resolve continuous/installation motion with these actual attachments and
qualify released wire shape, adhesive bonds and the remaining retainer bridges.
The protected battery, shipping firmware, factory acceptance and powered/RF/water
tests remain open. The unchanged r05l Gerber retains its two recorded JLC passes.

## Reproduce

```sh
.venv-dfm/bin/python -m pip install -r assembly/internal-charge-r03/requirements.txt
.venv-dfm/bin/python scripts/check_charge_restraint.py
.venv-dfm/bin/python -m unittest discover -s tests -p test_charge_restraint.py -v
.venv-dfm/bin/python scripts/export_charge_restraint.py
python3 scripts/make_charge_restraint_sheet.py
python3 scripts/verify_charge_restraint.py
```

The read-only verifier requires standard Python. Regeneration needs the existing
geometry environment, pinned Manifold 3.5.4, OpenSCAD, rsvg-convert and pdfunite.
The nests are built with Manifold; OpenSCAD supplies their engraved labels and
renders the delivered STL files. The mathematical clearance bound and inflated
STL witnesses check the channel definition separately. Preserve the completed
checkpoint and use a successor for changes.
Source links and SHA256 identities are published; the inspected third-party PDF
caches remain local and are optional for read-only verification.
