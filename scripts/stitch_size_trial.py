#!/usr/bin/env python3
"""Add a clearance-checked ground via in filled GND islands lacking one.

Uses actual filled polygons (including holes), not the zone's outline origin.
Any island too small for an ordinary 0.6/0.2 via is reported, never hidden.
"""
import json,math,sys
from pathlib import Path
import pcbnew as k
PCB=Path(sys.argv[1]);b=k.LoadBoard(str(PCB));GND=b.FindNet('/GND')
def xy(v):return (v.x/1e6,v.y/1e6)
def distance(x,y,a,z):
    dx=z[0]-a[0];dy=z[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy))) if dx or dy else 0
    return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)
pads=[];tracks=[];vias=[];keepouts=[]
for f in b.GetFootprints():
    for p in f.Pads():
        if not any(p.IsOnLayer(l) for l in [k.F_Cu,k.B_Cu,k.In1_Cu,k.In2_Cu]):continue
        bb=p.GetBoundingBox();pads.append((bb.GetLeft()/1e6,bb.GetTop()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6,f.GetReference()+'.'+p.GetNumber(),p.GetNetname()))
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA':vias.append((*xy(t.GetPosition()),t.GetWidth(k.F_Cu)/2e6,t.GetNetname()))
    elif t.GetNetname()!='/GND':tracks.append((xy(t.GetStart()),xy(t.GetEnd()),t.GetWidth()/2e6))
for z in b.Zones():
    if z.GetIsRuleArea() and z.GetDoNotAllowVias():
        bb=z.GetBoundingBox();keepouts.append((bb.GetLeft()/1e6,bb.GetTop()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6))
def free(x,y):
    if not(100.701<=x<=134.299 and 100.701<=y<=127.299):return False
    for box in pads+keepouts:
        if math.hypot(max(box[0]-x,0,x-box[2]),max(box[1]-y,0,y-box[3]))<.501:return False
    for a,z,r in tracks:
        if distance(x,y,a,z)<.501+r:return False
    return all(math.hypot(x-vx,y-vy)>=.501+r for vx,vy,r,n in vias)
result=[]
for zone in b.Zones():
    if zone.GetIsRuleArea() or zone.GetNetname()!='/GND' or zone.GetLayer()==k.In1_Cu:continue
    poly=zone.GetFilledPolysList(zone.GetLayer())
    for i in range(poly.OutlineCount()):
        if any(n=='/GND' and poly.Contains(k.VECTOR2I_MM(x,y),i) for x,y,r,n in vias):continue
        ol=poly.COutline(i);pts=[xy(ol.CPoint(j)) for j in range(ol.PointCount())]
        xmin=min(p[0] for p in pts);xmax=max(p[0] for p in pts);ymin=min(p[1] for p in pts);ymax=max(p[1] for p in pts)
        cx=(xmin+xmax)/2;cy=(ymin+ymax)/2
        candidates=[(ix/10,iy/10) for ix in range(math.ceil(xmin*10),math.floor(xmax*10)+1) for iy in range(math.ceil(ymin*10),math.floor(ymax*10)+1)]
        candidates.sort(key=lambda p:(p[0]-cx)**2+(p[1]-cy)**2)
        found=next(((x,y) for x,y in candidates if poly.Contains(k.VECTOR2I_MM(x,y),i) and free(x,y)),None)
        entry={'layer':b.GetLayerName(zone.GetLayer()),'island':i,'bounds_mm':[xmin,ymin,xmax,ymax],'via':found}
        if found:
            x,y=found;v=k.PCB_VIA(b);v.SetPosition(k.VECTOR2I_MM(x,y));v.SetWidth(k.FromMM(.6));v.SetDrill(k.FromMM(.2))
            v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(GND)
            v.SetFrontTentingMode(k.TENTING_MODE_TENTED);v.SetBackTentingMode(k.TENTING_MODE_TENTED);b.Add(v);vias.append((x,y,.3,'/GND'))
        else:
            entry['ground_pads']=[label for x1,y1,x2,y2,label,net in pads if net=='/GND' and poly.Contains(k.VECTOR2I_MM((x1+x2)/2,(y1+y2)/2),i)]
        result.append(entry)
k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(PCB),b)
PCB.with_suffix('.stitching.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
