# Resume the PCB work

The current state is in [STATUS](STATUS.md). The next task is implementation,
not another requirements interview. Read [the Paul/nano-SIM notes](paul-nanosim.md)
before editing. This handoff does not require private chat history or other projects.

## Open the project

On the existing Mac:

```sh
cd /Users/gok/codex/projects/collar-tracker
python3 scripts/resume.py
```

For a new checkout, clone `https://github.com/gokselozgur5/pcb-design-collar-tracker.git`
to a working directory, enter it and run the same command. The repository is public.
Read-only verification uses only Python 3's standard library. Opening the native
project also works without rerunning the historical generators.

## Tools

| Tool | Working environment / override |
|---|---|
| KiCad | 10.0.7. `scripts/kicad-cli` and `scripts/kicad-python` use the existing SSD install; `COLLAR_KICAD_CONTENTS` can select another macOS install. |
| Native Python | KiCad's bundled Python 3.9 with `pcbnew`; ordinary Python cannot replace it. |
| Geometry Python | `.venv-dfm/bin/python`, Python 3.11 + Shapely 2.1.2 + NumPy 2.4.6. Install from `requirements-dfm.txt` in a new venv if missing. |
| Router | Java + Freerouting 2.5.0. Pinned JAR `/Volumes/GOKSSD/codex/tools/freerouting/freerouting-2.5.0.jar`; SHA256 `f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7`. |
| JLC browser | Node + Playwright 1.64.1; `COLLAR_PLAYWRIGHT_MODULE` can select a local installation. |
| PDF/image review | `pdftotext`, `pdftoppm`, `rsvg-convert`; render locally and actually inspect. |
| Mechanical CAD | OpenSCAD (`COLLAR_OPENSCAD` can select the executable); `pdfunite` joins the review sheets. |

Mount GOKSSD before using its paths. Do not silently create a substitute mount.
Set `COLLAR_KICAD_PYTHON` or `COLLAR_KICAD_CLI` to absolute executables for another
platform/install. That Python must provide pcbnew and the matching KiCad libraries.
The wrappers keep new runtime config/cache in the checkout's ignored `.runtime/`.

On a new machine, `npm install --prefix .runtime/browser --no-save playwright@1.64.1`
installs the browser library inside the ignored runtime directory. Install its Chromium
browser normally if needed; no profile or credentials are distributed in Git.

## Working commands

Continue from `experiments/power-r05l-charge-interlock/hardware/`. Read its README,
`evidence/charge-checkpoint.json` and `assembly/charge-interlock-r01/README.md`.
Native DRC/ERC/parity are zero. Two actual same-ZIP JLC runs each have 0/0/455.
81 fitted references have exact candidate MPNs; candidate BOM/CPL exclude DNP
parts and bare harness/debug/extension contacts. Procurement, CPL library rotations,
SMT, powered, RF and ingress acceptance remain open.

The hardware interlock is implemented: two VSYS-powered TLV3012B comparators and
a NAND drive /CE. The old r05k grounded-/CE/50°C finding is preserved and is no
longer the active circuit. The new temperature model has explicit full-curve,
leakage and cell/sensor coupling assumptions. Startup, brownout, low-cell recovery,
sensor insertion and physical thermal performance still need bench qualification.

Next: use `assembly/pack-r03/README.md` and its CT-BAT-001-A supplier request.
The proposed email to EEMB and dimensioned PDF are ready, but have not been sent.
Separate user authorization to send was requested; do not infer it from elapsed
time or from this handoff. No supplier response or battery approval exists.
The request's 600mA continuous rating is engineering headroom, not Nordic's
continuous demand. The PC3 source tables describe typical 1ms TX-subframe averages
and additional microsecond peaks, not a guaranteed reporting-cycle load profile.
The reviewed EEMB 350mA PCM is not accepted by the new geometry study. Larger
Jauch/VARTA alternatives have explicit size/charge limitations in the review.
Proceed independently with controlled harness/dock details
while awaiting a supplier response. Reconcile a returned specification against
voltage, current, protection/recovery, NTC and in-service dimensions before selection.
CAPH/ZETA are now prototype antenna candidates; cable end datums/tolerance fit,
feed bond and clip strength remain open. Follow with harness/dock,
seal/material/fastener definitions and firmware/factory test.
The provisional firmware VIO wait remains 1s. UVLO is not a zero-current battery
disconnect. Read the manufacturer sequencing exception before adding circuitry.

