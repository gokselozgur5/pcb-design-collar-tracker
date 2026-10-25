#!/usr/bin/env python3
"""Isolated 35 x 28 mm routing experiment; never changes the 0.2.1 source.

Retains the reviewed copper/mask apertures and schematic paths from 0.2.1.
All routing is new. Inner copper layers are reserved for ground in the router.
This is a geometry experiment, not electrical/RF or assembly qualification.
"""
from pathlib import Path
import argparse,hashlib, json, shutil
import pcbnew as k

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--inner2-signal',action='store_true');args=parser.parse_args()
OUT=ROOT/('experiments/35x28-in2' if args.inner2_signal else 'experiments/35x28')
HW=OUT/'hardware'; BUILD=OUT/'build'; EVID=OUT/'evidence'
for d in [HW,BUILD,EVID,OUT/'previews']: d.mkdir(parents=True,exist_ok=True)
for name in ['collar-tracker.kicad_sch','collar-tracker.kicad_pro','fp-lib-table','sym-lib-table']:
    src=ROOT/'hardware'/name
    if src.exists():shutil.copy2(src,HW/name)
for src in (ROOT/'hardware').iterdir():
    if src.suffix=='.pretty':shutil.copytree(src,HW/src.name,dirs_exist_ok=True)
    elif src.suffix=='.kicad_sym':shutil.copy2(src,HW/src.name)
PCB=HW/'collar-tracker.kicad_pcb'
V=k.VECTOR2I_MM;MM=k.FromMM
PLACEMENT={
 'U1':(111,113,0,'F'),'U2':(123,116.5,180,'F'),
 'U3':(103.5,123,0,'F'),'U4':(103,102.5,0,'F'),'U5':(129,104.5,0,'F'),
 'J1':(118.3,122.3,0,'F'),'J2':(128.3,111.8,0,'F'),
 'J3':(102.5,126.2,0,'F'),'J4':(106,126.2,0,'B'),
 'J5':(127.5,110,0,'B'),'J6':(111,122,0,'B'),'J7':(104,106,0,'B'),
 'FB1':(102,114,90,'F'),
 'C1':(102,110.7,0,'F'),'C2':(102,109.1,90,'F'),'C3':(102,118.3,90,'F'),
 'C4':(105.7,116.8,0,'B'),'C5':(113.75,105.8,0,'F'),'C6':(116,105.3,0,'F'),
 'C7':(107.75,121,0,'F'),'C8':(104.8,112,0,'B'),
 'R1':(101.8,110,90,'B'),'C9':(101.8,113.7,90,'B'),'R2':(104.7,110,0,'B'),
 'C10':(104,119,0,'B'),
 'R3':(113.5,120.3,0,'F'),'C11':(111.2,120.3,180,'F'),'C12':(113.5,122.4,180,'F'),
 'L1':(120.5,116.25,270,'F'),'C13':(119.3,117.65,180,'F'),'C14':(124.5,113.1,180,'F'),
 'R4':(126.3,119.3,0,'F'),'R5':(126.3,120.7,0,'F'),
 'C15':(126,117.8,0,'F'),'C16':(128.4,119.5,90,'F'),
 'C17':(102,121.8,90,'B'),'C18':(101.7,120.8,0,'F'),'C19':(108.2,123.3,0,'F'),
 'R6':(106,125.8,0,'F'),'R7':(108.2,125.8,0,'F'),
 'R8':(110,102,0,'B'),'R9':(113,102,0,'B'),
 'C20':(106,101.8,0,'F'),'C21':(106,103.5,0,'F'),
 'R10':(110,112,0,'B'),'R11':(113,112,0,'B'),'C22':(113,114,0,'B'),
 'C23':(132,103.4,0,'F'),'C24':(132,105.5,0,'F'),
 'R12':(124.8,102.3,0,'F'),'R13':(124.8,104.5,0,'F'),
 'R14':(124,115,0,'B'),'R15':(127,115,0,'B'),
}
source=ROOT/'hardware/collar-tracker.kicad_pcb'
old=k.LoadBoard(str(source));b=k.BOARD();b.SetCopperLayerCount(4)
ds=b.GetDesignSettings();ds.SetBoardThickness(MM(.8))
ds.m_MinClearance=MM(.1);ds.m_TrackMinWidth=MM(.2);ds.m_ViasMinSize=MM(.6)
ds.m_MinThroughDrill=MM(.2);ds.m_HoleToHoleMin=MM(.25);ds.m_HoleClearance=MM(.2)
ds.m_CopperEdgeClearance=MM(.4);ds.m_SolderMaskExpansion=0
ds.m_MinSilkTextHeight=MM(1);ds.m_MinSilkTextThickness=MM(.2)
ns=ds.m_NetSettings
power=['/VSYS','/VDD_NRF','/VBAT','/VIN_5V']
rf=['/LTE_RF','/LTE_ANT','/GPS_RF','/GNSS_ANT','/GNSS_FEM_IN','/GNSS_FEM_OUT','/FILT_OUT','/AMP_IN']
for name,width,names in [('Default',.2,[]),('Power',.25,power),('RF',.2,rf)]:
    nc=ns.GetDefaultNetclass() if name=='Default' else k.NETCLASS(name)
    nc.SetClearance(MM(.2));nc.SetTrackWidth(MM(width));nc.SetViaDiameter(MM(.6));nc.SetViaDrill(MM(.2))
    if name!='Default':ns.SetNetclass(name,nc)
    for net in names:ns.SetNetclassPatternAssignment(net,name)
