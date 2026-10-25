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
| Geometry Python | `.venv-dfm/bin/python`, Python 3.11 + Shapely 2.1.2. Install from `requirements-dfm.txt` in a new venv if missing. |
| Router | Java + Freerouting 2.4.1. Existing JAR `/Volumes/GOKSSD/codex/tools/freerouting/freerouting-2.4.1.jar`. |
| JLC browser | Node + Playwright 1.64.1; `COLLAR_PLAYWRIGHT_MODULE` can select a local installation. |
| PDF/image review | `pdftotext`, `pdftoppm`, `rsvg-convert`; render locally and actually inspect. |

Mount GOKSSD before using its paths. Do not silently create a substitute mount.
Set `COLLAR_KICAD_PYTHON` or `COLLAR_KICAD_CLI` to absolute executables for another
platform/install. That Python must provide pcbnew and the matching KiCad libraries.
The wrappers keep new runtime config/cache in the checkout's ignored `.runtime/`.

On a new machine, `npm install --prefix .runtime/browser --no-save playwright@1.64.1`
installs the browser library inside the ignored runtime directory. Install its Chromium
browser normally if needed; no profile or credentials are distributed in Git.

## Working commands

Continue from `experiments/paul-nanosim-r04d/hardware/collar-tracker.kicad_pcb`.
Read STATUS and the trial's current hash-bound evidence before editing. r04 is a
fallback; r04c is a rejected experiment. Neither supersedes r04d.

The latest clean-clearance stage has six opens: VSYS (J5 branch), CHG_STAT,
CHG_FAULT, SPI_SCK, SIM_IO and SIM_CLK. A local SIM-corridor experiment added
three clearance errors and was restored from `build/corridor-2.kicad_pcb`.
Preserve that backup and the rejected-stage evidence.

The next step is to validate the DSN model against native connectivity, not to
repeat an unchanged router run. The stopped obstacle-model trial repeated 28
unrouted items / 89 router violations. The native-ground model reported 58
incompletes with fanout disabled, including 15 GND, while native DRC still has
six non-GND opens. Distinguish actual pin connectivity from unused branches and
routing-model contact detection. None of those search results was imported.

The isolated no-routing round-trip is in `build/roundtrip-native.ses` and
`evidence/import-lock-regression.json`. It exposed duplicate locked native/SES
signals in the old importer. The fixed importer gives the original six opens,
14 dangling-item warnings and no added drill/clearance/parity findings. The
active source remains unchanged; `build/roundtrip-fixed.kicad_pcb` is test output.

For future paired export/import, use matching lock options. In particular:

```sh
LC_ALL=C scripts/kicad-python scripts/export_paul_route.py \
  experiments/paul-nanosim-r04d NEW_STEM --native-ground \
  --protect experiments/paul-nanosim-r04d/evidence/protected-fanout.json
# Run the router only after reviewing the model; preserve the source first.
LC_ALL=C scripts/kicad-python scripts/import_paul_route.py \
  experiments/paul-nanosim-r04d \
  experiments/paul-nanosim-r04d/build/NEW_STEM.ses \
  --protect experiments/paul-nanosim-r04d/evidence/protected-fanout.json
```

`NEW_STEM` is a placeholder for a new experiment, not an existing completed
session. Use `--keep-locked` on both sides only when deliberately retaining all
original locks. The importer verifies unchanged placement/GND/explicit escapes
and restores exact RF geometry. Always follow with native checks:

```sh
LC_ALL=C scripts/kicad-cli pcb drc --format json --severity-all \
  --schematic-parity --all-track-errors \
  -o experiments/paul-nanosim-r04d/evidence/NEW_STEM-drc.json \
  experiments/paul-nanosim-r04d/hardware/collar-tracker.kicad_pcb
```

No router or completion process remains at this checkpoint. Recheck live state
before starting one. Logs stay local; the portable JSON evidence records the
observed outcomes and why the trials were stopped.

For a materially revised routing experiment, `export_paul_route.py TRIAL STEM
--protect UUID_JSON` protects only the explicit manual escapes. `--keep-locked`
retains all native locks and prevented useful remote rip-up in r04c. Neither
option changes the native source during export. `--native-ground` retains fixed
GND copper, real pads and the two inner planes in the routing copy. A replayed
export reproduced the diagnostic DSN after normalizing its filename. For repair
trials, use the explicit CLI `--router.fanout.enabled=false`; the installed
2.4.1 parser reads but discards the older DSN fanout flag. This controls a routing
pre-pass, not a DRC rule. Avoid repeating a failed trial
without changing the blocked topology.

`finish_paul_route.py BOARD DRC_JSON [OUTPUT_BOARD]` is the local outer-layer
completion helper. It includes native copper connectivity, footprint keepouts,
0.4 mm power / 0.3 mm VIO trunks and short 0.2 mm pad escapes. Its grid is a
planner, not native acceptance. It saves partial progress on interruption and
records source hashes. A proposed connection over 40 mm is rejected for topology
review; this is a planning screen, not a universal signal-length limit. Save its
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
   verify actual GND via containment on both inner fills. These stages have not
   yet been accepted on r04d.
4. `label_paul_trial.py TRIAL` seeds English labels once. Export `geometry.json`,
   then use `size_trial_labels.py plan/apply TRIAL`. Inspect actual glyphs and
   interface association; automatic clearance does not prove a label is useful.
5. Run all-severity DRC/parity/all-track checks and schematic ERC. Preserve the
   recorded rule profile/default ignored checks. Old exporters are specific to
   53-footprint, earlier-layer boards; do not relabel their output as this revision.

Once a new ZIP passes local checks:

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
