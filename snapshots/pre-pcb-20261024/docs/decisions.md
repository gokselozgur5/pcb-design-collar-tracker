# Design decisions — 2026-10-24 (pre-PCB snapshot)

## Direction at this snapshot

| Topic | Status |
|---|---|
| Türkiye | Owner decision |
| Shared small/light enclosure | Owner target; validate weight and mounting on the smallest dogs |
| eSIM | Owner requirement; provider/profile and physical part open |
| nRF9151 | Draft candidate; qualify LTE-M/NB-IoT service and intended coverage |
| Heart rate | Requested; physical measurement method and sensor unselected |
| Battery, enclosure and board dimensions | Open; runtime between charges unspecified |

500 mAh is not a fixed requirement. The owner asked about a smaller enclosure,
using Apple Watch Ultra as an example. Earlier size estimates are not lower bounds.
Develop the board outline, battery, antennas, sensor contact and enclosure together.
An initial OpenSCAD study exists; there is no physical enclosure. Capacity and charge
interval remain unselected.

## First mechanical study

`mechanical/packing-study.scad` contains two scenarios:

| Scenario | Body | Example battery | Reserved PCB volume |
|---|---|---|---|
| Compact | 38 × 30 × 14 mm | 250 mAh; 32 × 20.5 × 5.3 mm | 30 × 22 × 0.8 mm |
| 500 mAh comparison | 44 × 36 × 14 mm | 36 × 29 × 4.75 mm | 30 × 22 × 0.8 mm |

Both assume a 0.6 mm contact protrusion and exclude collar mounting. These are
research targets, not owner-selected production dimensions.
[EEMB's cell page](https://www.eemb.com/product-130) lists 31 mm length and its
[retail pack page](https://eemb.store/products/lp502030) lists 32 mm; the model uses
the larger value. Both cells are size examples only. Peak discharge, protection,
NTC, cable exit and swelling allowance still need verification.

Reserved volumes fit inside rounded walls, floor and lid without overlap. This is
not actual BOM placement/routing or proof of a working product. Orange LTE/GNSS
blocks are not selected antennas; their real clearances may enlarge the enclosure.
The heart-rate head is hypothetical. Seals, mounts, charging contacts, assembly
and durability remain undesigned. Evidence/reproduction: [mechanical notes](../../../mechanical/README.md).

## What was inspected from Apple Watch Ultra

The first-generation [iFixit teardown](https://www.ifixit.com/News/65598/apple-watch-ultra-is-beautiful-rugged-and-repairability-is-just-within-reach)
and two internal photos were inspected. They show a shaped battery, SiP and flex
connections. iFixit reports antennas integrated with the screen/body. The
[teardown video](https://www.youtube.com/watch?v=b4-lT12eSQs) includes Creative
Electron X-rays; no comprehensive PCB analysis of the video/X-rays was performed.
Photo provenance/hashes: `references/apple-watch-ultra/manifest.json`; images belong
to iFixit.

[Apple's dimensional drawing](https://developer.apple.com/download/files/accessories/dimensional-drawings/apple-watch-ultra.pdf)
shows external dimensions and sensor/charger clearances. This search did not find
a complete Apple-published Ultra schematic, Gerber or editable PCB package; it does
not establish that no such file exists anywhere online.

Design inference: develop battery, outline, antennas and enclosure as one placement
problem. Photos cannot reconstruct electrical connections, layers or RF design.
The [Nordic nRF9151 DK hardware package](https://docs.nordicsemi.com/r/bundle/ug_nrf9151_dk/page/ug/nrf91_dk/intro/kit_content.html)
provides schematic, PCB, BOM and Gerber references. The package itself had not
been downloaded or inspected at this snapshot. A development board's size is
not our product's minimum size.

## Earlier size estimate — not placement validation

The assistant's initial estimate was:

- Electronics PCB: about 30–35 × 25–30 mm, assuming separate enclosure space for
  antennas. Fit was unverified because placement had not been done.
- Main GPS/eSIM body with a 500 mAh-class cell, antenna space and enclosure:
  about 45–50 × 35–40 × 14–18 mm (length × width × thickness).
- Excluded the sensor contact head/electrodes and collar mount. Antenna requirements
  could increase the envelope.
- Not an owner decision, fixed limit or production drawing. Neither 500 mAh nor
  battery life was established.

Dimension references: [nRF9151](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/physical_characteristics.html)
12.1 × 11.1 × 1.2 mm and an [Adafruit 500 mAh example](https://www.adafruit.com/product/1578)
36 × 29 × 4.75 mm. The cell was not electrically selected/approved for pulse current,
NTC or other requirements. Stacking, insulation, wiring, mounting and enclosure
allowances were assumed; RF and actual mechanical assembly were not verified.

## Schematic working assumptions

- nRF9151 provides the application processor, GPS and LTE-M/NB-IoT.
- GPIO/digital sensors use 1.8 V; the SIM uses the modem's separate SIM_1V8 domain.
  These supplies are not tied together.
- A single 4.2 V Li-ion/LiPo cell is a candidate. Cell protection and a cell-contact
  NTC are required; capacity/current limits remain open.
- BQ25185 charger/power-path and TPS7A02 1.8 V regulator are initial candidates.
  The 100 mA charge setting must be recalculated for the selected cell.
- SKY65943-11 is the GNSS filter/LNA candidate, powered at 1.8 V for GPIO-compatible enable.
- LIS2DW12 is the motion-sensor candidate. Acceleration is not claimed to be heart rate.
- A digital interface is reserved for sensor experiments. Animal-contact electrodes
  or optics require a separately designed front end.

## Before placement

1. Turkish operator, LTE-M activation/coverage and eSIM profile delivery.
2. Cell capacity, peak discharge, charge current, NTC and protection.
3. VDD ≥3.0 V under all required conditions; hardware shutdown/restart thresholds.
   Cell protection alone does not guarantee this.
4. VDD/ENABLE/VDD_GPIO sequencing. Nordic recommends ≥6 ms delay; accepting earlier
   GPIO behavior requires explicit review and measurement.
5. Exact eSIM part, 1.8 V compatibility, footprint and profile provider. A generic
   schematic connection is not a concrete eSIM ordering code.
6. GNSS/LTE antennas, enclosure/body effects, RF matching and supplier stackup.
   A 50-ohm netclass name does not validate physical impedance.
7. Heart-rate contact design, comfort and reference-measurement comparison.
8. OTA partitioning and an external-flash footprint if required.

## Primary manufacturer references

- [nRF9151 pinout](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/pinout.html)
- [Recommended circuit and passives](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/schematic_design.html)
- [VDD](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/vdd.html)
- [VDD_GPIO](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/vdd_gpio.html)
- [GNSS](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/gps_if.html)
- [UICC](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/uicc_if.html)
- [BQ25185](https://www.ti.com/product/BQ25185)
- [TPS7A02](https://www.ti.com/product/TPS7A02)
- [LIS2DW12](https://www.st.com/en/mems-and-sensors/lis2dw12.html)

Nordic web documents were read through browser sources; direct downloads returned
403. Failed downloads were not marked successful in the manifest.
