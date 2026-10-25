#!/usr/bin/env python3
"""Bind the tested PCB/ZIP/JLC result and deliver the exact analyzed bytes."""
from pathlib import Path
import hashlib,json,math,re,shutil,zipfile
R=Path(__file__).resolve().parents[1]
T=R/'experiments/35x28-clearance-r033';E=T/'evidence'
B=R/'evidence/zero-warning-r033/baseline032-result'
J=R/'evidence/zero-warning-r033/candidate033-1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pcb=T/'hardware/collar-tracker.kicad_pcb'
assert sha(pcb)=='ab78d20c04a6b872dec1dfaad2b50d3995f3112f852905cbfc1ee378c5b992ea'
archive=E/'collar-tracker-0.3.3-iteration1.zip'
assert sha(archive)=='6fc0fa2a60f7820cf1ea0a2b06f517fcde13f5683420a5f289cc2b1dabe0f312'
d=json.loads((E/'drc.json').read_text())
assert not any(d[k] for k in ['violations','unconnected_items','schematic_parity'])
assert (E/'drc.json').stat().st_mtime>=pcb.stat().st_mtime
local=json.loads((E/'iteration1-local-checks.json').read_text())
assert sum(x['pads'] for x in local['sides'].values())==268
assert all(not x['uncovered'] and not x['pad_gaps_below_6mil'] and x['mask_bridges_below_6mil']==0 for x in local['sides'].values())
basehw=R/'experiments/35x28-zero-r033/hardware'
for name in ['collar-tracker.kicad_pro','collar-tracker.kicad_dru','collar-tracker.kicad_sch']:
 assert (basehw/name).read_bytes()==(T/'hardware'/name).read_bytes()
for name in ['collar-tracker-PTH.drl','collar-tracker-NPTH.drl']:
 norm=lambda s:'\n'.join(l for l in s.splitlines() if not l.startswith(('; DRILL file','; #@! TF.CreationDate,')))
 assert norm((R/'release/collar-tracker-0.3.2-35x28-dfm'/name).read_text())==norm((E/'iteration1-gerbers'/name).read_text())
old={'release/collar-tracker-0.3.2-35x28-dfm.zip':'c09893e5c211a3e98fdaba4b1ae3fafa7e17e737543e1a02530f64e386254d04',
 'release/collar-tracker-0.3.1-35x28-dfm.zip':'616a26fcc55a17004994cd455970d1841c65877e6102e5f5bbb29f50c6a83ffc',
 'experiments/35x28-zero-r033/hardware/collar-tracker.kicad_pcb':'345544f51eec67767cb7154620392a062bba0ac8ea19051c3e0de5a2beee255b',
 'experiments/35x28-mask-r032/hardware/collar-tracker.kicad_pcb':'4dbc5ce1fe08628c8239f155c70aed1a46200ec83cbfd1dc0b765716c79e0b18',
 'hardware/collar-tracker.kicad_pcb':'61d6f37123e53f4f5284e3da7178212036f7e0b26254874c8b8d93de76ec7929'}
assert all(sha(R/f)==h for f,h in old.items())
cfg=lambda p:next(f for f in p.glob('*downloadByFileAccessId.bin') if f.read_bytes().startswith(b'{'))
assert cfg(B).read_bytes()==cfg(J).read_bytes()
before=json.loads((B/'dfm.json').read_text());after=json.loads((J/'dfm.json').read_text())
rules=lambda d:[(a['name'],[(c['name'],c['range'],c['type']) for c in a['categories']]) for a in d['actions']]
assert rules(before)==rules(after)
counts={}
for a in after['actions']:
 if a['name']=='jlc_analysis_smt':
  assert not a['results'];continue
 assert a['results']
 for layer in a['results']:
  for m in layer.get('meas') or []:
   c=a['categories'][m['cat_num']];shape=m['meas_shape']
   assert c['type']=='CGT_LINE_SEGMENT',('Unexpected flagged object',c,m)
   assert len(shape)==5 and shape[2]=='L'
   value=math.hypot(shape[3]-shape[0],shape[4]-shape[1])
   assert value>=c['range'][1],('Not green',c,m)
   counts[c['name']]=counts.get(c['name'],0)+1
info=after['check']['board_base_info']
assert info['cu_layers']==4
assert abs(info['size']['x']*25.4-35)<.0001 and abs(info['size']['y']*25.4-28)<.0001
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for name in z.namelist():assert z.read(name)==(E/'iteration1-gerbers'/name).read_bytes()
 files=len(z.namelist())
pdf=J/'DFM analysis report_JLCDFM_collar-tracker-0.3.3-iteration1.zip.pdf'
assert pdf.is_file() and pdf.stat().st_size>100000
dest=R/'release/collar-tracker-0.3.3-35x28-dfm.zip'
report=R/'release/collar-tracker-0.3.3-jlc-dfm-report.pdf'
for src,dst in [(archive,dest),(pdf,report)]:
 if dst.exists():assert dst.read_bytes()==src.read_bytes(),'Refuse to replace existing release'
 else:shutil.copy2(src,dst)
 assert sha(src)==sha(dst)
receipt={'pcb':str(pcb),'pcb_sha256':sha(pcb),'zip':str(dest),'zip_sha256':sha(dest),'zip_bytes':dest.stat().st_size,'files':files,
 'report':str(report),'report_sha256':sha(report),'jlc_url':'https://jlcdfm.com/viewer?pcbUploadFileId=637105049294819330',
 'jlc_report_time':'2026-10-25 06:29:27 Europe/Istanbul','jlc_danger':0,'jlc_warning':0,'jlc_pcb_analyzed':True,'jlc_smt_analyzed':False,
 'native_errors':0,'native_warnings':0,'native_opens':0,'native_parity':0,'same_rules_sha256':sha(cfg(J)),
 'all_pads_exposed':268,'mask_bridge_minimum_mm':.155,'board_mm':[35,28,.8],'unchanged_drilled_holes':77,
 'exact_tested_zip_bytes_delivered':True,'old_sources_releases_unchanged':True,'jlc_green_counts':counts,
 'limitation':'PCB DFM only; U5 customized land and U2 mask process choices still need assembly qualification. BOM/power/RF/eSIM/firmware/fixture/enclosure remain open; not order-ready PCBA.'}
(E/'delivery.json').write_text(json.dumps(receipt,indent=2)+'\n')
(R/'release/collar-tracker-0.3.3-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
