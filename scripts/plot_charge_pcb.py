#!/usr/bin/env python3
"""Plot the saved r05l PCB without refilling or changing the board."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'experiments/power-r05l-charge-interlock/hardware/collar-tracker.kicad_pcb'
OUT=ROOT/'release/r05l-review'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    source=sha(PCB)
    operations=[]
    flags=['--mode-single','--fit-page-to-board','--exclude-drawing-sheet']
    for side,layers,mirror in [('top','F.Cu,F.Silkscreen,Edge.Cuts',False),
                               ('bottom','B.Cu,B.Silkscreen,Edge.Cuts',True)]:
        cmd=[str(ROOT/'scripts/kicad-cli'),'pcb','export','svg',*flags,'-l',layers,
             '-o',str(OUT/(side+'.svg'))]
        if mirror:cmd.append('--mirror')
        subprocess.run([*cmd,str(PCB)],check=True)
        subprocess.run(['rsvg-convert','-w','1400','-o',str(OUT/(side+'.png')),
                        str(OUT/(side+'.svg'))],check=True)
        operations.append(dict(side=side,layers=layers,mirror=mirror))
    assert sha(PCB)==source
    receipt=dict(pcb=str(PCB.relative_to(ROOT)),pcb_sha256=source,tool='KiCad CLI 10.0.7',
                 operations=operations,flags=flags,native_exit_codes=[0,0],
                 files={p.name:sha(p) for p in sorted(OUT.iterdir()) if p.name in ['top.svg','bottom.svg','top.png','bottom.png']},
                 scope='Read-only native PCB exports; no zone refill. Copper/silkscreen views, not a physical assembly.')
    (OUT/'plot-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':main()
