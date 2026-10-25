# r05 supervised-power candidate

This separate revision implements a proposed repair for the three r04i power
findings. **Electrical acceptance remains HOLD.** Native connectivity checks
and conditional timing calculations do not establish powered behavior. The
saved r04i PCB and its two actual zero-warning JLC reports remain unchanged.

The r05 circuit has 71 components including the two existing DNP RF capacitors.
R10/R11/C22 are removed. Of the remaining original connected pins, only R1.1,
U4.3 and U1.73 change nets; 205 retain their original membership.

## Circuit changes

| Block | Implementation | Purpose |
|---|---|---|
| Modem rail | U6 TPS3808G01, R17/R18 divider, R19 feedback | Sense the actual filtered modem rail and add restart hysteresis |
| Restart delay | U6 CT with C25 | Hold the modem disabled after a recognized fault |
| GPIO sequence | R1/C9 and U7 TPS3808G30 | Delay GPIO supply after ENABLE reaches high |
| Shutdown | U8 SN74LVC1G14, dual FET Q1 and R21 | Clamp the LDO enable low and discharge GPIO power before delayed ENABLE falls |
| Battery reading | U9 MAX17048; pull-ups on switched VIO | Replace the continuously connected battery-to-ADC divider with a 1.8 V I2C interface |

The Schmitt inverter tolerates the POWER_GOOD edge; a plain CMOS inverter was
not retained. Both Q1 sources connect to GND, both gates to POWER_FAULT. One
drain discharges VIO through 22 ohms; the other clamps the LDO enable directly.
U9 is supplied from the protected cell. Its alert pull-up is on VIO, not VBAT.
The old analog measurement input becomes a digital alert input. This does not
provide heart-rate sensing or establish state-of-charge accuracy for an unknown cell.

## Checks and limits

```sh
python3 scripts/check_power_r05.py
python3 -m unittest discover -s tests -p test_power_r05.py -v
```

The checker returns **2 for HOLD**, even when its topology and model checks pass.
Use `--refresh --write` after deliberate schematic changes to export the real
native netlist and update derived evidence. Run native all-severity ERC first.
The seven regressions reject restored always-on GPIO power, a battery-powered
GPIO pull-up, wrong FET grounding and inadequate restart/enable capacitance.

The source-bound [calculation](evidence/power-check.json) includes threshold,
resistor, leakage and capacitor bounds, with unqualified inputs named explicitly
in [timing-inputs.json](evidence/timing-inputs.json). Its current conditional
results are:

| Calculated quantity | Bound |
|---|---|
| Falling threshold | 3.249–3.448 V |
| Restart threshold | 3.419–3.756 V; independent population corners, not one part's hysteresis |
| ENABLE guaranteed-low duration after a recognized fault | At least 1.275 s under the declared retained-supply assumptions |
| GPIO enable after ENABLE guaranteed high | At least 32.9 ms under the declared input-load/capacitor assumptions |
| Latest GPIO enable after POWER_GOOD | About 611 ms, before the LDO's actual settling time |
| Fully-on shutdown latency budget after estimated rail discharge | About 0.544 ms for the remaining switch/LDO behavior |
| Conservative rail-retention interval until ENABLE is guaranteed low | About 96.7 ms |

**The supervisor is not an energy reserve.** Abrupt supply collapse can outrun
the sequence. The selected source must sustain the required interval, or the
shutdown architecture must be revised. Short-fault detection/reset of CT,
partial startup, depleted-cell recovery, charger removal and actual switching
latency still require qualification. Do not label these calculated bounds as
manufacturer guarantees or oscilloscope measurements.

Capacitor effective values, the hot FET resistance allowance and the input-load
bounds are engineering assumptions. TPS3808's delay scaling is extrapolated from
specified endpoints; fault propagation/minimum pulse widths are typical-only.
The checks intentionally retain these limitations instead of closing the old
findings merely because named components were added.

Firmware must defer peripheral/modem use until the actual VIO startup has been
validated, recover the I2C bus after power transitions and configure the selected
cell model. Do not quick-start the fuel gauge on every processor reset. A fixed
600 ms wait is shorter than the current calculated upper bound and is not accepted.

## Source and land-pattern review

Manufacturer references and inspected revision identities:

- [Nordic ENABLE](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/enable.html)
  and [power sequence](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/enable_sequence.html):
  ENABLE high/low levels, one-second disable interval and GPIO ordering.
