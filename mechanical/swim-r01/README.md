# Swim enclosure r01

A serviceable enclosure prototype for the actual 40 × 32 mm r04i PCB. The user
selected swimming and an IP68 design target. **No ingress test has been performed.**
The provisional engineering condition is 2 m of fresh water for 60 minutes; the
user has not yet confirmed depth/time or the magnetic charging preference.

Open `review.pdf` for the review sheet and dimensioned drawing. `enclosure.scad`
is the parametric source. STLs are millimeters at 1:1 scale; disable slicer scaling.
They are fit prototypes, not evidence that printed walls will seal.

## What is designed

| Item | Prototype definition |
|---|---|
| Rigid shell | 57.4 × 49.4 × 17.6 mm, corner radius 4 mm; 58.7 mm including docking key |
| PCB | 40 × 32 × 0.8 mm, bottom surface at Z=10 mm; removable carrier, no new PCB holes |
| Main seal | Continuous EPDM 70 Shore A O-ring, AS568-033 / Parker 2-033; 50.52 mm ID × 1.78 mm section |
| Seal groove | 49 × 41 mm centerline, R6 corners, 2.50 ±0.05 mm width, 1.34 ±0.02 mm depth; bottom R0.2 |
| Closure | Four M2 × 16 screws with captive M2 nuts, outside the main seal; hard mating faces limit compression |
| Charging | Two custom turned targets, each with an independent radial O-ring; J3 receives 5 V and GND |
| Contact seals | 4.50 ±0.10 mm ID × 1.80 ±0.08 mm section; root Ø4.64 ±0.01, bore Ø7.34 ±0.02, groove width 2.80 ±0.05 mm |
| Magnetic alignment | Two Ø3 × 1 mm magnets in external blind slots; no opening into the dry cavity |
| SIM service | Open the lid and lift the PCB carrier; insert/remove the card outside the shell, then reseal |
| Collar mount | Flexible TPU boot, 20 mm collar by default; required to capture the magnet plugs |

The boot is 60.4 × 52.4 × 22.4 mm, with a 2.5 mm strap passage and a
retaining lip. Pull strength, wear, snag behavior and animal comfort are untested.
One electronics design does not yet prove suitability for every dog size.

The first smaller gland left only about 0.28 mm at a cavity corner. The current
shell adds 3 mm in each planar dimension and leaves over 2 mm at that corner.
The first contact groove overfilled at a tolerance extreme; widening it to 2.8 mm
resolves that geometric issue. Regression tests retain both rejected cases.

## What the model actually proves

`parameters.json` is the single dimension source. `build_swim_enclosure.py`
creates the CAD include and `checks.json`, tied to the actual PCB hash. It checks
board/cell corners, vertical reservations, declared seal tolerances, screw/groove
webs, captive-nut walls and contact clearance. It includes cross-section reduction
from stretch and uses torus/annular volumes for contact gland fill.

The shell, lid, carrier, contact, contact seal, magnet plug, dock alignment shell and boot are
actual exported solids. The gasket model is a display of the compressed standard
O-ring, not a custom gasket purchasing drawing. `mesh-checks.json` checks exported
triangle bounds and topology; a closed mesh is not a water-tight physical part.

The green PCB block is the actual board outline, **not a model of all populated
components**. Gray volumes reserve 3.0 mm above and 1.8 mm below it. The battery
reservation is 34 × 23.5 × 5.8 mm around a 32 × 20.5 × 5.3 mm example. The two
30 × 5 mm orange regions are antenna reservations. An approved protected pack
with NTC, real cable exits, antenna drawings, RF clearances and placed component
heights must replace those reservations before releasing enclosure tooling.

## Manufacturing and assembly definition

- Prototype rigid shell/lid: CNC polycarbonate, with the actual material grade
  approved for the chosen seal compound and cleaning environment. Do not use an
  FDM fit print to claim ingress protection. Molded production parts need their
  own draft, shrinkage, flatness and process review.
- Main mating face: target Ra ≤0.8 µm and ≤0.01 mm combined local flatness at the
  seal. Groove surfaces must be free of burrs, chips and machining marks that
  cross the sealing path. The nominal CAD samples the R0.2 groove bottom.
- Contact bodies: custom brass targets with a qualified nickel/gold coating;
  the drawing defines a smooth radial sealing land and rear M4 thread. The STL
  represents the thread's major diameter, not a printable working thread. Break
  sharp assembly edges and apply R0.1 maximum at the groove bottom; include the
  resulting small volume change in supplier review. Bore entrance chamfer is
  required for seal installation; retain the specified straight sealing length.
