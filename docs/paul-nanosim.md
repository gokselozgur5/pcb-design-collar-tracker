# Paul review and nano-SIM revision

These are the applicable requirements from Paul's earlier GIMP review, adapted to
this different PCB. The earlier GIMP board's acceptance does not validate this one.
The source review was the archived 2026-09-24 second-review record and GIMP v0.1.6
implementation. Company board files are not copied into this personal repository.

| Review point | Collar action | Acceptance still needed |
|---|---|---|
| GND vias connected by long tracks | Short pad-to-via connections; planes carry GND | All grounds connected, short stubs, no long serial ground bus |
| Two GND core layers | Reserve In1.Cu and In2.Cu for GND | No inner signal/power tracks; inspect actual filled planes |
| Return beside signal via | Add local GND vias | Screen all non-GND vias at ≤2 mm; review RF/ESD needs individually |
| Broken power pours / thin paths | Size continuous power traces | Trunks, pad escapes and worst-case current/drop reviewed |
| Unbalanced copper on small passives | Avoid excessive copper on one end | Inspect both pads, width/count/length of copper attachment |
| Awkward angles and detours | Clean local routing | DRC plus actual geometry inspection |
| SMT and useful labels | Real SMT SIM socket; clear interface labels | BOM/CPL/body/card clearance and supplier assembly acceptance |
| Jumpers, USB/CAN connectors, mounting pattern | GIMP-specific details | Do not add irrelevant circuits or blindly copy hole coordinates |

The 2 mm screen came from the earlier implementation; Paul did not establish a
universal numerical RF limit. More than 2 mm is a review candidate, not by itself a
demonstrated product failure. Fewer vias is not the goal; connected local returns are.

## Socket and ESD

GCT SIM8051-6-0-14-00-A is the no-peg SMT nano-SIM candidate. Manufacturer drawing D5
was inspected locally; revision D6 was subsequently obtained from Mouser and its
full drawing and enlarged land pattern were also inspected. The relevant dimensions
match. Do not add the optional peg holes to this part. Verify insertion and
removal access before placement acceptance. Reference files and hashes are in
`references/paul-nanosim-r04/sources.json`.

| Socket pin | Function | Board net |
|---|---|---|
| 1 / C1 | VCC | SIM_1V8 |
| 2 / C2 | Reset | SIM_RST |
| 3 / C3 | Clock | SIM_CLK |
| 5 / C5 | Ground | GND |
| 6 / C6 | VPP | Unconnected |
| 7 / C7 | I/O | SIM_IO |
| 8 (two physical lands) | Shield | GND |

Contact lands: 1.00 × 1.10 mm at x = −2.54, 0, +2.54 and y = ±5.90 mm.
Shield lands: 1.00 × 3.00 mm at x = ±5.30, y = 0 mm.
Coordinates are component-side drawing coordinates, before bottom-side placement.
Central keepout: x = ±3.575, y = −2.15 to +2.70 mm. Six 1.20 × 1.00 mm
wiper keepouts: x = −2.54, 0, +2.54; y = −4.15 and +3.45 mm.
The builder expresses these as side-specific copper/pad/track/via keepouts.

TI TPD4E1U06DCKR is the four-channel SIM ESD candidate (SC70-6): pin 1 reset,
6 clock, 3 SIM supply, 4 data, 2 GND and 5 NC. Check TI's package drawing against
the project footprint. Connector → ESD → modem routing and the ESD ground return
must be short; adding a named component alone does not verify ESD protection.

