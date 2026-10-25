#!/usr/bin/env python3
"""Native pcbnew PCB generation from KiCad's exported XML, for DFM review.

RF is prerouted; all other nets are passed to a local Freerouting process.
This revision preserves the schematic's explicitly unresolved power/eSIM/
health interfaces. It is not a functional or production release.
"""
from pathlib import Path
import json, math, os, re, sys
import xml.etree.ElementTree as ET
import pcbnew as k

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT/'hardware'
BUILD = ROOT/'build/pcb'
BUILD.mkdir(parents=True,exist_ok=True)
LIBS = Path(os.environ['KICAD10_FOOTPRINT_DIR'])
V=k.VECTOR2I_MM
MM=k.FromMM
IO=k.PCB_IO_KICAD_SEXPR()
PCB=HW/'collar-tracker.kicad_pcb'

# x, y, rotation, side. Coordinates in mm. Edge.Cuts is 100,100 -> 130,122.
PLACEMENT = {
 'U1':(110,110,0,'F'), 'U2':(122,113.5,180,'F'),
 'U3':(102.5,118.2,0,'F'),'U4':(102.6,101.58,0,'F'),'U5':(123,103.5,0,'F'),
 'J1':(117.3,119.3,0,'F'),'J2':(127.3,108.8,0,'F'),
 'J3':(102.3,120.7,0,'F'),'J4':(104.5,120.5,0,'B'),
 'J5':(120.8,108,0,'B'),'J6':(108,117,0,'B'),'J7':(104,104,0,'B'),
 'FB1':(101.8,111.3,90,'F'),
 'C1':(101.7,109.2,0,'F'),'C2':(101.7,108.1,90,'F'),
 'C3':(101.8,114.6,90,'F'),'C4':(104.7,113.8,0,'B'),
 'C5':(112.75,102.8,0,'F'),'C6':(115,102.5,0,'F'),
 'C7':(106.75,117.9,0,'F'),'C8':(103.8,109,0,'B'),
 'R1':(101.5,107.5,90,'B'),'C9':(101.5,109.7,90,'B'),'R2':(103.8,107.5,0,'B'),
 'C10':(103.6,115,0,'B'),
 'R3':(112.5,117.3,0,'F'),'C11':(110.2,117.3,180,'F'),'C12':(112.5,119.4,180,'F'),
 'L1':(119.5,113.25,270,'F'),'C13':(118.3,114.65,180,'F'),'C14':(123.5,110.1,180,'F'),
 'R4':(125.3,116.3,0,'F'),'R5':(125.3,117.7,0,'F'),
 'C15':(125,114.8,0,'F'),'C16':(127.4,116.5,90,'F'),
 'C17':(101.8,115.7,90,'B'),'C18':(108.5,119.7,0,'F'),'C19':(106,119.7,0,'F'),
 'R6':(106,121,0,'F'),'R7':(108,121,0,'F'),
 'R8':(108,102,0,'B'),'R9':(110,102,0,'B'),
 'C20':(106,101,0,'F'),'C21':(106,102.5,0,'F'),
 'R10':(108,109,0,'B'),'R11':(110,109,0,'B'),'C22':(110,110.5,0,'B'),
 'C23':(125.5,102.5,0,'F'),'C24':(125.5,104,0,'F'),
 'R12':(119,102.2,0,'F'),'R13':(119,103.8,0,'F'),
 'R14':(122,112,0,'B'),'R15':(124,112,0,'B'),
}

