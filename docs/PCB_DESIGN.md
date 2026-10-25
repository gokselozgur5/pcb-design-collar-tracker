# PCB Design

Treat PCB work like software engineering: requirements, versioned source, small
changes, checks and a verified release. Use this workflow for future boards too.

This file defines the method. The current board state is in [STATUS](STATUS.md),
its decisions in [decisions](decisions.md), and the application of Paul's review
in [paul-nanosim](paul-nanosim.md). Dimensions and results from one board do not
automatically apply to another.

## Software engineering equivalents

| Software | PCB equivalent |
|---|---|
| Requirements and acceptance criteria | Use, dimensions, power, interfaces, environment, manufacturing and test targets |
| Architecture and API contracts | Block diagram, power tree, pins, voltages, timing and connectors |
| Source code | Schematic, native PCB, project rules, footprint and symbol libraries |
| Dependency lock | CAD version, exact MPN, datasheet revision, library commit and stackup |
| Build | Netlist, Gerber, drill, BOM, CPL, stencil and mechanical outputs |
| Static analysis | ERC, DRC, schematic–PCB parity and geometry checks |
| Unit/regression tests | Pin mapping, footprint dimensions, connectivity and before/after failure examples |
| Integration tests | Actual supplier DFM, assembly review and physical board measurements |
| Release | Checked manufacturing package linked to source by hashes |
| Production smoke test | Bring-up, programming, power/radio/sensor and end-to-end function tests |

**Clean ERC/DRC does not prove the board works. Clean PCB DFM does not qualify
assembly or functionality.** State the scope of each result.

## 1. Define the requirements

Record the following before designing. Mark unknowns as assumptions; do not
silently turn them into decisions.

- Use: what does the device do, under which conditions and how often?
- Country/operator/service: are the connectivity technology and actual service compatible?
- Mechanics: board, battery, antennas, enclosure, mounts, cables and access clearances.
- Power: supply range, peak/average current, operating modes, charging and runtime.
- Interfaces: voltage levels, pin mapping, timing, boot/reset and debug.
- Manufacturing: quantity, budget, layer count, thickness, assembly and hand-soldering needs.
- Delivery: bare PCB, assembled board, or programmed and function-tested device?
- Acceptance: which measurement or test demonstrates completion?

Do not fix battery capacity or board dimensions from an estimate alone. Place real
components, antennas and mechanical volumes together; verify fit and runtime separately.

## 2. Architecture and component selection

Draw a block diagram and power tree. Define each block's inputs, outputs, power
domain and failure behavior. Review supply dips, reset, insertion/removal and
back-powering through interfaces while the device is off.

Every physical component needs an exact MPN, manufacturer, package, pinout and
manufacturer document. A distributor SKU does not replace the MPN. Availability
and suitability are dated evidence. Similar part names do not establish matching
manufacturers, packages or pins.

Read the manufacturer's datasheet and reference design first. Record source URL,
revision, download date and SHA-256. A library symbol or AI explanation alone is
not evidence of the manufacturer's pinout.

## 3. Schematic and footprints

- Make power domains, net names, NC pins, pull-ups/downs and debug paths explicit.
- Check the chain: pin number → manufacturer function → schematic net → PCB pad.
- Run ERC and record ignored checks and justified exceptions separately.
- Independently check critical connections in the netlist. Reading the same wrong
  table used by the generator is not independent verification.
- Compare each footprint with the package drawing: pin 1, top/bottom view, pitch,
  pad dimensions, exposed pad, pegs/holes, mask, paste, courtyard and keepouts.
- Check flipped bottom-side parts and CPL rotations separately.
- One pad number can identify multiple physical pads. Use UUIDs or pad indices.
- Version project-specific footprints in a local library. Resolve differences
  between the native board and library instead of hiding mismatch warnings.

Connector lands fitting on the PCB does not establish usability. Leave space for
card insertion/removal, cable bends, latch release and tools.

## 4. Manufacturing constraints and layer stack

Use the actual supplier's limits for the selected process, layers and thickness.
Set track width, copper clearance, drill, annular ring, mask bridge, board-edge
and silkscreen rules in the project. Keep a dated capability reference.

