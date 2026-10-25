# r05b pin-exit placement — unfinished

The saved native board is the continuation point. **14 open connections, 27
dangling-via warnings and two return-via screen gaps remain.** There is no r05b
Gerber, supplier analysis or manufacturing approval. Electrical release remains
HOLD under the unchanged [r05 circuit review](../power-r05-supervised/README.md).

PCB SHA256: `4c047c3a5b69110ad758f83091236c7aa2c25a96f374732dcd8bda79bb88027e`.
Open `hardware/collar-tracker.kicad_pro`; the saved board, matching project rules,
schematic and local libraries are authoritative. Historical preparation and
placement scripts must not be replayed over this checkpoint.

## What changed

Twenty new or changed parts were placed with every connected pin given a local
exit, including the three changed original pins. The placement reserves 64 exits
and adds 63 vias. U6/U7, U8 and Q1 lands were corrected against the manufacturer
drawings recorded in `evidence/source-land-refinement.json`. This did not change
the circuit, native rules, mask policy or the preserved r04i/r05 boards.

A local route from the refined placement produced 14 open connections. The
separate Freerouting attempt left 24 and is not selected. Twenty-one obsolete
leaf segments were removed only after native pad-island comparisons passed;
19 belonged to the protected placement geometry. The remaining 1,350 protected
items retain their exact UUID and geometry. All 24 original RF segments remain.
The NTC and revision labels were moved/updated without changing their stroke or
font sizes; the final native report has no silkscreen violations.

| Saved check | Result |
|---|---|
| Board | 40 × 32 × 0.8 mm; four copper layers; 71 footprints |
| Native DRC | 14 opens; 27 `via_dangling` warnings; zero other violations or schematic mismatches |
| Ground | 97 physical pads / 94 unique terminals have local track paths; 113 GND vias join both continuous inner GND planes |
| Return screen | 141 of 143 non-GND vias within 2 mm; VIO_1V8 at 2.062 mm and I2C_SCL at 2.255 mm remain |
| SIM | Four paths through their clamp lands, no copper bypass; 19 other bottom-side bodies clear the projected entry lane |
| Existing power backbone | All 12 checked paths remain connected; resistance estimates exclude source, contacts and transient behavior |
| Populated fit | [69 populated envelopes pass](../../mechanical/swim-r03-r05b-fit/README.md), with explicit unresolved part requirements |

Open connections by net: POWER_GOOD 3; VDD_NRF, VIO_ENABLE, UV_SENSE and NRF_ENABLE
2 each; VBAT, FG_ALERT and VIO_DELAY 1 each. The 27 dangling vias are unfinished
pin-exit work, not waived manufacturing warnings. The detailed native report and
source-bound geometry/attachment/passive/SIM/power reports are under `evidence/`.

Native reports use the unchanged inherited project settings. The five inherited
disabled DRC categories are `missing_courtyard`, `track_not_centered_on_via`,
`tuning_profile_track_geometries`, `footprint_filters_mismatch` and
`footprint_type_mismatch`. ERC retains `single_global_label`, `four_way_junction`,
`simulation_model_issue` and `footprint_filter` disabled. This revision adds no
exclusions; the verifier requires identical settings and reports to r05. Results
for those disabled categories are not claimed.

## Next implementation

Local exits did not guarantee a full route through fixed copper. A narrower
low-current VDD_NRF/VBAT branch trial made no changes and left all 14 opens.
Do not repeat that unchanged search or accept the rejected 73 mm FG_ALERT detour.
Inspect free-space barriers and return-only GND stitches in an isolated copy;
relocate only justified obstructions while retaining local ground attachments,
the original working routes, both inner planes, RF and protected SIM topology.
The proposed stitch review has not yet established which vias can move safely.

After routing, finish the two return gaps and passive/footprint reviews, regenerate
native checks and enclosure fit, then export a final package for two fresh actual
JLC runs with unchanged rules. Exact resistor MPNs/tolerances/TCR, effective
capacitor bounds, source retention and powered sequencing remain unqualified.
The 0.40 mm R1/R16–R23 height limits are requirements, not approved parts.

`evidence/routing-checkpoint.json` records the published files. Preparation and
intermediate receipts are historical and carry their own source hashes. Only
`native-drc.json` and the source-bound final reports describe the current PCB.
Disposable native backups and router files stay local; continuation needs only
the saved native project and published evidence. Read-only integrity check:

```sh
python3 scripts/verify_handoff.py
```
