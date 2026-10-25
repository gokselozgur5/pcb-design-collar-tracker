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
candidate = result['rf_candidate']
print(f"Active: r05i RF geometry candidate; {candidate['native_drc']['unconnected_items']} open connections; "
      f"{len(candidate['supplier_records'])} verified same-ZIP JLC PCB passes.")
print(f"Other native violations/warnings: {candidate['native_drc']['violations']}; "
      f"schematic mismatches: {candidate['native_drc']['schematic_parity']}.")
print('Electrical/RF: HOLD; stack/etch/mask confirmation, module pad treatment, R3 balance and powered measurements remain open.')
print('Mechanical: 69 populated envelopes pass the modeled 0.71–0.91 mm thickness interval; nine part requirements remain unqualified.')
print('Preserved: r04i/swim-r02 review bundle; pack, antennas, assembly and physical qualification remain open.')
print('Git:')
sys.stdout.flush()
subprocess.run(['git', 'status', '--short', '--branch'], cwd=root, check=True)
print('\n' + (root / 'docs/STATUS.md').read_text())
print('Next: read docs/RESUME.md and docs/paul-nanosim.md, then execute the next unfinished step.')