- Each contact needs an M4 thin nut, insulated ring terminal and strain relief
  on the dry side. Positive Y contact is +5 V; negative Y is GND. A factory harness
  connects them to J3. Battery/NTC harness connects to J4. Wire terminations and
  programming belong to factory assembly; no end-user soldering is intended.
- Select actual screw head/nut drawings to fit the declared recesses. The lid
  closes against its hard stop. Set torque by prototype clamp/creep trials and
  verify the seam closes evenly; no production torque has been qualified.
- Retain magnets with the modeled plugs, qualified encapsulation and the boot.
  The bottom-entry blind slots remain outside the dry cavity and lid groove.
  The boot blocks plug escape; use it for the magnetic-contact prototype. Opposed pole orientation assists
  alignment; the asymmetric key prevents the intended dock from rotating 180°.
- The supplied dock is an alignment shell only. Spring contacts, USB power
  wiring, current limiting and reverse-polarity protection remain to be selected.
  Use a dry, current-limited 5 V fixture for future bench charging tests.
- Fit the SIM before closing the shell. Provide service slack so the carrier can
  lift out without detaching soldered wires. Keep wires away from the main groove.
  Clean and inspect seals after every opening; validate repeated service cycles.

The SUNMON 904-00002 catalog candidate was not selected: its linked drawing says
IP65, despite broader waterproof wording on the product page. That is insufficient
support for this immersion target. The custom contact proposal still needs its
own coating, resistance, sealing and durability qualification.

## Prototype acceptance plan

1. Inspect CNC dimensions, surface finish, seal compound/certificate and actual
   electronic/pack/antenna fit. Re-run the geometry checks after any substitution.
2. Assemble an empty shell with the final contacts, seals, screws and harness
   penetrations. Check closure, SIM service and repeated opening before immersion.
3. Run the provisional 2 m / 60 min fresh-water engineering immersion with the
   charging interface unmated. Record water/device temperature, orientation,
   elapsed time, internal moisture indicator and pre/post inspection. Retest
   after mechanical and service-cycle conditioning; any ingress is a failure.
4. Commission the applicable IEC 60529 IP6X and agreed IPX8 tests on the final
   assembly. The lab must define the complete procedure and acceptance conditions.
   The standard's full test procedure was not purchased or reproduced here.
5. Validate the powered assembly: battery protection/NTC, sealed charging thermal
   behavior, connector corrosion/contact resistance, RF/body performance and
   collar retention. Fix and repeat affected tests before release.

There is no dust, immersion, pressure, drop, pull, thermal, powered or RF result.
No order, payment, supplier message or certification request has been made.

## Reproduce

From the repository root:

```sh
python3 scripts/build_swim_enclosure.py
python3 -m unittest discover -s tests -p test_enclosure.py -v
python3 scripts/export_swim_enclosure.py
python3 scripts/make_swim_review.py
```

The exporter regenerates all eight meshes and three previews, then verifies the
actual STL bounds and oriented edges. For a single disposable fit variant, use
OpenSCAD directly and keep its output separate from this checked checkpoint.

Other `part` values: `lid`, `carrier`, `contact`, `contact_seal`, `dock`, `boot`,
`magnet_plug`, `assembly`, `exploded`, `section`, `mounted`. Supported collar widths
are 12–25 mm. For a 25 mm collar boot, add
`-D collar_width=25`. Review fit/strength again; it is not an automatic approval.

## Sources and their limits

- [Parker O-Ring Handbook PTD5705](https://www.parker.com/content/dam/Parker-com/Literature/Praedifa/Catalogs/Catalog_O-Ring-Handbook_PTD5705-EN.pdf),
  printed pages 10, 20 and 47: face-gland guidance, section tolerance and standard
  size table. The displayed dimensions and numerical screens above are our
  prototype calculations; Parker has not reviewed this enclosure.
- [IEC 60529](https://webstore.iec.ch/en/publication/2447): IP classification scope.
- [TÜV Rheinland IP testing](https://www.tuv.com/japan/jp/about-us/laboratories/global-technology-assessment-center-(gtac)/ip-testing/):
  IP6X dust protection and IPX8 immersion under specified conditions.
- [SUNMON drawing](https://smeconn.com/wp-content/uploads/2025/12/904-00002.pdf):
  the rejected candidate's stated IP65 limit.

Dimensions are engineering proposals. No source gives this assembled product an
IP rating, and its PCB DFM passes do not qualify its enclosure.
