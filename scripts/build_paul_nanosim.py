#!/usr/bin/env python3
"""Build an isolated Paul-review/nano-SIM candidate; never overwrite a release.

Run with kicad-python. Routing is restricted to the two outer layers; GND
uses explicit local pad-to-via connections and two inner reference planes.
"""
import argparse
import collections
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET

import pcbnew as k
import build_draft as sch

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'experiments/35x28-clearance-r034/hardware'
parser = argparse.ArgumentParser()
parser.add_argument('--name', default='paul-nanosim-r04')
parser.add_argument('--width', type=float, default=35)
parser.add_argument('--height', type=float, default=28)
args = parser.parse_args()
OUT = ROOT / 'experiments' / args.name
HW, BUILD, E = OUT/'hardware', OUT/'build', OUT/'evidence'
for d in [HW, BUILD, E, OUT/'previews']:
    d.mkdir(parents=True, exist_ok=True)
PCB = HW/'collar-tracker.kicad_pcb'
assert not PCB.exists(), 'Use a new trial name; finished candidates must not be overwritten'
source = BASE/'collar-tracker.kicad_pcb'
assert hashlib.sha256(source.read_bytes()).hexdigest() == '597ebdee59550b6d07eb104274eabee57b038ea6c87da2dec38c1201f78c89b2'
for p in BASE.iterdir():
    if p.is_dir() and p.suffix == '.pretty':
        shutil.copytree(p, HW/p.name, dirs_exist_ok=True)
    elif p.is_file() and p.suffix in ['.kicad_pro', '.kicad_dru', '.kicad_sym']:
        shutil.copy2(p, HW/p.name)
for name in ['fp-lib-table', 'sym-lib-table']:
    shutil.copy2(BASE/name, HW/name)
LIB = HW/'Collar04.pretty'
LIB.mkdir(exist_ok=True)
IO = k.PCB_IO_KICAD_SEXPR()
MM = lambda x: round(x*1e6)
V = lambda x,y: k.VECTOR2I(MM(x),MM(y))
xy = lambda p: (p.x/1e6,p.y/1e6)

def rect(f, x1,y1,x2,y2, layer, width=.05):
    g=k.PCB_SHAPE(f);g.SetShape(k.SHAPE_T_RECT);g.SetStart(V(x1,y1));g.SetEnd(V(x2,y2))
    g.SetWidth(MM(width));g.SetLayer(layer);f.Add(g)

def nano_footprint():
    # GCT SIM8051 D5 drawing, sheet1 recommended component-side PCB layout.
    # D6 published drawing text retains these land/keepout dimensions.
    # 00 suffix: no locating pegs, therefore no mounting holes.
    f=k.FOOTPRINT(None);f.SetFPIDAsString('Collar04:SIM8051_6_0_14_00_A')
    f.SetReference('REF**');f.SetValue('SIM8051-6-0-14-00-A');f.SetAttributes(k.FP_SMD)
    f.SetLibDescription('GCT SIM8051 no-peg nano-SIM; manufacturer land and moving-contact keepouts')
    for pin,x,y,w,h in [(7,-2.54,-5.9,1,1.1),(6,0,-5.9,1,1.1),(5,2.54,-5.9,1,1.1),
                         (3,-2.54,5.9,1,1.1),(2,0,5.9,1,1.1),(1,2.54,5.9,1,1.1),
                         (8,-5.3,0,1,3),(8,5.3,0,1,3)]:
        p=k.PAD(f);p.SetNumber(str(pin));p.SetAttribute(k.PAD_ATTRIB_SMD);p.SetShape(k.PAD_SHAPE_RECT)
        p.SetPosition(V(x,y));p.SetSize(V(w,h));ls=k.LSET()
        for layer in [k.F_Cu,k.F_Mask,k.F_Paste]:ls.AddLayer(layer)
        p.SetLayerSet(ls)
        f.Add(p)
    rect(f,-4.47,-6.1,4.47,6.1,k.F_Fab,.10)
    rect(f,-6.05,-6.70,6.05,6.70,k.F_CrtYd)
    # Contact/wiper and shell clearance regions apply to this component side;
    # inner reference planes remain intact. No footprints anywhere in its body.
    keepouts=[(-3.575,-2.15,3.575,2.70)]
    keepouts += [(x-.6,y-.5,x+.6,y+.5) for x in [-2.54,0,2.54] for y in [-4.15,3.45]]
    for x1,y1,x2,y2 in keepouts:
        z=k.ZONE(f);z.SetLayer(k.F_Cu);z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowZoneFills(True)
        z.SetDoNotAllowPads(True);z.SetDoNotAllowFootprints(False)
        ol=z.Outline();ol.NewOutline()
        for x,y in [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]:ol.Append(V(x,y))
        f.Add(z)
    IO.FootprintSave(str(LIB),f)
    return f

