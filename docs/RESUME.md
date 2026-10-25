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

For a new checkout, clone `https://github.com/gokselozgur5/collar-tracker.git`
to a working directory, enter it and run the same command. The repository is private.
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

Start by resolving the documented builder error, then run:

```sh
scripts/kicad-python scripts/build_paul_nanosim.py --name paul-nanosim-r04
```

That builder is WIP. It is not a complete rerouting pipeline. It preserves the
0.3.4 hash, writes the new SIM schematic/footprints and tries to build placement.
Ground fanout and GND-excluded DSN export still need implementation.

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
- Duplicate pad numbers exist (U.FL grounds and nano-SIM shield). Index by UUID
  or ref/pad/index instead of assuming one pad per number.
- Check GND via containment against saved filled polygons on both inner layers.
  A net name alone does not prove the via joins a plane.
- Do not confuse solid zone attachment with balanced copper on a small passive.
- The old GIMP's review counts are not this board's test results.

## Keep the next handoff current

One coherent change per commit. Update STATUS after measurable progress and
WORKLOG after a checkpoint. Run `python3 scripts/verify_handoff.py`, inspect the
staged paths, commit and normally push to the existing private origin.
Never commit `.runtime`, browser captures/profile, venvs or personal memory files.

Repository verification checks saved evidence and hashes. It does not rerun KiCad,
JLC, RF tests, SMT assembly or powered hardware tests. State that distinction.
