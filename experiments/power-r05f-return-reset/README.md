# r05f routing checkpoint — WIP

**Five open connections; zero other native DRC violations or warnings.**

Continue from this saved native project. It starts from r05c and keeps the working
original signal routes. The joint-routing alternatives were worse and were not
imported. No r05f Gerber or supplier analysis exists; electrical release remains
on HOLD.

PCB SHA256: `1b2b4bd7b90c3931bd8cbb151637408902332a94260d4a2a820ae6df04838a09`.

| Check | Result |
|---|---|
| Native DRC / parity | Five opens; no other violations, warnings or schematic mismatches |
| Open nets | NRF_ENABLE, VBAT, FG_ALERT; two VIO_ENABLE connections |
| Ground | 97 physical pads; all 94 unique terminals have local track paths |
| Planes / RF | Two continuous GND planes, no inner tracks; all 24 original RF segments retained |
| Vias / returns | 83 GND and 129 non-GND vias; **44 exceed the inherited 2 mm return screen** |
| SIM | Four clamp paths without bypass; 20 other bottom-side bodies clear the card entry strip |
| Power | All 12 original backbone checks pass; the new VDD_NRF control branch is connected |
| Enclosure | Fresh preliminary screen: 69 populated envelopes and 30 analytical shell checks pass |

The 25 removed return-only ground stitches need replacement after routing.
Local ground attachments and RF-adjacent ground vias were retained. The return
screen is deliberately unfinished; zero native geometry warnings does not make
this an accepted layout.

POWER_GOOD closed with a 68.085 mm candidate route. C9 moved to B.Cu at
(101.8, 114.3), closer to the modem ENABLE pin, and its signal connection closed.
Its new 1.118 mm ground track goes directly to a via without passing through
another component pad. Five unused signal exits and 14 unnecessary single-layer
via junctions were removed or replaced with planar connections. Ten whole loose
segments and a 0.65 mm unused end were then trimmed. Every applied cleanup retained
the native terminal groups; whole-segment deletion was refused where it would
disconnect a live branch. The newly available space allowed a 16.103 mm VDD_NRF
control connection to close. The original power trunks were not narrowed.

The planner's 100 mm candidate limit is not a manufacturing rule or approval of
the long POWER_GOOD path. Its detour still needs review. Native/supplier rules,
manufacturer lands, the circuit and original RF/SIM topology are unchanged.
The inherited `CT 0.5B` legend needs updating before a final export.

`native-drc.json` and the final source-bound audits describe these saved bytes.
Intermediate receipts keep their own source hashes. `final-search-routing.json`
records the last route; both exact-polygon and bounding-box region models still
separate the remaining nets. These are conservative planning models, not proof
that every possible native route is impossible. The VBAT model cannot enter the
charger pad center; its existing native power connection still passes.

**Next:** inspect the barriers at U7's enable pins, U4's enable exit and the gauge
connections. Make a small, measured placement or crossing change in an isolated
copy, preserving the existing power backbones, RF, SIM, local grounds and both
planes. Do not repeat the unchanged search or remove all working trunks again.
Finish the five connections, then restore and review all return paths, inspect
passive attachments, refresh fit and obtain two fresh same-ZIP JLC analyses.

The part/source-retention assumptions from r05 remain unqualified. Exact resistor
MPNs, battery/NTC, antennas, assembly/programming/test, enclosure retention and
physical ingress qualification are still open. This is not ready to order.

```sh
python3 scripts/verify_routing_candidate.py experiments/power-r05f-return-reset
```

This checks saved evidence; it performs no new KiCad, supplier or physical test.
