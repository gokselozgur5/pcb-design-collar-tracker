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

Continue from the saved r04 PCB. First inspect
`experiments/paul-nanosim-r04/evidence/routed-5-drc.json`: four open connections and
four dangling vias remain after local charger rework. `routing-checkpoint.json`
binds that result to the source hash. No routing job is still running. Do not rerun
the builder over this board or discard its ground fanout.

To reproduce initial placement in a **new** experiment only:

```sh
LC_ALL=C scripts/kicad-python scripts/build_paul_nanosim.py --name paul-nanosim-r04-rebuild
```

The builder now saves placement, protecting the 0.3.4 hash. Its overwrite guard is
intentional. The pipeline remains WIP; it is not a complete accepted board.

Implemented stages are `plan_ground_fanout.py` (geometry Python),
`apply_ground_fanout.py` (KiCad Python), `export_paul_route.py` (KiCad Python),
Freerouting and `import_paul_route.py` (KiCad Python). Each script takes the trial
directory; import also takes its SES path. Read their guards before replaying them.
`build/ground-base.kicad_pcb` preserves the clean ground-only stage;
`build/routed-1.ses` is the first completed router output. The imported board keeps
all 190 GND items and restores the original 24 RF segments exactly.

The first router reported 19 opens / 12 router violations. The native imported
board reports 14 opens / three dangling vias / zero parity issues. These are
different checks, not evidence that the remaining routing is accepted.

Use `finish_paul_route.py` for the new outer-layer completion helper. It considers
footprint keepouts, connected copper/pads and 0.4 mm power / 0.3 mm VIO trunks
with provisional 0.2 mm pad escapes. Native DRC remains mandatory. Its latest
four-open search failed; inspect topology before rerunning. The original
`finish_size_trial.py` still has board-zone-only and fixed-width assumptions.

`adjust_charger_escapes.py` records the latest local rework from its exact input
hash; it is a one-time stage, not a command to replay on the current board.
The first charger adjustment and intermediate DRC reports are also preserved.
`build/routed-3.kicad_pcb` has three opens but the rejected 77.33 mm CHG_FAULT
detour. `build/routed-5.kicad_pcb` matches the current four-open stage.

`export_paul_route.py TRIAL STEM` now preserves rounded native GND obstacle
geometry and allows rip-up of signal tracks in the exported copy. `route3.dsn`
was a repair experiment; the repeated router result was not imported. Do not
treat its ground-obstacle model or router counts as native acceptance.

After routing is resolved, export fresh `evidence/route-geometry.json` with
`dfm_geometry.py`, then use `plan_return_vias.py TRIAL` with geometry Python and
`apply_return_vias.py TRIAL` with KiCad Python. Both require matching source
hashes. These return-via stages are implemented but **not yet executed/accepted**.
Refill and check actual inner-plane containment and native DRC after applying.

Use `build_size_trial.py`, `import_size_trial.py`, `finish_size_trial.py` and
`dfm_geometry.py` as existing implementation references. Read before executing:
some historical scripts overwrite old sources, assume 53 footprints, use hardcoded
35 × 28 mm bounds, or permit In2 signal routing. Those assumptions are wrong for r04.
Old exporters/finalizers are revision-specific. Do not relabel old output as r04.

For new native checks, write results into the active trial's evidence directory:

```sh
scripts/kicad-cli pcb drc --help
scripts/kicad-cli sch erc --help
```

Use all severities, schematic parity and the matching project libraries. Keep the
same profile/exclusions and report defaults that KiCad leaves ignored.

After a new ZIP passes local checks:

```sh
node scripts/jlc_dfm_trial.cjs /absolute/path/to/new-dfm.zip r04-check1
node scripts/jlc_dfm_trial.cjs /absolute/path/to/new-dfm.zip r04-check2
```

Run one browser process at a time. The existing dedicated logged-in profile is
local under `evidence/zero-warning-r033/browser-profile/`; it is intentionally not
in Git. Same-Mac sessions may reuse it. A new machine needs normal user login via
`node scripts/jlc_login.cjs`; never export credentials or bypass authentication.
Uploads contain manufacturing layers/drills only. No orders or messages.

The helper waits for login hydration, pins the new record ID and ZIP hash, and
requires 29 analyzed rows stable twice. Inspect raw measurements, unchanged config,
UI and PDF. Two fresh results must refer to the exact same final ZIP bytes.
The baseline rule SHA256 is in `evidence/release-034/manifest.json`'s rules entries.

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