Supplier minima need not be the design targets. Leave margin where possible.
If fixed package pitch requires an exception, scope it to that geometry; do not
lower every track/via clearance.

Choose layer count and stackup from signal, current and RF requirements. This
project's four-layer/two-inner-GND choice is not a rule for every board.
For controlled impedance, calculate against actual dielectric thickness, material,
copper and supplier stackup. A trace width alone does not establish 50 ohms.

## 5. Placement and routing

Place mechanical constraints, connector/antenna access and critical power/RF
blocks first. Follow manufacturer layouts for decoupling and sensitive feedback
loops. Review critical paths before leaving them to an autorouter.

### Ground and return paths

- Connect the pins that require GND. Connecting every pin to ground is not a goal.
- A GND net name, zero open connections and a good return path are different findings.
- Avoid unnecessary splits in reference planes. Follow return paths across layer
  changes and plane interruptions.
- Give GND pads short local connections to the plane. Do not daisy-chain unrelated
  small passives along a long ground trace.
- Adjacent IC ground pins may share a suitable short connection; record its geometry.
- Place return vias near the relevant signal/power transition. Evaluate spacing
  against the signal and stackup; an inherited number is not a universal standard.
- Measure actual connection to the correct filled plane, not just via count.
  Check isolated islands and saved fills.

### Power, thermal behavior and RF

- Size power paths from peak current, allowed drop, copper thickness and temperature.
- Measure short pad escapes separately from long power runs. A netclass setting
  does not prove that every actual trace uses that width.
- Review sequencing, UVLO, charge limits, NTC/protection and transients.
- Compare copper attached to both pads of small passives. Assess soldering and
  thermal balance when one side has a plane and the other a narrow neck.
- Check RF geometry against the reference design and real stackup. Antenna
  keepouts, enclosure, battery and body proximity may need separate measurements.
- Adding an ESD part is insufficient by itself. Review connector → protection → IC
  routing and the protection device's ground path.

### Autorouting

Pin CAD/router versions and settings. Export a copy rather than altering the native
source. Expanded pads or keepouts used by the router are not production geometry.
Prevent long autorouted GND buses where ground should connect through planes.

After import, recheck placements, pad/net mapping, layers, locked critical traces,
ground connections, via diameters/drills and minimum widths. A router completion
message does not replace native DRC.

## 6. Verification: what actually passed?

| Check | Required evidence | Does not prove |
|---|---|---|
| ERC | Report for the right schematic/revision, with ignored defaults | Physical operation |
| DRC + parity | Violations, opens and schematic match for the right PCB/project | RF/EMC or power stability |
| Ground review | Pin/net mapping, actual fill, local connection and return measurements | Laboratory EMC performance |
| Geometry regression | Check fails on the old defect and passes on the fix | Every supplier algorithm |
| Gerber review | Actual exported layers, pads, holes and dimensions compared | Assembly correctness |
| Supplier PCB DFM | Uploaded ZIP hash, record ID, rules, completed result and PDF | SMT or functional acceptance |
| PCBA review | BOM/CPL/part/orientation/stencil/factory-preview match | Firmware and product behavior |
| Physical acceptance | Conditions, board revision, firmware and actual test results | Untested environments |

