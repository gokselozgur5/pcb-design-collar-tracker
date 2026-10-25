# Current state — 2026-10-25

**Active: finish Paul's layout review and the physical nano-SIM revision.**

Repository: [gokselozgur5/pcb-design-collar-tracker](https://github.com/gokselozgur5/pcb-design-collar-tracker).
All repository and GitHub content is English.

**r04h passes native checks and has no remaining return-via screen gaps.
SIM insertion clearance is unresolved, so this is still WIP.**

| Item | Verified state | Evidence under the active trial |
|---|---|---|
| Active source | `experiments/paul-nanosim-r04h-review-40x32/hardware/`, 40 × 32 mm, 55 footprints | `evidence/routing-checkpoint.json` |
| Native checks | Zero DRC violations, warnings, opens, parity findings or ERC findings | `native-drc.json`, `native-erc.json` |
| Ground | All 82 GND pads reach local vias; 90 GND vias join both continuous inner GND fills | `contact-components.json`, `layout-inventory.json` |
| Inner routing / RF | No inner tracks; 24 baseline RF segments retained exactly | `layout-inventory.json`; RF performance remains unqualified |
| Return-via screen | All 91 non-GND vias are within the inherited 2 mm screen | `layout-inventory.json` |
| SIM protection | D1 protects the upper three contacts; D2 protects data. All four paths reach the clamp land without a copper bypass | `esd-paths.json`, `r04g-esd-before.json` |
| Passive copper | C2/C20/C21/R1/R9 attachments reworked; native lands and masks unchanged | `passive-copper-review.json`, `passive-copper-before.json` |
| Mechanical issue | D1 and C10 occupy the projected card-insertion corridor on B.Cu | `card-insertion-review.json`; resolve before release |
| Supplier DFM | No r04h JLC result. The preserved r04g source passed twice at 0/0 | r04g `evidence/jlc-check1/`, `jlc-check2/` |

Current PCB SHA256:
`9c65b1b2f845d76e16e4a2598b5ec0d2894ee1e812cba25a538d53ae0a028aea`.

## Next: clear the SIM insertion corridor

J6 remains at (127,108), B.Cu, angle 0. Its opening faces the y=98 board edge.
The GCT D6 drawing gives an 8.80 mm card width. The nominal projected entry lane
across this PCB is x=122.60…131.40, y=98…101.90 mm, before tolerance/mounting margin.

D1 at (127,99.5) and C10 at (130.6,100.35) are on that side, inside this lane.
The courtyard check does not model the moving card. The placement is not accepted.
Move these bodies outside the swept card volume or to a verified opposite-side
arrangement, then reroute and rerun every affected check. Do not rotate the socket
back inward. Its previously rejected 180-degree orientation was wrong.

The native r04h source is the continuation point. Ignored `.runtime` trials are
not needed to resume. Preserve this checkpoint in a new experiment before editing.
No router or browser process remains running.

After the mechanical fix:

1. Recheck the actual connector → clamp → modem copper topology. Same-net routing
   can reconnect through the connector pad and silently bypass the intended clamp.
2. Refill, rerun all-severity native DRC/ERC/parity, local ground paths, both inner
   fills, return spacing, passive copper and power estimates. Inspect actual views.
3. Review the auxiliary supply paths against their eventual loads. The current
   copper-only estimates include VSYS to J5.3: 39.50 mm / 52.16 mΩ, and VIO to
   J5.2: 57.33 mm / 95.38 mΩ. These exclude cell/IC/contact/ferrite impedance,
   temperature rise and transients; they do not establish powered performance.
4. Export a uniquely named Gerber ZIP. Run two fresh JLC analyses of identical
   final bytes with unchanged rules; inspect all rows, measurements, UI and PDFs.
   Old r04g acceptance does not transfer to r04h or its successor.
5. Update the English handoff, commit coherent changes, normally push and verify.

## Preserved evidence

- 0.3.4 remains unchanged, with its original two 0/0 PCB DFM reports.
- r04g remains unchanged: PCB `e68faf7db8b588cb69afdca76b0ab6b106ad0eed400cc95a2cf140a8f7142f79`,
  ZIP `b739e0baf4286482b9b195b88327967fc1d0db63208c7ec1c8a6d93fe854dc53`,
  JLC records `637221644721938434` and `637222172922957825`. SMT was off.
- r04h `build/return-only-native-clean.kicad_pcb` preserves the earlier clean
  return-only repair, SHA `e2b765df135612d7e47913a534b652deaa59228709d33b572024a0d924b18e07`.
  Its `return-only-*` reports are separate. Use the matching r04g project/schematic
  in an isolated directory if rerunning native checks on that earlier board.

Nano-SIM now, eSIM later. J5 is a digital expansion port, not a heart-rate sensor.
Factory assembly/programming/test is required. No order, payment, supplier
message, powered test or production approval has occurred.