```sh
python3 scripts/verify_charge_candidate.py
python3 scripts/check_charge_r05l.py
python3 -m unittest discover -s tests -p test_charge_r05l.py -v
python3 scripts/verify_handoff.py
python3 scripts/verify_antenna_candidate.py
python3 scripts/package_antenna_review.py --verify
python3 scripts/verify_pack_request.py
```

The preserved antenna mechanical source is `mechanical/swim-r08-antennas/`. It retains the
r07 U12 relief and support shift, adds two cable routes and four internal lid
guides, and raises the rigid shell plus lid to 20.6mm. Its 85 populated envelopes
pass four thickness cases. Eight meshes pass integrity checks; both the original
carrier and deliberately undersized cable channels fail the CAD controls. The
initial and widened-straight GNSS guide failures are preserved under `evidence/`;
the final guide has a curved channel. Pack, cable tolerances, retention and
physical tests remain unqualified. All older models and packages are preserved.

The latest **requested-pack study** is `mechanical/swim-r09-pack-request/`.
It includes the 32 x 30.5 x 5.3mm requested pack body, a flat SEMITEC sensor and
explicit tape budgets. The complete reservation is 33 x 31.5 x 6.2mm. Raising
the board, antenna routes and shell by 0.4mm gives a 57.4 x 49.4 x 21.0mm rigid
enclosure. This is an unapproved supplier request, not a purchasable complete pack.
J4 pinout is verified against the native r05l netlist; lead/strain-relief drawings,
service swelling, attachment and thermal response remain open. Do not substitute
the existing EEMB PCM or call the entire device ready to order.

```sh
.venv-dfm/bin/python -m unittest discover -s tests -p test_pack_request.py -v
python3 scripts/verify_pack_request.py
```

Only regenerate its CAD deliberately using `scripts/export_pack_enclosure.py`.
The command also checks mesh integrity and actual CAD intersections; it takes
several minutes. Read-only verification does not need OpenSCAD or the geometry venv.

The preserved thermal-fit source is `mechanical/swim-r11-thermal-fit/`. Read its README
and dimensioned sheet. Four radial keys and larger guide/cavity clearances address
the r10 thermal interference calculation; component reliefs and cable paths cover
the larger assigned movement. The contact stem is now 7.50mm, matching the wall.
The PCB, outside size, prior CAD and all-green JLC evidence are preserved.

```sh
python3 scripts/verify_thermal_assembly.py
.venv-dfm/bin/python -m unittest discover -s tests -p test_thermal_assembly.py -v
```

The saved study includes 85 component envelopes, 27 cable poses, four capture tabs,
nine meshes, eight CAD controls and five views. Seven regressions reproduce the
old thermal/clearance problems, missing key/tab, closing-stack and key-tolerance
failures, and compare the fast cable evaluator against the preserved implementation.
Only deliberately regenerate using the README commands; saved verification is
read-only and works without the geometry environment or OpenSCAD.

The -10 to +45°C model uses assigned CTE/tolerance limits, not supplier guarantees.
Cable pose search can change plug azimuth; permissible force/orientation, complete
continuous movement and flex life remain unqualified. Tilt/load, moisture/creep,
actual machining limits and physical thermal fit must also be checked. Next local
work is controlled harness/dock; supplier selection, firmware
and factory/physical acceptance remain open. Do not describe this as order-ready.

