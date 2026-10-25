# 0.3.4 order-readiness review — 2026-10-25

**This board is not ready to order as a factory-assembled, working device.**
Two JLC PCB DFM reports show 0 Danger / 0 Warning; SMT, electrical operation and
RF are not qualified. The ground layout from Paul's GIMP review has not been fully
applied to this revision. See [STATUS](STATUS.md) for subsequent r04 work.

Reviewed source:
`/Users/gok/codex/projects/collar-tracker/experiments/35x28-clearance-r034/hardware/collar-tracker.kicad_pcb`

- PCB SHA256: `597ebdee59550b6d07eb104274eabee57b038ea6c87da2dec38c1201f78c89b2`
- Gerber ZIP SHA256: `735ff8506629eb931cdd4a1847796e0eae2ec24deebb4f579f7441bb2182c990`
- Neither source nor ZIP changed during this review.
- Reproducible measurements: [audit.py](../evidence/order-readiness-20261025-r034/audit.py)
  and [audit.json](../evidence/order-readiness-20261025-r034/audit.json).

## Layers and connections

The 35 × 28 × 0.8 mm board has four copper layers.

| Layer | Actual copper |
|---|---|
| F.Cu | 446 track segments + GND fill |
| In1.Cu | GND plane; no drawn signal/power traces |
| In2.Cu | 116 signal/power segments + GND fill |
| B.Cu | 230 track segments + GND fill |

Both outer layers carry traces, but this is not yet a
`signal / GND / GND / signal` stack with two dedicated inner references.

There are 78 schematic GND pads. Fresh DRC found no opens or parity issues.
U1's 30 nRF9151 GND pin numbers match [Nordic's list](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/gnd.html).
This review did not recheck every other component's functions against manufacturer
documents. Signal and supply nets must retain their separate schematic connections;
not every net should be GND.

16 of 77 vias are GND. Their centers lie inside saved GND fills on all four layers.
This and zero opens support connectivity, not short/low-impedance returns or
thermal/RF adequacy.

## Comparison with Paul's earlier review

Sources were archived GIMP `CHANGES_v0.1.4.md` (second Paul review),
`CHANGES_v0.1.2.md` (two inner GND layers), `tools/return_vias.py` and
`docs/REVIEW_v0.1.6.md`. These are records from another project, not evidence that
Paul reviewed this collar board.

| Earlier review point | Verified on 0.3.4 |
|---|---|
| Short GND-pad connections to planes; remove unnecessary buses | 206 GND segments, total 151.485 mm, 16 GND vias. Not every segment was classified as unnecessary; local escapes and long links need individual review. |
| Ground-return vias near signal layer changes | Under the inherited 2 mm screen, 9 of 61 non-GND vias pass and **52 fall outside**. Maximum 7.0902 mm: `I2C_SDA`, x127.0031/y105.2826. |
| Two inner ground references | In1 is dedicated; In2 has 116 signal/power segments. A second uninterrupted reference is absent. |
| Solder/thermal balance of two-pad parts | All four zones use solid connections; 77 GND pads inherit this and one explicitly selects solid. Not automatically defective; pad-level copper balance and assembly process were not reviewed. |
| Adequate short/wide power routes | VDD_NRF 0.25 mm; VIN_5V/VBAT/VSYS 0.20–0.25 mm; VIO_1V8 0.20 mm. Current, voltage drop and heating unmeasured. Copying GIMP's 0.4 mm without justification would not validate them. |

2 mm is a historical geometry screen, not Paul's universal numeric requirement or
an RF/EMC standard. The 52 distant vias are not 52 proven functional failures,
but show that the previous return-via check was not completed here. Distances are
straight center-to-center measurements, not solved current-return paths.

[Nordic's stackup guide](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/pcb_stack_up.html?contentId=hAMpO_HZkUUtvaGq7NCRUw)
calls for adjacent dedicated ground references, controlled RF impedance and a
continuous return reference. The effect of In2 traces on bottom-side routing needs
review. This is a source-based review requirement, not a measured RF-loss claim.

## Remaining work before ordering

- **Power and RF:** returns/layers, actual supplier stackup and 50 Ω routes,
  antennas/body/enclosure effects, power-path drop, cell/NTC/protection, UVLO and
  VDD_GPIO sequencing. Nordic's recommended 6 ms delay or tolerance of early GPIO
  behavior has not been verified; see [manufacturer guidance](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/vdd_gpio.html).
- **Functions:** in this baseline J6 is only SIM contacts; actual SIM/profile and
  Turkish operator are unselected. J5 is a digital expansion port, not a heart-rate sensor.
- **Assembly:** 53 BOM entries: 46 fitted parts, two DNP and five contact interfaces.
  30 fitted parts lack exact MPNs. 32 parts top / 14 bottom require double-sided
  assembly. CPL/orientation, U1 stencil and customized U2/U5 lands/masks are unqualified.
- **Working delivery:** battery/antenna connections, solder-free SWD fixture,
  firmware, factory test procedure and enclosure for 35 × 28 mm remain unfinished.

Resolve selections and schematic/power gaps, then ground/RF placement/routing,
new DRC/ERC/DFM/SMT and assembled-prototype acceptance. The review does not prove
35 × 28 mm is final or must grow before the new layout requirements are evaluated.

## Check scope

Fresh KiCad 10.0.7 DRC: 0 violations / 0 opens / 0 parity issues; ERC: 0 violations.
Reports retain default ignored checks: five DRC, four ERC. No rules, severities or
exclusions changed. [DRC](../evidence/order-readiness-20261025-r034/drc.json),
[ERC](../evidence/order-readiness-20261025-r034/erc.json).

No new JLC upload, order, payment, supplier message or powered test occurred during
this review. The two JLC reports refer to the previously delivered identical ZIP.
