# r05j — R3 and LTE tuning junctions

R3 now has one 0.36 mm copper entry on each land. It moves 0.30 mm to keep the
nearby branch outside all three review contours. The C11 tuning branch shortens;
C12's signal land sits on the main path instead of a long branch. Both capacitors
remain DNP.

[Before / after drawing](evidence/rf-junction-review.pdf) ·
[Gerber ZIP](evidence/collar-tracker-05j-rf-40x32-dfm.zip) ·
[JLC report 1](evidence/jlc-check1/report.pdf) ·
[JLC report 2](evidence/jlc-check2/report.pdf)

| Check | Result |
|---|---|
| PCB / circuit | 40 × 32 mm, six Cu layers, unchanged 71-part r05 circuit |
| Native DRC / ERC / parity | Zero findings and zero opens |
| R3 copper ratios at 0.05 / 0.15 / 0.30 mm | 2.288 / 2.413 / 2.090 → 1.004 / 1.003 / 1.001 |
| C11 branch centerline | 1.31 → 0.42 mm |
| C12 branch centerline | 2.84 mm branch removed; signal land is on the main path |
| RF reference projection | 1,742 native probes agree; no RF trace copper outside In1.Cu GND |
| Ground / return screen | 94 local terminals, 110 GND vias, both continuous planes, 128/128 returns |
| Populated fit | 69 envelopes pass at 0.71 / 0.81 / 0.84088 / 0.91 mm; old carrier still fails |
| JLC PCB DFM | Two same-ZIP runs, each 0 Danger / 0 Warning / 450 Good; all 29 rows analyzed |
| Supplier scope | Unchanged rules, SMT off; no order or physical test |

PCB SHA256: `51fc05ccc66009995daa8c5d5466aa983436e00e7ff338f0ddfb0927c92b4580`.
ZIP SHA256: `8fd625d3da7b8bd3c59ea9aa0fd625dc93d458fe23b64a6fd7bc69d4c6915e50`.
JLC records: `637352328236847105` and `637352583225630721`.

The tradeoff is a longer main feed: the combined centerline from the module to
R3 and R3 to J1 grows from 5.89 to 8.91 mm, excluding the resistor body. This
reduces tuning stubs and improves the local copper balance, but does not prove
lower RF loss or correct impedance. DNP lands still introduce discontinuities.
Fitting C11/C12 requires a new RF and assembly review; their copper is asymmetric.

All other component poses, lands, vias, non-LTE tracks, module escapes, GNSS/FEM
routes, inner copper, GND fills, stack and design rules remain unchanged. The
four SIM clamp paths and bottom-side card lane are inherited through exact
unchanged copper and placement checks. The first local trial is preserved in
`initial-layout/`: it improved the immediate R3 entry but worsened the outer
contour. Its export manifests retain their historical paths and are not the
delivered ZIP. Only the final `evidence/` package has supplier acceptance.

## Module-pad reference decision

Retain In1.Cu beneath both module RF pads for this prototype. Their transverse
land width is 0.30 mm against the 0.36 mm main route, so the classic wide-land
capacitive discontinuity is not established by width alone. Both have In2.Cu
VBAT beneath them; opening In1.Cu would expose lower power copper. Bounded local
reroute trials found no alternative without other changes; that is not proof
that rerouting is impossible.

[Nordic recommends](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/ant_if.html)
reducing pad capacitance by opening nearby GND while avoiding exposure to noisy
routes and maintaining a continuous route reference. This prototype retains
the reference pending an actual transition model or measurement; it does not
claim the pad-capacitance recommendation has been fully implemented.
[AMD's transition guidance](https://docs.amd.com/r/en-US/ug583-ultrascale-pcb-design/SMT-Pads)
explains the wide-pad mechanism and the need for 3D analysis or measurement when
selecting a cutout. Its example is not an nRF9151 qualification.

The [r05i stack review](../power-r05i-rf-stack/README.md) still applies: the live
calculator, catalog and guide disagree on Er, etch, mask and finished-thickness
conventions. Supplier confirmation and impedance/loss measurements remain open.
The modeled 0.36 mm routes are a prototype candidate, not certified 50-ohm lines.

## Next work and release limits

PCB DFM is complete for this exact ZIP. The next local task is exact component
selection: R1/R16–R23 MPN, tolerance and TCR, followed by effective C9/C25/C26
bounds and the power-sequencing model. Do not start another routing revision just
to repeat the same green checks. Preserve this source before a justified edit.

Protected pack/NTC, antennas, operator field tests, factory BOM/CPL/programming/test,
harness/dock, positive retention and seal/material selection remain incomplete.
IP68 is a target with provisional 2 m fresh-water / 60-minute conditions; no
physical ingress test exists. Heart-rate sensing is not implemented.

**Electrical, RF and manufacturing release remain HOLD.** Copper balance and
PCB DFM do not establish reflow, working electronics or swimming performance.

```sh
python3 scripts/verify_rf_junction_candidate.py
.venv-dfm/bin/python scripts/check_rf_thickness_fit.py --trial experiments/power-r05j-rf-junctions
.venv-dfm/bin/python scripts/make_rf_junction_review.py
python3 scripts/resume.py
```

The seed/refinement scripts are source-bound one-shot history, not commands to
rerun over tested files. The checkpoint indexes the exact public source and reports.
