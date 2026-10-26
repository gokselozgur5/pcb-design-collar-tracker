#!/usr/bin/env python3
"""Make a compact r16 review from the actual exported previews and measurements."""
import json
from pathlib import Path
import shutil

import package_charge_review as drawing

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/swim-r16-contact-retention'


def main():
    r=json.loads((OUT/'checks.json').read_text())
    assert r['result']=='CONTACT_RETENTION_GEOMETRY_PASS'
    drawing.OUT=OUT
    drawing.page('contact-retention-sheet','CT-CONTACT-RET-001-A / REAR CONTACT RETENTION',
        'Geometric prototype. Internal wire routing, factory process and physical qualification remain open.',
        [(OUT/'review.png','r16 / unchanged outside size; new dry-side bearing pockets'),
         (OUT/'section.png','r16 / custom terminals, washer and M3 thin nut')],
        ['CHANGED / DIMENSIONS IN mm',
         'Bearing faces: case X=22.60 +/-0.05.',
         'Contact stem: 5.90 +/-0.05; M3 x 0.5 thread: 4.80.',
         'Terminal base: 9.0 wide; Z=2.35 to 8.65; 1.0 thick.',
         'Tail: 0.50 thick above Z=9.25; 1.20 wire hole.',
         'Positive tail: Y=-3.30, Z=13.30; red to J3.1.',
         'Ground tail: Y=+6.00, Z=13.30; black to J3.2.',
         'Washer HRDW-M3-A2 / nut HFN-M3-A2 candidates.'],
        ['CHECKED / NOT A FINISHED CHARGING PATH',
         'Old 6.4mm circular stack is smaller than the bore.',
         'New plate bears on both sides of the 7.34mm bore.',
         'Minimum calculated ear bearing: 4.413mm2 each.',
         'All 85 swept populated envelopes clear new metal.',
         'Minimum component gap: 2.146mm at C10.',
         'Head, seal glands and dock contact locations retained.',
         'PCB/Gerber unchanged: both actual JLC runs 0/0/455.'],
        ['Custom machined terminals; use contact.json and contacts.scad. Not a purchased Keystone lug or a plastic printed part.',
         'Torque, pull, resistance, plating, creep and water/dust tests remain open. No supplier enquiry or order was sent.'])


if __name__=='__main__':main()