def local_contacts(name, rows, cols, pitch, size):
    f=k.FOOTPRINT(None);f.SetFPIDAsString('Collar:'+name)
    f.SetReference('REF**');f.SetValue(name);f.SetAttributes(k.FP_SMD | k.FP_EXCLUDE_FROM_POS_FILES)
    for col in range(cols):
        for row in range(rows):
            number=col*rows+row+1
            p=k.PAD(f);p.SetNumber(str(number));p.SetAttribute(k.PAD_ATTRIB_SMD)
            p.SetShape(k.PAD_SHAPE_RECT if number==1 else k.PAD_SHAPE_OVAL)
            p.SetSize(V(*size));p.SetPosition(V((col-(cols-1)/2)*pitch,(row-(rows-1)/2)*pitch))
            layers=k.LSET();layers.AddLayer(k.F_Cu);layers.AddLayer(k.F_Mask)
            p.SetLayerSet(layers);f.Add(p)
    w=(cols-1)*pitch+size[0]+0.5;h=(rows-1)*pitch+size[1]+0.5
    shape=k.PCB_SHAPE(f);shape.SetShape(k.SHAPE_T_RECT);shape.SetStart(V(-w/2,-h/2));shape.SetEnd(V(w/2,h/2));shape.SetLayer(k.F_CrtYd);shape.SetWidth(MM(.05));f.Add(shape)
    IO.FootprintSave(str(HW/'Collar.pretty'),f)

for name, rows, cols, pitch, size in [
 ('Solder_1x02_P2.5mm',1,2,2.5,(1.5,1.6)),('Solder_1x03_P2.5mm',1,3,2.5,(1.5,1.6)),
 ('Contact_2x06_P1.27mm',2,6,1.27,(.8,.8)),('Contact_1x05_P1.27mm',1,5,1.27,(.8,.8)),
 ('Contact_2x03_P1.27mm',2,3,1.27,(.8,.8))]:
    local_contacts(name,rows,cols,pitch,size)

root=ET.parse(ROOT/'evidence/collar-tracker.xml').getroot()
comps={c.attrib['ref']:c for c in root.findall('./components/comp')}
pad_net={};net_nodes={}
for net in root.findall('./nets/net'):
    name=net.attrib['name'];nodes=[(n.attrib['ref'],n.attrib['pin']) for n in net.findall('node')]
    net_nodes[name]=nodes
    for node in nodes:pad_net[node]=name

b=k.BOARD();b.SetCopperLayerCount(4)
ds=b.GetDesignSettings();ds.SetBoardThickness(MM(.8))
ds.m_MinClearance=MM(.1);ds.m_TrackMinWidth=MM(.1);ds.m_ViasMinSize=MM(.45)
ds.m_MinThroughDrill=MM(.2);ds.m_HoleToHoleMin=MM(.25);ds.m_HoleClearance=MM(.2);ds.m_CopperEdgeClearance=MM(.3)
ds.m_SolderMaskMargin=MM(.05);ds.m_MinSilkTextHeight=MM(.8);ds.m_MinSilkTextThickness=MM(.15)
ns=ds.m_NetSettings
default=ns.GetDefaultNetclass();default.SetClearance(MM(.1));default.SetTrackWidth(MM(.15));default.SetViaDiameter(MM(.45));default.SetViaDrill(MM(.2))
for cname, width, names in [('Power',.3,['/VSYS','/VDD_NRF','/VBAT','/VIN_5V']),('RF',.2,['/LTE_RF','/LTE_ANT','/GPS_RF','/GNSS_ANT','/GNSS_FEM_IN','/GNSS_FEM_OUT','/FILT_OUT','/AMP_IN'])]:
    nc=k.NETCLASS(cname);nc.SetClearance(MM(.1));nc.SetTrackWidth(MM(width));nc.SetViaDiameter(MM(.45));nc.SetViaDrill(MM(.2));ns.SetNetclass(cname,nc)
    for n in names:ns.SetNetclassPatternAssignment(n,cname)
ns.RecomputeEffectiveNetclasses()
nets={}
for name in net_nodes:
    ni=k.NETINFO_ITEM(b,name);b.Add(ni);nets[name]=ni