The preserved pack-retention source is `mechanical/swim-r12-pack-retention/`. Read its
README and drawing. It adds the pack cradle/cap without changing the PCB, shell
outside size, contact/seal geometry or antenna routing. The pack seats 0.3mm lower
on the existing floor. The new minimum-size requirement and allowed contact regions
still require the supplier's approval. It is not a complete approved battery pack.

```sh
python3 scripts/verify_pack_retention.py
.venv-dfm/bin/python -m unittest discover -s tests -p test_pack_retention.py -v
```

The study checks all 85 populated envelopes, full upward pack/sensor travel and
four guaranteed capture regions. Two changed meshes, seven reused r11 parts and
seven CAD controls are source-bound. The cap and PCB support share a carrier
datum; preserve that relationship when checking the raised NTC clearance.
Do not treat tilt/load, pouch pressure/abrasion, cap strength or ingress as tested.
Next: actual harness/dock parts, pack lead exit/strain relief and routing, then
firmware and factory/physical qualification. The existing supplier email remains
unsent and requires the outstanding explicit sending authorization.

Saved native files are authoritative. Do not rerun one-shot seed/routing scripts
against an existing target. Use a successor for further circuit/PCB edits and
repeat its native checks/export/two supplier runs. Do not repeat DFM for unchanged
bytes. Preserve every prior all-green source and package.

The six-layer signal order is F/In2/In3/B, with dedicated GND on In1/In4.
The inherited 0.36mm port routes and matching remain candidates; all 27 original RF
segments are unchanged in r05l. C31's attachment imbalance is reviewed using unique
copper contours in the charge review; it is not an accepted SMT/reflow process.

The native RF exporter preserves polygon holes and records Contains probes.
The independent checker must agree with those probes; a centerline-only check
missed the original GNSS edge intrusion. Do not treat coverage as an EM simulation.

Keep `power-r05j-rf-junctions`, `power-r05i-rf-stack` and `power-r05h-six-layer` byte-exact: these are checked
baselines. Saved sources are authoritative; seed/refinement scripts are one-shot history.
Load each PCB beside its matching project/rules. One native LoadBoard per process;
wait for exit 0 and keep crash dialogs visible.

The preserved four-layer r05f has five opens. r05g's local crossing repair ended
with six opens and was not selected. Neither is the continuation point.

The r04i PCB and its two actual same-byte JLC passes remain immutable in
`experiments/paul-nanosim-r04i-sim-access-40x32/`. Its power audit still reproduces
the three original findings. Both `audit_power_architecture.py` and
`check_power_r05.py` deliberately return exit code 2 for electrical HOLD.
The latter verifies conditional model bounds; neither performs a powered test.
Read the [manufacturer-exception follow-up](power-sequence-followup.md) before
adding more retention hardware or simplifying shutdown sequencing. No circuit
change or electrical approval has been inferred from that exception.

```sh
python3 scripts/check_power_r05.py
python3 -m unittest discover -s tests -p test_power_r05.py -v
LC_ALL=C scripts/kicad-python scripts/check_kicad_flip.py
```

The flip smoke check must print PASS **and exit 0**. Add a library-loaded footprint
to its owning BOARD before flipping it. A prior unowned test crashed in native
`BOARD::FlipLayer`; a separate earlier process crashed during Python finalization,
whose exact cause remains unverified. Do not suppress crash dialogs globally or
treat a failed process as successful because an output file exists.

Always load a checkpoint beside its matching `.kicad_pro`: loading a bare build
snapshot can substitute default rules and overwrite the real project's settings
on save. The r05 placement helper now checks design-rule and net-class identity.

Protected NTC pack selection and antenna assembly qualification follow the
implemented r05l circuit. r11 adds conditional thermal capture geometry; actual
material/physical acceptance and dock/harness remain open.
Read `mechanical/swim-r08-antennas/README.md`, the current pack/antenna review and
`docs/turkiye-connectivity.md` before assuming a modem/plan is field-qualified.
The r05l/r08 thickness review checks 85 populated envelopes over 0.71–0.91mm;
eight meshes and both CAD interference controls are verified. The old r05j nine
height reservations are historical. Factory and physical qualification remain open.

