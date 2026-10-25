# Pack and antenna selection — 2026-10-26

The prototype antenna choices are **Synzen CAPH SZK-C-3L30** for LTE and
**ZETA SZK-C-0G04** for GNSS. Both use the existing U.FL interface and a nominal
100 mm cable. The [r08 assembly](../../mechanical/swim-r08-antennas/README.md)
places their actual size classes and routes both cables at the native connectors.
This is a mechanical prototype selection, not RF or purchasing acceptance.
The [external candidate BOM](external-candidate-bom.csv) keeps these parts separate
from the unchanged 81-reference PCB BOM; the unselected battery is not disguised
as a purchasable line item.

| Item | Manufacturer information | Design treatment |
|---|---|---|
| CAPH | 30 × 15 × 0.2 mm; 100 mm MHF1 cable; product page specifies 1.13 mm coax | 30.7 × 15.7 × 0.4 mm envelope. Drawing omits tolerances; assigned allowances require confirmation. |
| ZETA | 40 × 10 × 0.2 mm; drawing gives ±0.3 mm in-plane and 100 ±2 mm cable; 1.13 mm coax, MHF1 | 40.7 × 10.7 × 0.4 mm envelope. Cable tolerance fit is not yet established. |
| MHF1 mating | Existing J1/J2 are Hirose U.FL-R-SMT-1(10) | Existing 2.5 mm mated-height envelope retained. Exact supplied plug exit datum still needs confirmation. |

Sources: [CAPH Rev A](https://synzen.com.tw/uploads/product-specs/CAPH-SZK-C-3L30---Datasheet---4G-LTE-NB-IoT-FPC-Adhesive-Antenna---Rev-A.pdf),
[CAPH product page](https://synzen.com.tw/products/caph),
[ZETA Rev A](https://synzen.com.tw/uploads/product-specs/zeta-szk-c-0g04---datasheet---gnss-fpc-antenna---rev-a.pdf).
Document identities and reviewed pages are in [sources.json](sources.json).
Downloaded originals are not redistributed.

CAPH's Rev A table says 3M 868, while its mechanical page and product page say
3M 468. The web page also contains a PETRA2 name typo. Confirm the supplied adhesive
and cable configuration. Both antenna reports use 2 mm ABS and RF chokes; their
performance numbers do not transfer to this populated, sealed, body-worn assembly.
The enclosure lid is 2.5 mm. Test both antennas together, with the real battery,
housing, wet fur and intended collar position before RF release.

## Battery decision

No reviewed pack is released for purchasing. The battery block in r08 remains a
reservation; no larger pack was quietly substituted.

| Complete pack | Established facts | Decision |
|---|---|---|
| VARTA EasyPack S 56455 701 014 | 660 mAh nominal / 630 mAh minimum; 1.26 A continuous; integrated 10k ±1%, B3435 ±1% NTC; 43.5 ±0.2 × 35.4 ±0.2 × 5.8 ±0.2 mm | Does not fit the current reservation/cavity. The 100 mA charger and nominal six-hour timer also need a new charge budget. Not selected. |
| Akyga LP403035 / AKY1581 | Complete assembly maximum 39.5 × 31 × 4.5 mm; advertised cell discharge 2C, 400 mAh | Pack is larger than the reservation. Reviewed document does not provide a PCM continuous-current/threshold table. Not selected. |
| Akyga LP403035 / AKY1604 | Complete assembly maximum 37.5 × 31 × 4.5 mm; cell table lists 5C, 400 mAh | Same missing PCM characterization; identical cell names are not interchangeable pack specifications. Not selected. |
| EEMB LP503030-PCM-LD | Previously reviewed PCM: 350 mA continuous, 1 A for 3 s; bare cell: 700 mA | Still fails the inherited 600 mA continuous headroom screen. Reassess using the actual load waveform; this screen alone does not prove incompatibility. |

VARTA data comes from its [current design library](https://www.varta-ag.com/fileadmin/varta_storage/downloads/products/power/cellpac-lite/design-library/VARTA_Design_Library_EASYPACK_S_56455_701_014.zip),
Rev 1-0225. Its protection thresholds differ from older 099-pack publications;
do not reuse those older electrical values. The current library still includes
099-named mechanical files, so production geometry also needs confirmation.

At 100 mA, six uninterrupted hours provide at most 600 mAh before CV taper or
other reductions. A 90 mA example provides 540 mAh. This identifies a charge-budget
problem for an empty 630–660 mAh pack; it is not a measured charge test or a claim
that every pack always times out. The [BQ25185](https://www.ti.com/lit/ds/symlink/bq25185.pdf)
has a nominal 360-minute safety timer and ±10% fast-charge accuracy under its stated
conditions. Its 10%-of-charge-current termination also differs from VARTA's
recommended 6.3 mA endpoint. No charging resistor was changed in this revision.

The 600 mA continuous target is an engineering allowance, **not a Nordic requirement**.
Nordic describes approximately [500 mA peak at 3.7 V](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/power_supply/maximum_output_power.html).
Average-current tables cannot establish worst-case pulse duration or recovery.
The next pack decision needs a bounded operating profile, loaded voltage/drop,
PCM transient/recovery behavior, temperature and charge compatibility. Do not
keep enlarging the enclosure solely to satisfy an invented continuous load, or
approve a smaller pack from a peak-current headline alone.

No supplier was contacted, and no order, payment or account change was made.
