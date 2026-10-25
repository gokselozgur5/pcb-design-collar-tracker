#!/usr/bin/env python3
"""Prepare a preliminary r05b fit profile without inheriting r02 acceptance."""
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'mechanical/swim-r02-fit'
OUT = ROOT / 'mechanical/swim-r03-r05b-fit'
TRIAL = 'experiments/power-r05b-pin-exits'


def main():
    OUT.mkdir(exist_ok=True)
    assert not (OUT / 'fit-profile.json').exists(), 'Preserve subsequent fit edits'
    parts = json.loads((ROOT / TRIAL / 'hardware/design.json').read_text())['parts']
    active = {p['ref']: p for p in parts if p['onboard']}
    profile = json.loads((BASE / 'fit-profile.json').read_text())
    rows = {p['ref']: p for p in profile['parts'] if p['ref'] in active}
    rows['R1'].update(mpn=None, status='component_envelope_requirement', source_url=None,
                      basis='22 kOhm 1% 0402 component must fit the 0.40 mm height requirement; exact MPN and TCR remain unqualified.')

    def add(ref, mpn, height, url, basis, status='candidate_part'):
        rows[ref] = dict(ref=ref, mpn=mpn, height_max_mm=height, status=status,
                         source_url=url, basis=basis)

    add('C9', active['C9']['mpn'], 1.35,
        'https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM21BR71C105KA01-01.pdf',
        'T = 1.25 +/- 0.10 mm. Effective capacitance is not qualified by this dimensional screen.')
    add('C25', active['C25']['mpn'], .95,
        'https://www.murata.com/-/media/webrenewal/tool/library/common-pdf/static-model/component-list-s-mlcc-2506.ashx?cvid=20250805040438000000&la=ko-kr',
        'Manufacturer component list: T maximum 0.95 mm for GRM219R71E684KA88. Packaging suffix and effective capacitance remain candidates.')
    add('C26', 'GRM155R71C473KA01D', .55,
        'https://ds.murata.co.jp/simsurfing/mlcc.html?partnumbers=%5B%22GRM155R71C473KA01%22%5D',
        'Manufacturer model list: 47 nF, 16 V X7R, T maximum 0.55 mm. Effective capacitance and packaging suffix remain unqualified.')
    for ref in ('C27', 'C28', 'C29', 'C30'):
        add(ref, 'GRM155R71C104KA88D', .55,
            'https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM155R71C104KA88-01A.pdf',
            'Same 100 nF 16 V X7R drawing used in r02: T = 0.50 +/- 0.05 mm. Candidate, not released AVL.')
    for ref in ('U6', 'U7'):
        add(ref, active[ref]['mpn'], 1.45, 'https://www.ti.com/lit/ds/symlink/tps3808.pdf',
            'DBV0006A maximum height 1.45 mm; drawing 4214840/G 08/2024.')
    add('U8', active['U8']['mpn'], 1.1, 'https://www.ti.com/lit/ds/symlink/sn74lvc1g14.pdf',
        'DCK0005A maximum height 1.10 mm; drawing 4214834/G 11/2024.')
    add('Q1', active['Q1']['mpn'], 1.1, 'https://www.diodes.com/datasheet/download/DMN62D2UDW.pdf',
        'SOT363 A1 maximum 0.10 mm plus A2 maximum 1.00 mm; DS44897 Rev. 1-2 page 7.')
    add('U9', active['U9']['mpn'], .8, 'https://mds.analog.com/api/public/content/tdfn_21-0168.pdf',
        'T822-3 package A maximum 0.80 mm; 21-0168 Rev. M.')
    for i in range(16, 24):
        add('R' + str(i), None, .4, None,
            '0402 part height must be <= 0.40 mm before solder/warp allowance. Exact value, tolerance, TCR and MPN are unresolved. This is a required envelope, not a sourced part.',
            status='component_envelope_requirement')
    assert set(rows) == set(active) and len(rows) == 71
    profile.update(parts=[rows[r] for r in sorted(rows)], revision='swim-r03-r05b-fit',
                   scope='Preliminary 71-footprint r05b fit: sourced device/capacitor heights plus explicit unresolved resistor and harness requirements. No full assembly acceptance.')
    profile['open_items'] += [
        'R1/R16-R23 exact MPN, tolerance and TCR; height envelopes are requirements',
        'Refresh every source-bound fit check after the final routed PCB hash',
    ]
    (OUT / 'fit-profile.json').write_text(json.dumps(profile, indent=2) + '\n')
    parameters = json.loads((BASE / 'parameters.json').read_text())
    parameters['revision'] = 'swim-r03-r05b-fit'
    parameters['status'] = 'Preliminary r05b populated fit; electrical, assembly and ingress acceptance remain open'
    parameters['pcb']['trial'] = TRIAL
    (OUT / 'parameters.json').write_text(json.dumps(parameters, indent=2) + '\n')
    shutil.copy2(BASE / 'enclosure.scad', OUT / 'enclosure.scad')
    print('Prepared 71 fit entries; native export and dimensional checks remain pending.')


if __name__ == '__main__':
    main()