nano=nano_footprint()
esd=IO.FootprintLoad(str(Path(os.environ['KICAD10_FOOTPRINT_DIR'])/'Package_TO_SOT_SMD.pretty'),'SOT-363_SC-70-6')
assert esd
esd.SetFPIDAsString('Collar04:TPD4E1U06DCKR')
esd.SetReference('REF**');esd.SetValue('TPD4E1U06DCKR')
for g in list(esd.GraphicalItems()):
    if g.GetLayer() in [k.F_SilkS,k.B_SilkS]:g.SetLayer(k.F_Fab)
esd.Reference().SetVisible(False);esd.Value().SetVisible(False)
IO.FootprintSave(str(LIB),esd)
table=(HW/'fp-lib-table').read_text().rstrip()
(HW/'fp-lib-table').write_text(table[:-1]+'\n(lib (name "Collar04") (type "KiCad") (uri "${KIPRJMOD}/Collar04.pretty") (options "") (descr "Nano-SIM revision local footprints")))\n')

# Reuse deterministic schematic symbols/UUIDs; preserve all existing parts' nets.
b=k.LoadBoard(str(source))
oldfps={f.GetReference():f for f in b.GetFootprints()}
for p in sch.parts:
    if p['ref'] in oldfps:p['footprint']=oldfps[p['ref']].GetFPIDAsString()
sch.chip('SIM8051',[(1,'C1_VCC','passive'),(2,'C2_RST','passive'),(3,'C3_CLK','passive'),
                       (7,'C7_IO','passive'),(6,'C6_VPP_UNUSED','no_connect')],[],24,[5,8],
         source='https://gct.co/connector/sim8051')
j6=next(p for p in sch.parts if p['ref']=='J6')
j6.update(symbol='SIM8051',value='SIM8051-6-0-14-00-A',mpn='SIM8051-6-0-14-00-A',
          footprint='Collar04:SIM8051_6_0_14_00_A',nets={'1':'SIM_1V8','2':'SIM_RST','3':'SIM_CLK','7':'SIM_IO','5':'GND','8':'GND'},
          status='SMT removable nano-SIM; 1.8V UICC and LTE-M/NB-IoT service required',onboard=True)
sch.chip('TPD4E1U06',[(1,'D1+','passive'),(6,'D1-','passive'),(3,'D2+','passive'),(4,'D2-','passive'),(5,'NC','no_connect')],[],24,[2],
         source='https://www.ti.com/lit/ds/symlink/tpd4e1u06.pdf')
sch.add('D1','TPD4E1U06','TPD4E1U06DCKR',515,306,{1:'SIM_RST',6:'SIM_CLK',3:'SIM_1V8',4:'SIM_IO',2:'GND'},
        'Collar04:TPD4E1U06DCKR',mpn='TPD4E1U06DCKR',status='SIM ESD; place beside socket with short GND connection')
sch.graphics=[g.replace('05 / eSIM AND DEBUG INTERFACES','05 / NANO-SIM AND DEBUG INTERFACES') for g in sch.graphics
              if 'J6 is NOT a purchasable' not in g]
sch.text('J6: removable 1.8V nano-SIM, C6/VPP unconnected.\nSIM_1V8 is separate from VIO_1V8. Power down modem\nbefore card removal; no hot-swap/card-detect support.',465,272,1.0)
content=f'''(kicad_sch (version 20250114) (generator "collar_tracker_draft")
 (uuid {sch.ROOT_UUID}) (paper "A2")
 (title_block (title "Collar tracker — nano-SIM / Paul layout revision") (date "2026-10-25") (rev "0.4")
 (comment 1 "Layout/DFM candidate; power, RF, firmware and functional qualification remain open"))
 (lib_symbols {''.join(s['text'] for s in sch.symbols.values())})
 {''.join(sch.instance(p) for p in sch.parts)} {''.join(sch.graphics)}
 (sheet_instances (path "/" (page "1"))))'''
(HW/'collar-tracker.kicad_sch').write_text(content)
(HW/'Collar.kicad_sym').write_text('(kicad_symbol_lib (version 20250114) (generator "collar_tracker_draft")\n'+
 '\n'.join(s['text'].replace('(symbol "Collar:', '(symbol "',1) for s in sch.symbols.values())+'\n)\n')
with (HW/'bom.csv').open('w') as stream:
    fields=['ref','value','mpn','footprint','dnp','onboard','status','lcsc']
    writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
    for p in sch.parts:
        if p['ref'].startswith('#'):continue
        row={key:p.get(key,'') for key in fields}
        row['lcsc']={'J6':'C7363812','D1':'C194628'}.get(p['ref'],'')
        writer.writerow(row)
(HW/'design.json').write_text(json.dumps({'parts':sch.parts,'root_uuid':sch.ROOT_UUID},indent=2)+'\n')

