# Four-cable routing r17 — static geometry candidate

The two RF leads and both charging wires now pass together at all **27 sampled
PCB poses**. The model uses the existing r16 shell, r12 carrier and r11 lid,
retainer and antenna guides. PCB, enclosure dimensions and antenna positions
are unchanged. Complete harness assembly and device release remain **HOLD**.

[Assembly view](review.png) · [Authoritative routes](routing.json) ·
[Independent checks](checks.json) · [CAD evidence](cad-checks.json)

## Change and result

The GNSS route's fifth indexed control point rises by 0.6mm. Its initial handle
length is adjusted at each existing plug angle to retain the 98.5mm centreline
length. LTE curves are retained. The nine upper PCB poses use more flexible
spline representations for the black charge lead. These are geometry controls,
not additional physical wire segments or joints.

| Screen | Result |
|---|---|
| Combined static poses | 27/27; 29 RF and 49 charge checks per pose |
| RF lengths | 98.5mm each, within the 0.001mm numerical interval tolerance |
| Charge lengths | 43.765806mm red / 54.920909mm black, same numerical tolerance |
| Minimum RF-to-RF gap | 0.204589mm, including declared position/travel allowances |
| Minimum charge-to-RF gap | 0.214946mm |
| Minimum charge-to-component gap | 0.213040mm |
| Charge-wire bend requirement | 6.604mm, unchanged |
| Existing guide apertures | All 27 RF poses fit; the curved hole uses the frozen SCAD polyline |

Short handles can make an interval bound unnecessarily loose. The checker
refines continuous Bezier bounds and records the resolution; it never substitutes
sampled curvature for bend acceptance. Two difficult poses use 16,001 clearance
points with a correspondingly tighter derivative-based travel allowance. Every
original gap and bend requirement is retained.

The JSON contains source control points only. Old search scores, radii and
pass flags are not carried into the new route definition. The independent
report binds its inputs before checking and rejects changes during the run.

## CAD and regressions

Two closed RF witness meshes cover the guide regions at nominal cable diameter.
Their intersection with the actual, unchanged lid is empty. A known 0.3mm cube
inside the LTE guide wall produces the expected 0.027mm³ intersection. Position
and travel allowances are checked analytically, separately from nominal CAD.

Seven regressions cover the existing aperture, excessive GNSS lift, a curve
that leaves the actual curved hole, reversion to the old RF route, changing a
wire's length, missing/changed assembly data and non-finite geometry. The ten
shared harness regressions also pass.

## Limits and next work

These are individual static curves. They do not prove that an unrestrained
wire naturally adopts the curves, that the paths form a continuous deformation,
or that the same physical cut length covers wire thermal expansion and cutting
tolerance. The 0.001mm tolerance is numerical, not a production cutting instruction.
The RF feed-joint exclusion is inherited and remains physically unqualified.

Next implement charge-wire restraint and a forming/assembly fixture, then check
continuous motion and the installation/service sequence. Keep the native J3
polarity and bonded-wire geometry. Factory joining, RF plug loads, pull/flex
life, powered resistance/fault behavior and actual supplier process acceptance
remain open. The protected battery supplier request is still unsent; physical
powered/RF/water/dust tests and IP68 are unqualified. No order is authorized.

## Reproduce

```sh
.venv-dfm/bin/python scripts/check_cable_integration.py
.venv-dfm/bin/python scripts/export_cable_integration.py
.venv-dfm/bin/python -m unittest discover -s tests -p test_cable_integration.py -v
python3 scripts/verify_cable_integration.py
python3 scripts/verify_handoff.py
```

Read-only saved verification uses standard Python. Geometry/CAD reproduction
uses the existing geometry venv and OpenSCAD. Preserve this checkpoint and the
older r02/r11 sources when developing the next assembly revision.
