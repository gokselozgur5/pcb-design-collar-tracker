# Working on pcb-design-collar-tracker

## Start here

1. Read `docs/STATUS.md`. This is the current project state.
2. Run `python3 scripts/resume.py`. It is read-only and checks the saved baseline.
3. Read `docs/RESUME.md` for the next commands and toolchain.
4. For the active PCB revision, read `docs/paul-nanosim.md`.
5. Use the relevant stage of `docs/PCB_DESIGN.md` for the reusable PCB workflow,
   review criteria, release evidence and lessons that apply to later boards.

A request to continue means continue the next unfinished step, regardless of the
language used in chat.
Do not restart the design or ask for decisions already recorded here.
Inspect the actual working tree before changing anything. Preserve later user edits.
If another session has advanced STATUS, use that newer state.

## Product decisions

- Small GPS/cellular dog-collar tracker, first market Türkiye.
- One electronics design for different dog sizes; different collar mounts are possible.
- Software features are preferred over extra hardware. No on-device AI requirement.
- Physical nano-SIM for this revision. eSIM is deferred.
- Factory assembly, programming and functional testing are required; avoid hand soldering.
- Heart-rate sensing is requested but not implemented. J5 is a digital expansion port.
- Battery capacity is not fixed at 500 mAh. Cell, runtime and update interval remain open.

## Work already authorized

Apply the applicable Paul layout review, implement nano-SIM, run real JLC DFM,
and reach zero Danger / zero Warning without weakening the checks.
Start at 35 × 28 mm; grow only if measured placement/routing requires it.
Local implementation, verification, project commits/pushes and manufacturing-file
uploads to JLC DFM are in scope. Orders, payments and supplier messages are not.

## Evidence and source rules

- Preserve released 0.3.4 files and hashes. Work in a new experiment directory.
- `hardware/` is legacy 30 × 22 mm source, not the current board.
- KiCad connectivity, ground-return quality, PCB DFM, SMT acceptance and functional
  testing are different checks. Report them separately.
- Never turn off a rule, hide an exclusion or shrink a manufacturer land solely to
  make a checker green. Resolve geometry against the actual part drawing.
- Ground pads connect locally to planes. Do not connect arbitrary signal pins to GND.
- 2 mm return-via spacing is the inherited screening target, not a universal RF rule.
- “All green” for a new revision requires two fresh JLC runs of the same final ZIP,
  matching hashes/rules, fully analyzed rows, raw results and PDF evidence.
- No claim that the active revision is routed, DRC-clean or all-green until its
  own evidence exists. Read STATUS for the current experiment directory.
- Check card insertion/removal against populated bodies and their swept volume;
  a footprint courtyard pass is insufficient. Check SIM copper for a route that
  bypasses the clamp land, even when all native nets are connected.
- No subagents unless Göksel explicitly requests them.

## Git and handoff

- Repository: `gokselozgur5/pcb-design-collar-tracker`, public. Use the personal account;
  do not switch global `gh` authentication or mix in work repositories.
- Make one coherent change per commit with an honest subject. WIP must say WIP.
  Normal pushes only; do not rewrite published history by default.
- All repository and GitHub content must be in English: documentation, code
  comments, generated labels, commits, issues and PRs. Chat can remain Turkish.
- Stage explicit paths. Never stage browser profiles, session state, credentials,
  raw browser captures, virtual environments or unrelated private continuity.
- Update STATUS with the exact next action whenever work advances. Append the
  outcome to `docs/WORKLOG.md`; avoid copying the full state into the log.
- Before a handoff, run `python3 scripts/verify_handoff.py` and inspect `git status`.
- On Göksel's Mac, writes stay under `/Users/gok/codex` or mounted
  `/Volumes/GOKSSD/codex`. Tool binaries/cache are not source files.

Reply in short, natural Turkish. Use absolute paths or a copyable `open -R` command
for delivered local artifacts. Explain progress without calling an unfinished
design ready to order.
