#!/usr/bin/env python3
"""Preserve reviewed manufacturing evidence without browser/session captures."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import zipfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('capture',type=Path)
parser.add_argument('output',type=Path)
parser.add_argument('zip',type=Path)
parser.add_argument('--allow-findings',action='store_true')
a=parser.parse_args();root=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((a.capture/'upload-receipt.json').read_text())
assert receipt['zip_sha256']==sha(a.zip)
rows=re.findall(r'([^\n]+)\t(\d+),\s*(\d+),\s*(\d+)\tDetails',(a.capture/'latest.txt').read_text())
assert len(rows)==29
assert receipt['record_id'] in (a.capture/'url.txt').read_text()
profiles=[];reports=[]
for path in sorted(a.capture.glob('*downloadByFileAccessId.bin')):
 if path.read_bytes().startswith(b'{'):
  d=json.loads(path.read_text())
  if 'jlc_analysis_ss' in d:profiles.append(path)
 elif zipfile.is_zipfile(path):
  with zipfile.ZipFile(path) as z:
   for name in z.namelist():
    if Path(name).name!='dfm.json':continue
    raw=z.read(name);d=json.loads(raw)
    if 'actions' in d and all(x['name']=='jlc_analysis_smt' or x['results'] for x in d['actions']):reports.append((path,raw,d))
assert len(profiles)==1 and reports
rules=profiles[0];assert sha(rules)=='f1bebb3b2b5ac2ba0579f882fc0605d169c1d6a3a852a07beb8652b719e0a725'
raw,dfm=reports[-1][1:];counts={'danger':0,'warning':0,'good':0};measurements=0
for action in dfm['actions']:
 if action['name']=='jlc_analysis_smt':assert not action['results'];continue
 for layer in action['results']:
  for measure in layer.get('meas') or []:
   cat=action['categories'][measure['cat_num']];shape=measure['meas_shape']
   assert cat['type']=='CGT_LINE_SEGMENT' and len(shape)==5 and shape[2]=='L'
   value=math.hypot(shape[3]-shape[0],shape[4]-shape[1]);measurements+=1
   counts['danger' if value<cat['range'][0] else 'warning' if value<cat['range'][1] else 'good']+=1
ui={'danger':sum(int(r[1]) for r in rows),'warning':sum(int(r[2]) for r in rows),'good':sum(int(r[3]) for r in rows)}
assert counts==ui,(counts,ui)
if not a.allow_findings:assert counts['danger']==counts['warning']==0
pdfs=list(a.capture.glob('*.pdf'));assert len(pdfs)==1 and pdfs[0].read_bytes().startswith(b'%PDF')
assert not a.output.exists(),'Preserve prior evidence'
a.output.mkdir(parents=True)
receipt['zip']=str(a.zip.resolve().relative_to(root))
(a.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
(a.output/'rows.txt').write_text('\n'.join(f'{n}\t{d}, {w}, {g}\tDetails' for n,d,w,g in rows)+'\n')
(a.output/'dfm.json').write_bytes(raw)
shutil.copyfile(rules,a.output/'rules.json')
shutil.copyfile(pdfs[0],a.output/'report.pdf')
shutil.copyfile(a.capture/'screen.png',a.output/'screen.png')
summary=dict(record_id=receipt['record_id'],zip_sha256=receipt['zip_sha256'],rules_sha256=sha(rules),analyzed_rows=len(rows),measurement_count=measurements,counts=counts,smt_analyzed=False,scope='PCB DFM only. No PCBA, powered hardware, RF or ingress acceptance.')
(a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