ns.RecomputeEffectiveNetclasses()
nets={};fps={}
for oldf in old.GetFootprints():
    # Duplicate preserves paths, physical apertures and the intentional U.FL mask setting.
    f=k.Cast_to_FOOTPRINT(oldf.Duplicate(False));b.Add(f)
    x,y,r,side=PLACEMENT[f.GetReference()]
    assert f.IsFlipped()==(side=='B')
    f.SetPosition(V(x,y));f.SetOrientationDegrees(r)
    fps[f.GetReference()]=f
    for p,op in zip(f.Pads(),oldf.Pads()):
        name=op.GetNetname()
        if name:
            if name not in nets:
                ni=k.NETINFO_ITEM(b,name);b.Add(ni);nets[name]=ni
            p.SetNet(nets[name])
        else:p.SetNetCode(0)
assert set(fps)==set(PLACEMENT)
def pad(ref,pin):return next(p for p in fps[ref].Pads() if p.GetNumber()==str(pin))
def xy(p):return (p.GetPosition().x/1e6,p.GetPosition().y/1e6)
def trace(net,points,width=.2):
    for a,z in zip(points,points[1:]):
        if a==z:continue
        t=k.PCB_TRACK(b);t.SetStart(V(*a));t.SetEnd(V(*z));t.SetWidth(MM(width))
        t.SetLayer(k.F_Cu);t.SetNet(nets[net]);t.SetLocked(True);b.Add(t)
def connect(r1,p1,r2,p2,mid=()):
    a=pad(r1,p1);z=pad(r2,p2);assert a.GetNetname()==z.GetNetname()
    trace(a.GetNetname(),[xy(a),*[(x+1,y+3) for x,y in mid],xy(z)])
connect('U1',35,'R3',1,[(112.25,117.04)])
connect('R3',2,'J1',1,[(113.8,117.3),(115.775,119.275)])
connect('C11',1,'R3',1)
connect('C12',1,'J1',1,[(115.675,119.4)])
connect('U1',42,'C13',2,[(116.9,114.25037),(117.3,114.65)])
connect('C13',1,'U2',10)
connect('U2',5,'C14',2,[(123.1875,110.2675)])
connect('C14',1,'J2',1,[(124.475,110.1)])
connect('U2',7,'L1',1,[(120,113)])
connect('U2',8,'L1',2,[(120,113.5)])
# 0.4 mm-pitch WSON charger: short 0.2 mm escape traces, then spread the endpoints.
# Width is not reduced below the advertised 0.2 mm trial minimum.
for pin in range(1,11):
    p=pad('U3',pin);x,y=xy(p);sgn=-1 if x<103.5 else 1
    straight=.4+(.8-abs(y-123))
    trace(p.GetNetname(),[(x,y),(x+sgn*straight,y),(x+sgn*1.6,y+(y-123)*.75)])
corners=[(100,100),(135,100),(135,128),(100,128)]
for a,z in zip(corners,corners[1:]+corners[:1]):
    e=k.PCB_SHAPE(b);e.SetShape(k.SHAPE_T_SEGMENT);e.SetStart(V(*a));e.SetEnd(V(*z))
    e.SetLayer(k.Edge_Cuts);e.SetWidth(MM(.05));b.Add(e)
for layer in [k.F_Cu,k.In1_Cu,k.In2_Cu,k.B_Cu]:
    z=k.ZONE(b);z.SetLayer(layer);z.SetNet(nets['/GND']);z.SetZoneName('GND_'+b.GetLayerName(layer))
    z.SetLocalClearance(MM(.2));z.SetMinThickness(MM(.2));z.SetPadConnection(k.ZONE_CONNECTION_FULL)
    ol=z.Outline();ol.NewOutline()
    for p in corners:ol.Append(V(*p))
    b.Add(z)
