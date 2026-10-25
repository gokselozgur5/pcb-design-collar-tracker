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
