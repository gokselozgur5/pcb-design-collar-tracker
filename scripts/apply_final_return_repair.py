#!/usr/bin/env python3
"""Apply the bounded six-layer return repair before rerouting two signal crossings."""
from pathlib import Path
import hashlib
import json
import pcbnew as k
from trim_power_r05_tails import islands

root=Path(__file__).resolve().parents[1];trial=root/'experiments/power-r05h-six-layer'
pcb=trial/'hardware/collar-tracker.kicad_pcb';plan_path=trial/'evidence/final-return-repair-plan.json'
plan=json.loads(plan_path.read_text());receipt=trial/'evidence/final-return-repair-applied.json'
before=hashlib.sha256(pcb.read_bytes()).hexdigest();assert before==plan['before_sha256'] and not receipt.exists()
board=k.LoadBoard(str(pcb));assert board.GetCopperLayerCount()==6
nets={p.GetNetname() for f in board.GetFootprints() for p in f.Pads()}
allowed={'/UV_DELAY','/COEX0','/HEALTH_INT','/I2C_SDA'}
protected=islands(board,nets-allowed)
items={t.m_Uuid.AsString():t for t in board.GetTracks()}
vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6))
layers={board.GetLayerName(l):l for l in [k.F_Cu,k.In2_Cu,k.In3_Cu,k.B_Cu]}

def add_via(pos,net,uid=None):
    v=k.PCB_VIA(board);v.SetPosition(vec(pos));v.SetWidth(k.FromMM(.6));v.SetDrill(k.FromMM(.2))
    v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(board.FindNet(net))
    v.SetFrontTentingMode(k.TENTING_MODE_TENTED);v.SetBackTentingMode(k.TENTING_MODE_TENTED)
    if uid:
        assert uid not in items
        v.SetUuid(k.KIID(uid))
    board.Add(v);return v.m_Uuid.AsString()

for row in plan['restore']:
    assert row['net'] in {'/UV_DELAY','/COEX0'} and row['diameter']==.6 and row['drill']==.2
    add_via(row['pos'],row['net'],row['id'])
move=plan['ground_move'];v=items[move['id']]
assert v.GetNetname()=='/GND' and v.GetPosition()==vec(move['old'])
changed=[]
for t in board.GetTracks():
    if t.GetClass()!='PCB_TRACK' or t.GetNetname()!='/GND':continue
    touched=False
    if t.GetStart()==vec(move['old']):t.SetStart(vec(move['new']));touched=True
    if t.GetEnd()==vec(move['old']):t.SetEnd(vec(move['new']));touched=True
    if touched:changed.append(t.m_Uuid.AsString())
assert len(changed)==1
v.SetPosition(vec(move['new']))
new_tracks=[]
for row in plan['cuts']:
    old=items[row['id']]
    assert old.GetClass()=='PCB_TRACK' and old.GetNetname()==row['net'] in {'/HEALTH_INT','/I2C_SDA'}
    assert old.GetWidth()==k.FromMM(.2) and old.GetStart()==vec(row['start']) and old.GetEnd()==vec(row['end'])
    board.Delete(old)
    for piece in row['pieces']:
        assert len(piece)==2
        t=k.PCB_TRACK(board);t.SetStart(vec(piece[0]));t.SetEnd(vec(piece[1]))
        t.SetWidth(k.FromMM(.2));t.SetLayer(layers[row['layer']]);t.SetNet(board.FindNet(row['net']))
        t.SetLocked(True);board.Add(t);new_tracks.append(t.m_Uuid.AsString())
ground_id=add_via(plan['ground_add'],'/GND')
assert islands(board,nets-allowed)==protected
assert all(len(islands(board,{net}))==1 for net in ['/UV_DELAY','/COEX0'])
k.ZONE_FILLER(board).Fill(board.Zones())
(trial/'build/before-final-return-repair.kicad_pcb').write_bytes(pcb.read_bytes())
assert k.SaveBoard(str(pcb),board)
receipt.write_text(json.dumps(dict(before_sha256=before,source_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),
    plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),ground_id=ground_id,
    ground_track_changed=changed,new_tracks=new_tracks,protected_terminal_groups=len(protected),
    scope='UV_DELAY and COEX0 terminal groups restored; I2C_SDA and HEALTH_INT crossing repair and full native checks pending.'
),indent=2)+'\n')
print('Restored two transitions; added/moved their GND returns; unrelated terminal groups unchanged')
