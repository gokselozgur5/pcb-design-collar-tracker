# Charge-wire thermal clearance correction r18

This successor corrects an omission in r17: its charge-wire screen used nominal
component and retainer geometry, although its RF screen included the declared
thermal and retainer-movement envelopes. The unchanged r17 routes fail the
expanded charge screen at all 27 poses. The preserved r17 checkpoint remains
valid evidence of its narrower calculation, not complete thermal clearance.

[Routes](routing.json) · [Relief dimensions](retainer-reliefs.json) ·
[Current checks](checks.json) · [Original failures](baseline-failures.json) ·
[Assembly view](review.png) · [CAD evidence](cad-checks.json)

All **27/27 static poses pass** the combined 82 checks per pose (2,214 checks).
Four closed mesh files, five CAD controls and seven regressions also pass.

| Minimum after declared allowances | Result | Required |
|---|---:|---:|
| Charge wire to thermal component envelope | 0.204214mm | 0.2mm |
| Charge wire to swept retention | 0.289911mm | 0.2mm |
| Charge wire to RF lead | 0.232517mm | 0.2mm |
| RF pair | 0.213954mm | 0.2mm |
| Continuous charge-wire bend bound | 6.605489mm | 6.604mm |

These are conditional geometric results; they do not release the device for
manufacture or establish wire cut accuracy, restraint or physical performance.

## Design change

Two local top reliefs give the charge leads room over the moving PCB retainer.
The cuts start at assembled Z=12.0mm and retain a 0.5mm lower bridge. They remove
3.255mm³ in total. All four PCB capture tabs and all four radial keys remain.
Frame strength, creep and manufacturing capability are not established by this
geometric change.

| Relief | X interval | Y interval | Remaining frame height |
|---|---|---|---|
| Red lead | 19.9–21.4mm | −5.8–−1.4mm | 0.5mm |
| Black lead | 19.9–21.4mm | 3.5–8.4mm | 0.5mm |

The GNSS control point at index 4 moves down 0.2mm and index 5 moves up 0.6mm,
relative to r17. This raises its lower turn while retaining space below LTE at
the left guide. Its initial handle is retuned to the same 98.5mm centreline
length. All four existing lid guides are retained; the hole does not move
with the proposed cable. LTE, antennas, native PCB and enclosure size are unchanged.

Charge routes change around the expanded component envelopes. The numerical
target lengths remain 43.765806mm red and 54.920909mm black. Their 0.001mm
interval tolerance is a numerical check, not a factory cutting specification.
All original 0.2mm gap and 6.604mm charge-wire bend requirements remain in force.

## Verification scope

The successor runs the inherited 49 charge checks and 29 RF checks at each
correlated PCB pose, plus four explicit charge checks for thermal component and
swept retention envelopes. Its supplemental clearance uses continuous-curve
travel bounds. The retainer sections are cut before expansion, so tolerances
shrink the available reliefs rather than treating their nominal openings as
guaranteed space. The frame sweep is conservative; a failed envelope does not
by itself demonstrate contact in a physical unit.
RF retention checks keep the full old frame envelope, which contains the
relieved part and is therefore conservative for the revised frame as well.

Nominal CAD separately checks wire/joint clearance from the assembled shell,
carrier, retainer and components, plus wire passage through the terminal plates.
A Boolean comparison measures the two removed frame volumes and rejects added
material. A nominal GNSS witness is checked against the actual unchanged lid.
These mesh checks do not replace the numerical tolerance envelopes.

## Remaining work

Complete-device release remains **HOLD**. This revision does not implement
operating wire restraint or a forming/assembly fixture. The sampled curves do
not establish continuous deformation, connector loads, manufacturing cut/thermal
tolerance, service movement or flex life. The retainer bridge also requires
physical strength/creep acceptance. Supplier pack approval, factory joining,
powered/RF tests and water/dust qualification remain open. No order or supplier
message is authorized by this checkpoint.

## Reproduce

```sh
.venv-dfm/bin/python scripts/check_charge_thermal_clearance.py --baseline
.venv-dfm/bin/python scripts/check_charge_thermal_clearance.py
.venv-dfm/bin/python scripts/export_charge_thermal_clearance.py
.venv-dfm/bin/python -m unittest discover -s tests -p test_charge_thermal_clearance.py -v
python3 scripts/verify_charge_thermal_clearance.py
python3 scripts/verify_handoff.py
```

Saved verification uses standard Python. Recomputing geometry/CAD needs the
existing geometry venv and OpenSCAD. Preserve r17 and this checkpoint when
developing the next assembly revision.
