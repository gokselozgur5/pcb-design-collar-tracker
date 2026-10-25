# Project checkpoints

## 2026-10-25 — Repository and fresh-session handoff

- Event: Göksel requested atomic GitHub commits and a Claude session that can
  continue without another explanation of the project.
- Decision: Preserve the verified 0.3.4 baseline and checkpoint the unfinished
  Paul/nano-SIM revision separately. Use a private personal repository.
- Result: Source, historical revisions, selected DFM evidence, manufacturer
  references and explicit project entry files are included. Browser sessions,
  credentials, raw browser captures and unrelated private continuity stay local.
- Next: Resolve the r04 builder's KiCad/SWIG board-mutation failure, then implement
  ground fanout/routing and complete the new revision's own acceptance checks.

Earlier engineering decisions are in `docs/decisions.md` and the revision reports.
Their evidence is dated; do not transfer an older pass to a newer source file.

## 2026-10-25 — Nano-SIM ground layout and first route

- Event: Continued the authorized Paul/nano-SIM implementation after publication.
- Decision: Preserve 0.3.4; use two inner GND planes and local pad-to-via stubs.
- Result: Fixed KiCad board mutation; saved 54-footprint placement. Connected
  81 ground pads through 68 vias; ground-stage native DRC has zero violations,
  zero parity issues, no open GND and 84 remaining non-GND connections. Imported
  the first route while preserving ground and RF geometry. Native result:
  14 opens, three dangling vias, zero parity issues. No new JLC acceptance.
- Next: Finish routing, review returns/power/copper balance and run the new
  revision's own native and supplier checks. See STATUS for exact source/evidence.

## 2026-10-25 — Reusable PCB workflow and English repository

- Event: The owner requested a reusable PCB Design workflow and English-only
  GitHub content, and renamed the repository.
- Decision: Apply English to docs, comments, generated labels, commits, issues and
  PRs, even when chat is Turkish. Use the live canonical repository name
  `gokselozgur5/pcb-design-collar-tracker`; keep the existing local directory.
- Result: Added `docs/PCB_DESIGN.md`, linked project entry instructions, translated
  current and historical documentation, and regenerated the mechanical review
  sheet in English. Updated remote/repository links. Published hardware, release
  ZIPs and raw supplier evidence retain their original bytes.
- Validation: Reviewed English prose and the rendered sheet, scanned repository
  text, checked local Markdown links/Python syntax and verified saved baseline
  evidence. Historical documents retain their original verification limits.
- Next: Continue the unfinished r04 routing from STATUS. The language change does
  not add new manufacturing or functional acceptance.

## 2026-10-25 — Local routing and charger escape checkpoint

- Event: Continued the authorized PCB work and verified that the English commit
  was present on the renamed public repository.
- Decision: Preserve every released baseline. Add footprint-aware routing and
  retain native checks at each stage; remove an excessive signal detour rather
  than presenting a lower open-net count as layout completion.
- Result: Local routing reduced 14 opens to three, but CHG_FAULT took 77.33 mm.
  Removing that detour and adjusting charger/ground exits leaves four opens and
  four dangling vias, zero parity issues and no copper-clearance violations.
  All 67 GND via centers remain in both inner fills; 81 ground pads are connected.
  A Freerouting repair repeated unchanged results and was stopped without import.
- Validation: Fresh native DRC and filled-plane check are bound to the current
  source in `routing-checkpoint.json`. Return-via planner/application scripts are
  present but unexecuted. Socket access, TI land-pattern differences and Nordic
  power guidance were recorded; they remain review items, not acceptance claims.
- Next: Resolve charger/SPI fanout and socket/ESD placement. Then complete return,
  power and passive-copper review, native checks and two real same-byte JLC runs.

## 2026-10-25 — Localized charger trial and import regression

- Event: Continued the Paul/nano-SIM work while keeping all repository content
  and the new handoff in English.
- Decision: Reject the whole-net r04c rework; retain working remote pin escapes
  and the original outward-facing SIM orientation in r04d. Use TI's DCK land
  example. Preserve failed stages and the accepted 0.3.4 source/ZIP.
