#!/usr/bin/env python3
"""Require two fresh JLC checks of identical bytes before delivering 0.3.4."""
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import hashlib,json,math,re,shutil,zipfile
R=Path(__file__).resolve().parents[1]
T=R/'experiments/35x28-clearance-r034';E=T/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=json.loads((E/'export-source.json').read_text())
local=json.loads((E/'local-checks.json').read_text())
assert local['verified'] and local['source_sha256']==expected['pcb_sha256']
assert local['zip_sha256']==expected['zip_sha256']
pcb=T/'hardware/collar-tracker.kicad_pcb';archive=Path(expected['zip'])
assert sha(pcb)==expected['pcb_sha256'] and sha(archive)==expected['zip_sha256']
base=json.loads((R/'evidence/zero-warning-r033/repro033-finalname/dfm.json').read_text())
def rules(d):
 return {a['name']:{c['name']:(c['range'],c['type']) for c in a['categories']} for a in d['actions']}
reports=[]
for tag in ['candidate034-check1','candidate034-check2']:
 p=R/'evidence/zero-warning-r033'/tag
 receipt=json.loads((p/'upload-receipt.json').read_text())
 assert receipt['zip_sha256']==expected['zip_sha256']
 url=(p/'url.txt').read_text();assert parse_qs(urlparse(url).query)['pcbUploadFileId']==[receipt['record_id']]
 txt=(p/'latest.txt').read_text()
 rows=re.findall(r'([^\n]+)\t(\d+),\s*(\d+),\s*(\d+)\tDetails',txt)
 assert len(rows)==29 and all(int(d)==int(w)==0 for _,d,w,_ in rows)
 assert 'Unanalyzed' not in txt and 'Performing DFM' not in txt
 # Select the final analyzed response, not the initial unanalysed parse.
 analyzed=[];config=[]
 for f in sorted(p.glob('*downloadByFileAccessId.bin')):
  if zipfile.is_zipfile(f):
   with zipfile.ZipFile(f) as z:
    if 'dfm.json' in z.namelist():
     d=json.loads(z.read('dfm.json'))
     if any(a.get('results') for a in d['actions']):analyzed.append(d)
  elif f.read_bytes().startswith(b'{'):config.append(f)
 assert analyzed and len(config)==1
 d=analyzed[-1];assert rules(d)==rules(base)
 assert sha(config[0])=='f1bebb3b2b5ac2ba0579f882fc0605d169c1d6a3a852a07beb8652b719e0a725'
 green={}
 for a in d['actions']:
  if a['name']=='jlc_analysis_smt':assert not a['results'];continue
  assert a['results'],a['name']
  for layer in a['results']:
   for m in layer.get('meas') or []:
    c=a['categories'][m['cat_num']];s=m['meas_shape']
    assert c['type']=='CGT_LINE_SEGMENT' and len(s)==5 and s[2]=='L',(c,m)
    v=math.hypot(s[3]-s[0],s[4]-s[1]);assert v>=c['range'][1],(c,m)
    green[c['name']]=green.get(c['name'],0)+1
 info=d['check']['board_base_info'];assert info['cu_layers']==4
 assert abs(info['size']['x']*25.4-35)<.0001 and abs(info['size']['y']*25.4-28)<.0001
 pdf=p/'DFM analysis report_JLCDFM_collar-tracker-0.3.4-35x28-dfm.zip.pdf';assert pdf.stat().st_size>100000
 (p/'dfm.json').write_text(json.dumps(d,indent=2)+'\n')
 reports.append({'record_id':receipt['record_id'],'url':url,'zip_sha256':receipt['zip_sha256'],
  'pdf':str(pdf),'pdf_sha256':sha(pdf),'danger':0,'warning':0,'smt_checked':False,'green_counts':green})
assert reports[0]['record_id']!=reports[1]['record_id']
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for name in z.namelist():assert z.read(name)==(E/'gerbers'/name).read_bytes()
 files=len(z.namelist())
oldzip=R/'release/collar-tracker-0.3.3-35x28-dfm.zip'
assert sha(oldzip)=='6fc0fa2a60f7820cf1ea0a2b06f517fcde13f5683420a5f289cc2b1dabe0f312'
assert sha(R/'experiments/35x28-clearance-r033/hardware/collar-tracker.kicad_pcb')=='ab78d20c04a6b872dec1dfaad2b50d3995f3112f852905cbfc1ee378c5b992ea'
dest=R/'release/collar-tracker-0.3.4-35x28-dfm.zip';pdfdest=R/'release/collar-tracker-0.3.4-jlc-dfm-report.pdf'
for src,dst in [(archive,dest),(Path(reports[-1]['pdf']),pdfdest)]:
 if dst.exists():assert dst.read_bytes()==src.read_bytes()
 else:shutil.copy2(src,dst)
 assert sha(src)==sha(dst)
delivery={'source':str(pcb),'source_sha256':sha(pcb),'zip':str(dest),'zip_sha256':sha(dest),'bytes':dest.stat().st_size,'files':files,
 'pdf':str(pdfdest),'pdf_sha256':sha(pdfdest),'supplier_runs':reports,
 'native_errors':0,'native_warnings':0,'native_opens':0,'native_parity':0,'only_route_change':'U1.71 GND track .2 -> .3 mm',
 'unchanged_pads_masks_paste_vias_nets_rules':True,'old_033_preserved':True,
 'scope':'PCB DFM only; two fresh zero-result observations, not an assertion about all future runs or functional/SMT qualification.'}
(E/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
(R/'release/collar-tracker-0.3.4-verification.json').write_text(json.dumps(delivery,indent=2)+'\n')
print(json.dumps(delivery,indent=2))
