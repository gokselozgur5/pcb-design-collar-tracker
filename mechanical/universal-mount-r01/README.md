# Adjustable collar attachment and complete 3D view

Open [viewer.html](viewer.html) in a browser. It works offline and shows the
assembled tracker, exploded layers, attachment underside, PCB envelopes and
separate mount parts. Drag to rotate, scroll to zoom, or select a collar example.
The [overview](design-overview.png) and [PDF](design-overview.pdf) show the design
without requiring a 3D application. The [actual PCB render](pcb-top.png) comes
from the current KiCad r05m source; four missing package models are dimensional
visual substitutes, as recorded in [visual provenance](visual-provenance.json).

This is a prototype design for an adjustable attachment. It replaces the old
12–25 mm collar-loop concept with two independent wrap straps and interchangeable
grip pads. The existing rigid housing, gasket, PCB and internal assembly remain
unchanged. No holes are added to the housing's pressure boundary.

## Dimensions and checked examples

| Item | Nominal dimensions |
| --- | --- |
| PCB | 40 × 32 × 0.84088 mm; six copper layers |
| Rigid body with closed lid | 57.4 × 49.4 × 21 mm |
| Rigid body including charging key | 61.4 mm overall X |
| Flexible outer holder | 60.8 × 52.8 × 27.3 mm |
| Holder with charging key projection | 63.1 mm overall X |
| Holder and flat pad | 29.6 mm overall Z before the collar |
| Holder and V-groove pad | 33.8 mm overall Z before the collar |
| Wrap strap section | 10 × 1.4 mm; keeper 14.6 mm wide and 4.4 mm high |
| Strap lengths | 120 mm short / 220 mm long; paired holes at 5 mm pitch |

| Collar example | Pad | Strap option |
| --- | --- | --- |
| Flat 8 × 1 mm | Flat | Two short |
| Flat 25 × 3 mm | Flat | Two short |
| Flat 60 × 8 mm | Flat | Two long |
| Round Ø4 / Ø8 / Ø16 mm | V-groove | Two short |

Those six cases are checked nominal examples, not validation of every size
between them. There must be a clear collar segment spanning both strap stations,
whose centres are 35 mm apart. Buckles, rivets, D-rings, chain links and decorative
features can obstruct the attachment. A common electronics design does not prove
that this size or weight is comfortable for every dog, especially very small dogs.

## Parts to make and assemble

The source [mount.scad](mount.scad) is parametric OpenSCAD in millimetres.
Select `part="boot"`, `"flat_pad"`, `"round_pad"` or `"strap"`; choose the strap
length with `strap_length`. The delivered STL files use millimetres and have
their lowest point at Z=0. They are meshes, not editable STEP boundary models.

| Delivered part | Quantity per tracker | Purpose |
| --- | --- | --- |
| [boot.stl](boot.stl) | 1 | Flexible holder with two blind anchor tunnels |
| [flat_pad.stl](flat_pad.stl) | 1, for a flat collar | Ribbed grip surface |
| [round_pad.stl](round_pad.stl) | Alternative to flat pad | V-groove support for a round collar |
| [strap_short.stl](strap_short.stl) | 2 when selected | 120 mm strap with two buttons, holes and keeper |
| [strap_long.stl](strap_long.stl) | 2 when selected | 220 mm version of the same closure |

For a fit prototype, the holder and straps need flexible material; start with
TPU around Shore 95A and a softer grip pad if available. These are starting
process choices, not qualified material specifications. Do not print the holder
in rigid resin and expect its lip to stretch over the housing. Tunnel ceilings
and the strap keeper need a suitable flexible-print process and inspected
clearance. A moulded silicone/TPU production version needs separate tooling and
material/closure validation. The printed outer holder is not the water seal.

1. Fit the chosen pad's two locating nubs into the blind underside sockets.
2. Feed the free, perforated tail of each strap through one downward slot, across
   its anchor tunnel and out the second slot. Keep the buttons and keeper outside
   the tunnel; their wider section is not intended to pass through it.
3. Seat the closed tracker inside the holder and engage the upper retaining lip.
   The side window exposes the charging targets and key. New-holder compatibility
   with the existing charging dock has not been checked; remove the holder before
   docking for the initial prototype.
4. Place the collar against the pad. Wrap each strap independently, engage two
   adjacent holes on its two buttons, and pass the spare tail through the keeper.
   Keep the closure accessible, with no hard fittings trapped against the dog.
   At least 5 mm of tail must remain beyond the keeper. Secure excess tail before
   wear; do not use the device as a leash attachment.

The [closure length screen](closure-screen.json) checks hole reach and remaining
tail for the six examples. It demands about 1.73–8.70% strap extension, which is
not yet a measured working strain or holding force. The installed 3D bands show
their centreline routing and section. The flat strap files contain the actual
buttons, holes and keeper; the scene does not simulate their deformed overlap.

## Existing internal assembly

The view uses the current r16 body/contacts/terminals, r11 lid, r12 retained-pack
carrier and r18 retainer/cable routes, plus the r19 staking envelopes. The battery
is the requested 32 × 30.5 × 5.3 mm pack envelope, not a supplier-approved pack.
The internal PCB sits at Z=10.4 mm. Package envelopes in the assembly view are
conservative simplifications; use the separate KiCad render for copper and
package appearance. Antennas are the current CAPH/ZETA placement envelopes.
Lead wires are hidden when layers separate to avoid implying stretched cables.

## Verification and limits

- [33 exported meshes](mesh-checks.json) have closed, oriented surfaces. Each of
  the five new printable parts is one connected surface.
- [25 nominal interference queries](fit-checks.json) contain no positive-volume
  intersection between holder/housing, straps/holder, straps/collar, pad/straps
  and pad/collar. Exact grip-rib contact produces only CGAL edges and an empty
  84-byte STL; that contact is recorded, not treated as a broken delivered mesh.
- The failing initial pad is retained under `evidence/initial-flat-pad/`.
  It penetrated the flat collar by about 5.01, 15.02 and 25.03 mm³ and had tangent,
  disconnected ribs. The corrected ribs overlap their base and end at the collar
  contact plane. No clearance rule was relaxed.
- [Browser checks](viewer-checks.json) cover all five views, six collar examples,
  layer separation, transparency, reference image, camera input and mobile width.
  The single-file viewer starts from `file://` with external network blocked.

These checks establish exported geometry and example fits. They do not establish
closure retention, wet grip, fatigue, snag resistance, long-term comfort, actual
weight, RF performance or water protection. IP68 remains a design target.
The original PCB/PCBA release status and manufacturing files are unchanged.

The next physical step is a holder/pad/two-strap fit sample with an inert dummy
housing: verify threading, lip retention, closure pull/cycle behavior, wet grip
and comfort before an animal wears a powered prototype.

## Reproduce

From the repository root, `scripts/prepare_universal_visuals.py` builds an ignored
visual-only PCB copy without changing the native manufacturing source. The
current rendering was made with KiCad 10.0.7 and OpenSCAD 2021.01.

```sh
python3 scripts/export_universal_mount.py solids
python3 scripts/export_universal_mount.py checks
python3 scripts/export_universal_mount.py previews
python3 scripts/build_universal_viewer.py
node scripts/check_universal_viewer.cjs
python3 scripts/finish_universal_mount.py
python3 scripts/verify_universal_mount.py
```

The portable ZIP preserves repository-relative STL imports for `mount.scad`.
The offline viewer needs no server or installation. It embeds Three.js 0.180.0;
its MIT license and pinned download hash are in `viewer-assets/`.
