# r04i power-domain review

**HOLD: the existing board has three open electrical findings.**

This review reads the actual KiCad schematic and checks 148 unique power-related
pins against the saved board geometry. See `power-review.json` for the actual
count and input hashes. It does not change r04i or invalidate its PCB-only DFM
results. It does prevent interpreting those results as electrical acceptance.

Reproduce with the committed inventory and Python's standard library:

```sh
python3 scripts/audit_power_architecture.py
```

Exit code **2** means the evidence reproduced but electrical acceptance is HOLD.
An exception means the inventory, source or topology changed and needs review.
To regenerate the inventory from native KiCad and update the derived report:

```sh
LC_ALL=C python3 scripts/audit_power_architecture.py --refresh --write
```

The XML is exported into an ignored temporary directory. The committed inventory
contains component values, pin/net membership and the schematic hash, without
absolute machine paths. No network or powered device is involved.

| Finding | Actual circuit | Consequence |
|---|---|---|
| PWR-01 | U3 SYS → FB1 → U1 VDD; R1 pulls ENABLE toward VDD, with no independent undervoltage control | The charger cutoff does not establish the modem's required voltage margin |
| PWR-02 | U4 IN and EN both connect to VSYS; its output powers U1 VDD_GPIO | Neither start-up delay nor ordered shutdown is implemented |
| PWR-03 | VBAT → R10 2 MΩ → U1.73, with R11 1 MΩ to ground | The ADC remains driven when the GPIO supply is absent; off-state leakage needs review |

## What the calculations establish

The three positive-rail copper paths total about 32.29 mΩ under the existing
35 µm copper / 20 µm via plating / 20°C estimate. At an illustrative 500 mA,
3.01 V at J4 would become about 2.994 V at U1 even if the charger and ferrite had
zero loss; U3's BAT pin would still be about 3.005 V. The charger has a **typical**,
not min/max-qualified, 3.0 V battery
cutoff. This is a counterexample to a claimed guaranteed margin; it is not a
measured failure or a worst-case component model. Cell, contact, ground-return,
ferrite, IC and transient losses are not included.

R1 10 kΩ and C9 100 nF give a nominal 1 ms time constant and 2.207 ms to 89% of
an ideal supply step. The separately specified LDO startup time is 0.75 ms typical
and 1.2 ms maximum at its stated 1 µF / 1 mA test load. The real VIO net has
7.1 µF nominal capacitance and other loads, so these numbers are **not** a transient
simulation of this board. They cannot demonstrate the recommended GPIO delay.

At a nominal 4.2 V cell, the unloaded divider presents 1.4 V. Its top resistor
limits available current to at most 2.1 µA before the lower resistor and input
clamp are considered. That bounds a potential feed path; it does not establish
actual clamp current, device damage or acceptable battery drain.

The nominal charger settings are consistent: 18 kΩ selects 4.2 V / 500 mA input
limit and 3 kΩ gives 100 mA charging. These do not approve a battery, NTC curve,
temperature range or charging-interface protection.

Manufacturer URLs, revision identities and interpreted inputs are in
[review-inputs.json](review-inputs.json). Nordic's [VDD guidance](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/vdd.html),
[GPIO guidance](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/vdd_gpio.html)
and [ENABLE requirements](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/enable.html)
define the relevant limits. The
[charger](https://www.ti.com/lit/ds/symlink/bq25185.pdf) and
[LDO](https://www.ti.com/lit/ds/symlink/tps7a02.pdf) data sheets supply component
parameters. The local PDF hashes identify what was inspected; downloading a later
revision must not silently replace those inputs.

## Next circuit revision

Preserve the released source. Before routing a successor, implement and review:

1. Modem-rail supervision with threshold tolerance, load-step headroom and a
   controlled restart; cell protection alone is insufficient.
2. A GPIO startup/shutdown strategy. Either enforce the recommended ordering, or
   explicitly review every driven peripheral and off-state feed path under
   Nordic's permitted undefined-state exception. No exception is accepted here.
3. An ADC path that cannot sustain an unintended powered rail after shutdown.
4. At least one second with ENABLE low after a shutdown, including a brief brownout
   and battery rebound. A nominal delay calculation is insufficient.
5. Recovery with a depleted cell and charger connected, abrupt charger removal,
   transmission pulses and unpowered debug/external interfaces.

TPS3840 and TPS3899 were examined as supervisor candidates, not selected parts.
In particular, the [TPS3899 delay-capacitor guidance](https://www.ti.com/lit/ds/symlink/tps3899.pdf)
warns that short faults can leave timing capacitors partly charged and shorten
the next delay. Do not equate a nominal one-second RC delay with a guaranteed
one-second disable interval. A supervisor alone does not resolve GPIO ordering
or battery-ADC backfeed. No repair, new PCB DFM or physical validation is claimed.
