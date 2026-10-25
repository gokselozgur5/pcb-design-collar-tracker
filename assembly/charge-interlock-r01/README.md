# Hardware charge-temperature interlock

The r05l circuit replaces the grounded BQ25185 charge-enable pin with a
VSYS-powered temperature window. This implements the correction identified in
the [preserved r05k battery review](../pack-charge-r01/README.md). The PCB and
schematic implement the circuit; assembled electrical qualification remains open.

Two TLV3012B push-pull comparators compare BAT_NTC against separate reference
dividers. A SN74LVC1G00 NAND drives active-low /CE. Both comparators must report
valid temperature to enable charging. Their specified low POR outputs command
disable through the NAND after its supply is valid. The MCU and switched VIO
rail do not control this permission. Slow ramps and the supply-invalid interval
still require bench measurements.

| Item | Implemented choice |
|---|---|
| Hot comparator / divider | U10; R24 196k / R25 49.9k; nominal threshold 0.2520 V |
| Cold comparator / divider | U11; R26 27.4k / R27 49.9k; nominal threshold 0.8018 V |
| Logic / fail-state bias | U12 NAND; R28 /CE pull-up; R29/R30 comparator-output pull-downs |
| Local capacitors | Three 100nF bypasses, two 1nF reference capacitors, one 1nF TS capacitor |
| Candidate sensor | SEMITEC 103JT-025, 10k/B3435, bonded to the cell; attachment not selected |
| Charge settings | Existing 4.2 V / 100mA charge / 500mA input limits retained |
| Open / short sensor | Steady-state cold / hot invalid respectively; charging disabled |

The [source inventory](sources.json) identifies manufacturer documents and the
downloaded PDF hashes. The two TI DCK land patterns use the manufacturer's copper
dimensions; DFM repairs did not shrink lands, drill diameters or annuli.

## Calculation and remaining assumptions

`python3 scripts/check_charge_r05l.py` checks native exported net membership,
original-pin preservation and the temperature model. The four regressions include
the original 50°C failure, restored grounded /CE and reversed cold-input polarity.

| Screen | Result |
|---|---|
| Nominal sensor window | 6.29–36.21°C |
| Possible-enable window across declared corners | 3.22–42.64°C |
| Guaranteed-normal window within this model | 9.41–30.63°C |
| 45°C cell, sensor reading 43°C | 2.58mV disable margin |
| 0°C cell, sensor reading 2°C | 45.45mV disable margin |
| Previously permitted 50°C case | Disabled at the modeled corners |

These are conditional calculations, not guaranteed complete-device limits. The
model includes resistor tolerance/TCR plus 0.5% drift sensitivity, reference error
and drift, comparator offset/hysteresis/PSRR/CMRR, and NTC R25/B variation with an
additional curve allowance. The published R/T table is interpolated in inverse
kelvin and log resistance. A 100nA input-leakage allowance is an engineering
assumption: the comparator's tabulated pA specification is at 25°C only.

The 2°C cell-to-sensor allocation includes temperature gradients and lag; it must
be demonstrated with the selected pack and sensor attachment. The hot-side margin
is small enough that this allocation and full-temperature leakage matter. Verify
the sensor curve, comparator output levels at actual VSYS, /CE loading, TS bias,
startup, brownout, absent battery, low-cell recovery and sensor insertion before
charging a production pack. The NAND's additional current with intermediate input
levels is excluded from the illustrative branch-current estimate; that number is
not a maximum or a battery-runtime prediction.

No protected pack is selected. The previously reviewed EEMB PCM is rated 350mA
continuous despite the bare cell's 700mA rating. Full pack current, protection,
recharge recovery, factory NTC attachment and the actual modem load remain
selection requirements. No single-component-fault safety certification is claimed.

## Layout review

The new circuit adds 16 parts. All 71 prior footprints retain their position,
orientation and land geometry. Only original pin U3.4 changes net. The local VIN
transfer is rerouted to let /CE escape; the 27 existing RF segments, stack, rules
and keepout definitions remain unchanged. Dedicated In1/In4 GND planes and local
ground connections are checked on the final PCB, not inherited by assertion.

C31's raw segment-width sum flags 2.5:1 because overlapping segments are counted
separately. Unique-copper contour ratios are 1.107 / 1.582 / 1.662 at
0.05 / 0.15 / 0.30mm offsets; both maximum individual exits are 0.4mm. This is a
documented reflow-review cue, not a passed SMT process test. C11/C12 are DNP and
C20's existing attachment is unchanged. Supplier stencil/reflow acceptance remains
open for all fitted parts.

The final Gerber passed two JLC PCB analyses with unchanged rules, 29 analyzed
rows and 0 Danger / 0 Warning / 455 Good each. SMT analysis was off. Native DRC,
ERC, opens and schematic parity are zero. See the
[r05l source and reports](../../experiments/power-r05l-charge-interlock/README.md).
