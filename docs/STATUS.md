# Current state — 2026-10-25

**Active: finish Paul's layout review and the physical nano-SIM revision.**

Repository: [gokselozgur5/pcb-design-collar-tracker](https://github.com/gokselozgur5/pcb-design-collar-tracker).
All repository and GitHub content is English.

**The current PCB passes native checks and two real JLC PCB DFM runs. Two
return-via screen gaps and the remaining layout review are still open.**

| Item | Verified state | Evidence under the active trial |
|---|---|---|
| Active source | `experiments/paul-nanosim-r04g-returns-40x32/hardware/`, 40 × 32 mm | Native board; `evidence/routing-checkpoint.json` |
| Native checks | Zero DRC violations, warnings, opens, parity findings or ERC findings | `evidence/collar-tracker-04g-preflight-40x32/` |
| Ground | 81 pads have local copper paths to ground vias; 86 GND vias join both continuous inner GND fills | `evidence/contact-components.json`, `layout-inventory.json` |
| Inner routing / RF | No inner tracks; 24 baseline RF segments retained exactly | `evidence/layout-inventory.json`; RF performance remains unqualified |
| Return-via screen | 2 of 88 non-GND vias exceed the inherited 2 mm screen | Same inventory; exact points below |
| Actual JLC PCB DFM | Two fresh runs: **0 Danger / 0 Warning**, all 29 rows analyzed, identical ZIP and unchanged rules | `evidence/jlc-check1/`, `jlc-check2/` |
| Labels | Nine English labels; native minimum 1 mm height / 0.2 mm stroke | `evidence/label-validation.json`, top/bottom review images |
| Production readiness | SMT, complete power/RF/BOM/firmware/fixture/mechanics qualification remains open | `docs/pcba-delivery.md` |

Current PCB SHA256:
`e68faf7db8b588cb69afdca76b0ab6b106ad0eed400cc95a2cf140a8f7142f79`.

Tested ZIP: `evidence/collar-tracker-04g-preflight-40x32.zip`, SHA256
`b739e0baf4286482b9b195b88327967fc1d0db63208c7ec1c8a6d93fe854dc53`.
JLC records: `637221644721938434` and `637222172922957825`.
Both complete PDFs and native top/bottom views were inspected. SMT was unchecked.
This is an intermediate layout package, not a production release or order approval.

## Next: finish the two return gaps

| Signal | Via position (mm) | Nearest GND via |
|---|---|---:|
| SIM_IO | (117.9105, 111.2211) | 2.06496 mm |
| COEX0 | (118.2668, 112.1266) | 2.44752 mm |

The inherited 2 mm value is a screening target, not a universal RF law. Neither
point has been waived or reported as resolved. Rework the coupled nRF escape
region while keeping all native connections and actual clearances valid.

`build/incomplete-return-gap-rework.kicad_pcb` preserves a separate experiment:
moving these two signal vias brings every transition inside the screen, but
leaves one HEALTH_INT open and two dangling-track warnings. Its own DRC,
inventory and change records are under `evidence/incomplete-return-rework*`.
**It is not the active source.** Test a copied board beside the matching project
and schematic, never directly under `build/` with missing project rules.

Local return-site trials are recorded in `rework-provenance.json`. The accepted
changes move R12/R13 into the spare top margin, add five GND vias, move two existing
returns, and reroute ACC_INT/SIM_IO locally. Native routing remains complete.
Do not repeat the already failed isolated via placements without changing the
routing hypothesis. Preserve usable fine-pitch pin exits during wider rerouting.

A later isolated router experiment shifted the open to HEALTH_RESET and produced
two near-duplicate SIM_IO/COEX0 vias on import. It was not accepted. Lock names or
router completion alone do not prove physical preservation; compare native
coordinates, drilled holes and source-bound DRC.

## DFM fixes and remaining review

The first r04f supplier run reported 0 Danger / 2 Warning. Its exact results are
preserved under `experiments/paul-nanosim-r04f-40x32/evidence/jlc-preflight/`.
r04g moves the D1 ground via from (124.8,116) to (124.78,116), and moves the
adjacent CHG_STAT horizontal run down 0.15 mm away from J3.1's mask. Manufacturer
lands, mask apertures and DFM rules are unchanged. Both supplier warnings close.

The current copper-only power estimates keep the main supply paths connected.
The auxiliary J5 branch remains 39.50 mm / approximately 52.16 mΩ at 20 °C under
its recorded assumptions. Review ESD topology, passive copper balance, short
returns and real supply behavior; these estimates exclude the cell, ferrite,
contacts, dynamic impedance and thermal behavior.

After any further layout change, regenerate native/geometry checks and run two
fresh unchanged-rule JLC analyses of the same final ZIP. The current 0/0 result
belongs only to the source and bytes above. Keep STATUS and WORKLOG current,
commit coherent changes, and deliver literal absolute artifact paths.

## Preserved sources

- Released 0.3.4: unchanged 35 × 28 mm baseline and its original two 0/0 reports.
- r04f: unchanged native-clean 40 × 32 mm checkpoint with nine return gaps.
- r04e: unchanged 35 × 28 mm checkpoint with five opens / eight dangling warnings.
- r04d, earlier r04 and rejected r04c remain available. The original SIM opening
  direction is correct; do not repeat the rejected socket reversal.

Nano-SIM now, eSIM later. J5 is a digital expansion port, not a heart-rate sensor.
Factory assembly/programming/test is required. No order, payment, supplier
message, powered test or production approval has occurred.
