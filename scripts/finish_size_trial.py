#!/usr/bin/env python3
"""Complete DRC-reported opens at >=0.20 mm, F/B only, with 0.60/0.20 vias.

Conservative pad boxes and existing copper are obstacles. Final native DRC and
the independent geometry audit are mandatory; grid sampling alone is not proof.
Usage: kicad-python finish_size_trial.py BOARD DRC_JSON [OUTPUT_BOARD]
"""
from pathlib import Path
import collections,heapq,itertools,json,math,re,sys
import pcbnew as k

PCB=Path(sys.argv[1]);DRC=Path(sys.argv[2]);OUTPUT=Path(sys.argv[3]) if len(sys.argv)>3 else PCB
b=k.LoadBoard(str(PCB));d=json.loads(DRC.read_text());layers=[k.F_Cu,k.B_Cu];STEP=.05
config=PCB.parent.parent/'evidence/source.json'
if config.exists() and json.loads(config.read_text()).get('inner2_signal',False):layers.append(k.In2_Cu)
def xy(v):return (v.x/1e6,v.y/1e6)
def point_segment(px,py,ax,ay,bx,by):
    dx,dy=bx-ax,by-ay
    t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy))) if dx or dy else 0
    return math.hypot(px-ax-t*dx,py-ay-t*dy)
def geometry():
    cells=collections.defaultdict(list);objects=[]
    for f in b.GetFootprints():
        for p in f.Pads():
            bb=p.GetBoundingBox();box=(bb.GetLeft()/1e6,bb.GetTop()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6)
            for l in layers:
                if p.IsOnLayer(l):objects.append(('pad',l,p.GetNetname(),box,box))
    for t in b.GetTracks():
        if t.GetClass()=='PCB_VIA':
            v=k.Cast_to_PCB_VIA(t);x,y=xy(v.GetPosition());r=v.GetWidth(k.F_Cu)/2e6
            for l in layers:objects.append(('via',l,t.GetNetname(),(x,y,r),(x-r,y-r,x+r,y+r)))
        else:
            ax,ay=xy(t.GetStart());bx,by=xy(t.GetEnd());r=t.GetWidth()/2e6
            objects.append(('track',t.GetLayer(),t.GetNetname(),(ax,ay,bx,by,r),(min(ax,bx)-r,min(ay,by)-r,max(ax,bx)+r,max(ay,by)+r)))
    for z in b.Zones():
        if not z.GetIsRuleArea():continue
        bb=z.GetBoundingBox();box=(bb.GetLeft()/1e6,bb.GetTop()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6)
        for l in layers:
            if z.IsOnLayer(l):
                if z.GetDoNotAllowTracks():objects.append(('keepout',l,'',box,box))
                elif z.GetDoNotAllowVias():objects.append(('via_keepout',l,'',box,box))
    for item in objects:
        box=item[4]
        for x in range(math.floor(box[0]-.7),math.floor(box[2]+.7)+1):
            for y in range(math.floor(box[1]-.7),math.floor(box[3]+.7)+1):cells[(item[1],x,y)].append(item)
    return cells
def clearance_checker(net,width,cells):
    def clear(x,y,layer,r=None,via=False):
        r=width/2 if r is None else r
        if not (100.401+r<=x<=134.599-r and 100.401+r<=y<=127.599-r):return False
        for kind,l,oname,data,box in cells[(layer,math.floor(x),math.floor(y))]:
            if kind=='via_keepout' and not via:continue
            if oname==net and not (via and kind in ['pad','via']):continue
            if kind in ['pad','keepout','via_keepout']:
                distance=math.hypot(max(box[0]-x,0,x-box[2]),max(box[1]-y,0,y-box[3]));limit=r+.19999
            elif kind=='via':distance=math.hypot(x-data[0],y-data[1]);limit=r+data[2]+.19999
            else:distance=point_segment(x,y,*data[:4]);limit=r+data[4]+.19999
            if distance<limit-1e-8:return False
        return True
    return clear
def addvia(x,y,net):
    v=k.PCB_VIA(b);v.SetPosition(k.VECTOR2I_MM(x,y));v.SetWidth(k.FromMM(.6));v.SetDrill(k.FromMM(.2))
    v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(b.FindNet(net))
    v.SetFrontTentingMode(k.TENTING_MODE_TENTED);v.SetBackTentingMode(k.TENTING_MODE_TENTED);b.Add(v)
stitches=[]
if any('Zone ' in it['description'] for op in d['unconnected_items'] for it in op['items']):
    clear=clearance_checker('/GND',.2,geometry())
    for x,y in [(133,126),(133,101.5),(119,102),(107.5,104),(130.5,123),(133,110)]:
        if all(clear(x,y,l,.3,True) for l in layers):addvia(x,y,'/GND');stitches.append([x,y])
    print('ground stitches',stitches,flush=True)