```sh
.venv-dfm/bin/python -m unittest discover -s tests -p test_populated_fit.py -v
python3 -m unittest discover -s tests -p test_power_architecture.py -v
python3 scripts/verify_handoff.py
```

For a deliberate mechanical revision, copy the active directory first and follow
its reproduction commands. Do not overwrite checked r01/r02 bundles or their
inputs while experimenting. The exact next action is in STATUS.


The r04i builder records only the initial isolated placement, not all subsequent
manual routing. The saved native source and hash-bound evidence are authoritative.
Ignored routing trials are unnecessary for continuation. Preserve r04h/r04g/0.3.4.

These review commands leave the native design unchanged and refresh its reports:

```sh
.venv-dfm/bin/python scripts/audit_sim_topology.py TRIAL
.venv-dfm/bin/python scripts/audit_pad_attachments.py TRIAL
.venv-dfm/bin/python scripts/audit_passive_copper.py TRIAL
.venv-dfm/bin/python -m unittest discover -s tests -p test_sim_topology.py -v
```

Export current `route-geometry.json` first; all three audits reject a stale source.
The topology audit reports bypasses; explicitly inspect its four results. It does
not establish ESD immunity. Passive contour widths are review cues, not reflow tests.
The following r04g routing commands are retained as examples for an isolated copy;
do not rerun them over the preserved source.

Export/import must preserve native grounds, RF and explicit pin escapes. Generate
fresh geometry and plane inventory, then normalize exact copper contacts:

```sh
LC_ALL=C scripts/kicad-python scripts/dfm_geometry.py \
  experiments/paul-nanosim-r04g-returns-40x32/hardware/collar-tracker.kicad_pcb \
  experiments/paul-nanosim-r04g-returns-40x32/evidence/route-geometry.json
LC_ALL=C scripts/kicad-python scripts/audit_paul_layout.py experiments/paul-nanosim-r04g-returns-40x32
LC_ALL=C scripts/kicad-python scripts/export_paul_route.py \
  experiments/paul-nanosim-r04g-returns-40x32 NEW_STEM --native-ground \
  --protect experiments/paul-nanosim-r04g-returns-40x32/evidence/protected-fanout.json
.venv-dfm/bin/python scripts/normalize_router_contacts.py \
  experiments/paul-nanosim-r04g-returns-40x32 --input-stem NEW_STEM --output-stem NEW_CONTACTS
```

Use new stems; preserve earlier evidence. The normalizer refuses connectors that
would add copper outside the source geometry. It does not replace native DRC.
KiCad's `route` token loads as USER_FIXED in Freerouting; the exporter deliberately
emits `normal`. Inspect the *loaded* locks using the pinned 2.5.0 JAR:

```sh
FREEROUTING__USAGE_AND_DIAGNOSTIC_DATA__DISABLE_ANALYTICS=true \
  /opt/homebrew/opt/openjdk/bin/java -Djava.awt.headless=true \
  -Djava.io.tmpdir=/Users/gok/codex/projects/collar-tracker/.runtime/java-tmp \
  -cp /Volumes/GOKSSD/codex/tools/freerouting/freerouting-2.5.0.jar \
  scripts/InspectRouterLocks.java INPUT.dsn OUTPUT.json .runtime/lock-inspect --require-movable
```

The regression in r04e rejects the old model and accepts the corrected one.
Movable segments can merge into fewer polylines on load. Ground/RF/explicit fixed
items must remain protected; the post-load count need not equal the DSN count.

For search, explicitly set `--router.fanout.enabled=false`,
`--router.strict_drc=true`, `--router.copper_to_edge_clearance_um=400` and
`--router.hole_clearance_um=200`. Disable whole-net neck retries with
`--router.neck_width_um=0`; the 200 µm retry produced an unacceptable auxiliary
power detour in r04e. Native checks remain the authority even when router counts
include shape/model artifacts. Do not weaken native or supplier rules.

