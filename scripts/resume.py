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
print('PCBA r01: actual JLC match 43/44 MPNs; 13 supplier-angle corrections; preview has 80/81 parts, missing mandatory Q1.')
print('Next manufacturing: resolve Q1, missing J6 model and J1/J2 library mapping, then complete placement/SMT review.')
print('Power: tolerance/TCR/leakage and typical-capacitance screens pass conditionally; powered and RF acceptance remain HOLD.')
print('Mechanical: r08 adds CAPH/ZETA prototype antennas, two nominal cable routes and four lid guides; 85 envelopes and four thickness cases checked.')
print('r09 pack/NTC request study raises the shell by 0.4mm; this is not an approved supplier part or a complete harness.')
print('r10 adds a keyed captive-PCB frame: 85 swept component envelopes, 27 cable poses and nine closed meshes checked at assigned ambient limits.')
print('r11 adds radial keys and conditional thermal fit: 85 envelopes, 27 cable poses and nine meshes checked; material and physical qualification remain open.')
print('r12 adds a pack cradle/cap: 85 component and lifted-pack checks, two changed meshes and seven CAD controls; supplier/physical acceptance remains open.')
print('r13 adds a sourced charging-dock prototype: 29 checks, three closed meshes and six CAD controls; holding/power/process acceptance remains open.')
print('r14 bounds constant-length wire movement: 42 checks, two housing meshes, six CAD controls and twelve tests. Physical cycling remains open.')
print('r15 implements a padded wire clamp and assembly fixture; geometry is checked, but actual endpoint retention remains unqualified.')
print('r16 implements rear contact terminal pockets; r18 corrects charge-wire thermal clearances at 27 static poses.')
print('r19 defines three staking regions and two forming nests; adhesion, continuous/installation motion and physical qualification remain open.')
print('Published review: release/r16-current-review/review.pdf and release/collar-tracker-r05l-r16-review.zip. Latest addendum: assembly/internal-charge-r03/restraint-sheet.pdf.')
print('Cable end datums/tolerances, feed bond, retention and physical thermal behavior remain unqualified.')
print('Charge: independent hot/cold comparators and NAND now drive /CE. Corner model passes conditionally; physical startup/thermal tests remain open.')
print('Tracker r02: DNS caller deadlines and watchdog/modem recovery; target build and host tests only, no flashing or observed hardware reset.')
print('Tracker r03: development-signed boot and bounded trial built/tested; no flashing. Further OTA work is deferred behind manufacturing review.')
print('Next assembly: continuous/installation motion with r19 attachments, released wire shape and adhesion. Supplier-message approval remains pending.')
print('Preserved: r04i/swim-r02 review bundle; pack, antennas, assembly and physical qualification remain open.')
print('Git:')
sys.stdout.flush()
subprocess.run(['git', 'status', '--short', '--branch'], cwd=root, check=True)
print('\n' + (root / 'docs/STATUS.md').read_text())
print('Next: read docs/RESUME.md and docs/paul-nanosim.md, then execute the next unfinished step.')