[Nordic's UICC interface](https://docs.nordicsemi.com/r/bundle/ps_nrf9151/page/ip/radio_lte/doc/simif_lte_m/frontpage.html)
requires external ESD for a removable card and uses native 1.8 V Class C UICC.
SIM supply is not VIO_1V8. Power the modem down before card removal; this design
does not implement hot-swap/card-detect behavior.

[Turkcell NB-IoT](https://www.turkcell.com.tr/kurumsal/dijital-is-servisleri/iot-nesnelerin-interneti/nb-iot)
is an activated M2M service. A physical nano-SIM does not turn nRF9151 into a
general LTE Cat-1 modem or establish moving-dog coverage. Operator, plan and
mobility behavior still need qualification. These are open product checks.

## Existing candidate placement

The active 40 × 32 mm source is `experiments/paul-nanosim-r04g-returns-40x32/hardware/`.
The 35 × 28 mm r04e source is preserved separately.
J6 (127,108), D1 (126.8,116.2), J5 (125,125), R14 (121.5,119),
R15 (126,118) and C10 (123,115.7) are on B.Cu. Charger U3 is at (105,123)
on F.Cu; C17 is at (106.2,120.25) on B.Cu, C18 at (103,120.85) and C19
at (101.8,122.5) on F.Cu. J4 is at (106,126.05) on B.Cu.
The current stage has zero open connections, violations, warnings or parity
findings. Two return-via screen gaps remain. Two actual JLC PCB DFM runs pass
at 0/0; see STATUS for their exact source, ZIP and supplier identities.
Power trunks are provisionally 0.4 mm, VIO 0.3 mm, signal minimum 0.2 mm;
via target 0.60/0.20 mm. A width setting is not an ampacity or voltage-drop test.

The initial r04 ground stage connected 81 GND pads through 68 vias. The current
r04g rework uses 86: its native inventory finds all 86 centers inside both saved
inner fills, each with one filled outline and no inner tracks. U3.4 joins its own
exposed GND pad. Perimeter nRF ground necks are 0.25 mm to leave clearance beside
the 0.5-mm-pitch contacts. Adjacent IC ground pins may share a local connection;
do not route a ground bus through separate passive components. The original
2.1071 mm maximum planned stub is historical, not a final r04g measurement.

Preserve the 0.3.4 source. Its RF segments are locked/copied by the WIP builder;
their original 50 Ω stackup/body/antenna qualification is still open.

## Placement review and corrections

The [GCT product page](https://gct.co/connector/sim8051) identifies a push-pull
socket, with no card-detect switch. Rechecking the complete D6 component-side
drawing against native bottom-side pad coordinates resolved an earlier mistake:
the original angle of 0 degrees already points the opening toward y=100, near
C1/C2/C3 at y=102.1. D1, C10 and R15 are behind the closed end. The rejected r04c
180-degree rotation pointed the opening inward and is not used in r04d.
Do not repeat that rotation. This establishes the drawing direction; final
enclosure access, card removal and physical fit still need qualification.

The [TI datasheet](https://www.ti.com/lit/ds/symlink/tpd4e1u06.pdf), DCK0006A
drawing 4214835/D, gives a land/paste example of 0.90 × 0.40 mm, 0.65 mm pitch
and 2.20 mm between row centers. r04d now uses that example, with 0.05 mm corner
radius, matching local library and native footprint. The earlier KiCad-derived
1.025 × 0.35 mm lands / 1.675 mm row spacing are retained only in older sources.
This footprint correction does not establish assembly acceptance or ESD layout
quality. Review connector-to-ESD-to-modem topology and the short ESD ground return
after the final routing changes.

[Nordic's VDD guidance](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/vdd.html)
sets a routing DCR target below 0.1 Ω and calls for local filtering, decoupling and
low-impedance grounds. Measure actual path widths/lengths and supply droop; a
0.4 mm netclass setting does not establish compliance. Battery, ferrite, vias,
copper thickness and dynamic supply impedance must be distinguished from trace
resistance alone. `scripts/audit_power_paths.py` estimates centerline copper and
via-barrel resistance from a hash-matched geometry export; it excludes ferrite,
IC, contact and cell impedance, pad spreading, transients and thermal behavior.
The current r04g report includes the connected J5 supply branch and its remaining
power-review limits.
The earlier snapshot's estimate is preserved as `power-path-routed1-review.json`.
Rerun the audit after routing changes; complete power qualification remains open.
