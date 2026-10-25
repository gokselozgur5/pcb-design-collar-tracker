#!/usr/bin/env python3
"""Release four screened signal transitions for a ground-constrained inner reroute."""
from pathlib import Path
import hashlib
import json
import math
import pcbnew as k
from trim_power_r05_tails import islands

root=Path(__file__).resolve().parents[1]
trial=root/'experiments/power-r05h-six-layer';pcb=trial/'hardware/collar-tracker.kicad_pcb'
g=json.loads((trial/'evidence/route-geometry.json').read_text())
source=hashlib.sha256(pcb.read_bytes()).hexdigest();assert source==g['source_sha256']
receipt=trial/'evidence/distant-vias-released.json';assert not receipt.exists()
expected={'8e9b4df1-9b50-4461-885e-b98225403b04','15db4be5-6530-477c-a74c-0cb8ae9415a3',
          '9505bdb5-6aaf-4d14-9302-75f9cc6ac86c','da077cfd-ac3b-445f-8f8c-e768cc4cf86a'}
ground=[v['pos'] for v in g['vias'] if v['net']=='/GND']
selected=[v for v in g['vias'] if v['net']!='/GND' and min(math.dist(v['pos'],p) for p in ground)>2]
assert {v['id'] for v in selected}==expected
allowed={'/VDD_NRF','/UV_DELAY','/COEX0','/HEALTH_CS'}
assert {v['net'] for v in selected}==allowed
board=k.LoadBoard(str(pcb));assert board.GetCopperLayerCount()==6
nets={p.GetNetname() for f in board.GetFootprints() for p in f.Pads()}
protected=islands(board,nets-allowed);before=islands(board,allowed)
items={t.m_Uuid.AsString():t for t in board.GetTracks()}
layers={board.GetLayerName(l):l for l in [k.F_Cu,k.In2_Cu,k.In3_Cu,k.B_Cu]}
vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6))
bridges=[]
for via in selected:
    assert items[via['id']].GetClass()=='PCB_VIA'
    for t in g['tracks']:
        if t['net']!=via['net']:continue
        a,z=t['start'],t['end'];dx,dy=z[0]-a[0],z[1]-a[1]
        q=max(0,min(1,((via['pos'][0]-a[0])*dx+(via['pos'][1]-a[1])*dy)/(dx*dx+dy*dy))) if dx or dy else 0
        contact=[a[0]+q*dx,a[1]+q*dy];distance=math.dist(contact,via['pos'])
        if distance<=1e-6 or distance>(via['diameter']+t['width'])/2+1e-6:continue
        assert t['layer'] in layers
        new=k.PCB_TRACK(board);new.SetStart(vec(via['pos']));new.SetEnd(vec(contact))
        new.SetWidth(k.FromMM(t['width']));new.SetLayer(layers[t['layer']])
        new.SetNet(board.FindNet(via['net']));new.SetLocked(True);board.Add(new)
        bridges.append(dict(id=new.m_Uuid.AsString(),net=via['net'],layer=t['layer'],
                            start=via['pos'],end=contact,width=t['width']))
    board.Delete(items[via['id']])
assert islands(board,nets-allowed)==protected
after=islands(board,allowed)
k.ZONE_FILLER(board).Fill(board.Zones())
(trial/'build/before-distant-via-release.kicad_pcb').write_bytes(pcb.read_bytes())
assert k.SaveBoard(str(pcb),board)
receipt.write_text(json.dumps(dict(before_sha256=source,
    source_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),removed=selected,
    planar_attachment_bridges=bridges,affected_before=before,affected_after=after,
    protected_terminal_groups=len(protected),
    scope='WIP reroute. Four signal transitions removed; no GND or RF copper removed. Full DRC and constrained replacement required.'
),indent=2)+'\n')
print('Removed four distant signal transitions; unrelated terminal groups preserved')
