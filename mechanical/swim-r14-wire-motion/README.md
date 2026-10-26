# r14 — charging-wire movement study

The r13 drawing used straight pigtails behind spring contacts that can move in
their housing. That drawing did not allocate enough wire for the full conservative
movement bound. r14 replaces those paths with constant-length outward loops and
provides space for their complete calculated envelope. This is a conditional
geometry prototype, not a completed or qualified charger.

The wearable, PCB, seals, key and spring-contact seats are unchanged. Only the
external dry dock grows from 60 to **94 x 36 x 16mm**, excluding screw heads and
cable. This is a review prototype; the added length is not a new wearable size.

## Results and assumptions

| Item | Result |
|---|---|
| Free insulated span, each pigtail at 23C | 40.95 +/- 0.10mm between defined end planes |
| In-service free-span envelope | 40.775 to 41.125mm, including a separate 0.075mm service allowance |
| Rear-seated contact tail, nominal | X=11.3029mm |
| Conservative contact forward movement | 2.1421mm; ignores the barb's earlier physical stop |
| Start plane, all assigned tolerances | X=8.9108 to 11.5529mm |
| Fixed insulated-wire end plane | X=49.00 +/- 0.10mm feature and +/- 0.20mm thermal allowance |
| Minimum residual slack | 0.3858mm at the largest possible endpoint span |
| Continuous bend-radius lower bound | 8.6961mm; Alpha 2843/7 requirement is 8.382mm |
| Clearance envelope radius | 0.4191mm insulation + 0.15mm position + 0.02mm service + 0.10mm shell allowance |
| Minimum calculated side-wall gap | 0.2720mm within the full envelope |
| Rear flange shoulder left intact | At least 0.6727mm axial material at the assigned feature limit |
| PCB and Gerber | Unchanged r05l; both recorded JLC runs remain 0 Danger / 0 Warning |

The 0.25mm start-plane allowance covers 0.1524mm contact-tail length, 0.05mm
housing feature and the full tail datum's conservative thermal movement.
The temperature screen is -10 to +45C from a 23C reference. Housing CTE <=100ppm/K
and effective free-wire length CTE <=50ppm/K are engineering requirements, not
manufacturer guarantees. The 0.20mm end-plane and 0.075mm wire-service allowances
exceed the calculated 0.1617mm and 0.0676mm thermal movements, respectively.
The separate 0.10mm shell budget covers nearby wall/relief movement and feature
tolerance. Wire and housing temperatures may vary independently within the bounds.
The independent end-plane, cut-length and route limits still need factory and
physical qualification. The first nominal calculation omitted these full-span
thermal budgets; it is not the result reported by this checkpoint.

`checks.json` contains 42 analytical checks. `mesh-checks.json` records two closed
housing meshes and six CAD controls. The continuous wire envelope, stationary
harness, seated pins and wearable have empty intersections with the new housing.
The old housing intersects the required wire envelope; the reversed key still
intersects the nose before the inherited earliest conductive-touch bound.
Twelve regressions also reject stretched straight wire, short cuts, tight bends,
an undersized cavity, excess wire and inadequate numerical-error allowances.

## What the calculation proves

For normalized position t, each wire follows
`x = start + span*t`, `y = +/-[6 + A*(1-cos(2*pi*t))/2]`, `z = 5.5`.
Amplitude A is chosen for constant arc length. Both ends have a tangent parallel
to the contact axis. The shortest possible span and longest possible cut give
the largest required amplitude. The curvature bound applies for every t and
every endpoint position in the declared intervals, not just the nine calculated
poses (three shown in the preview). Composite midpoint integration has an explicit
derivative-based error bound; that bound is checked before it is used to enclose amplitude.

The CAD sweep uses interval cells enclosing all permitted endpoint/amplitude
combinations, expanded by the insulation, route and shell allowances. Near the
circular rear bores, the cells use a circumscribed circular YZ envelope and flat
expanded X end planes; the larger rectangular boxes are used in the open cavity.
This deliberately includes impossible combinations to remain conservative.
The contact itself is only modeled rear-seated in the pin CAD
control: the full wire allowance exceeds the actual barb-limited travel.

## Factory work still required

The source components and pinout are preserved from
[charge-harness-r01](../../assembly/charge-harness-r01/README.md). The fuse moves
to X=53.5..61mm, its rear splice to X=61..66mm, and the USB splay to X=68..86mm.
The jacket bay is X=86..93mm. Splice allowances are now **5 x 2.4mm**, not the old
4mm length. The incoming insulated fuse remains at most 7.5 x 4mm.

The 40.95mm dimension is **not a total wire cut length**. Crimp insertion, stripped
conductor and splice overlap must be added by the approved factory termination
process. The USB cable also needs controlled jacket removal and unequal red/black
lead preparation; its supplied 25 +/- 5mm fanout is insufficient for this layout.
No end-user soldering is intended.

The model assumes the X=49 end planes are restrained and the loops stay in the
declared planar family. **A fixed-end clamp/strain relief, forming fixture and
retention process are not implemented or qualified here.** A free wire can buckle
out of this family. The calculated envelope therefore establishes available
space, not guaranteed motion of an assembled harness. Alpha's bend requirement
does not establish repeated-flex life. Test crimp pull, endpoint slip, cycling,
insulation abrasion and temperature after defining the fixture and process.

Dock holding, actual spring force at the largest stroke, internal contact lugs
and the J3 route, supply/fault behavior, protected-pack approval, firmware and
physical power/RF/water/dust tests remain open. IP68 is still a design target.
The unused catalogue research in the local references directory is not a
selected retention mechanism and is not part of this revision.

## Reproduce

```sh
python3 scripts/check_dock_wire_motion.py
python3 -m unittest discover -s tests -p test_dock_wire_motion.py -v
python3 scripts/export_dock_wire_motion.py
python3 scripts/make_dock_wire_sheet.py
python3 scripts/verify_dock_wire_motion.py
```

Read-only verification needs only standard Python. Regenerating CAD needs
OpenSCAD; rendering the drawing needs rsvg-convert. Earlier revisions are
preserved. Source hashes, evidence and the remaining conditions travel together.
