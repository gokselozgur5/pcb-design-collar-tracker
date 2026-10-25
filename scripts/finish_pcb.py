#!/usr/bin/env python3
"""Finish short local opens from the actual DRC, then re-run KiCad DRC.

Bounded grid search around each open. Uses conservative pad rectangles,
track/via geometry and through-via clearance on every copper layer. Fills
are regenerated after routing. KiCad DRC remains the acceptance authority.
"""
from pathlib import Path
import collections,hashlib,heapq,itertools,json,math,re
import pcbnew as k
ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'hardware/collar-tracker.kicad_pcb'
source_hash=hashlib.sha256(PCB.read_bytes()).hexdigest()
b=k.LoadBoard(str(PCB));d=json.loads((ROOT/'evidence/pcb-route-r6-drc.json').read_text())
layers=[k.F_Cu,k.B_Cu,k.In2_Cu,k.In1_Cu]
STEP=.05
def xy(v):return (v.x/1e6,v.y/1e6)
def point_segment(px,py,ax,ay,bx,by):
    dx,dy=bx-ax,by-ay
    t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy))) if dx or dy else 0
    return math.hypot(px-ax-t*dx,py-ay-t*dy)

def geometry():
    cells=collections.defaultdict(list);pads=[]
    for f in b.GetFootprints():
        for p in f.Pads():
            bb=p.GetBoundingBox();box=(bb.GetLeft()/1e6,bb.GetTop()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6)
            for layer in layers:
                if p.IsOnLayer(layer):pads.append((layer,p.GetNetname(),box))
    objects=[]
    for layer,net,box in pads:objects.append(('pad',layer,net,box,box))
    for t in b.GetTracks():
        if t.GetClass()=='PCB_TRACK' and t.GetNetname()=='/CHG_FAULT' and t.GetLayer()==k.F_Cu and min(t.GetStart().y,t.GetEnd().y)/1e6>116.3:
            continue
        if t.GetClass()=='PCB_VIA':
            v=k.Cast_to_PCB_VIA(t);x,y=xy(v.GetPosition());r=v.GetWidth(k.F_Cu)/2e6
            for layer in layers:objects.append(('via',layer,t.GetNetname(),(x,y,r),(x-r,y-r,x+r,y+r)))
        else:
            ax,ay=xy(t.GetStart());bx,by=xy(t.GetEnd());r=t.GetWidth()/2e6
            objects.append(('track',t.GetLayer(),t.GetNetname(),(ax,ay,bx,by,r),(min(ax,bx)-r,min(ay,by)-r,max(ax,bx)+r,max(ay,by)+r)))
    for item in objects:
        box=item[4]
        for x in range(math.floor(box[0]-.6),math.floor(box[2]+.6)+1):
            for y in range(math.floor(box[1]-.6),math.floor(box[3]+.6)+1):cells[(item[1],x,y)].append(item)
    return cells

for t in b.GetTracks():
    if t.GetClass()=='PCB_TRACK' and t.GetWidth()<k.FromMM(.1):t.SetWidth(k.FromMM(.1))

# The auto-router enclosed the unconnected BAT pin with the neighbouring
# status trace. Re-route that local status escape after connecting BAT.
ripped=[]
for t in list(b.GetTracks()):
    if t.GetClass()=='PCB_TRACK' and t.GetNetname()=='/CHG_FAULT' and t.GetLayer()==k.F_Cu and min(t.GetStart().y,t.GetEnd().y)/1e6>116.3:
        ripped.append(t)
assert len(ripped)==6, ('Unexpected status-escape source',len(ripped))
d['unconnected_items'].append({'items':[
    {'description':'Pad 3 [/CHG_FAULT] of U3 on F.Cu','pos':{'x':101.4,'y':118.2}},
    {'description':'Via [/CHG_FAULT] on B.Cu','pos':{'x':102.4947,'y':116.4438}}]})

