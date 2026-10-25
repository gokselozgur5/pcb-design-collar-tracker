#!/usr/bin/env python3
"""Remove reported unused signal vias only when all native terminal groups survive.

These temporary exits can prevent the planner from placing a useful via nearby.
Ground/RF/SIM are protected. Fresh DRC and return checks remain required.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pcbnew as k
from trim_power_r05_tails import islands

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('trial',type=Path)
p.add_argument('--drc',type=Path,required=True)
p.add_argument('--state',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--only-net',action='append',default=[])
a=p.parse_args()
assert a.trial.name=='power-r05f-return-reset'
assert not a.output.exists()
pcb=a.trial/'hardware/collar-tracker.kicad_pcb'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before_sha=sha(pcb);assert json.loads(a.state.read_text())['source_sha256']==before_sha
d=json.loads(a.drc.read_text())
assert not d['schematic_parity']
assert all(v['type'] in {'via_dangling','track_dangling'} for v in d['violations'])
b=k.LoadBoard(str(pcb));tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
protected={'/GND','/LTE_RF','/LTE_ANT','/GPS_RF','/GNSS_ANT','/GNSS_FEM_IN',
           '/GNSS_FEM_OUT','/FILT_OUT','/AMP_IN','/SIM_1V8','/SIM_CLK','/SIM_IO','/SIM_RST'}
ids={v['items'][0]['uuid'] for v in d['violations'] if v['type']=='via_dangling'}
assert ids and ids<=tracks.keys()
if a.only_net:
 ids={uid for uid in ids if tracks[uid].GetNetname() in a.only_net}
assert ids,'No unused vias matched the requested nets'
nets={p.GetNetname() for f in b.GetFootprints() for p in f.Pads()}
before=islands(b,nets);removed=[]
for uid in sorted(ids):
 t=tracks[uid]
 assert t.GetClass()=='PCB_VIA' and t.GetNetname() not in protected
 removed.append({'id':uid,'net':t.GetNetname(),'position':[t.GetPosition().x/1e6,t.GetPosition().y/1e6]})
 b.Delete(t)
assert islands(b,nets)==before,'Unused-exit removal changed a native terminal group; not saved'
k.ZONE_FILLER(b).Fill(b.Zones());assert k.SaveBoard(str(pcb),b)
a.output.write_text(json.dumps({'before_sha256':before_sha,'source_sha256':sha(pcb),
    'drc_sha256':sha(a.drc),'input_state_sha256':sha(a.state),'removed':removed,'only_nets':a.only_net,
    'native_terminal_groups_preserved':len(before),
    'scope':'Unused temporary exits removed. Full native DRC, routing and return review still required.'},indent=2)+'\n')
print('Removed',len(removed),'unused vias; preserved',len(before),'native terminal groups')
