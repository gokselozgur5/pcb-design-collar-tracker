# Current state — 2026-10-25

**Active: Paul layout fixes + physical nano-SIM + real JLC DFM all green.**

Repository: [gokselozgur5/pcb-design-collar-tracker](https://github.com/gokselozgur5/pcb-design-collar-tracker).
The local directory remains `/Users/gok/codex/projects/collar-tracker`.
All repository and GitHub content must be English. The new PCB is unfinished.

| Item | Verified state | Evidence/source |
|---|---|---|
| Accepted PCB DFM baseline | 0.3.4, 35 × 28 × 0.8 mm; two JLC PCB runs 0 Danger / 0 Warning | `evidence/release-034/`, `release/` |
| Baseline integrity | Original source and released ZIP hashes preserved | `scripts/verify_handoff.py` |
| Active native source | `experiments/paul-nanosim-r04d/hardware/`; 54 footprints, 286 native pads | Trial `evidence/layout-inventory.json` |
| Ground | 81 GND pads, 66 GND vias; every via center inside both inner GND fills; no inner tracks | Same inventory; native DRC |
| RF geometry | All 24 baseline RF segments preserved exactly | Same inventory; impedance/body performance remains unqualified |
| Return-via screen | 29 of 75 non-GND vias outside the inherited 2 mm screen | Same inventory; return-via work remains open |
| Current routing | Six open connections; seven dangling tracks and seven dangling vias; zero parity or other DRC violations | Trial `evidence/corridor2-drc.json`, `routed-2-drc.json` |
| Socket orientation | Original bottom-side orientation retained; opening faces the y=100 board edge | GCT D6 drawing and actual pad coordinates |
| D1 lands | TI DCK example applied: 0.90 × 0.40 mm, 0.65 mm pitch, 2.20 mm row centers | Native footprint and project library |
| New revision JLC DFM | Not run | Baseline acceptance does not transfer |
| Production readiness | Power, RF, BOM, SMT, firmware, fixture and mechanics still open | `docs/order-readiness-0.3.4.md`, `docs/pcba-delivery.md` |

## Continue from r04d

Open nets are **VSYS, CHG_STAT, CHG_FAULT, SPI_SCK, SIM_IO and SIM_CLK**.
The main charger-to-modem power path is connected; the remaining VSYS opening is
the auxiliary J5 branch. The current `power-path-review.json` explicitly records
that disconnected branch. Its other path estimates are preliminary, tied to this
source hash and exclude component impedance, transients and thermal behavior.

Current PCB SHA256:
`38882bf0111a0190a9a55e756b72be96f91e325de29d909a93c6a57759bbed44`.
`build/corridor-2.kicad_pcb` preserves this stage. Check live hashes and processes
before continuing; a checkpoint is not a claim that a background job is complete.

The latest local planner could not close these six nets without long detours.
The proposed SIM-corridor change introduced three clearance violations, so it
was rejected and the native-clear stage restored. The rejected board and its
DRC are retained under `build/sim-corridor-rejected.kicad_pcb` and `evidence/`.

**Next: validate the DSN routing model before another search.** The obstacle-model
repair repeated 28 unrouted items / 89 router violations across four passes. The
native-ground model saw 49 unrouted items after fanout; a direct run with fanout
disabled saw 58 incompletes, including 15 GND. Map these counts to actual native
connectivity and dangling branches before treating them as missing connections.
These searches were stopped without importing their routes. No router remains
running at this checkpoint. Their stop reports are retained in `evidence/`.

A no-routing/no-fanout DSN/SES round-trip reproduced the same six native opens,
but exposed an importer bug: native locked signals were kept beside replacement
SES routes, adding two co-located drill warnings. The importer now matches the
export lock policy. In an isolated copy, the corrected round-trip preserved 189
GND items, 24 RF segments and 28 manual escapes, with the original six opens /
14 dangling-item warnings / zero parity and no added clearance or drill findings.
See `evidence/import-lock-regression.json`. The active source was not replaced
by either round-trip copy.

## Preserved alternatives

- `paul-nanosim-r04`: four-open fallback, source SHA256
  `2e9c0666d6561330a5ad5608c65ae7d49485f0731130f3652b0a99ce19004398`.
  Charger topology is older; do not describe it as the active board.
- `paul-nanosim-r04c`: rejected whole-net rework. It discarded useful remote
  escapes and incorrectly reversed the SIM opening. Its completed router result
  had 26 unrouted items / 22 router violations and was not imported.
- r04d `build/routed-1.kicad_pcb`: four-open intermediate with rejected 59.98 mm
  VSYS and 79.59 mm CHG_STAT detours. Those routes are absent from the active source.

Do not rerun a placement builder over an existing experiment. Builders reproduce
initial stages only; later native snapshots and their evidence preserve the rework.

## Remaining acceptance

1. Close the six routes and remove unused copper with fresh native connectivity checks.
2. Review power paths, ESD topology, passive copper balance and short ground returns.
3. Add nearby return vias, refill both planes and verify their actual connections.
4. Place useful English labels; inspect real copper, mask, paste, drill and silk output.
5. Pass native DRC/ERC/parity, then run two fresh JLC analyses of identical final ZIP
   bytes with unchanged rules. Save raw measurements, UI, PDFs and source hashes.
6. Update this state, make atomic commits and deliver an absolute artifact path.

Nano-SIM now, eSIM later. J5 is a digital expansion port, not a heart-rate sensor.
Factory assembly/programming/test is required; no order, payment, supplier message,
powered test or production approval has occurred.
