# Preliminary fit after the power-layout changes

The native placements come from r05c. All 69 populated component envelopes pass
the dimensional screen; the 30 analytical shell checks also pass.

PCB SHA256: `74db248dedc96a0dd6f137ae8d443dc26bd2ce7fbad404614d4f19424e5acfd1`.

C26 is now on the bottom. The changed capacitor, resistor and supervisor-area
placements fit the existing carrier. The minimum checked gap remains C10 to the
carrier at 0.24 mm. The original carrier still fails the D1 negative control.

This uses the r03 component-height profile and r02 shell geometry. Nine resistor
height limits remain requirements, not sourced component approvals. Pack,
antennas, dock, harness, retention and seal selections remain open.

Body: 57.4 × 49.4 × 17.6 mm; 58.7 mm including the key.
Boot: 60.4 × 52.4 × 22.4 mm.

The swimming target remains provisional at 2 m fresh water for 60 minutes.
No physical ingress result, new mesh qualification or production approval is
claimed. Re-export native placements and rerun the checks after a PCB revision.