fps={}
design=json.loads((HW/'design.json').read_text())
assert set(PLACEMENT)==set(comps),(set(PLACEMENT)-set(comps),set(comps)-set(PLACEMENT))
for ref,c in comps.items():
    full=c.findtext('footprint');nick,name=full.split(':',1)
    f=IO.FootprintLoad(str(HW/'Collar.pretty' if nick=='Collar' else LIBS/(nick+'.pretty')),name)
    assert f is not None, full
    f.SetReference(ref);f.SetValue(c.findtext('value'));f.SetFPIDAsString(full)
    f.SetPath(k.KIID_PATH(c.find('sheetpath').attrib['tstamps'].rstrip('/')+'/'+c.findtext('tstamps')))
    b.Add(f)
    x,y,rot,side=PLACEMENT[ref];f.SetPosition(V(x,y))
    if side=='B': f.SetLayerAndFlip(k.B_Cu)
    f.SetOrientationDegrees(rot)
    for field in c.findall('./fields/field'):
        if field.attrib['name'] not in ['Reference','Value','Footprint']:
            f.SetField(field.attrib['name'],field.text or '')
    for field in f.GetFields():field.SetVisible(False)
    f.Reference().SetLayer(k.B_Fab if side=='B' else k.F_Fab)
    f.Reference().SetVisible(True);f.Reference().SetTextSize(V(.65,.65));f.Reference().SetTextThickness(MM(.1))
    if ref in ['C11','C12']: f.SetAttributes(f.GetAttributes() | k.FP_DNP)
    fps[ref]=f
    for p in f.Pads():
        name=pad_net.get((ref,p.GetNumber()))
        if name:p.SetNet(nets[name])
    # Keep courtyard/fab intact; silk graphics remain library geometry.

def pad(ref,num):
    return next(p for p in fps[ref].Pads() if p.GetNumber()==str(num))

def trace(net, points, width=.2, layer=k.F_Cu):
    for a,z in zip(points,points[1:]):
        if a==z:continue
        t=k.PCB_TRACK(b);t.SetStart(V(*a));t.SetEnd(V(*z));t.SetLayer(layer);t.SetWidth(MM(width));t.SetNet(nets[net]);t.SetLocked(True);b.Add(t)

def xy(p):return (p.GetPosition().x/1e6,p.GetPosition().y/1e6)
def connect(ref1,p1,ref2,p2,mid=(),width=.2):
    a=pad(ref1,p1);z=pad(ref2,p2);assert a.GetNetname()==z.GetNetname()
    trace(a.GetNetname(),[xy(a),*mid,xy(z)],width)

connect('U1',35,'R3',1,[(112.25,117.04)])
connect('R3',2,'J1',1,[(113.8,117.3),(115.775,119.275)])
connect('C11',1,'R3',1)
connect('C12',1,'J1',1,[(115.675,119.4)])
connect('U1',42,'C13',2,[(116.9,114.25037),(117.3,114.65)])
connect('C13',1,'U2',10)
connect('U2',5,'C14',2,[(123.1875,110.2675)])
connect('C14',1,'J2',1,[(124.475,110.1)])
connect('U2',7,'L1',1,[(120,113.0)])
connect('U2',8,'L1',2,[(120,113.5)])

for a,z in [((100,100),(130,100)),((130,100),(130,122)),((130,122),(100,122)),((100,122),(100,100))]:
    edge=k.PCB_SHAPE(b);edge.SetShape(k.SHAPE_T_SEGMENT);edge.SetStart(V(*a));edge.SetEnd(V(*z));edge.SetLayer(k.Edge_Cuts);edge.SetWidth(MM(.05));b.Add(edge)

# Full ground reference planes, with no autorouted signal tracks on either one.
for layer in [k.In1_Cu,k.In2_Cu,k.F_Cu,k.B_Cu]:
    z=k.ZONE(b);z.SetLayer(layer);z.SetNet(nets['/GND']);z.SetZoneName('GND_'+b.GetLayerName(layer))
    z.SetLocalClearance(MM(.15));z.SetMinThickness(MM(.1));z.SetPadConnection(k.ZONE_CONNECTION_FULL)
    ol=z.Outline();ol.NewOutline()
    for p in [(100,100),(130,100),(130,122),(100,122)]:ol.Append(V(*p))
    b.Add(z)
