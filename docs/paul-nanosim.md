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

The current overrides are J6 (127,108), D1 (126.8,116.2), J5 (125,125),
R14 (121.5,119), R15 (126,118), C10 (123,115.7), all on B.Cu.
D1 and R14 moved to free local ground-via sites. The ground-stage native DRC has
zero violations/parity and no open GND connections; signal routing remains open.
Power trunks are provisionally 0.4 mm, VIO 0.3 mm, signal minimum 0.2 mm;
via target 0.60/0.20 mm. A width setting is not an ampacity or voltage-drop test.

81 GND pads now connect through short local stubs to 68 through vias. All 68 via
centers are inside the filled GND regions on both In1.Cu and In2.Cu. The longest
planned stub is 2.1071 mm; perimeter nRF ground necks are 0.25 mm to leave clearance
beside the 0.5-mm-pitch contacts. Adjacent IC ground pins may share a local connection;
the planner does not route a ground bus through separate passive components.

Preserve the 0.3.4 source. Its RF segments are locked/copied by the WIP builder;
their original 50 Ω stackup/body/antenna qualification is still open.
