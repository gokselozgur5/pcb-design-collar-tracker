# r05i — RF stack and routing candidate

The six 50-ohm port nets now use 0.36 mm main tracks. Two short module escapes
remain 0.20 / 0.28 mm to fit the fixed pin pitch. The GNSS elbow moves away from
a SIM supply via's reference-plane opening. No pads, vias, component positions,
non-port tracks, schematic connections or DRC limits changed.

The six FEM interstage matching segments stay at 0.20 mm. They are part of the
SKY65943 input matching network, not independent 50-ohm port routes.

[Before / after review](evidence/rf-review.pdf) ·
[Gerber ZIP](evidence/collar-tracker-05i-rf-40x32-dfm.zip) ·
[JLC report 1](evidence/jlc-check1/report.pdf) ·
[JLC report 2](evidence/jlc-check2/report.pdf)

| Check | Result |
|---|---|
| PCB | 40 × 32 mm, six Cu layers, 71 footprints |
| Native DRC / ERC / parity | Zero findings, including zero open connections |
| JLC PCB DFM | Two independent same-ZIP runs: 0 Danger / 0 Warning / 450 Good each |
| JLC scope | All 29 rows analyzed; unchanged rules; SMT off |
| Ground | 110 GND vias in both continuous dedicated planes; 94 unique terminals locally connected |
| Return screen | All 128 non-GND vias within 2 mm; unchanged from r05h |
| RF reference projection | 1,761 native Contains probes agree; no revised RF track copper projects outside In1.Cu GND |
| Thickness fit | 69 envelopes pass at 0.71, 0.81, 0.84088 and 0.91 mm; old carrier control still fails |

PCB SHA256: `0db809c4ecefbf577db1001164886709708f02ab6ba54f7a572e948583d726a1`.
ZIP SHA256: `f662f1db64ef1958e7e15c63b44869413883fd36e80b82642b9e8262f0e72f2d`.
JLC records: `637347019288170498` and `637347305582972929`.

## Stack decision and limits

Candidate stack: **JLC06081H-7628**, nominal 0.8 mm class, Nan Ya NP-155F.
The [public calculator](https://jlcpcb.com/pcb-impedance-calculator) returned
0.3586 mm for a coated, non-coplanar 50-ohm F.Cu route referenced to In1.Cu.
The prototype rounds this to 0.36 mm. The 2116 alternative returned 0.1814 mm,
below our 0.20 mm minimum; that rule was retained.

| Layer / dielectric | Thickness | Catalog Er |
|---|---:|---:|
| F.Cu | 0.035 mm | — |
| 7628 prepreg | 0.2104 mm | 4.4 |
| In1.Cu, GND | 0.0152 mm | — |
| Core | 0.075 mm | 3.99 |
| In2.Cu, signals/power | 0.0152 mm | — |
| 2116 prepreg | 0.1088 mm | 4.16 |
| In3.Cu, signals/power | 0.0152 mm | — |
| Core | 0.075 mm | 3.99 |
| In4.Cu, GND | 0.0152 mm | — |
| 7628 prepreg | 0.2104 mm | 4.4 |
| B.Cu | 0.035 mm | — |

These values are explicitly recorded in the native board. Copper and dielectric
sum to 0.8104 mm. Adding 0.01524 mm mask on each face gives the CAD model's
0.84088 mm; the supplier label instead says finished 0.81 ± 0.10 mm. The fit
review covers that whole label interval. Do not silently alter the dielectric
stack to force a rounded thickness match.

There are unresolved differences between the catalog, live calculation and
[calculator guide](https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator):
the request uses Er 4.3 instead of the catalog's 4.4, a 0.5 mil width taper instead
of the guide's 0.7 mil, and 1.0 mil base mask instead of 1.2 mil. The guide also
distinguishes nominal copper weight from its calculation thickness. The displayed
0.5% calculation tolerance is not a manufacturing guarantee. Sanitized inputs,
results and screenshots are in [supplier-stack-review.json](evidence/supplier-stack-review.json).
Supplier confirmation, coupon measurements and the real antenna path remain open.

## RF and assembly work still open

[Nordic's ANT guidance](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/ant_if.html)
and [GNSS guidance](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/gps_if.html)
recommend a continuous reference under the route and reduced pad capacitance,
while avoiding exposed noisy routing when opening the plane. Both module RF pads
currently have In2.Cu VBAT copper directly beneath them. In1.Cu remains intact;
opening it without moving that copper would expose the pads to the power route.
This is a documented review item, not a completed pad-capacitance optimization.

- Two stepped module escapes and component lands are impedance discontinuities.
- C11/C12 remain DNP tuning branches; their stubs have not been EM-qualified.
- R3 still has two copper entries on its first pad. Its unique-copper ratio is
  2.09–2.41 across the three contours, versus 2.06–2.35 in r05h. Resolve the junction
  placement or obtain assembly acceptance; PCB DFM does not decide tombstoning.
- C13 ratios are 1.00–1.30 and C14 1.02–1.47. The two DNP shunts are about 1.80;
  fitting them later requires a fresh matching and assembly review.
- Power-path estimates now use 15.2 µm inner copper and the 0.91 mm upper board
  thickness for full-barrel resistance. Plating, load and temperature remain assumptions.
- Exact BOM, power timing, protected pack/NTC, antennas, harness/dock, positive
  retention, firmware, factory programming/test and physical ingress remain open.

**Electrical, RF and manufacturing release remain HOLD.** No physical RF, powered,
assembly or IP68 test occurred. The heart-rate sensor is still unimplemented.

## Reproduce and continue

Preserve this tested revision and r05h. Do not rerun the one-shot seed over either.
Use a new copy for subsequent copper changes and obtain fresh native / supplier results.

```sh
python3 scripts/verify_rf_candidate.py
.venv-dfm/bin/python -m unittest discover -s tests -p test_rf_reference.py -v
python3 scripts/resume.py
```

The RF checker tests the full projected trace area, not only its centerline.
The r05h GNSS route's centerline passes, but 0.006699 mm² of trace copper projects
into a reference opening. The revised elbow closes that geometric gap. This
measurement does not calculate fringe fields or prove 50-ohm impedance.
