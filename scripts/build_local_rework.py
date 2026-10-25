#!/usr/bin/env python3
"""Make a separate r04b placement trial from the saved four-open checkpoint.

Keep 35 x 28 mm and both ground planes. Free charger/SIM routes together,
face the SIM opening toward the board edge, and use TI's DCK land example.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pcbnew as k

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'experiments/paul-nanosim-r04'
parser=argparse.ArgumentParser()
parser.add_argument('--name',default='paul-nanosim-r04c')
args=parser.parse_args()
trial=ROOT/'experiments'/args.name
pcb=source/'hardware/collar-tracker.kicad_pcb'
source_sha=hashlib.sha256(pcb.read_bytes()).hexdigest()
assert source_sha=='2e9c0666d6561330a5ad5608c65ae7d49485f0731130f3652b0a99ce19004398'
assert not trial.exists(), 'Preserve earlier trials'
shutil.copytree(source/'hardware',trial/'hardware',ignore=shutil.ignore_patterns('*.lck','*.kicad_prl','*.local-routing.json'))
for name in ['build','evidence','previews']:(trial/name).mkdir()

# Remove zones only from an analysis copy to identify local copper islands.
# An inner ground plane would otherwise join every ground pad in this search.
probe=k.LoadBoard(str(pcb))
for z in list(probe.Zones()):
    if not z.GetIsRuleArea():probe.Delete(z)
probe.BuildConnectivity();connectivity=probe.GetConnectivity()
moving={'U3','C17','C18','C19','J6','D1'}
ground_refs=moving|{'R6','J4','J2'}
targets=[p for f in probe.GetFootprints() if f.GetReference() in ground_refs
         for p in f.Pads() if p.GetNetname()=='/GND']
ground_items={}
for pad in targets:
    for item in [pad,*connectivity.GetConnectedItems(pad)]:
        if item.GetNetname()=='/GND':ground_items[item.m_Uuid.AsString()]=item
ground_pad_ids=[uid for uid,item in ground_items.items() if item.GetClass()=='PAD']

b=k.LoadBoard(str(pcb));fps={f.GetReference():f for f in b.GetFootprints()}
nets={p.GetNetname() for ref in moving for p in fps[ref].Pads()
      if p.GetNetname() and p.GetNetname()!='/GND' and not p.GetNetname().startswith('unconnected-')}
nets.update(['/SPI_SCK','/I2C_SCL','/I2C_SDA','/ACC_INT'])
removed=[]
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in ground_items or t.GetNetname() in nets:
        removed.append(t.m_Uuid.AsString());b.Delete(t)

v=lambda x,y:k.VECTOR2I(round(x*1e6),round(y*1e6))
placement={'U3':(105.0,123.0,0,k.F_Cu),'C18':(103.0,120.85,0,k.F_Cu),
           'C17':(106.2,120.2,90,k.B_Cu),'C19':(101.8,122.5,180,k.F_Cu),
           'J6':(127.0,108.0,180,k.B_Cu),
           'D1':(123.0,107.0,0,k.F_Cu)}

# Normalize the ESD footprint on the front at the origin before library export.
f=fps['D1']
if f.IsFlipped():f.SetLayerAndFlip(k.F_Cu)
f.SetOrientationDegrees(0);f.SetPosition(v(0,0))
pin_positions={'1':(-1.1,-.65),'2':(-1.1,0),'3':(-1.1,.65),
               '4':(1.1,.65),'5':(1.1,0),'6':(1.1,-.65)}
for pad in f.Pads():
    pad.SetPosition(v(*pin_positions[pad.GetNumber()]))
    pad.SetSize(v(.9,.4));pad.SetRoundRectRadiusRatio(.125)
for g in list(f.GraphicalItems()):
    if g.GetLayer() in [k.F_CrtYd,k.B_CrtYd]:f.Delete(g)
outline=k.PCB_SHAPE(f);outline.SetShape(k.SHAPE_T_RECT)
outline.SetStart(v(-1.8,-1.25));outline.SetEnd(v(1.8,1.25))
outline.SetWidth(50000);outline.SetLayer(k.F_CrtYd);f.Add(outline)
io=k.PCB_IO_KICAD_SEXPR()
io.FootprintSave(str(trial/'hardware/Collar04.pretty'),f)

for ref,(x,y,angle,layer) in placement.items():
    f=fps[ref]
    if f.GetLayer()!=layer:f.SetLayerAndFlip(layer)
    f.SetOrientationDegrees(angle);f.SetPosition(v(x,y))

def route(net,points,layer,width):
    for a,z in zip(points,points[1:]):
        if a==z:continue
        t=k.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*z))
        t.SetWidth(round(width*1e6));t.SetLayer(layer);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)

def via(net,pos):
    t=k.PCB_VIA(b);t.SetPosition(v(*pos));t.SetWidth(600000);t.SetDrill(200000)
    t.SetViaType(k.VIATYPE_THROUGH);t.SetLayerPair(k.F_Cu,k.B_Cu);t.SetNet(b.FindNet(net))
    t.SetFrontTentingMode(k.TENTING_MODE_TENTED);t.SetBackTentingMode(k.TENTING_MODE_TENTED)
    t.SetLocked(True);b.Add(t)

# Reserve all charger pin exits together before choosing the remaining grounds.
# The top and bottom pins escape vertically; middle pins use staggered vias.
for net,pin_path,pos in [
    ('/VIN_5V',[(106.1,122.2),(106.1,121.55)],(106.1,121.55)),
    ('/CHG_FAULT',[(103.9,123.0),(102.9,123.0),(102.6,123.3)],(102.6,123.3)),
    ('/CHG_STAT',[(106.1,122.6),(106.7,122.6),(107.1,122.2)],(107.1,122.2)),
    ('/ISET',[(106.1,123.0),(108.0,123.0)],(108.0,123.0)),
    ('/ILIM_VSET',[(106.1,123.4),(106.7,123.4),(107.1,123.8)],(107.1,123.8)),
    ('/BAT_NTC',[(106.1,123.8),(106.1,124.7)],(106.1,124.7)),
]:
    route(net,pin_path,k.F_Cu,.2);via(net,pos)
route('/VIN_5V',[(106.2,120.68),(106.1,120.78),(106.1,121.55)],k.B_Cu,.4)
route('/VSYS',[(103.9,122.2),(103.45,121.75)],k.F_Cu,.2)
route('/VSYS',[(103.45,121.75),(103.125,121.75),(102.225,120.85)],k.F_Cu,.4)
route('/VBAT',[(103.9,122.6),(103.15,122.6),(103.0,122.45)],k.F_Cu,.2)
route('/VBAT',[(103.0,122.45),(102.28,122.45),(102.23,122.5),
               (102.23,121.75),(101.2,121.75),(101.1,121.65)],k.F_Cu,.4)
via('/VBAT',(101.1,121.65))

manual_ground_refs={'U3','C17','C18','C19','R6','J4'}
route('/GND',[(103.9,123.4),(105,123.4)],k.F_Cu,.2)
route('/GND',[(103.9,123.8),(105,123.8)],k.F_Cu,.2)
route('/GND',[(105,123.0),(105,124.3)],k.F_Cu,.3)
via('/GND',(105,124.3))
route('/GND',[(106.2,119.72),(105.32,119.72),(105.3,119.7)],k.B_Cu,.4)
via('/GND',(105.3,119.7))
route('/GND',[(103.775,120.85),(104.8,120.85)],k.F_Cu,.4)
via('/GND',(104.8,120.85))
route('/GND',[(101.32,122.5),(100.75,123.07),(100.75,123.25)],k.F_Cu,.4)
via('/GND',(100.75,123.25))
route('/GND',[(106.51,125.8),(106.51,126.86),(106.9,127.25)],k.F_Cu,.2)
route('/GND',[(106,126.2),(106.9,127.1),(106.9,127.25)],k.B_Cu,.3)
via('/GND',(106.9,127.25))
ground_pad_ids=[uid for uid in ground_pad_ids
                if ground_items[uid].GetParentFootprint().GetReference() not in manual_ground_refs]
b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones())
target=trial/'hardware/collar-tracker.kicad_pcb'
assert k.SaveBoard(str(target),b)
(trial/'evidence/ground-target-pads.json').write_text(json.dumps(ground_pad_ids,indent=2)+'\n')
actual={ref:[f.GetPosition().x/1e6,f.GetPosition().y/1e6,f.GetOrientationDegrees(),
             'B' if f.IsFlipped() else 'F'] for ref,f in fps.items()}
(trial/'build/placement.json').write_text(json.dumps(actual,indent=2)+'\n')
extra={'bounds':[100,100,135,128],'footprints':{},'keepouts':[]}
xy=lambda p:[p.x/1e6,p.y/1e6]
for f in b.GetFootprints():
    extra['footprints'][f.GetReference()]={'pos':xy(f.GetPosition()),'side':b.GetLayerName(f.GetLayer())}
    for z in f.Zones():
        if not z.GetIsRuleArea():continue
        poly=z.Outline()
        extra['keepouts'].append({'ref':f.GetReference(),'layer':b.GetLayerName(z.GetLayer()),
            'tracks':z.GetDoNotAllowTracks(),'vias':z.GetDoNotAllowVias(),
            'poly':[[xy(poly.COutline(n).CPoint(i)) for i in range(poly.COutline(n).PointCount())]
                    for n in range(poly.OutlineCount())]})
(trial/'evidence/placement-extra.json').write_text(json.dumps(extra,indent=2)+'\n')
subprocess.run([sys.executable,str(ROOT/'scripts/dfm_geometry.py'),str(target),
                str(trial/'evidence/placement-geometry.json')],check=True)
report={'parent_source_sha256':source_sha,'source_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'changed_placement':{r:actual[r] for r in placement},'reroute_nets':sorted(nets),
        'removed_copper_items':len(removed),'ground_pads_to_reconnect':len(ground_pad_ids),
        'scope':'Placement trial only. Ground reconnection, native DRC and routing are pending.'}
(trial/'evidence/placement-rework.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
