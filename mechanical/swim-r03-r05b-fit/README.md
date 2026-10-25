# Preliminary r05b populated fit

This revision applies the existing swim-r02 shell/carrier geometry to the actual
[r05b PCB](../../experiments/power-r05b-pin-exits/README.md). Its 71 footprint
profiles include two DNP capacitors; all 69 populated envelopes pass the declared
dimensional screen. The 30 analytical shell/seal checks also pass. These results
do not release the parts, assembly or IP68 performance.

PCB SHA256: `4c047c3a5b69110ad758f83091236c7aa2c25a96f374732dcd8bda79bb88027e`.
The native export, populated-fit report, shell checks and preview are bound by
`checkpoint.json`. `populated.png` shows conservative body boxes, antenna
reservations and the pack reservation; it is not a finished assembly model.

Maximum component envelopes, including solder and warp allowances, remain
2.75 mm above and 1.75 mm below the board. The smallest checked component gap is
C10 to the carrier, 0.24 mm against the 0.20 mm target. The original carrier still
fails the negative control at D1. Rigid body size remains 57.4 × 49.4 × 17.6 mm,
58.7 mm including the key; the boot envelope is 60.4 × 52.4 × 22.4 mm.

New supervisor, logic, MOSFET, gauge and capacitor heights cite manufacturer
drawings in `fit-profile.json`. R1/R16–R23 instead carry nine explicit 0.40 mm
height requirements: exact resistor MPN, tolerance and TCR remain unresolved.
Do not treat those dimensional assumptions as sourcing approval. Selected pack,
NTC, antennas, feeds, harness, dock electronics, positive PCB retention, seal
materials, fasteners and torque remain open, as recorded in the inherited
[selection review](../swim-r02-fit/selection-review.md).

The provisional immersion condition is 2 m fresh water for 60 minutes; this and
magnetic charging remain engineering assumptions. No physical dust, immersion,
RF or powered testing has occurred. The eight mesh checks and CAD intersection
acceptance of r02 are preserved for that revision only; no new r03 mesh package
or independent CAD boolean acceptance is claimed.

To refresh this preliminary screen after a deliberate PCB change, first export
its current route geometry, then run from the repository root:

```sh
python3 scripts/build_swim_enclosure.py \
  --parameters mechanical/swim-r03-r05b-fit/parameters.json \
  --output mechanical/swim-r03-r05b-fit
LC_ALL=C scripts/kicad-python scripts/export_populated_geometry.py \
  experiments/power-r05b-pin-exits/hardware/collar-tracker.kicad_pcb \
  --output mechanical/swim-r03-r05b-fit/components.native.json
.venv-dfm/bin/python scripts/audit_populated_fit.py \
  --directory mechanical/swim-r03-r05b-fit
```

Never regenerate the preserved r02 fit while working on r05b. Refresh the preview
and file manifest after all inputs settle. `python3 scripts/verify_handoff.py`
checks saved identities; it does not run a new physical test.
