# Pack and antenna selection review

These findings keep unselected parts from being treated as finished geometry.
They are an engineering screen dated 2026-10-25, not purchasing approval or a
claim that no suitable part exists. The 42 × 34 mm cavity and 34 × 23.5 × 5.8 mm
pack reservation are still provisional.

## Protected battery

The nRF9151 guidance calls for roughly 500 mA peak capability at 3.7 V; temperature,
supply voltage and antenna mismatch affect the demand. Capacity alone does not
establish pulse capability. [Nordic power guidance](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/power_supply/maximum_output_power.html).

| Candidate | Verified evidence | Decision |
|---|---|---|
| LiPol LP502030, 250 mAh | Manufacturer drawing specifies PCM, no NTC and 250 mA maximum continuous discharge | Do not release it for this design without a suitable pulse/voltage qualification and an NTC-equipped pack drawing |
| EEMB LP502030 | Bare-cell/product dimensions were found; the linked full pack PDF returned 404 | Do not assume the dimensions include PCM/NTC or prove discharge capability |
| Varta EasyPack S, 56455 701 014 | Handbook lists a protected 660 mAh pack with NTC, 43.5 × 35.4 × 5.8 mm | Does not fit the present 42 × 34 mm cavity or battery reservation |

Sources: [LiPol pack drawing](https://www.lipolbattery.com/LiPo-Battery-Datahseet/LiPo_Battery_LP502030.pdf),
[EEMB product](https://www.eemb.com/product-130),
[EEMB pack sizing FAQ](https://www.eemb.com/faq-6),
[Varta handbook](https://www.varta-ag.com/fileadmin/varta_storage/publications/Technical_Handbook_CellPac_LITE_Rev._2.6.pdf).

The pack procurement drawing must include PCM, NTC characteristic, harness,
polarity, dimensional tolerances and swelling allowance. It must support the
actual modem pulse waveform over the intended temperature, state-of-charge and
aging range while keeping the module rail above its minimum. The present
100 mA charging setting remains provisional. Do not bypass protection or replace
the NTC with a fixed resistor to make a candidate appear compatible.

## Antennas

The two old 30 × 5 mm rectangles are reservations, not real antenna drawings.

| Candidate | Manufacturer dimensions / integration evidence | Decision |
|---|---|---|
| 2J 2JF1424P LTE | 40 × 20 × 0.2 mm; ground dependent; published measurements use a 110 × 40 mm ground and 38 mm coax | A possible experiment, not proven on this 40 × 32 mm ground plane. Cable orientation and ground geometry need design review and measurement |
| Taoglas FXP14 LTE | 70 × 20 mm footprint | Does not fit flat inside the current cavity |
| KYOCERA AVX 1002289 LTE | 53.6 × 25.1 mm footprint | Does not fit flat inside the current cavity |
| Antenova Bentoni SRFG017-100 GNSS | 40 × 14 × 0.15 mm, ground independent, 100 mm cable | Fits neither 30 × 5 mm reservation. Full assembly drawing and metal/cable clearance must be checked before selection |
| Taoglas FXP611 GNSS | 38 × 37 mm footprint | Does not fit flat inside the current cavity |

Sources: [2J datasheet and integration note](https://www.2j-antennas.com/media/original/datasheets/2jf1424p.pdf),
[Taoglas FXP14](https://www.taoglas.com/product/fxp14-2g3g-cellular-flexible-pcb-ipex-mhfi-2/),
[KYOCERA AVX 1002289](https://www.kyocera-avx.com/product/lte-cellular-wide-band-fpc-embedded-antenna-1002289/),
[Antenova Bentoni](https://www.antenova.com/bentoni),
[Taoglas FXP611](https://www.taoglas.com/product/cloud-fxp611-gps-glonass-compass-flexible-pcb-2/).

Do not infer RF performance from a dimensional fit or transplant the published
efficiency from a larger reference ground. Do not fold an antenna without an
approved bend/integration drawing. The next antenna choice needs the actual
Türkiye service bands, connector/plug drawing, feed and cable route, enclosure
material and body-loaded RF evaluation. Body proximity and wet fur belong to the
evaluation, along with GNSS reception and cellular operation during movement.
