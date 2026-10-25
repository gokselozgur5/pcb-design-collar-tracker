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
candidate = result['selected_parts_candidate']
print(f"Active: r05k selected component candidate; {candidate['native_drc']['unconnected_items']} open connections; "
      f"{len(candidate['supplier_records'])} verified same-ZIP JLC PCB passes.")
print(f"Other native violations/warnings: {candidate['native_drc']['violations']}; "
      f"schematic mismatches: {candidate['native_drc']['schematic_parity']}.")
print('Parts: 65 fitted references / 38 exact candidate MPNs; four value changes; all r05j copper/placements preserved.')
print('Power: tolerance/TCR/leakage and typical-capacitance screens pass conditionally; powered and RF acceptance remain HOLD.')
print('Mechanical: 69 populated envelopes pass at 0.71–0.91 mm, with sourced heights replacing the nine resistor reservations.')
print('Next: protected NTC pack and actual antennas, then harness/dock/retention and factory firmware/programming/test.')
print('Preserved: r04i/swim-r02 review bundle; pack, antennas, assembly and physical qualification remain open.')
print('Git:')
sys.stdout.flush()
subprocess.run(['git', 'status', '--short', '--branch'], cwd=root, check=True)
print('\n' + (root / 'docs/STATUS.md').read_text())
print('Next: read docs/RESUME.md and docs/paul-nanosim.md, then execute the next unfinished step.')
