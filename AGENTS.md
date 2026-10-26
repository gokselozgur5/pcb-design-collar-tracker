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
- The device must resist dust and water while the dog swims. IP68 is the selected
  design target; immersion depth/time must be recorded explicitly. Enclosure,
  gasket, charging interface and service access belong to the current scope.
  PCB DFM does not prove ingress protection; retain whole-assembly test evidence.

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
- A dangling-track warning can identify a segment that also carries a live branch.
  Preserve native terminal groups; trim only its unused end when deleting the
  whole segment would disconnect pins. Unused single-layer via junctions can be
  replaced only with checked planar connections and fresh full native DRC.
- On this Mac, use one native LoadBoard per probe process. Repeated initialization
  produced wx duplicate-handler warnings; separate probes avoid that path. Check
  process exit codes and source identities; do not suppress crash dialogs globally.
- Check card insertion/removal against populated bodies and their swept volume;
  a footprint courtyard pass is insufficient. Check SIM copper for a route that
  bypasses the clamp land, even when all native nets are connected.
- Separate peak, average and continuous current, and label engineering headroom
  separately from manufacturer requirements. Select a battery from complete-pack
  protection and charge limits; a bare-cell rating does not qualify its PCM.
- A retained PCB needs movement and tolerance checks against components, cables,
  SIM access and the closed-lid stack. A seated-board fit is not retention proof.
  Keep sampled cable poses distinct from continuous-motion and physical evidence;
  resolve material expansion before describing an assembly as ready to order.
- Apply the same declared thermal and retention-movement envelopes to every
  cable family. A combined result must not mix expanded RF checks with nominal
  power-wire checks. Keep the failing baseline when correcting an omission;
  search scores and sampled curvature do not replace independent continuous bounds.
- An adhesive envelope is not a qualified strain relief. Name its owning
  conductors/substrates, retain electrical separation, and do not assume PTFE
  adhesion. Report deformation demanded by static poses separately from proven
  material behavior. Forming tools need delivered-solid checks and released-shape
  acceptance; a numerical route-length tolerance is not a factory cut tolerance.
- No subagents unless Göksel explicitly requests them.
- A firmware link is not a powered-device test. For nRF91 modem work, use the
  non-secure/TF-M target, preserve external-I/O startup timing, inspect the actual
  merged reset vectors and exclude persistent storage from programmed bytes.
  A default bootloader partition map can link successfully while leaving address
  zero empty. Do not disable warnings or infer bootability from compile success.
  GNSS configuration requires its functional mode enabled; keep interrupt callbacks
  to signaling and do flash/network work in the owning application thread.
- A DNS caller deadline is not cancellation. Preserve worker/result ownership until
  completion, free late allocations and prevent overlapping calls. Keep watchdog
  expiry sticky; a late phase transition must not restore feeding. Distinguish host
  fault injection from actual modem/SoC reset and measured power behavior.
- For signed images, verify against the key embedded in the actual bootloader,
  reject copied public SDK private keys, and inspect the complete flash image.
  Match the staging API to the compiled swap mode; swap-offset starts one sector
  into the secondary slot. Trial confirmation needs bounded health evidence.
  Keep software downgrade checks distinct from hardware counters/debug protection.
  Sysbuild child caches need explicit forwarding; inspect every child's cache path.

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