ds.SetAuxOrigin(V(100,122));ds.SetGridOrigin(V(100,100))

def text(value,x,y,size,layer=k.F_SilkS):
    t=k.PCB_TEXT(b);t.SetText(value);t.SetPosition(V(x,y));t.SetTextSize(V(size,size));t.SetTextThickness(MM(.15));t.SetLayer(layer)
    if layer==k.B_SilkS:t.SetMirrored(True)
    b.Add(t)
text('COLLAR 0.2 DFM',119,119.7,.85,k.B_SilkS)
text('SIM EXT',108,115.8,.8,k.B_SilkS)
text('HEALTH EXT',120.8,110,.8,k.B_SilkS)
text('1V8 SWD',104,106,.8,k.B_SilkS)

k.SaveBoard(str(PCB),b)
# Keep actual routing rules in the project file read by the CLI/GUI as well.
project=json.loads((HW/'collar-tracker.kicad_pro').read_text())
rules={'min_clearance':.1,'min_track_width':.1,'min_via_diameter':.45,'min_through_hole_diameter':.2,'min_hole_clearance':.2,'min_hole_to_hole':.25,'min_copper_edge_clearance':.3,'min_silk_clearance':.15,'min_text_height':.8,'min_text_thickness':.15}
project['board']={'design_settings':{'rules':rules,'defaults':{'solder_mask_clearance':.05},'drc_exclusions':[]}}
project['net_settings']={'meta':{'version':4},'classes':[{'name':'Default','clearance':.1,'track_width':.15,'via_diameter':.45,'via_drill':.2},{'name':'Power','clearance':.1,'track_width':.3,'via_diameter':.45,'via_drill':.2},{'name':'RF','clearance':.1,'track_width':.2,'via_diameter':.45,'via_drill':.2}], 'netclass_patterns':[{'netclass':c,'pattern':n} for c,nn in [('Power',['/VSYS','/VDD_NRF','/VBAT','/VIN_5V']),('RF',['/LTE_RF','/LTE_ANT','/GPS_RF','/GNSS_ANT','/GNSS_FEM_IN','/GNSS_FEM_OUT','/FILT_OUT','/AMP_IN'])] for n in nn]}
(HW/'collar-tracker.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')

# Export a working copy: NC pads remain physical keepouts and ground planes
# remain plane nets; remove only outer fills so they cannot conceal routing.
for z in list(b.Zones()):
    if z.GetLayer() in [k.F_Cu,k.B_Cu]: b.Remove(z)
for f in b.GetFootprints():
    for p in f.Pads():
        if p.IsOnLayer(f.GetLayer()) and (p.GetNetname().startswith('unconnected-') or not p.GetNetname()):
            p.SetNetCode(0)
            box=p.GetBoundingBox()
            z=k.ZONE(b);z.SetLayer(f.GetLayer());z.SetIsRuleArea(True);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowZoneFills(False);z.SetDoNotAllowPads(False);z.SetDoNotAllowFootprints(False)
            ol=z.Outline();ol.NewOutline()
            for x,y in [(box.GetLeft(),box.GetTop()),(box.GetRight(),box.GetTop()),(box.GetRight(),box.GetBottom()),(box.GetLeft(),box.GetBottom())]:ol.Append(k.VECTOR2I(x,y))
            b.Add(z)
assert k.ExportSpecctraDSN(b,str(BUILD/'collar-tracker.dsn'))
dsn=(BUILD/'collar-tracker.dsn').read_text()
# Freerouting detects both >50% ground fills as power planes. Do not put
# wire_keepouts over them: that also blocks through-via insertion in 2.4.1.
(BUILD/'collar-tracker.dsn').write_text(dsn)
(BUILD/'placement.json').write_text(json.dumps(PLACEMENT,indent=2)+'\n')
print(json.dumps({'pcb':str(PCB),'size_mm':[30,22,.8],'footprints':len(fps),'nets':len(nets),'prerouted_segments':len(list(b.GetTracks()))}))
