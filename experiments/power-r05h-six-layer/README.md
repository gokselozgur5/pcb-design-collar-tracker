# r05h — PCB DFM complete, electrical release on hold

The six-layer 40 × 32 × nominal 0.8 mm board is fully connected. Native DRC, ERC
and schematic parity have zero findings. Two fresh JLC PCB analyses of the same
final ZIP each report **0 Danger / 0 Warning / 449 Good**, with all 29 rows analyzed.

[Design review](evidence/review.pdf) ·
[Final Gerber ZIP](evidence/collar-tracker-05h-final2-40x32-dfm.zip) ·
[JLC report 1](evidence/jlc-final-check1/report.pdf) ·
[JLC report 2](evidence/jlc-final-check2/report.pdf) ·
[Top](evidence/top.png) · [Bottom](evidence/bottom.png)

| Check | Result |
|---|---|
| Parts / ground | 71 footprints; 97 physical GND pads, all 94 unique terminals locally connected |
| Planes | Dedicated GND on In1.Cu and In4.Cu; one continuous fill each; all 110 GND vias inside both |
| Routing | F.Cu, In2.Cu, In3.Cu and B.Cu; no tracks on either GND layer |
| Returns | All 128 non-GND vias within 2 mm of GND; maximum 1.986755 mm |
| RF | 24 original RF segments unchanged; the new stack still needs impedance qualification |
| SIM | Four clamp paths without copper bypass; 20 other bottom-side bodies clear the entry strip |
| Power | All 12 original backbone paths connected; original trunks not narrowed |
| Fit | 69 populated envelopes and 30 shell checks pass at nominal board thickness |
| Supplier | Records `637343111455133697` and `637343305880473601`; unchanged rules; SMT off |

PCB SHA256: `aecb8e431819fa2aa23dfecc98ff1f6a064b5ae81afe7679a6e317f3571c3171`.
Final ZIP SHA256: `2cae8b12bdf20b3c8633f8db0c59cc6911a49a43ed82e1e1bdc381e6a9d69e34`.

Two added routing layers resolved the five connections left by r05f without
reusing either dedicated ground plane. The POWER_GOOD replacement route is
18.214 mm with no new vias, replacing the earlier 68.085 mm detour. Return work
added 27 GND vias, moved two signal transitions and rerouted two others. Every
cleanup preserved native terminal groups; live branches inside reported dangling
segments were retained. C30 now has equal 0.2 mm pad attachments, with unchanged
lands. C20's unique-copper contour ratio remains about 1.14; overlapping segment
counts alone exaggerate that attachment imbalance.

The first JLC package had four Danger and two Warning findings at the CT/NTC
silkscreen. The full-size text moved by (1.9, 0.2) mm and (-0.2, 0) mm respectively.
That rejected package and report remain separate. Only `final2` is the accepted
PCB DFM input. No rules, exclusions, manufacturer lands or font sizes were weakened.

## Remaining release work

This is PCB manufacturing geometry evidence, not approval for a finished PCBA.
The unchanged r05 circuit still needs source/bench qualification, exact resistor
MPNs/tolerances/TCR, battery/NTC and antenna selection, factory BOM/CPL/programming
and functional-test acceptance. Heart-rate sensing remains unimplemented.

Six-layer 0.8 mm manufacturing is listed by [JLCPCB](https://jlcpcb.com/6-layer-pcb).
The dielectric stack and finished-thickness tolerance are not yet selected. The
original 0.2 mm RF geometry cannot establish 50 ohms on a new stack; resolve that
before RF or production release. Copper DCR estimates use provisional 35/17.5 µm
outer/inner foil and conservative full-depth via resistance.

The [r06 fit](../../mechanical/swim-r06-six-layer-fit/README.md) retains a swimming
prototype with a provisional 2 m fresh-water / 60-minute target. Pack, antennas,
harness, dock, positive PCB retention, material/seal choices and physical ingress
qualification remain open. IP68 has not been demonstrated.

**Next:** select and model the actual six-layer stack and RF geometry, then close
the remaining circuit/BOM/pack/antenna and factory-test requirements. Preserve
these tested bytes; any PCB change needs fresh native checks, export and two
same-ZIP supplier runs.

```sh
python3 scripts/verify_routing_candidate.py experiments/power-r05h-six-layer
```

The saved native project is authoritative. Do not rerun historical seed scripts
over it. Intermediate receipts retain their own hashes; final source-bound audits
and supplier records are indexed by `evidence/routing-checkpoint.json`.
