# Initial mechanical volume study

This model evaluates PCB, battery, enclosure and antenna space together. It is not
a placed/routed PCB or a production-ready enclosure.

| Scenario | Main body | Height including contact | Example cell dimensions |
|---|---|---|---|
| `compact_250` | 38 × 30 × 14 mm | 14.6 mm | 250 mAh; 32 × 20.5 × 5.3 mm |
| `reference_500` | 44 × 36 × 14 mm | 14.6 mm | 500 mAh; 36 × 29 × 4.75 mm |

Collar mounting is excluded. 250 mAh is not selected capacity; runtime has not been
calculated/measured. The preferred charge interval remains open.

## Model contents

- Yellow: manufacturer/retailer-sized battery example. Protection, NTC, cable exit,
  swelling and assembly allowances are not checked against an approved pack drawing.
- Green: 30 × 22 × 0.8 mm PCB volume, with no actual component placement.
- Dark gray: nRF9151 package, 12.1 × 11.1 × 1.2 mm.
- Other gray blocks: aggregate budgets for power, eSIM, sensors, passives and
  connections. Individual footprints are not placed.
- Orange: requested LTE/GNSS volumes. Antennas, ground plane, RF clearances,
  matching and body effects are unverified. Real antennas may need more space
  or different placement.
- Pink: hypothetical heart-rate head with a 0.6 mm protrusion. Sensor, optics or
  electrodes and animal-contact method are unselected.
- Light gray: 1.2 mm walls/lid. No screws, clips, gasket, charging-contact or
  sealing design. No water-resistance claim.

## Opening and size trials

Open `packing-study.scad` in OpenSCAD. `variant` selects the scenario; `view_mode`
selects `exploded`, `section`, `assembled` or `mockup`.

`compact-250-sizing-dummy.stl` and `reference-500-sizing-dummy.stl` are **solid
sizing dummies**, at 1:1 in millimeters. Disable automatic slicer scaling. They are
not hollow electronics enclosures. Dummy mass does not represent product mass,
since CAD volume does not model battery/electronics density.

`../previews/compact-250-review.svg` is a self-contained dimensioned review sheet,
also available as PNG/PDF. Its displayed/printed image is not 1:1 scale.

## Checks and reproduction

`../scripts/check_packing.py` checks the specified rectangular volumes against
rounded internal walls, floor/lid and each other. It also verifies that the 500 mAh
example is rejected in the compact body. Results: `packing-checks.json`.
It does not read OpenSCAD solids; update dimensions in both files together.
Volume checks do not prove RF performance or manufacturability.

Actual exported STL triangle bounds were measured separately in `stl-bounds.json`;
both dummies match their external dimensions.

From the project root, using OpenSCAD 2021.01:

```sh
python3 scripts/check_packing.py
openscad -o mechanical/compact-250-sizing-dummy.stl --export-format binstl -D 'view_mode="mockup"' mechanical/packing-study.scad
openscad -o mechanical/reference-500-sizing-dummy.stl --export-format binstl -D 'view_mode="mockup"' -D 'variant="reference_500"' mechanical/packing-study.scad
openscad -o previews/compact-250-exploded.png --imgsize 1400,1100 --projection o --viewall --autocenter --camera 0,0,0,65,0,35,140 --colorscheme Tomorrow -D 'view_mode="exploded"' mechanical/packing-study.scad
python3 scripts/make_packing_sheet.py
rsvg-convert -o previews/compact-250-review.png previews/compact-250-review.svg
rsvg-convert -f pdf -o previews/compact-250-review.pdf previews/compact-250-review.svg
```

Sources: [EEMB cell](https://www.eemb.com/product-130),
[EEMB pack example](https://eemb.store/products/lp502030),
[Adafruit 500 mAh example](https://www.adafruit.com/product/1578),
[Nordic package dimensions](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/physical_characteristics.html).
