# r12 — conditional battery retention

The r11 assembly reserved space for the pack but did not retain it.
r12 adds a cradle to the shell and a cap to the removable PCB carrier.
The pack now sits on the existing floor, 0.3mm below the r09 visualization.
External dimensions, PCB, seals, contacts and antenna geometry are unchanged.

**Prototype review only. No supplier pack, physical retention or ingress approval.**

[Dimensioned review](pack-retention-sheet.pdf) · [Input dimensions](pack-retention.json) ·
[Geometric checks](pack-retention-checks.json) · [CAD evidence](mesh-checks.json)

| Feature | Controlled geometry / requirement |
|---|---|
| Complete-pack maximum | 32 x 30.5 x 5.3mm, including protection, insulation and service swelling |
| Minimum pack for this capture study | 30.5 x 29 x 4.8mm; new engineering requirement, **not supplier-confirmed** |
| Cradle opening / outside | 33 x 31.5 / 34.4 x 33.0mm |
| Pouch support / wall top | Z=1.80 / 7.10mm |
| Retaining cap | Z=7.56–8.31mm; integrated into the PCB carrier |
| Cap clearance cuts | C9, C25, J4, J6 and U7; north tongue retains the remaining capture region |
| NTC / cover | Original requested 26 x 4.1 x 0.5mm sensor; 0.15mm bond and 0.10mm cover budgets |
| Sensor opening | 33 x 11mm central opening; never a pouch-bearing surface |
| Outside dimensions | Rigid 57.4 x 49.4 x 21.0mm; boot 60.4 x 52.4 x 25.8mm; docking key adds 1.3mm in X |

The maximum and minimum pack dimensions are acceptance requirements for an
unapproved custom pack. They do not establish that an available pack fits.
[CT-BAT-001-A](../../assembly/pack-r03/README.md) is unchanged and unsent.
Its supplier response must be reconciled with these added minimum dimensions,
contact regions and lead routing before this carrier can be selected.

## What was checked

- All 85 populated component envelopes against the added cradle, cap and bridges,
  including the r11 assigned board movement and thermal/tolerance allowances.
- Maximum seated pack, four guaranteed overlap regions for the minimum pack,
  full upward pack travel, NTC opening and raised sensor/cover versus the PCB.
- Contact thread/backing envelopes, cavity boundaries and bridge attachment.
- Two newly exported meshes: body and carrier. Seven other parts reuse the
  hash-bound r11 meshes; they were not presented as new exports.
- Actual CAD booleans, including 0.05mm XY / 0.13mm Z expansion of the new cap
  for the component screen, with deliberate failure controls for missing component
  reliefs, a blocked NTC opening and an undersized cradle.
- Seven regressions, including a taller sensor stack that fails only after
  accounting for full upward travel.

The cap bearing and PCB support are part of the same monolithic carrier.
For the lifted sensor check, common floor/carrier translation cancels.
The relative cap-to-PCB height uses the cold carrier scale, 0.10mm total feature
error and an independently hot component-height bound. This avoids combining
physically incompatible cap-up and support-down poses. Component heights already
include the retained solder/warp allowance. The calculation retains the 0.20mm
component-gap criterion; it does not qualify actual thermal gradients or materials.

The initial unrelieved design and failed report are in `evidence/initial-fit/`.
The design was changed to resolve those findings; prior releases and PCB DFM rules
were not changed. Lowering the pack avoids growing the enclosure.

## Assembly and service

1. Inspect the supplier-approved pack, insulation, sensor and defined lead exit.
   Reject dimensions outside the controlled range. Do not compress the pouch to fit.
2. Seat the pack on the clean, smooth cradle floor. No adhesive or rigid preload
   is assumed. The supplier must approve surface contact, edge radii and abrasion.
3. Fit the carrier/cap, keeping the sensor inside its opening. The cap is a travel
   stop, not a clamp. The 0.75mm cap and its bridges need load/creep qualification.
4. Finish the controlled harness routing and strain relief before closure.
   No lead route, contact lug, crimp or solder process is approved by this model.
5. Fit the PCB/retainer and antennas using the preserved r11 procedure. Inspect
   cable clearances and seal surfaces. Never force the lid closed.

All joining, programming and functional testing belong to the factory process;
this work does not introduce end-user soldering. Pack and PCB tilt, impact,
pressure on the pouch, abrasion, adhesive/material compatibility, actual lead
exit, thermal response and assembled water/dust testing remain open.

## Reproduce

Read-only saved verification uses standard Python:

```sh
python3 scripts/verify_pack_retention.py
```

Only regenerate this revision deliberately:

```sh
.venv-dfm/bin/python scripts/check_pack_retention.py
.venv-dfm/bin/python -m unittest discover -s tests -p test_pack_retention.py -v
.venv-dfm/bin/python scripts/export_pack_retention.py
.venv-dfm/bin/python scripts/make_pack_retention_sheet.py
```

`enclosure.scad` preserves the r11 modules and adds the cradle/cap wrappers.
It includes the unchanged r11 parameter, populated-part, cable and retainer files.
Keep those directories together. `pack.scad` and the new dimension include are
emitted by the checker; source dimensions are in `pack-retention.json`.

Next: controlled harness/dock, including actual wire/lug/spring-contact drawings
and a pack lead-exit definition. Supplier selection, firmware, factory tests and
physical ingress qualification are still required for a complete working device.