- Result: r04d has six open connections and 14 dangling-item warnings, with zero
  parity or other native DRC violations. All 66 GND via centers lie in both inner
  fills, no inner tracks remain, and 24 RF segments match the baseline. The
  29/75 return-via screen and auxiliary J5 supply connection remain open.
  Rejected 59.98/79.59 mm detours and the three-clearance-error SIM experiment
  are preserved separately. No new JLC analysis was run.
- Validation: A no-routing DSN/SES round-trip reproduced an importer defect:
  old locked signal routes survived beside replacements, adding two co-located
  drill findings. Matching export/import locks removed those findings while
  preserving the original six opens, 189 GND items and 28 manual escapes. Native
  DRC, source hashes, power estimates and replay evidence are tied together in
  r04d's `evidence/routing-checkpoint.json`.
- Next: Reconcile the router model's larger incomplete count with actual native
  connectivity before another search. No routing process remains. Finish the
  six connections and remaining layout reviews, then run both real JLC checks.

## 2026-10-25 — Router contact fixes and complete native routing

- Event: Continued the authorized Paul/nano-SIM layout and English repository work.
- Decision: Fix actual DSN contacts and loaded lock states before further routing.
  Preserve r04e at 35 × 28 mm; test 40 × 32 mm after measured routing failures.
  Reject the 83.52 mm auxiliary supply detour in the earlier unlocked trial.
- Result: r04f closes every net after one nearby GND-via move. Removing two unused
  charger vias gives zero native opens, violations, warnings and parity findings.
  Fifteen added GND return vias keep those checks clean and reduce 30 screening
  gaps to nine. All 81 GND pads reach a local via, all 81 GND via centers lie in
  both inner fills, no inner tracks exist, and 24 RF segments remain exact.
- Validation: The loaded-lock regression rejects the old 930 USER_FIXED model
  and accepts the corrected model. Native source/evidence hashes are recorded in
  r04f `routing-checkpoint.json`; accepted 0.3.4 bytes are preserved.
- Next: Resolve nine return-screen gaps, review power/ESD/passive balance, add
  useful English labels and run two new unchanged-rule same-byte JLC analyses.
  No new supplier acceptance, order, powered test or production approval yet.

## 2026-10-25 — Native-clean r04g, English labels and two actual JLC passes

- Event: Continued the Paul/nano-SIM revision and verified the English-only
  repository requirement against the live personal repository.
- Decision: Preserve 0.3.4 and r04f; keep successful local repairs in r04g and
  retain the incomplete coupled-return alternative separately. Supplier success
  applies to its exact PCB/ZIP, not to the remaining review or production.
- Result: r04g has 81 locally connected GND pads, 86 ground vias in both continuous
  inner planes, no inner tracks and 24 unchanged RF segments. Native DRC/ERC,
  connectivity and parity are clean. Return-screen gaps fall from nine to two.
  Nine English labels meet native silk minima; source-bound placement rejects
  stale plans. Actual top/bottom views were inspected.
- DFM: The first r04f analysis was 0 Danger / 2 Warning. Moving the D1 GND via
  0.02 mm and the nearby CHG_STAT run 0.15 mm closes the two measured gaps without
  changing lands, apertures or rules. The identical r04g ZIP passed twice at 0/0,
  all 29 rows complete: records 637221644721938434 and 637222172922957825. Both
  raw measurements, UI views, complete PDFs and hashes were checked. SMT was off.
- Boundary: A coupled SIM_IO/COEX0 move clears the distance screen but leaves one
  HEALTH_INT open and two dangling warnings; it is preserved as an incomplete
  experiment. Wider routing also exposed moved/duplicated signal vias and a
  blocked HEALTH_RESET exit; those alternatives were not accepted. A help-only
  Freerouting invocation migrated its default local settings version before the
  workspace profile was specified; subsequent invocations use explicit paths.
- Next: Resolve SIM_IO and COEX0 return gaps, finish ESD/passive/power review,
  and repeat native plus two same-byte JLC checks after further layout changes.
  No order, payment, supplier message or physical acceptance occurred.
