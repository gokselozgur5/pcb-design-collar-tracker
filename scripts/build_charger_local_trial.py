#!/usr/bin/env python3
"""Apply the reviewed charger placement while retaining remote routed copper.

The r04c whole-net trial discarded working U1 escapes and misread the mirrored
SIM opening. Keep r04's original J6 orientation and D1 behind its closed end.
Only the charger neighborhood is replaced; new native DRC remains mandatory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import pcbnew as k

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--name',default='paul-nanosim-r04d')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
parent=root/'experiments/paul-nanosim-r04'
donor=root/'experiments/paul-nanosim-r04c'
trial=root/'experiments'/args.name
assert args.name.startswith('paul-nanosim-') and '/' not in args.name
assert not trial.exists(), 'Never overwrite an existing trial'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old_pcb=parent/'hardware/collar-tracker.kicad_pcb'
new_pcb=donor/'hardware/collar-tracker.kicad_pcb'
assert sha(old_pcb)=='2e9c0666d6561330a5ad5608c65ae7d49485f0731130f3652b0a99ce19004398'
assert sha(new_pcb)=='566a82b06209dc240ee8fc700828fc764d48851de7053de13f951260eac72d12'
for name in ['build','evidence','previews']:(trial/name).mkdir(parents=True)
shutil.copytree(parent/'hardware',trial/'hardware')
board=k.LoadBoard(str(old_pcb));candidate=k.LoadBoard(str(new_pcb))
fps={f.GetReference():f for f in board.GetFootprints()}
v=lambda x,y:k.VECTOR2I(round(x*1e6),round(y*1e6))
xy=lambda p:[p.x/1e6,p.y/1e6]
poses={'U3':(105,123,0,k.F_Cu),'C17':(106.2,120.2,90,k.B_Cu),
       'C18':(103,120.85,0,k.F_Cu),'C19':(101.8,122.5,180,k.F_Cu)}
for ref,(x,y,angle,layer) in poses.items():
    f=fps[ref]
    if f.GetLayer()!=layer:f.SetLayerAndFlip(layer)
    f.SetOrientationDegrees(angle);f.SetPosition(v(x,y))
assert fps['J6'].GetOrientationDegrees()==0 and fps['J6'].IsFlipped()

# TI DCK land and paste example, preserving the original rear socket placement.
f=fps['D1'];cx,cy=xy(f.GetPosition())
assert f.IsFlipped() and f.GetOrientationDegrees()==0
for p in f.Pads():
    x,y=xy(p.GetPosition())
    p.SetPosition(v(cx+(1.1 if x>cx else -1.1),y))
    p.SetSize(v(.9,.4));p.SetRoundRectRadiusRatio(.125)
for g in list(f.GraphicalItems()):
    if g.GetLayer() in [k.F_CrtYd,k.B_CrtYd]:f.Delete(g)
outline=k.PCB_SHAPE(f);outline.SetShape(k.SHAPE_T_RECT)
outline.SetStart(v(cx-1.8,cy-1.25));outline.SetEnd(v(cx+1.8,cy+1.25))
outline.SetWidth(50000);outline.SetLayer(k.B_CrtYd);f.Add(outline)
shutil.copy2(donor/'hardware/Collar04.pretty/TPD4E1U06DCKR.kicad_mod',
             trial/'hardware/Collar04.pretty/TPD4E1U06DCKR.kicad_mod')

original_ids={t.m_Uuid.AsString() for t in board.GetTracks()}
charger_nets={'/VIN_5V','/VBAT','/VSYS','/CHG_FAULT','/CHG_STAT','/BAT_NTC','/ILIM_VSET','/ISET'}
def intersects(t,bounds):
    if t.GetClass()=='PCB_VIA':points=[xy(t.GetPosition())]
    else:points=[xy(t.GetStart()),xy(t.GetEnd())]
    x1,y1,x2,y2=bounds
    # Bounding-box selection deliberately removes complete crossing segments.
    return min(p[0] for p in points)<=x2 and max(p[0] for p in points)>=x1 and min(p[1] for p in points)<=y2 and max(p[1] for p in points)>=y1
ground_region=(100,119,110,128)
charger_region=(100,119.5,109.3,124.9)
removed=[]
for t in list(board.GetTracks()):
    if (t.GetNetname()=='/GND' and intersects(t,ground_region) or
            t.GetNetname() in charger_nets and intersects(t,charger_region)):
        removed.append(t.m_Uuid.AsString());board.Delete(t)
added=[];protected=[]
for t in candidate.GetTracks():
    ground=t.GetNetname()=='/GND' and intersects(t,ground_region)
    fanout=t.GetNetname() in charger_nets and t.m_Uuid.AsString() not in original_ids
    if not (ground or fanout):continue
    if t.GetClass()=='PCB_VIA':
        item=k.PCB_VIA(board);item.SetPosition(t.GetPosition());item.SetWidth(600000);item.SetDrill(200000)
        item.SetViaType(k.VIATYPE_THROUGH);item.SetLayerPair(k.F_Cu,k.B_Cu)
        item.SetFrontTentingMode(k.TENTING_MODE_TENTED);item.SetBackTentingMode(k.TENTING_MODE_TENTED)
    else:
        item=k.PCB_TRACK(board);item.SetStart(t.GetStart());item.SetEnd(t.GetEnd())
        item.SetWidth(t.GetWidth());item.SetLayer(t.GetLayer())
    item.SetNet(board.FindNet(t.GetNetname()));item.SetLocked(True);board.Add(item)
    added.append(item.m_Uuid.AsString())
    if fanout:protected.append(item.m_Uuid.AsString())
board.BuildConnectivity();k.ZONE_FILLER(board).Fill(board.Zones())
target=trial/'hardware/collar-tracker.kicad_pcb';assert k.SaveBoard(str(target),board)
actual={ref:[*xy(f.GetPosition()),f.GetOrientationDegrees(),'B' if f.IsFlipped() else 'F'] for ref,f in fps.items()}
(trial/'build/placement.json').write_text(json.dumps(actual,indent=2)+'\n')
extra={'bounds':[100,100,135,128],'footprints':{},'keepouts':[]}
for f in board.GetFootprints():
    extra['footprints'][f.GetReference()]={'pos':xy(f.GetPosition()),'side':board.GetLayerName(f.GetLayer())}
    for z in f.Zones():
        if not z.GetIsRuleArea():continue
        poly=z.Outline()
        extra['keepouts'].append(dict(ref=f.GetReference(),layer=board.GetLayerName(z.GetLayer()),
            tracks=z.GetDoNotAllowTracks(),vias=z.GetDoNotAllowVias(),
            poly=[[xy(poly.COutline(n).CPoint(i)) for i in range(poly.COutline(n).PointCount())]
                   for n in range(poly.OutlineCount())]))
(trial/'evidence/placement-extra.json').write_text(json.dumps(extra,indent=2)+'\n')
(trial/'evidence/protected-fanout.json').write_text(json.dumps(protected,indent=2)+'\n')
report=dict(parent_sha256=sha(old_pcb),donor_sha256=sha(new_pcb),source_sha256=sha(target),
            changed_placement={ref:actual[ref] for ref in poses},socket_orientation_unchanged=0,
            esd_placement_unchanged=actual['D1'],removed_copper_items=removed,added_copper_items=added,
            scope='Localized placement/fanout trial. Existing remote routes retained; native DRC and reconnection pending.')
(trial/'evidence/local-rework.json').write_text(json.dumps(report,indent=2)+'\n')
subprocess.run([sys.executable,str(root/'scripts/dfm_geometry.py'),str(target),str(trial/'evidence/route-geometry.json')],check=True)
print(json.dumps({k:v for k,v in report.items() if k not in ['added_copper_items','removed_copper_items']},indent=2))
