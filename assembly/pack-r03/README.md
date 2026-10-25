# Battery request and fit study

**CT-BAT-001-A is a supplier request, not an approved battery. No enquiry has been sent.**

The [request](request.json) defines one complete pack interface instead of leaving
the battery as an unspecified block. The [email draft](supplier-request.txt) is
ready for review. It does not commit to an order or invent a supplier part number.
The proposed recipient is `DesignMyBattery@eemb.com`, published on EEMB's
[custom-pack page](https://www.eemb.com/custom). Sending the enquiry requires
separate user authorization under this repository's `AGENTS.md`.

The [r09 CAD study](../../mechanical/swim-r09-pack-request/README.md) fits the
requested pack, a flat SEMITEC 103JT-025 sensor and its bond/cover allowance.
Its rigid shell is 57.4 x 49.4 x 21.0 mm, 0.4 mm taller than r08. The main PCB,
contact positions and seal dimensions are unchanged. The active tested PCB and
two actual all-green JLC results remain r05l.

## Why this needs a supplier response

Nordic's [power guidance](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/power_supply/maximum_output_power.html)
describes approximately 500 mA peak at 3.7 V. Its
[PC3 tables](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/vdd_current_p3.html)
are typical averages over a **1 ms TX subframe**, not over an entire reporting
cycle. The same page explicitly describes additional microsecond peaks. Typical
values and a nominal reporting interval do not establish a worst-case load bound.
The 600 mA request is our whole-device engineering allowance, not a Nordic
continuous-current requirement. No network duty cycle or reduced radio power
class has been silently assumed.

The [BQ25185 source](https://www.ti.com/lit/ds/symlink/bq25185.pdf) specifies typical
termination at 10% of charge current: about 10 mA for this board's nominal 100 mA.
The request also discloses its nominal six-hour fast-charge safety timer. These
settings require pack compatibility confirmation; they do not establish a full
charge time or an exact termination limit across conditions.

| Candidate | Established limit | Consequence |
|---|---|---|
| EEMB LP503030-PCM-LD | 350 mA PCM continuous; 1 A for 3 s; 700 mA bare-cell limit | The reviewed pack is not accepted for the 600 mA request. No pulse-repetition or duty approval is inferred. Ask for a controlled complete-pack variant or alternative. |
| Jauch 252538 / LP503030JU | Rev 1.2, August 2024: 450 mAh typical, 430 mAh minimum, 1C maximum pack discharge | Its 1–2.6 A protection-trip range does not authorize that load. Not selected. |
| Jauch 246510 / LP102530JU | Rev 1.2, December 2024: 700 mA maximum pack discharge; 33 x 25.5 x 10.8 mm after cycling | Fits neither the current height budget nor the existing 100 mA/six-hour full-charge budget. Below 15 C charging is limited to 0.2C. Not selected. |
| VARTA EasyPack S 014 | 1.26 A continuous; integrated NTC; 43.5 x 35.4 x 5.8 mm nominal | Requires a larger cavity, mating battery contacts and a revised charge budget. Not selected. |

Sources: [EEMB manufacturer sheet, distributor-hosted](https://macrogroup.ru/upload/iblock/806/l9ka6axlc8lwl5b0dbf2xov43s2g5l33/LP503030.pdf),
[Jauch 252538](https://www.jauch.com/downloadfile/6791ed8abd374f1eabe17db59037d0cd3/matd_252538_lp503030jupcm2icntcmol._78172-3_50mm.pdf),
[Jauch 246510](https://www.jauch.com/downloadfile/677e39d5dc1812655afe7605fec75d931/matd_246510_20200507_680mah_-_lp102530ju_1s1p_2_wire_50mm.pdf),
[current VARTA library](https://www.varta-ag.com/fileadmin/varta_storage/downloads/products/power/cellpac-lite/design-library/VARTA_Design_Library_EASYPACK_S_56455_701_014.zip).
The old VARTA 56417201015 sheet was also found, but its 2008 revision and an
unverified backorder listing do not establish a current supply option.

## Factory interface

| Native pad | Signal | Factory wire |
|---|---|---|
| J4.1 | Protected pack positive / VBAT | Red |
| J4.2 | Protected pack negative / GND, also NTC return | Black |
| J4.3 | Other NTC terminal / BAT_NTC | White |

The checker verifies these assignments against the r05l native netlist. The sensor
return connects after the pack's protection circuit. No bare-cell terminal is
connected around the PCM. All termination and insulation are factory operations;
there is no end-user soldering step. Lead length, wire rating, joint dimensions,
routing and strain relief still need a controlled harness drawing.

The sensor stack uses a 0.15 mm bond budget and 0.10 mm cover budget. Prototype
material candidates are [3M 8805](https://multimedia.3m.com/mws/media/122119O/3m-thermally-conductive-adhesive-transfer-tapes-8800-series.pdf)
and [3M 5419](https://multimedia.3m.com/mws/media/136012O/3mtm-low-static-polyimide-film-tape-5419.pdf?fn=20351_R2.pdf).
Their published typical thicknesses are 0.125 mm and 0.07 mm. Our budgets are not
guaranteed supplier maxima or proof of adhesion to the pack. The sensor's active
area, material compatibility and cell-to-sensor error including thermal lag must
be verified; the charge model's 2 C allocation is still an assumption.

**Next:** obtain a controlled supplier response to this specific request. If its
limits differ, change the design and recheck it. Do not approve the existing
350 mA PCM from average current, a single three-second pulse, or the new CAD fit.
Positive retention, harness/dock and firmware work can proceed independently.
