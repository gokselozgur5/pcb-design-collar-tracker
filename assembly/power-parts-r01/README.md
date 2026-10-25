# Selected power components

The r05 power circuit had unspecified precision/high-value 0402 resistors and
unqualified timing-capacitor assumptions. This review selects exact prototype
parts, includes tolerance/TCR and leakage in the calculation, and preserves the
old circuit/model. It is implemented in
[r05k](../../experiments/power-r05k-selected-parts/README.md).

## Selections

| Ref | Selected value / MPN | Tolerance / TCR | Maximum body height |
|---|---|---|---|
| R1 | 22 kΩ — RC0402FR-0722KL | 1% / 100 ppm/°C | 0.40 mm |
| R16, R20 | 10 kΩ — RC0402FR-0710KL | 1% / 100 ppm/°C | 0.40 mm |
| R17 | 200 kΩ — RT0402BRD07200KL | 0.1% / 25 ppm/°C | 0.35 mm |
| R18 | 26.1 kΩ — RT0402BRD0726K1L | 0.1% / 25 ppm/°C | 0.35 mm |
| R19 | 3.4 MΩ — RC0402FR-073M4L | 1% / 100 ppm/°C | 0.40 mm |
| R21 | 22 Ω — CRCW040222R0FKEDHP | 1% / 100 ppm/°C | 0.40 mm |
| R22 | 1 MΩ — RC0402FR-071ML | 1% / 100 ppm/°C | 0.40 mm |
| R23 | 100 kΩ — RC0402FR-07100KL | 1% / 100 ppm/°C | 0.40 mm |
| C9, C25 | 1 µF / 16 V X7R — GRM21BR71C105KA01L | 10% | 1.35 mm |
| C26 | 47 nF / 16 V X7R — GRM155R71C473KA01D | 10% | 0.55 mm |

R17/R18/R19 previously specified 1 MΩ / 130 kΩ / 16.9 MΩ. The checked YAGEO RT
0402 25 ppm/°C range ends at 240 kΩ; the original 1 MΩ precision choice was not
established. The lower-impedance network uses exact manufacturer-listed values
and reduces input-leakage sensitivity. It adds a calculated 13.39 µA at 3.6 V,
or 0.321 mAh/day, in the nominal unloaded divider comparison. This excludes IC
consumption and is not a device-runtime measurement.

The previous C25, GRM219R71E684KA88, is NRND in the retrieved manufacturer catalogue.
C25 now shares the in-production 1 µF part with C9. This increases the reset delay;
it does not change the copper. The greater height passes the existing populated
fit screen with a 0.60 mm minimum gap to the battery reservation.

R21 uses the pulse-proof 0.2 W series. The model's 1.9 V / 12 µF discharge stores
21.66 µJ and initially dissipates about 0.167 W. This exceeds its simple 85°C
continuous derating slightly, so continuous wattage alone is insufficient.
The reviewed continuous-pulse graph exceeds the conservative 0.5 W / 10 ms
screen; full stored energy is included in average power and the decay tail is
retained. Actual board thermal conditions still require validation. Its recommended
0.60 × 0.60 mm lands at 1.05 mm pitch differ from the existing 0.54 × 0.64 mm
lands at 1.02 mm pitch; reflow acceptance of the existing footprint is open.
[Vishay datasheet, revision 17-Mar-2026](https://www.vishay.com/docs/20043/crcwhpe3.pdf).

## Reproducible calculation

```sh
python3 scripts/check_power_parts.py
python3 -m unittest discover -s tests -p test_power_parts.py -v
```

The [input selection](selection.json) and [report](component-check.json) distinguish
manufacturer limits, typical curves and engineering assumptions. Source URLs,
retrieval dates and document hashes are in [manufacturer-sources.json](manufacturer-sources.json).
Downloaded documents remain in the ignored local runtime; a fresh checkout can
verify the saved calculations from the committed numeric inputs and data extracts.

| Conditional result | Initial tolerance + TCR | Additional 0.5% independent resistance-drift sensitivity |
|---|---:|---:|
| Falling threshold | 3.244–3.432 V | 3.215–3.462 V |
| Restart threshold | 3.417–3.734 V | 3.387–3.767 V |
| Recognized-fault reset delay | 2.057–10.121 s | Same capacitor/timer inputs |
| Guaranteed-low ENABLE interval | ≥1.960 s | ≥1.958 s |
| GPIO supply-enable after ENABLE high | ≥26.08 ms | ≥25.50 ms |
| Latest GPIO enable after POWER_GOOD | 643 ms | 674 ms |
| Maximum RESET sink-current screen | 0.897 mA | 0.901 mA |

The temperature calculation spans −40 to +85°C around a 25°C reference. This is
an electronics analysis range, not an approved battery, charging or product range.
Resistance endpoints sum initial tolerance and independent TCR extremes. The
extra 0.5% drift scenario is an engineering sensitivity, not a service-life claim.

PG-high drop now includes inverter leakage, RESET leakage, feedback and the
declared ENABLE/SENSE load, including the source-leakage sign. The RESET-low
sink budget includes pull-ups, MR current and the initially charged C9.
TPS3808's unspecified minimum hysteresis is taken as zero.
[TI TPS3808 datasheet](https://www.ti.com/lit/ds/symlink/tps3808.pdf),
[TI inverter datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc1g14.pdf).

The provisional firmware rule is to wait at least 1 s after boot before accessing
the switched-domain peripherals, then verify/recover I2C and initialize the fuel
gauge and accelerometer. The old 600 ms wait fails the model. The 1 s value still
needs powered startup/ramp validation and is not implemented firmware.

## What is still conditional

Murata's 10 mVrms curves include temperature and selected DC bias. Their minima,
then −10% initial tolerance and a further −15% engineering loss allowance, give
654 / 687 / 33.3 nF for C9 / C25 / C26. The model retains 600 / 600 / 32 nF minima.
These are typical-curve screens, not guaranteed lot/aging bounds. CT charges to
about 1.23 V, rather than to the 5.5 V system-rail maximum. The timer scaling is
extrapolated from TI's specified 180 nF delay endpoints; verify selected values on
assembled hardware. [Murata aging guidance](https://www.murata.com/en-global/support/faqs/capacitor/ceramiccapacitor/char/0006).

The source-retention calculation assumes a stable supply until strict shutdown
finishes. It does not prove operation during abrupt collapse. Nordic permits late
VDD_GPIO fall when undefined GPIO states are acceptable; see the
[sequencing follow-up](../../docs/power-sequence-followup.md). No actuator is added,
but firmware/off-state interface behavior remains a separate acceptance item.

UVLO does not disconnect the battery. At a nominal 3.3 V fault rail, R16 and R20
alone can draw about 660 µA with their outputs clamped near zero. Protected-cell
cutoff, charging recovery, the actual NTC and cell pulse capability remain required.

Five regressions reject too-short reset/GPIO delays, the former firmware wait and
excessive ENABLE load, and independently compare divider KCL with its passive
equivalent. They validate calculations; no powered, RF, assembly or IP test is claimed.