def route(opening):
    items=opening['items'];a,z=items[0],items[1]
    net=re.search(r'\[([^]]+)\]',a['description'])[1]
    route_width=.15
    def lay(it):
        return next(layer for layer in layers if b.GetLayerName(layer) in it['description'])
    start=(a['pos']['x'],a['pos']['y'],lay(a));end=(z['pos']['x'],z['pos']['y'],lay(z))
    cells=geometry();memo={};via_memo={}
    def clear(x,y,layer,r=None,via=False):
        if r is None:r=route_width/2
        if not (100.3+r<=x<=129.7-r and 100.3+r<=y<=121.7-r):return False
        for kind,olayer,oname,data,box in cells[(layer,math.floor(x),math.floor(y))]:
            if oname==net and not(via and kind=='pad'):continue
            if kind=='pad':
                dx=max(box[0]-x,0,x-box[2]);dy=max(box[1]-y,0,y-box[3])
                distance=math.hypot(dx,dy)
                limit=.125 if oname==net else r+.105
            elif kind=='via':
                distance=math.hypot(x-data[0],y-data[1]);limit=r+data[2]+.105
            else:
                distance=point_segment(x,y,*data[:4]);limit=r+data[4]+.105
            if distance<limit-1e-8:return False
        return True
    def free(state):
        if state not in memo:memo[state]=clear(state[0]*STEP,state[1]*STEP,state[2])
        return memo[state]
    def via_free(ix,iy):
        key=(ix,iy)
        if key not in via_memo:via_memo[key]=all(clear(ix*STEP,iy*STEP,l,.225,True) for l in layers)
        return via_memo[key]
    def nearby(point):
        ix,iy=round(point[0]/STEP),round(point[1]/STEP)
        return [(ix+dx,iy+dy,point[2]) for dx in range(-1,2) for dy in range(-1,2)
                if free((ix+dx,iy+dy,point[2]))]
    starts=nearby(start);targets=set(nearby(end));assert starts and targets,(net,'no access')
    xmin=max(2007,math.floor((min(start[0],end[0])-5.5)/STEP));xmax=min(2593,math.ceil((max(start[0],end[0])+5.5)/STEP))
    ymin=max(2007,math.floor((min(start[1],end[1])-5.5)/STEP));ymax=min(2433,math.ceil((max(start[1],end[1])+5.5)/STEP))
    def h(s):return math.hypot(s[0]*STEP-end[0],s[1]*STEP-end[1])
    queue=[];dist={};parent={};serial=itertools.count()
    for s in starts:dist[s]=math.hypot(s[0]*STEP-start[0],s[1]*STEP-start[1]);heapq.heappush(queue,(dist[s]+h(s),next(serial),s));parent[s]=None
    visited=0;found=None
    while queue and visited<500000:
        cost,_,s=heapq.heappop(queue)
        if cost>dist[s]+h(s)+1e-8:continue
        visited+=1
        if s in targets:found=s;break
        neigh=[]
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            q=(s[0]+dx,s[1]+dy,s[2])
            if xmin<=q[0]<=xmax and ymin<=q[1]<=ymax and free(q) and clear((s[0]+dx/2)*STEP,(s[1]+dy/2)*STEP,s[2]):neigh.append((q,STEP*math.hypot(dx,dy)))
        if via_free(s[0],s[1]):
            neigh.extend(((s[0],s[1],l),1.2) for l in layers if l!=s[2])
        for q,extra in neigh:
            nd=dist[s]+extra
            if nd+1e-9<dist.get(q,1e20):dist[q]=nd;parent[q]=s;heapq.heappush(queue,(nd+h(q),next(serial),q))
    if found is None:
        print('local F.Cu access for',net, 'target',end,flush=True)
        for yy in [117.2+i*.1 for i in range(14)]:
            print(round(yy,2),''.join('.' if clear(100.4+i*.1,yy,k.F_Cu) else '#' for i in range(22)),flush=True)
    assert found is not None,(net,'no route',visited)
    path=[];cur=found
    while cur is not None:path.append(cur);cur=parent[cur]
    path.reverse()
    points=[start]+[(x*STEP,y*STEP,l) for x,y,l in path]+[end]
    # Compress only collinear same-layer segments.
    simplified=[]
    for p in points:
        if simplified and p==simplified[-1]:continue
        if len(simplified)>1 and p[2]==simplified[-1][2]==simplified[-2][2]:
            aa,zz=simplified[-2],simplified[-1]
            if abs((zz[0]-aa[0])*(p[1]-zz[1])-(zz[1]-aa[1])*(p[0]-zz[0]))<1e-9:simplified.pop()
        simplified.append(p)
    ni=b.FindNet(net)
    for aa,zz in zip(simplified,simplified[1:]):
        if aa[2]!=zz[2]:
            v=k.PCB_VIA(b);v.SetPosition(k.VECTOR2I_MM(aa[0],aa[1]));v.SetWidth(k.FromMM(.45));v.SetDrill(k.FromMM(.2));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(ni);v.SetFrontTentingMode(k.TENTING_MODE_TENTED);v.SetBackTentingMode(k.TENTING_MODE_TENTED);b.Add(v)
        else:
            t=k.PCB_TRACK(b);t.SetStart(k.VECTOR2I_MM(aa[0],aa[1]));t.SetEnd(k.VECTOR2I_MM(zz[0],zz[1]));t.SetLayer(aa[2]);t.SetWidth(k.FromMM(route_width));t.SetNet(ni);t.SetLocked(True);b.Add(t)
    print(net,'visited',visited,'segments',len(simplified),flush=True)
    return {'net':net,'points':simplified,'visited':visited}

result=[route(opening) for opening in sorted(d['unconnected_items'],key=lambda v:0 if '/VBAT' in v['items'][0]['description'] else 1)]
for t in ripped:b.Remove(t)
k.ZONE_FILLER(b).Fill(b.Zones());assert k.SaveBoard(str(PCB),b)
(ROOT/'evidence/local-routing-fixes.json').write_text(json.dumps({'input_sha256':source_hash,'routes':result,'output_sha256':hashlib.sha256(PCB.read_bytes()).hexdigest(),'acceptance':'pending independent KiCad DRC'},indent=2)+'\n')