Check commands against the installed KiCad version's `--help`. Include relevant
severities, all track errors and schematic parity. Refresh zone fills; do not
accidentally use `--save-board` on a released file.
[KiCad 10 CLI documentation](https://docs.kicad.org/10.0/en/cli/cli.html).

First map each warning to real coordinates, geometry and net. Similar locations
need not be the same defect. After fixing one, inspect its symmetric counterpart.
Do not weaken rules or arbitrarily shrink manufacturer lands to get green results.

Our release practice requires **two fresh DFM runs of the same final ZIP bytes**.
This is our repeatability check, not a universal supplier requirement. Confirm the
analysis finished, every row was evaluated and rules stayed unchanged. A loaded
web page is not an analysis result.

## 7. Assembly, programming and working delivery

The BOM needs exact parts, values/tolerances, packages, references and DNP status.
Match CPL references, side, coordinates, units, origin and rotation to the supplier
preview. Do not submit DNP parts or bare contact/test pads as fitted components.
[JLCPCB BOM requirements](https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly).

Confirm actual stock, substitutions, bottom-side assembly, stencil and special
processes for the intended order. A datasheet does not establish factory availability.

For programmed delivery, define the firmware image/hash, debug/pogo access,
programming procedure, serial identity and test fixture. Specify acceptance inputs,
measurement limits and failed-board handling.

Bring-up proceeds through short/resistance checks, polarity, current-limited power,
rails, reset/debug, firmware, then radio/sensor and end-to-end functions. Test the
battery, charger and protection against the selected cell's limits. Do not claim
unmeasured health or sensor performance as a validated product feature.

## 8. Git, scripts and releases

```text
AGENTS.md / CLAUDE.md   Entry instructions for a new session
docs/STATUS.md         Current revision, verified results, gaps and exact next step
docs/decisions.md      Decisions, assumptions and supporting evidence
docs/WORKLOG.md        Short record of meaningful completed steps
hardware/             Native source and local libraries
scripts/              Reproducible generation, checks and exports
experiments/<rev>/    Isolated trial sources and evidence
references/           Manufacturer sources, revisions and hash manifest
evidence/             Selected reports, measurements and before/after evidence
release/              Immutable delivery packages linked to source
mechanical/           Enclosure, mounts and real component volumes
```

Identify the actual current source in STATUS. A directory named `hardware/` is not
necessarily the latest revision.

- Use a dedicated repository; do not accidentally stage files in its parent repo.
- Write all GitHub-facing content in English: docs, comments, generated labels,
  commits, issues and PRs. Conversation language does not change this rule.
- One coherent change per commit. Keep related schematic/footprint/PCB changes
  together; separate independent fixes. Mark unfinished work as WIP.
- Preserve source and old releases. Create new trials separately; do not silently
  regenerate a finished board over its existing source.
- Compare placements, pad shapes/nets, rules and critical routes semantically.
  A large KiCad text diff alone is not a review.
- Bind source SHA, tool versions, output list, ZIP SHA, local checks and supplier
  records in a release manifest.
- Actually open Gerber/drill/mask/paste outputs. Check layers, outline, holes,
  pad openings, board edges and both sides' orientation.
- Submit only suitable manufacturing files. Exclude browser profiles, tokens,
  cookies, raw sessions, virtual environments, private notes and unrelated files
  from Git and manufacturing ZIPs.
- Check the release in a clean checkout. A useful regression must reject an
  incorrect source or changed output.

## Completion criteria

Name the completed stage: schematic, placement, local checks, PCB DFM, PCBA or
working product. Inspect evidence for every acceptance criterion in that stage.
Another revision's green result or a report title is insufficient.

Deliver a short result, real remaining gaps and the full artifact path.
For local files, provide a copyable command such as
`open -R "/absolute/path/package.zip"`. Update STATUS so the next session knows
where work stopped and what to do next.

## New PCB brief

```text
Purpose / use:
Confirmed requirements:
Open decisions / assumptions:
Board + battery + antenna + enclosure limits:
Power tree / peak and average current:
Critical interfaces / manufacturer references:
Supplier + process + stackup + design margins:
Current native source / revision:
Acceptance criterion → check → evidence file:
Manufacturing delivery scope:
First concrete next step:
```

## Lessons from this board

- Remembering Paul's GIMP review is not the same as applying it to this board.
  Review each new design against its actual source.
- Two copper pours do not prove two uninterrupted ground references. Inspect
  actual tracks and saved fills on each layer.
- The same 0.3.3 ZIP returned 0/0 and later 0/1. Recheck final bytes; do not turn
  one observation into a universal guarantee.
- The mask warning involved two similar ground necks. Match coordinates individually.
- Removing items while traversing KiCad 10 SWIG collections caused failures.
  Snapshot items first and use `Delete` for removed in-memory objects. Check the
  resulting native board with DRC.
- SIM form factor does not change modem technology. Nano-SIM does not remove
  LTE-M/NB-IoT operator compatibility or the 1.8 V UICC requirement.
- Check connector insertion against the manufacturer's drawing and an actual
  component-side CAD view. Bottom-side mirroring can reverse an assumed opening
  direction; a rotation angle alone does not prove access.
- Preserve working remote pin escapes during local placement changes. Removing
  whole nets can let later routes block fine-pitch pins that were already usable.
  Reserve nearby exits together before routing long connections.
- Test a suspected connectivity API limitation before changing the router around
  it. KiCad's recursive track connectivity already reached vias in this board;
  an initial one-step query was insufficient evidence of a missing connection.
- For a repair route, export and import must use the same lock policy. A no-routing
  DSN/SES round-trip exposed duplicated locked native copper and two co-located
  drill holes. Preserve the named escapes, unlock replacement routes on import,
  and check the result with native DRC before running a longer search.
- Reconcile router incompletes with native pin connectivity and dangling branches.
  A higher router count is not automatically that many new electrical opens.
  Disable a repair's fanout pre-pass explicitly when testing the existing escapes.

Add reusable lessons here. Current tasks and results belong in STATUS and WORKLOG,
not a growing diary inside this guide.

- Check the router's loaded lock state, not only native KiCad locks. Freerouting
  2.5.0 treats KiCad's `(type route)` token as `USER_FIXED`; use `(type normal)`
  for deliberately movable routes and retain `(type fix)` for protected copper.
  `InspectRouterLocks.java` must reject the old model and accept the corrected
  model. Count differences after loading can reflect merged polylines.
- Native copper can join a pad interior or a trace midpoint. A router expecting
  exact centers/endpoints can report false opens. Preserve coordinate precision,
  split real junctions and check modeled connectors against existing copper.
  Validate the transfer with an isolated no-route SES round-trip and native DRC.
- Run native DRC beside the matching project and schematic. Checking a copied
  board without its project can silently use different rules.
- A dangling track may feed a live branch at its midpoint. Trim only the unused
  tail, then recheck pin connectivity; deleting the whole track can break a net.
- Grow the board in a separate experiment when measured routing warrants it.
  Compare resulting power paths and native checks; more area alone does not
  establish better signal routing, enclosure fit or manufacturing acceptance.
- Read the units of individual supplier fields. The JLC measurements used here
  are in mils while board-size metadata uses inches; a shared JSON response does
  not imply one common unit. Keep raw coordinates and the explicit transform.
- Derive label bounds from the actual outline and text size/stroke from native
  rules. Check real glyphs against mask/drill geometry, bind the plan to a source
  hash, and inspect connector association after applying it.
- Give Freerouting an explicit workspace `--user_data_path` even for `-h` or
  version/help probes. Startup can migrate and save the default user settings.
- Reserve fine-pitch pin exits during wider repair routing. Inspect imported
  via coordinates and drilled holes; a nominally protected via can be retained
  beside a shifted router replacement, leaving two near-coincident holes.
- Preserve a moving connector's insertion/removal volume before placing nearby
  protection or decoupling parts. A static footprint courtyard does not model a
  card sliding over the PCB. Check the manufacturer drawing, populated bodies,
  heights and tolerances on the actual component side.
- Audit ESD routing as physical copper topology. An autorouter can connect a
  protected branch back through its same-net connector pad, bypassing the clamp.
  Compare before/after paths; a clamp-land cut can detect bypasses but cannot
  qualify surge performance. Test same-layer branches and via-mediated bypasses.
- Count unique copper around a passive pad. Summing overlapping segment widths
  can double-count one physical connection. Compare both pad exits, nearby rail
  branches and short necks; retain solder/reflow qualification as a separate step.
- Copy SWIG vector coordinates before a native mutation. A stored `GetEnd()`
  wrapper can alias the track and change after `SetEnd()`, creating a zero-length
  split segment. Construct a new `VECTOR2I` and verify native connectivity.
- A joint signal-via/ground-via move can open a site that isolated placement
  searches miss. Record the coupled geometry and recheck every affected net,
  filled plane and return-screen point instead of weakening the target.