ds.SetAuxOrigin(V(100,128));ds.SetGridOrigin(V(100,100))
for value,x,y in [('COLLAR 0.3 TEST',119,126.3),('SIM EXT',111,124),('HEALTH EXT',127.5,112),('1V8 SWD',104,108)]:
    t=k.PCB_TEXT(b);t.SetText(value);t.SetPosition(V(x,y));t.SetTextSize(V(1,1));t.SetTextThickness(MM(.2))
    t.SetLayer(k.B_SilkS);t.SetMirrored(True);b.Add(t)
k.SaveBoard(str(PCB),b)
project=json.loads((HW/'collar-tracker.kicad_pro').read_text())
rules={'min_clearance':.1,'min_track_width':.2,'min_via_diameter':.6,'min_through_hole_diameter':.2,
       'min_hole_clearance':.2,'min_hole_to_hole':.25,'min_copper_edge_clearance':.4,
       'min_silk_clearance':.2,'min_text_height':1,'min_text_thickness':.2}
project['board']={'design_settings':{'rules':rules,'defaults':{'solder_mask_clearance':0},'drc_exclusions':[]}}
project['net_settings']={'meta':{'version':4},'classes':[{'name':name,'clearance':.2,'track_width':w,'via_diameter':.6,'via_drill':.2}
    for name,w in [('Default',.2),('Power',.25),('RF',.2)]],
    'netclass_patterns':[{'netclass':c,'pattern':n} for c,nn in [('Power',power),('RF',rf)] for n in nn]}
(HW/'collar-tracker.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
(HW/'collar-tracker.kicad_dru').write_text('''(version 1)
# Fixed package pad pitch; this exception never applies to tracks or vias.
(rule "Unchanged package pad spacing"
  (condition "A.Type == 'Pad' && B.Type == 'Pad' && A.Reference == B.Reference")
  (constraint clearance (min 0.15mm)))
''')
# Export copy only. Physical NC copper stays in native PCB; routing keepouts protect it.
for z in list(b.Zones()):
    if z.GetLayer() in [k.F_Cu,k.B_Cu] or (args.inner2_signal and z.GetLayer()==k.In2_Cu):b.Remove(z)
for f in b.GetFootprints():
    for p in f.Pads():
        if p.IsOnLayer(f.GetLayer()) and (p.GetNetname().startswith('unconnected-') or not p.GetNetname()):
            p.SetNetCode(0);box=p.GetBoundingBox()
            z=k.ZONE(b);z.SetLayer(f.GetLayer());z.SetIsRuleArea(True);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True)
            z.SetDoNotAllowZoneFills(False);z.SetDoNotAllowPads(False);z.SetDoNotAllowFootprints(False)
            ol=z.Outline();ol.NewOutline()
            for x,y in [(box.GetLeft(),box.GetTop()),(box.GetRight(),box.GetTop()),(box.GetRight(),box.GetBottom()),(box.GetLeft(),box.GetBottom())]:ol.Append(k.VECTOR2I(x,y))
            b.Add(z)
        elif p.GetShape() in [k.PAD_SHAPE_ROUNDRECT,k.PAD_SHAPE_OVAL,k.PAD_SHAPE_CIRCLE]:
            # Conservative router obstacle; actual board retains manufacturer pad shape.
            p.SetShape(k.PAD_SHAPE_RECT)
dsn=BUILD/'collar-tracker.dsn';assert k.ExportSpecctraDSN(b,str(dsn))
settings='(autoroute_settings (autoroute on) (postroute on) (vias on)\n'
for name,active,direction in [('F.Cu','on','horizontal'),('In1.Cu','off','horizontal'),('In2.Cu','on' if args.inner2_signal else 'off','horizontal'),('B.Cu','on','vertical')]:
    settings+=f' (layer_rule {name} (active {active}) (preferred_direction {direction}) (preferred_direction_trace_costs 1.0) (against_preferred_direction_trace_costs 1.5))\n'
settings+=')'
text=dsn.read_text();text=text.replace('    (boundary','    '+settings+'\n    (boundary',1)
# Match the native fixed-package pad exception. Keep pad-to-track/via at 0.20.
text=text.replace('(clearance 50 (type smd_smd))','(clearance 150 (type smd_smd))')
text=text.replace('        (clearance 200)\n','        (clearance 200)\n        (clearance 150 (type smd_smd))\n')
dsn.write_text(text)
(BUILD/'placement.json').write_text(json.dumps(PLACEMENT,indent=2)+'\n')
(EVID/'source.json').write_text(json.dumps({'baseline':str(source),'baseline_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'size_mm':[35,28,.8],'footprints':len(fps),'nets':len(nets),'inner2_signal':args.inner2_signal,'note':'No electrical, RF or assembly qualification'},indent=2)+'\n')
print(json.dumps({'pcb':str(PCB),'footprints':len(fps),'nets':len(nets),'prerouted_segments':len(list(b.GetTracks()))}))
