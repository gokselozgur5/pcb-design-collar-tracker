# Internal charge harness r02 — WIP

Both leads now have explicit routes, stripped ends and solder-joint envelopes.
The nominal assembly passes 41 geometry checks. The complete harness is still
**HOLD**: restraint, a fixed-length movement family and the factory process are
unfinished. The PCB, Gerber, enclosure size and external dock are unchanged.

[Assembled view](review.png) · [CAD scene](harness.scad) ·
[Route checks](route-checks.json) · [Motion diagnostic](motion-screen.json)

The view includes both existing RF leads. Component blocks are bounding envelopes;
the silver solder solids reserve the maximum joint space, not a predicted meniscus.

## Wiring and preparation

| Contact | Wire | PCB pad | Native net |
|---|---|---|---|
| Case Y=-6 | Red | J3.1 | `/VIN_5V` |
| Case Y=+6 | Black | J3.2 | `/GND` |

Only these two internal wires use **Alpha 2841/7, 30 AWG, 7/38 stranded PTFE**.
The external dock keeps its existing 26 AWG wire. The manufacturer specifies
0.6604mm maximum jacket diameter and a bend radius of ten cable diameters;
the resulting limit is 6.604mm. The 0.34mm maximum conductor diameter is an
additional incoming requirement, not a published manufacturer tolerance.
Source URL, inspected facts and PDF identity are in [sources.json](sources.json).

The [controlled dimensions](harness.json) specify 1.8mm stripping at the terminal
and 2.4mm at the PCB, with a +/-0.1mm cut requirement. The clearance calculation
also accounts for route-position error at the insulation boundary. Nominal
centreline lengths are 43.766mm red and 54.921mm black; **these are not released
production cut lengths**.

The terminal tips end at X=22.4mm, inside the existing 1.2mm holes. Flat end faces,
insertion depth and the angled conductor envelope are checked against the r16
terminal and pocket. At J3, each tip is offset so at least 0.65mm of bonded wire
fits on its actual native copper polygon. Maximum PCB joint height is 1.05mm.
The factory must prepare, solder, clean, insulate and inspect the harness. No
end-user soldering is intended. Wetting, alloy/flux, temperature/time, strain
relief, insulation and measured resistance remain unqualified.

The internal wire's published maximum pull tension is about **3.914N**.
Do not copy the external dock's 5N pull target onto these thinner wires. A
qualified internal harness test and restraint specification remain required.

## Evidence and limits

- Continuous Bezier bounds give minimum bend radii of 7.438mm red and 6.905mm
  black. Chord/control-polygon bounds bracket the reported arc lengths.
- Both full routes, their insulation transitions, other populated bodies,
  existing RF leads, retention parts, antennas, lid, opposite wire and nonlocal
  self-clearance are checked. Own J3 copper is identified from the hash-matched
  native export; unowned PCB copper remains an obstacle.
- Both actual wire meshes are closed and oriented. The CAD intersections with
  the body/carrier/components/joint envelopes and with the terminal metal are
  empty. A deliberately lowered ground wire produces 1.538mm3 of interference.
- Eight regressions cover source geometry, swapped polarity, the old wire's
  bend requirement, an actual collision, continuous bounds and strip-position
  uncertainty.
- Nominal wire-only resistance at 20C is about 0.0304 ohm for the pair. The saved
  current sweep is a sensitivity calculation; it excludes joints, contact
  resistance, heating, transients and fuse clearing. It does not establish
  ampacity or fault-current coordination.

The initial movement proposal fails: translating the control points with the
PCB requires up to 0.978mm of wire-length change. Only the nominal one of 27
poses passes that proposal. Several other poses also fail RF clearance or bend
screens. These are conservative geometric screens, not measured physical
collisions. Manufacturing cut tolerance cannot make one wire change length as
the PCB moves. The next step is a constrained, constant-length route family
with actual restraint and an installation/service sequence.

The newer [constant-length search](fixed-length-search.json) produces candidate
curves for all 27 poses using the same 43.765806mm / 54.920909mm length targets.
The [independent full route checks](fixed-length-checks.json) accept **18 of 27
static poses**; every pose meets the 0.001mm numerical length tolerance. The
remaining nine are all at PCB top Z=11.97mm: the black lead fails RF separation
and, in eight cases, its continuous bend-radius bound. These candidate curves
have not replaced the nominal CAD meshes, and do not establish continuous flex
or physical restraint. The optimizer's own score is not the acceptance result.

Next rework the shared RF/charge-wire space at the upper PCB position, including
any affected lid guides. Recheck RF length, both wire families, pads, components
and retention together. Keep the existing 0.2mm separation and 6.604mm wire bend
requirements. Failed local searches do not prove that a route is impossible.

The initial insufficient-clearance route is preserved under `evidence/`.
This directory is an unreleased working candidate: regenerate its evidence
together when changing it, and retain each coherent revision in Git. Earlier
PCB, r16 mechanical files and published review archives remain untouched.

## Reproduce

```sh
.venv-dfm/bin/python -m pip install --cache-dir .runtime/pip-cache -r requirements-harness.txt
.venv-dfm/bin/python scripts/check_internal_harness.py
.venv-dfm/bin/python scripts/export_internal_harness.py
.venv-dfm/bin/python scripts/screen_internal_harness_motion.py
.venv-dfm/bin/python scripts/search_internal_harness_motion.py --output assembly/internal-charge-r02/fixed-length-search.json
.venv-dfm/bin/python scripts/check_internal_harness_motion.py
.venv-dfm/bin/python -m unittest discover -s tests -p test_internal_harness.py -v
python3 scripts/verify_internal_harness.py
```

The CAD scene supports `part="collision"`, `part="metal_collision"` and
`part="lowered_wire_control"`. Empty intersections are expected for the first
two; the last must produce a positive-volume solid. Saved evidence verification
does not rerun CAD or claim a physical test. There is no manufacturing, powered,
RF, water/dust or IP68 acceptance for the complete tracker.
