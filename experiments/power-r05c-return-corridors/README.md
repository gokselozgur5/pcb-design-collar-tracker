# r05c routing checkpoint — WIP

Six connections closed: **14 → 8 opens**.

The saved PCB is not ready for manufacturing. There are 21 dangling-via warnings
and 11 gaps in the inherited 2 mm return-via screen. No r05c Gerber or JLC analysis
has been produced. The circuit still has the r05 electrical and component-selection
holds.

PCB SHA256: `74db248dedc96a0dd6f137ae8d443dc26bd2ce7fbad404614d4f19424e5acfd1`.

| Check | Saved result |
|---|---|
| Native DRC | 8 opens; 21 dangling vias; no other violations or schematic mismatches |
| GND | 97 physical pads, 94 unique terminals with local paths, 108 ground vias |
| Inner planes | Two continuous GND fills; no inner signal tracks |
| RF / SIM | 24 original RF segments; four clamp paths without bypass |
| Card entry | All 20 other bottom-side bodies clear the entry strip |
| Original power backbones | All 12 checked paths connected |
| Enclosure | Fresh preliminary screen checks 69 populated envelopes; no physical ingress test |

C26 moved beside U7 on the bottom. R18 moved into the supervisor's sense region.
R16/R19 and their adjacent vias were adjusted to close the feedback connection.
U7's local ground path was shortened. Four return-only stitches were removed where
they blocked accepted routes; their removal and the changed placement increased
the return-screen gaps. Those gaps still need repair.

The original circuit, manufacturer lands, native rules, RF and SIM topology were
preserved. `feedback-adjusted-drc.json` is the final native routing check.
`native-drc.json` is an identical copy for the checkpoint verifier.
The earlier stage reports retain their own source hashes; they are history, not
acceptance for these final bytes.

The remaining nets are VDD_NRF, VBAT, POWER_GOOD, FG_ALERT, NRF_ENABLE and VIO_ENABLE.
Both fixed-copper search implementations exhausted their current search regions.
Repeating them without a geometry change is not the next step.

Joint-routing experiments retain this board as the fallback. Their pin exits,
power backbones, RF, SIM and local grounds need to survive any accepted reroute.
Validate the full native board and restore return coverage before exporting.
The inherited `CT 0.5B` silk label also needs a deliberate final revision update.

```sh
python3 scripts/verify_routing_candidate.py experiments/power-r05c-return-corridors
```

This verifies saved evidence and explicit WIP status. It does not run KiCad,
JLC, electrical testing or swimming qualification.