# Remove old routes and all pours in this in-memory copy only.
for t in list(b.GetTracks()):b.Remove(t)
for z in list(b.Zones()):b.Remove(z)
for g in list(b.GetDrawings()):b.Remove(g)
b.Remove(oldfps['J6'])
for ref,f in [('J6',nano),('D1',esd)]:
    b.Add(f);f.SetReference(ref);f.SetPath(k.KIID_PATH('/'+sch.ROOT_UUID+'/'+sch.uid(ref)))
    part=next(p for p in sch.parts if p['ref']==ref)
    for pad in f.Pads():
        pn=pad.GetNumber();net=part['nets'].get(pn)
        name='/'+net if net else f'unconnected-({ref}-'+('C6_VPP_UNUSED' if ref=='J6' else 'NC')+'-Pad'+pn+')'
        ni=b.FindNet(name)
        if ni is None or ni.GetNetCode()<0:
            ni=k.NETINFO_ITEM(b,name);b.Add(ni)
        pad.SetNet(ni)
    oldfps[ref]=f

placement={ref:[*xy(f.GetPosition()),f.GetOrientationDegrees(),'B' if f.IsFlipped() else 'F'] for ref,f in oldfps.items()}
placement.update(J6=[127,108,0,'B'],D1=[126,116.2,0,'B'],J5=[125,125,0,'B'],
                 R14=[123,118,0,'B'],R15=[126,118,0,'B'],C10=[123,115.7,0,'B'])
for ref,pos in placement.items():
    f=oldfps[ref];x,y,angle,side=pos
    if f.IsFlipped() != (side=='B'):f.SetLayerAndFlip(k.B_Cu if side=='B' else k.F_Cu)
    f.SetPosition(V(x,y));f.SetOrientationDegrees(angle)
    f.Reference().SetVisible(False);f.Value().SetVisible(False)
    for pad in f.Pads():pad.SetLocalZoneConnection(k.ZONE_CONNECTION_INHERITED)

ds=b.GetDesignSettings();ns=ds.m_NetSettings
power=['/VSYS','/VDD_NRF','/VBAT','/VIN_5V'];vio=['/VIO_1V8']
for name,width,names in [('Default',.2,[]),('Power',.4,power),('VIO',.3,vio)]:
    nc=ns.GetDefaultNetclass() if name=='Default' else k.NETCLASS(name)
    nc.SetClearance(MM(.2));nc.SetTrackWidth(MM(width));nc.SetViaDiameter(MM(.6));nc.SetViaDrill(MM(.2))
    if name!='Default':ns.SetNetclass(name,nc)
    for net in names:ns.SetNetclassPatternAssignment(net,name)
ns.RecomputeEffectiveNetclasses()
project=json.loads((HW/'collar-tracker.kicad_pro').read_text())
for c in project['net_settings']['classes']:
    if c['name']=='Power':c['track_width']=.4
project['net_settings']['classes'].append({'name':'VIO','clearance':.2,'track_width':.3,'via_diameter':.6,'via_drill':.2})
project['net_settings']['netclass_patterns'].append({'netclass':'VIO','pattern':'/VIO_1V8'})
(HW/'collar-tracker.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
corners=[(100,100),(100+args.width,100),(100+args.width,100+args.height),(100,100+args.height)]
for a,z in zip(corners,corners[1:]+corners[:1]):
    e=k.PCB_SHAPE(b);e.SetShape(k.SHAPE_T_SEGMENT);e.SetStart(V(*a));e.SetEnd(V(*z));e.SetWidth(MM(.05));e.SetLayer(k.Edge_Cuts);b.Add(e)
ds.SetAuxOrigin(V(100,100+args.height))
for layer in [k.In1_Cu,k.In2_Cu]:
    z=k.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet('/GND'));z.SetZoneName('GND_'+b.GetLayerName(layer))
    z.SetLocalClearance(MM(.25));z.SetMinThickness(MM(.2));z.SetPadConnection(k.ZONE_CONNECTION_FULL)
    ol=z.Outline();ol.NewOutline()
    for p in corners:ol.Append(V(*p))
    b.Add(z)
board=k.LoadBoard(str(source))
rf={'/LTE_RF','/LTE_ANT','/GPS_RF','/GNSS_ANT','/GNSS_FEM_IN','/GNSS_FEM_OUT','/FILT_OUT','/AMP_IN'}
for t in board.GetTracks():
    if t.GetNetname() in rf:
        n=t.Duplicate();n.SetNet(b.FindNet(t.GetNetname()));n.SetLocked(True);b.Add(n)
title=b.GetTitleBlock();title.SetRevision('0.4');title.SetDate('2026-10-25');b.SetTitleBlock(title)
assert k.SaveBoard(str(PCB),b)
(BUILD/'placement.json').write_text(json.dumps(placement,indent=2)+'\n')
(E/'source.json').write_text(json.dumps({'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'size_mm':[args.width,args.height,.8],'inner2_signal':False,'stage':'placement; ground fanout and autorouting pending',
    'physical_sim':'GCT SIM8051-6-0-14-00-A','sim_esd':'TPD4E1U06DCKR'},indent=2)+'\n')
print(json.dumps({'pcb':str(PCB),'footprints':len(list(b.GetFootprints())),'rf_segments':len(list(b.GetTracks())),'status':'placement ready; no connectivity acceptance yet'}))
