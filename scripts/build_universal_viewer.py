#!/usr/bin/env python3
"""Build the offline, single-file viewer from the exported design solids."""
import base64
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/universal-mount-r01'
ASSETS=OUT/'viewer-assets'

def encoded(path):
    return base64.b64encode(path.read_bytes()).decode()

def main():
    provenance=json.loads((ASSETS/'provenance.json').read_text())
    library=ASSETS/'three.bundle.mjs'
    assert hashlib.sha256(library.read_bytes()).hexdigest()==provenance['sha256']
    names=['body','lid','boot','flat_pad','round_pad','carrier','retainer','battery',
           'pcb_substrate','pcb_components','contacts','gasket','antennas','terminals',
           'charge_wires','fasteners','rf','staking','strap_short','strap_long']
    names += [case+'_'+kind for case in ['narrow','standard','wide','rope_small','rope','rope_large']
              for kind in ['collar','installed_straps']]
    payload={'three':encoded(library),'meshes':{name:encoded(OUT/(name+'.stl')) for name in names}}
    page=(ASSETS/'viewer.template.html').read_text()
    page=page.replace('__PCB_IMAGE__','data:image/png;base64,'+encoded(OUT/'pcb-top.png'))
    page=page.replace('__MODEL_DATA__',json.dumps(payload,separators=(',',':')))
    page=page.replace('__VIEWER_CODE__',(ASSETS/'viewer.mjs').read_text())
    (OUT/'viewer.html').write_text(page)
    print('Offline viewer:',len(page),'bytes;',len(names),'meshes')

if __name__=='__main__':main()