def item_points(item):
    ident=item.get('uuid');obj=None
    for t in b.GetTracks():
        if t.m_Uuid.AsString()==ident:obj=t;break
    if obj is None:
        obj=next((p for f in b.GetFootprints() for p in f.Pads() if p.m_Uuid.AsString()==ident),None)
    if obj is not None:
        def nodes(t):
            if t.GetClass()=='PCB_VIA':return [(*xy(t.GetPosition()),l) for l in layers]
            if t.GetClass()=='PAD':return [(*xy(t.GetPosition()),l) for l in layers if t.IsOnLayer(l)]
            return [(*xy(t.GetStart()),t.GetLayer()),(*xy(t.GetEnd()),t.GetLayer())]
        def key(p):return (round(p[0],4),round(p[1],4),p[2])
        edges=collections.defaultdict(list)
        for t in b.GetTracks():
            if t.GetNetname()==obj.GetNetname():
                ends=nodes(t)
                for p in ends:edges[key(p)].extend(ends)
        todo=nodes(obj);seen={}
        if obj.GetClass()=='PAD':
            bb=obj.GetBoundingBox()
            for t in b.GetTracks():
                if t.GetNetname()==obj.GetNetname():
                    todo.extend(p for p in nodes(t) if obj.IsOnLayer(p[2]) and bb.Contains(k.VECTOR2I_MM(p[0],p[1])))
        while todo:
            p=todo.pop();pk=key(p)
            if pk in seen:continue
            seen[pk]=p;todo.extend(edges[pk])
        return list(seen.values())
    l=next(l for l in layers if b.GetLayerName(l) in item['description'])
    return [(item['pos']['x'],item['pos']['y'],l)]
def route(opening):
    a,z=opening['items'][:2];net=re.search(r'\[([^]]+)\]',a['description'])[1]
    starts_exact=item_points(a);ends_exact=item_points(z);width=.2
    clear=clearance_checker(net,width,geometry());memo={};via_memo={}
    def free(s):
        if s not in memo:memo[s]=clear(s[0]*STEP,s[1]*STEP,s[2])
        return memo[s]
    def via_free(ix,iy):
        key=(ix,iy)
        if key not in via_memo:via_memo[key]=all(clear(ix*STEP,iy*STEP,l,.3,True) for l in layers)
        return via_memo[key]
    def nearby(points):
        result={}
        for point in points:
            ix,iy=round(point[0]/STEP),round(point[1]/STEP)
            for dx,dy in itertools.product(range(-1,2),repeat=2):
                s=(ix+dx,iy+dy,point[2])
                if free(s) and all(clear(point[0]+(s[0]*STEP-point[0])*t,point[1]+(s[1]*STEP-point[1])*t,point[2]) for t in [0,.25,.5,.75,1]):result[s]=point
        return result
    starts=nearby(starts_exact);targets=nearby(ends_exact)
    if not starts or not targets:raise RuntimeError((net,'no access',starts_exact,ends_exact))
    def h(s):return min(math.hypot(s[0]*STEP-e[0],s[1]*STEP-e[1]) for e in ends_exact)
    queue=[];dist={};parent={};origin={};serial=itertools.count()
    for s,p in starts.items():
        dist[s]=math.hypot(s[0]*STEP-p[0],s[1]*STEP-p[1]);parent[s]=None;origin[s]=p
        heapq.heappush(queue,(dist[s]+h(s),next(serial),s))
    visited=0;found=None
    while queue and visited<600000:
        cost,_,s=heapq.heappop(queue)
        if cost>dist[s]+h(s)+1e-8:continue
        visited+=1
        if s in targets:found=s;break
        neigh=[]
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            q=(s[0]+dx,s[1]+dy,s[2])
            if free(q) and clear((s[0]+dx/2)*STEP,(s[1]+dy/2)*STEP,s[2]):neigh.append((q,STEP*math.hypot(dx,dy)))
        if via_free(s[0],s[1]):neigh.extend(((s[0],s[1],l),2.) for l in layers if l!=s[2])
        for q,extra in neigh:
            nd=dist[s]+extra
            if nd+1e-9<dist.get(q,1e20):
                dist[q]=nd;parent[q]=s;origin[q]=origin[s];heapq.heappush(queue,(nd+h(q),next(serial),q))
    if found is None:raise RuntimeError((net,'no route',visited))
    path=[];cur=found
    while cur is not None:path.append(cur);cur=parent[cur]
    path.reverse();points=[origin[found]]+[(x*STEP,y*STEP,l) for x,y,l in path]+[targets[found]]
    simplified=[]
    for p in points:
        if simplified and p==simplified[-1]:continue
        if len(simplified)>1 and p[2]==simplified[-1][2]==simplified[-2][2]:
            aa,zz=simplified[-2],simplified[-1]
            if abs((zz[0]-aa[0])*(p[1]-zz[1])-(zz[1]-aa[1])*(p[0]-zz[0]))<1e-9:simplified.pop()
        simplified.append(p)
    for aa,zz in zip(simplified,simplified[1:]):
        if aa[2]!=zz[2]:addvia(aa[0],aa[1],net)
        else:
            t=k.PCB_TRACK(b);t.SetStart(k.VECTOR2I_MM(aa[0],aa[1]));t.SetEnd(k.VECTOR2I_MM(zz[0],zz[1]))
            t.SetLayer(aa[2]);t.SetWidth(k.FromMM(width));t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
    print(net,'visited',visited,'segments',len(simplified),flush=True)
    return {'net':net,'points':simplified,'visited':visited}
results=[];failures=[]
for opening in sorted(d['unconnected_items'],key=lambda op:0 if any('[/VBAT]' in item['description'] for item in op['items']) else 1):
    if any('Zone ' in item['description'] for item in opening['items']):continue
    try:results.append(route(opening))
    except RuntimeError as e:failures.append(str(e));print('FAILED',e,flush=True)
k.ZONE_FILLER(b).Fill(b.Zones());assert k.SaveBoard(str(OUTPUT),b)
OUTPUT.with_suffix('.local-routing.json').write_text(json.dumps({'routes':results,'ground_stitches':stitches,'failed':failures,'acceptance':'Pending native DRC and independent geometry audit'},indent=2)+'\n')
print('saved',str(OUTPUT),flush=True)