Import SES into an isolated copy containing the matching project, schematic,
placement JSON and protection list. Keep the SES inside that copy's `build/`:

```sh
LC_ALL=C scripts/kicad-python scripts/import_paul_route.py TRIAL TRIAL/build/NEW_STEM.ses \
  --protect TRIAL/evidence/protected-fanout.json
LC_ALL=C scripts/kicad-cli pcb drc --format json --severity-all \
  --schematic-parity --all-track-errors -o TRIAL/evidence/NEW_STEM-drc.json \
  TRIAL/hardware/collar-tracker.kicad_pcb
```

The importer checks unchanged placement/GND/explicit escapes and restores exact
RF segments. `--keep-locked` must match the export policy when deliberately used.
Copying a PCB into `build/` without its project can change the effective DRC rules;
run acceptance checks beside the matching native project and schematic.

`finish_paul_route.py BOARD DRC_JSON [OUTPUT_BOARD]` is the local outer-layer
completion helper. It includes native copper connectivity, footprint keepouts,
0.4 mm power / 0.3 mm VIO trunks and short 0.2 mm pad escapes. Its grid is a
planner, not native acceptance. It saves partial progress on interruption and
records source hashes. The default 40 mm detour screen is a planner policy, not a universal signal limit.
`--route-limit-mm` changes candidate generation only; it never changes native DRC.
Review any longer route against its actual signal and topology before accepting it. Save its
JSON under a new evidence name before rerunning, since the output stem is reused.

Do not replay builders over existing trials. `build_charger_local_trial.py
--name paul-nanosim-NEW` reproduces initial r04d placement from hash-pinned r04 and
r04c. It does not include later local repairs. `build_local_rework.py` reproduces
the rejected r04c approach and is retained as provenance, not the next action.

After routing is resolved:

1. Export fresh geometry with `dfm_geometry.py BOARD REPORT_JSON` using KiCad
   Python. Use `evidence/route-geometry.json` for power/return helpers.
2. Run `audit_power_paths.py TRIAL` with geometry Python and
   `audit_paul_layout.py TRIAL` with KiCad Python. Check source hashes and the
   documented estimate limits; neither establishes physical performance.
3. Use `plan_return_vias.py TRIAL` with geometry Python and
   `apply_return_vias.py TRIAL` with KiCad Python. Refill, run native DRC and
   verify actual GND via containment on both inner fills. The first r04f plan added 15 vias as explicit WIP
   using `--allow-partial`; r04g adds five more. r04h closes the remaining screen gaps. Never
   clear failed IDs to make a plan appear complete.
4. The current source already has nine English labels. For a new unlabeled trial,
   `label_paul_trial.py TRIAL` seeds labels using native silk minima. Export `geometry.json`,
   then use `size_trial_labels.py plan/apply TRIAL`. Inspect actual glyphs and
   interface association; automatic clearance does not prove a label is useful.
   The planner uses actual rectangular outline bounds and rejects stale source hashes.
5. Run all-severity DRC/parity/all-track checks and schematic ERC. Preserve the
   recorded rule profile/default ignored checks. Old exporters are specific to
   53-footprint, earlier-layer boards; do not relabel their output as this revision.

Export a new, uniquely named package after all-severity native checks:

```sh
python3 scripts/export_paul_dfm.py TRIAL NEW_PACKAGE_NAME
```

The exporter records native-input and output hashes, runs DRC/ERC, and packages
only manufacturing files. It does not establish remaining layout acceptance.
Never overwrite a tested ZIP. Once a new ZIP passes local checks:

```sh
node scripts/jlc_dfm_trial.cjs /absolute/path/to/new-dfm.zip r04-check1
node scripts/jlc_dfm_trial.cjs /absolute/path/to/new-dfm.zip r04-check2
```

Run one browser process at a time. The dedicated local profile is under
`evidence/zero-warning-r033/browser-profile/`, intentionally excluded from Git.
Reuse a working local session. On another machine use normal login via
`node scripts/jlc_login.cjs`; never export credentials or bypass authentication.

