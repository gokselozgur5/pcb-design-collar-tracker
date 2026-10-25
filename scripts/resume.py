#!/usr/bin/env python3
"""Show the exact local resume point without changing CAD or contacting services."""
from pathlib import Path
import subprocess
import sys
from verify_handoff import verify

root = Path(__file__).resolve().parents[1]
try:
    result = verify()
except (ValueError, OSError, KeyError) as error:
    print(f'Resume preflight failed: {error}', file=sys.stderr)
    sys.exit(1)
print(f'Project: {root}')
print('Baseline: 0.3.4 saved PCB DFM evidence verified; not production acceptance.')
print('Preserved PCB: r04i native/geometry evidence and two unchanged-rule JLC PCB passes verified.')
candidate = result['charge_candidate']
print(f"Active: r05l hardware charge interlock; {candidate['native_drc']['unconnected_items']} open connections; "
      f"{len(candidate['supplier_records'])} verified same-ZIP JLC PCB passes.")
print(f"Other native violations/warnings: {candidate['native_drc']['violations']}; "
      f"schematic mismatches: {candidate['native_drc']['schematic_parity']}.")
print('Parts: 81 fitted references / 44 exact candidate MPNs; original 71 footprints and 27 RF segments preserved.')
print('Power: tolerance/TCR/leakage and typical-capacitance screens pass conditionally; powered and RF acceptance remain HOLD.')
print('Mechanical: r08 adds CAPH/ZETA prototype antennas, two nominal cable routes and four lid guides; 85 envelopes and four thickness cases checked.')
print('r09 pack/NTC request study raises the shell by 0.4mm; this is not an approved supplier part or a complete harness.')
print('r10 adds a keyed captive-PCB frame: 85 swept component envelopes, 27 cable poses and nine closed meshes checked at assigned ambient limits.')
print('Cable end datums/tolerances, feed bond, retention and physical thermal behavior remain unqualified.')
print('Charge: independent hot/cold comparators and NAND now drive /CE. Corner model passes conditionally; physical startup/thermal tests remain open.')
print('Next: resolve retention material/thermal fit, then pack retention and controlled harness/dock details. CT-BAT-001-A supplier-message approval is still pending.')
print('Preserved: r04i/swim-r02 review bundle; pack, antennas, assembly and physical qualification remain open.')
print('Git:')
sys.stdout.flush()
subprocess.run(['git', 'status', '--short', '--branch'], cwd=root, check=True)
print('\n' + (root / 'docs/STATUS.md').read_text())
print('Next: read docs/RESUME.md and docs/paul-nanosim.md, then execute the next unfinished step.')