- [TPS3808](https://www.ti.com/lit/ds/symlink/tps3808.pdf), SBVS050N, August 2026:
  DBV pin map, adjustable/fixed thresholds, hysteresis and CT behavior.
- [SN74LVC1G14](https://www.ti.com/lit/ds/symlink/sn74lvc1g14.pdf), SCES218AA,
  October 2025: DCK pin map and Schmitt input characteristics.
- [DMN62D2UDW](https://www.diodes.com/datasheet/download/DMN62D2UDW.pdf),
  DS44897 Rev 1-2, September 2023: dual-FET top view and resistance conditions.
- [MAX17048/MAX17049](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX17048-MAX17049.pdf),
  Rev 7, November 2016: TDFN pin mapping, open-drain outputs, 1.8 V bus thresholds
  and CTG/QSTRT/CELL connections. Supply range is 2.5–4.5 V; the part stays on VBAT.
- [ADI 21-0168 Rev M](https://mds.analog.com/api/public/content/tdfn_21-0168.pdf)
  and [90-0065 Rev E](https://mds.analog.com/api/public/content/tdfn_90-0065.pdf):
  actual T822+3 package and land drawings were inspected. The data sheet explicitly
  references 90-0065. Its listed T822-3C has matching outline dimensions.

The local U9 footprint uses 0.70 × 0.30 mm lands at 0.50 mm pitch, 1.98 mm
row-center spacing and a 0.80 × 1.38 mm exposed pad. Copper follows the drawing.
The proposed 0.02 mm mask expansion leaves 0.16 mm between adjacent mask openings.
Two 0.65 × 0.60 mm paste apertures cover about 70.7% of the exposed pad; the
assembler must qualify that stencil. Other newly assigned standard footprints,
exact passive AVL, solder process and part availability remain review items.

## PCB continuation

The native candidate is in `hardware/`; it is not a manufacturing release.
Its current SHA256 is
`78df6a520fc978e08451c94e6c6f475877f401867b55c0218802ee3434d193a2`.
The [checkpoint](evidence/routing-checkpoint.json) binds the saved source and
reports. [Top](previews/pcb-top.png) and [bottom](previews/pcb-bottom.png) views
show the unfinished routing; the inherited `CT 0.4` legend still needs the final
revision-label review. [Schematic PDF](previews/schematic.pdf) is the current circuit.

| Saved native result | State |
|---|---|
| Geometry / parity | 0 violations, 0 mismatches |
| Connections | **23 non-GND opens** |
| Local GND / planes | 97 physical pads / 94 unique terminals; 100 vias in both continuous fills |
| Returns / RF | 4 of 99 signal/power vias outside the 2 mm screen; 24 RF segments preserved |
| SIM clamp paths | All four present; no copper bypass of the clamp land |
| Gerber / supplier | None for r05; no transfer of r04i acceptance |

The first placement was rejected for one courtyard overlap and four missing
local ground paths. The revised planner reserves ground escape space before
placing subsequent parts, and retains the 40 × 32 mm outline.

`seed_power_r05_pcb.py` explicitly removes old routing on VBAT, VSYS, VDD_NRF,
NRF_ENABLE and BAT_ADC before assigning changed pin nets. It retains all original
RF/SIM copper. The source-bound placement plan preserves the other footprints;
new ground paths use both continuous inner GND planes. Native DRC/parity and
full routing checks are required after every import.

The router works on a copy with native GND and 230 fixed SIM copper items;
RF geometry is preserved exactly on import. Its geometric approximation may
report fixed-item clearance differences that are absent in KiCad. Only fresh
native checks can accept the resulting board. Never relax native or JLC rules.

The first router/local pass had 26 opens and disrupted previously working signal
interfaces. The current continuation instead recovered 128 original rail items
that clear changed pads and new ground exits; 14 conflicting items were rejected.
Local routing then reached 23 opens, confined to the new power/gauge connections.
Three unused rail tails were removed after preserving every affected native
pad-island partition. Whole-net rip-up is not the next step.

The next placement trial must reserve **signal** pin exits as well as GND exits,
particularly around U6, U7, U9, Q1 and their nearby passives. The existing placement
passes courtyards and copper clearance but leaves several pins in closed routing
pockets. Work in a new isolated revision; do not overwrite this checkpoint or
rerun the initial builders expecting them to recreate the later manual stages.
The source-identical rail recovery and intermediate native snapshots are retained
in `build/` and `evidence/` for comparison. A matching project is required when
loading any snapshot; the report named `ground-invalid-project-drc.json` records
a rejected check run with substituted defaults, not the accepted rule profile.

`scripts/check_kicad_flip.py` checks the corrected BOARD ownership before a
footprint flip and must exit zero. The earlier failing scratch operation never
saved a PCB. A separate observed Python-finalization crash has no proven root
cause; do not present the flip repair as a fix for every historical crash.

Before final Gerbers: complete routing, recheck all local grounds/return vias,
power widths, SIM clamp topology/access, footprints/pad balance and the new
populated enclosure fit. Then obtain two fresh actual JLC analyses of identical
final ZIP bytes. The old r04i DFM result does not transfer to this revision.
