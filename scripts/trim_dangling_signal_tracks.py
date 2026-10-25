#!/usr/bin/env python3
"""Remove native-reported signal tails only if every terminal group is unchanged."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
import pcbnew as k
from trim_power_r05_tails import islands

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('trial',type=Path);p.add_argument('--drc',type=Path,required=True)
p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
p.add_argument('--probe-ids-json',help=argparse.SUPPRESS)
a=p.parse_args();assert a.trial.name=='power-r05f-return-reset' and not a.output.exists()
pcb=a.trial/'hardware/collar-tracker.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before_sha=sha(pcb);assert json.loads(a.state.read_text())['source_sha256']==before_sha
d=json.loads(a.drc.read_text());assert not d['schematic_parity']
assert all(v['type'] in {'track_dangling','via_dangling'} for v in d['violations'])
ids={v['items'][0]['uuid'] for v in d['violations'] if v['type']=='track_dangling'}
assert ids,'No reported tails'
b=k.LoadBoard(str(pcb));tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};assert ids<=tracks.keys()
protected={'/GND','/LTE_RF','/LTE_ANT','/GPS_RF','/GNSS_ANT','/GNSS_FEM_IN','/GNSS_FEM_OUT','/FILT_OUT','/AMP_IN','/SIM_1V8','/SIM_CLK','/SIM_IO','/SIM_RST'}
nets={p.GetNetname() for f in b.GetFootprints() for p in f.Pads()};before=islands(b,nets);removed=[];retained=[]
if a.probe_ids_json:
 probe_ids=json.loads(a.probe_ids_json);assert set(probe_ids)<=ids
 for uid in probe_ids:b.Delete(tracks[uid])
 sys.exit(0 if islands(b,nets)==before else 3)
for uid in sorted(ids):
 t=tracks[uid];assert t.GetClass()=='PCB_TRACK' and t.GetNetname() not in protected
 # A reported loose end can belong to a segment that also joins live branches
 # partway along its length. Never delete that entire segment to clear a warning.
 # One native LoadBoard per process avoids wx duplicate-handler initialization.
 probe_ids=[r['id'] for r in removed]+[uid]
 probe=subprocess.run([sys.executable,str(Path(__file__).resolve()),*sys.argv[1:],
                       '--probe-ids-json',json.dumps(probe_ids)],capture_output=True,text=True)
 assert probe.returncode in {0,3},('Native probe failed',probe.returncode,probe.stderr[-1000:])
 if probe.returncode==0:removed.append({'id':uid,'net':t.GetNetname()})
 else:retained.append({'id':uid,'net':t.GetNetname(),'reason':'Whole-segment deletion would change native terminal groups; inspect and trim only the loose end.'})
for row in removed:b.Delete(tracks[row['id']])
assert islands(b,nets)==before,'Tail deletion changed native terminal groups; not saved'
k.ZONE_FILLER(b).Fill(b.Zones());assert k.SaveBoard(str(pcb),b)
a.output.write_text(json.dumps({'before_sha256':before_sha,'source_sha256':sha(pcb),
 'input_state_sha256':sha(a.state),'drc_sha256':sha(a.drc),'removed':removed,'retained':retained,
 'native_terminal_groups_preserved':len(before),'scope':'Unused tails removed; fresh native DRC required.'},indent=2)+'\n')
print('Trimmed',len(removed),'tails; all',len(before),'native terminal groups retained')