The helper pins the new record ID and ZIP hash and requires 29 analyzed rows
stable twice. Inspect raw measurements, unchanged rules, UI and full PDF. Both
fresh results must use identical final ZIP bytes and report 0 Danger / 0 Warning.
The baseline rule hash is in `evidence/release-034/manifest.json`. Uploads are
manufacturing files for DFM only; no orders, payments or supplier messages.

## KiCad API lessons already learned

- `GetFPIDAsString()` works; `GetFPID().Format()` has SWIG overload issues.
- Use `SetLibDescription()` for footprint descriptions.
- Build an `LSET()` then `AddLayer(...)`; `LSET([layers])` failed here.
- Use `round(mm * 1e6)` for internal units; `FromMM` can truncate by 1 nm.
- Snapshot tracks/zones/drawings before mutation and use `Delete` for removed
  in-memory objects; iterating with `Remove` broke SWIG ownership here.
- Copy vector coordinates before changing a track: a saved `GetEnd()` SWIG value
  can alias native storage and change when `SetEnd()` runs. Use a new `VECTOR2I`.
- Use `LC_ALL=C` on this Mac to avoid unsupported-locale errors.
- Duplicate pad numbers exist (U.FL grounds and nano-SIM shield). Index by UUID
  or ref/pad/index instead of assuming one pad per number.
- Keep the footprint writer object alive during library saves; temporary SWIG
  wrappers caused an earlier isolated trial failure. Cast base track wrappers to
  `PCB_VIA` before reading layer-dependent via sizes.
- Recursive native track connectivity already reaches vias; a one-step query
  does not prove an API limitation.
- Check GND via containment against saved filled polygons on both inner layers.
  A net name alone does not prove the via joins a plane.
- Do not confuse solid zone attachment with balanced copper on a small passive.
- The old GIMP's review counts are not this board's test results.

## Keep the next handoff current

One coherent change per commit. Update STATUS after measurable progress and
WORKLOG after a checkpoint. Run `python3 scripts/verify_handoff.py`, inspect the
staged paths, commit and normally push to the existing origin.
Keep all repository/GitHub text in English, including generated labels.
Never commit `.runtime`, browser captures/profile, venvs or personal memory files.

Repository verification checks saved evidence and hashes. It does not rerun KiCad,
JLC, RF tests, SMT assembly or powered hardware tests. State that distinction.


## Current charging dock: r13

Read `mechanical/swim-r13-charge-dock/README.md` and
`assembly/charge-harness-r01/README.md`. Actual Mill-Max 0962, Alpha 2843/7,
Tensility 10-03388, Littelfuse 0251.750MXL and T18R tie candidates are recorded.
The two dock halves capture the spring flanges; the external collar key now
projects 4.0mm and extends down to Z=7.7mm. PCB/seals/pack/boot are unchanged.
The external dock is 60 x 36 x 16mm. 29 checks, three closed meshes, six CAD
controls and seven regression tests cover the declared geometric domain.

```sh
python3 scripts/verify_charge_dock.py
python3 -m unittest discover -s tests -p test_charge_dock.py -v
```

The first collision used the boot's print frame instead of its assembly frame;
that rejected source/result is preserved under `evidence/initial-frame/`.
The actual source export translates the boot +4mm for printing; r13 imports it
with -4mm for assembly. Do not change the old boot to fix a coordinate error.

Next: resolve positive holding/magnet force, exact internal lugs/J3 route and
factory terminations, source/fault behavior and pack lead exit. The current magnets
have no demonstrated holding force; 1.569N is only the pair's maximum *midstroke*
force, not the maximum across the whole tolerance stroke. The fuse is not a 500mA
current limiter, and the USB cable does not implement enumeration. No production
power-path approval exists. Supplier-message approval is still unanswered; no
message or order has been sent. Firmware and physical acceptance remain unfinished.
