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
print('Current: r04i native/geometry evidence and two unchanged-rule JLC PCB passes verified.')
candidate = result['power_pin_candidate']
print(f"Active: r05b pin-exit candidate; {candidate['native_drc']['unconnected_items']} open connections, "
      f"{candidate['return_screen_gaps']} return-screen gaps; no new Gerber or supplier analysis.")
print('Native warnings: 27 dangling vias; zero other violations or schematic mismatches.')
print('Electrical: HOLD; conditional circuit calculations do not establish powered behavior.')
print('Mechanical: r03 preliminary fit checks 69 populated envelopes; nine component requirements remain unqualified.')
print('Preserved: r04i/swim-r02 review bundle; pack, antennas, assembly and physical qualification remain open.')
print('Git:')
sys.stdout.flush()
subprocess.run(['git', 'status', '--short', '--branch'], cwd=root, check=True)
print('\n' + (root / 'docs/STATUS.md').read_text())
print('Next: read docs/RESUME.md and docs/paul-nanosim.md, then execute the next unfinished step.')
