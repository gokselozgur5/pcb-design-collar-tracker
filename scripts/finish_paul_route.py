#!/usr/bin/env python3
"""Complete r04 opens on the outer layers, preserving local GND connections.

Use 0.4 mm power / 0.3 mm VIO trunks with bounded 0.2 mm pad escapes.
Include footprint keepouts. Grid sampling is a planner, not DRC acceptance.
Usage: kicad-python finish_paul_route.py BOARD DRC_JSON [OUTPUT_BOARD]
"""
from pathlib import Path
import argparse
import collections,hashlib,heapq,itertools,json,math,re,subprocess,sys
import pcbnew as k

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('board',type=Path)
parser.add_argument('drc_json',type=Path)
parser.add_argument('output_board',type=Path,nargs='?')
parser.add_argument('--route-limit-mm',type=float,default=40,
                    help='Candidate detour review screen, not a DRC rule or signal qualification')
parser.add_argument('--sim-inputs', type=Path,
                    help='JSON list of incoming track IDs; reserve these and J6 pins 1/2/3 as obstacles')
parser.add_argument('--anchors', type=Path,
                    help='JSON net-to-via mapping; start from its F.Cu anchor when that island is selected')
parser.add_argument('--first-net', action='append', default=[],
                    help='Route this exact net name first; repeat to define a deliberate order')
parser.add_argument('--low-current-net', action='append', default=[],
                    help='Use 0.2 mm for added control branches only; verify the existing power backbone remains connected')
parser.add_argument('--only-net', action='append', default=[],
                    help='Attempt only these nets; the following native DRC must still cover the full board')
parser.add_argument('--relocatable-vias', type=Path,
                    help='Source-bound return-only GND via candidates; remove only those crossed by an accepted route')
parser.add_argument('--raster-python', type=Path,
                    help='Geometry Python executable for the faster 0.2 mm proposal search; native checks still apply')
parser.add_argument('--six-layer-signals', action='store_true',
                    help='Use F/In2/In3/B only in the isolated six-layer candidate; In1/In4 remain dedicated GND')
parser.add_argument('--via-ground-radius-mm',type=float,
                    help='Require every new signal via to be within this distance of an existing GND via')
args=parser.parse_args()
script_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
raster_script=Path(__file__).with_name('raster_route.py')
raster_sha=hashlib.sha256(raster_script.read_bytes()).hexdigest() if args.raster_python else None
assert math.isfinite(args.route_limit_mm) and args.route_limit_mm>0
PCB=args.board;DRC=args.drc_json;OUTPUT=args.output_board or PCB
b=k.LoadBoard(str(PCB));d=json.loads(DRC.read_text());layers=[k.F_Cu,k.B_Cu];STEP=.05
if args.six_layer_signals:
    assert PCB.resolve().parent.parent.name == 'power-r05h-six-layer'
    assert b.GetCopperLayerCount() == 6
    assert {z.GetLayer() for z in b.Zones() if not z.GetIsRuleArea()} == {k.In1_Cu,k.In4_Cu}
    assert all(z.GetNetname() == '/GND' for z in b.Zones() if not z.GetIsRuleArea())
    layers=[k.F_Cu,k.In2_Cu,k.In3_Cu,k.B_Cu]
source_sha=hashlib.sha256(PCB.read_bytes()).hexdigest()
sim_inputs=set(json.loads(args.sim_inputs.read_text())) if args.sim_inputs else set()
anchors=json.loads(args.anchors.read_text()) if args.anchors else {}
assert sim_inputs <= {t.m_Uuid.AsString() for t in b.GetTracks()}, 'Stale protected input IDs'
assert ('paul-nanosim' in str(PCB) or PCB.resolve().parent.parent.name in
        {'power-r05-supervised', 'power-r05b-pin-exits', 'power-r05c-return-corridors',
         'power-r05d-joint-routing', 'power-r05e-native-joint',
         'power-r05f-return-reset', 'power-r05g-local-crossings',
         'power-r05h-six-layer'}), 'Use an isolated nano-SIM trial'
branch_backbones={}
if args.low_current_net:
    assert PCB.resolve().parent.parent.name in {'power-r05b-pin-exits', 'power-r05c-return-corridors',
                                             'power-r05d-joint-routing', 'power-r05e-native-joint',
                                             'power-r05f-return-reset', 'power-r05g-local-crossings',
                                             'power-r05h-six-layer'}
    assert set(args.low_current_net)<={'/VDD_NRF','/VBAT','/VIO_1V8'}
    from trim_power_r05_tails import islands
    old=json.loads((Path(__file__).resolve().parents[1]/
        'experiments/paul-nanosim-r04i-sim-access-40x32/hardware/design.json').read_text())
    oldpins={p['ref']+'.'+str(n):'/'+v for p in old['parts'] for n,v in p['nets'].items() if p.get('onboard')}
    byid={p.m_Uuid.AsString():f.GetReference()+'.'+p.GetNumber() for f in b.GetFootprints() for p in f.Pads()}
    for net in args.low_current_net:
        groups=[]
        for _,uids in islands(b,{net}):
            original=sorted(byid[u] for u in uids if oldpins.get(byid[u])==net)
            if original:groups.append(original)
        assert len(groups)==1, ('Power backbone is not already connected',net,groups)
        branch_backbones[net]=groups[0]
edges=[item for item in b.GetDrawings() if item.GetLayer()==k.Edge_Cuts]
assert len(edges)==4 and all(item.GetShape()==k.SHAPE_T_SEGMENT for item in edges), 'Planner requires a rectangular outline'
corners={(p.x/1e6,p.y/1e6) for item in edges for p in [item.GetStart(),item.GetEnd()]}
xmin,ymin=min(p[0] for p in corners),min(p[1] for p in corners)
xmax,ymax=max(p[0] for p in corners),max(p[1] for p in corners)
assert corners=={(xmin,ymin),(xmin,ymax),(xmax,ymin),(xmax,ymax)}, 'Planner requires a rectangular outline'
assert all(item.GetStart().x==item.GetEnd().x or item.GetStart().y==item.GetEnd().y for item in edges)
vec=lambda x,y:k.VECTOR2I(round(x*1e6),round(y*1e6))
def xy(v):return (v.x/1e6,v.y/1e6)
ground_points=[xy(t.GetPosition()) for t in b.GetTracks()
               if t.GetClass()=='PCB_VIA' and t.GetNetname()=='/GND']
if args.via_ground_radius_mm is not None:
    assert 0 < args.via_ground_radius_mm <= 2 and ground_points
def point_segment(px,py,ax,ay,bx,by):
    dx,dy=bx-ax,by-ay
    t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy))) if dx or dy else 0
    return math.hypot(px-ax-t*dx,py-ay-t*dy)
def point_tree(points,depth=0):
    if not points:return None
    axis=depth%2;points=sorted(points,key=lambda p:p[axis]);mid=len(points)//2
    return points[mid],axis,point_tree(points[:mid],depth+1),point_tree(points[mid+1:],depth+1)
def nearest_squared(tree,x,y,best=math.inf):
    if tree is None:return best
    point,axis,left,right=tree
    best=min(best,(x-point[0])**2+(y-point[1])**2)
    delta=(x,y)[axis]-point[axis]
    near,far=(left,right) if delta<0 else (right,left)
    best=nearest_squared(near,x,y,best)
    if delta*delta<best:best=nearest_squared(far,x,y,best)
    return best
relocatable=set();removed_returns=[];ground_islands_before=None
if args.relocatable_vias:
    assert PCB.resolve().parent.parent.name=='power-r05c-return-corridors'
    candidates=json.loads(args.relocatable_vias.read_text())
    assert candidates['source_sha256']==source_sha, 'Stale return-only via candidates'
    relocatable={v['id'] for v in candidates['candidates']}
    tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
    assert relocatable and relocatable<=tracks.keys()
    for uid in relocatable:
        v=tracks[uid];assert v.GetClass()=='PCB_VIA' and v.GetNetname()=='/GND'
        x,y=xy(v.GetPosition());radius=v.GetWidth(k.F_Cu)/2e6
        # A conservative native check independently prevents removal of a local
        # ground-pad escape. This excludes pad bounding boxes on either side.
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.GetNetname()!='/GND':continue
                bb=p.GetBoundingBox()
                distance=math.hypot(max(bb.GetLeft()/1e6-x,0,x-bb.GetRight()/1e6),
                                    max(bb.GetTop()/1e6-y,0,y-bb.GetBottom()/1e6))
                assert distance>radius+.001, ('Via supplies local ground pad',uid)
        for t in tracks.values():
            if t.GetClass()!='PCB_TRACK':continue
            distance=point_segment(x,y,*xy(t.GetStart()),*xy(t.GetEnd()))-radius-t.GetWidth()/2e6
            if t.GetNetname()=='/GND':assert distance>.001, ('Via supplies local ground track',uid)
            if t.GetNetname() in {'/LTE_RF','/LTE_ANT','/GPS_RF','/GNSS_ANT','/GNSS_FEM_IN','/GNSS_FEM_OUT','/FILT_OUT','/AMP_IN'}:
                assert distance>2, ('Via is near RF copper',uid)
    from trim_power_r05_tails import islands
    ground_islands_before=islands(b,{'/GND'})
def geometry():
    cells=collections.defaultdict(list);objects=[]
    for f in b.GetFootprints():
        for p in f.Pads():
            bb=p.GetBoundingBox();box=(bb.GetLeft()/1e6,bb.GetTop()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6)
            for l in layers:
                if p.IsOnLayer(l):
                    net='protected_sim_input' if args.sim_inputs and f.GetReference()=='J6' and p.GetNumber() in ['1','2','3'] else p.GetNetname()
                    objects.append(('pad',l,net,box,box))
    for t in b.GetTracks():
        if t.m_Uuid.AsString() in relocatable:continue
        if t.GetClass()=='PCB_VIA':
            v=k.Cast_to_PCB_VIA(t);x,y=xy(v.GetPosition());r=v.GetWidth(k.F_Cu)/2e6
            for l in layers:objects.append(('via',l,t.GetNetname(),(x,y,r),(x-r,y-r,x+r,y+r)))
        else:
            ax,ay=xy(t.GetStart());bx,by=xy(t.GetEnd());r=t.GetWidth()/2e6
            net='protected_sim_input' if t.m_Uuid.AsString() in sim_inputs else t.GetNetname()
            objects.append(('track',t.GetLayer(),net,(ax,ay,bx,by,r),(min(ax,bx)-r,min(ay,by)-r,max(ax,bx)+r,max(ay,by)+r)))
    for z in [*b.Zones(), *(z for f in b.GetFootprints() for z in f.Zones())]:
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
        if via and args.via_ground_radius_mm is not None and min(
                math.hypot(x-gx,y-gy) for gx,gy in ground_points)>args.via_ground_radius_mm:
            return False
        r=width/2 if r is None else r
        if not (xmin+.401+r<=x<=xmax-.401-r and ymin+.401+r<=y<=ymax-.401-r):return False
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
    v=k.PCB_VIA(b);v.SetPosition(vec(x,y));v.SetWidth(k.FromMM(.6));v.SetDrill(k.FromMM(.2))
    v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(b.FindNet(net))
    v.SetFrontTentingMode(k.TENTING_MODE_TENTED);v.SetBackTentingMode(k.TENTING_MODE_TENTED);b.Add(v)
stitches=[]
assert not any('Zone ' in it['description'] or '[/GND]' in it['description'] for op in d['unconnected_items'] for it in op['items']), 'Ground must already be complete'

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
        # Native connectivity includes touching copper and pad interiors; an
        # endpoint-only graph can miss a valid branch or the other side of a via.
        b.BuildConnectivity()
        connectivity=b.GetConnectivity()
        todo=[obj];seen=set();points=[]
        while todo:
            current=todo.pop();ident=current.m_Uuid.AsString()
            if ident in seen:continue
            seen.add(ident);points.extend(nodes(current))
            if current.GetClass()=='PCB_TRACK':
                start,end=xy(current.GetStart()),xy(current.GetEnd())
                count=math.ceil(math.dist(start,end)/.4)
                points.extend((start[0]+(end[0]-start[0])*i/count,
                               start[1]+(end[1]-start[1])*i/count,current.GetLayer())
                              for i in range(1,count))
            todo.extend(t for t in connectivity.GetConnectedTracks(current)
                        if t.GetNetname()==obj.GetNetname())
            todo.extend(p for p in connectivity.GetConnectedPads(current)
                        if p.GetNetname()==obj.GetNetname())
        anchor=anchors.get(obj.GetNetname())
        if anchor and anchor['id'] in seen:
            via=next(t for t in b.GetTracks() if t.m_Uuid.AsString()==anchor['id'])
            assert via.GetClass()=='PCB_VIA' and math.dist(xy(via.GetPosition()),anchor['pos'])<.000001
            return [(*anchor['pos'],k.F_Cu)]
        return list(dict.fromkeys(points))
    l=next(l for l in layers if b.GetLayerName(l) in item['description'])
    return [(item['pos']['x'],item['pos']['y'],l)]
def route(opening):
    a,z=opening['items'][:2];net=re.search(r'\[([^]]+)\]',a['description'])[1]
    starts_exact=item_points(a);ends_exact=item_points(z)
    # Search out of the smaller copper island. A trapped pad can exhaust in a
    # few states; searching the entire board toward that pad wastes work.
    if len(starts_exact)>len(ends_exact):
        starts_exact,ends_exact=ends_exact,starts_exact
    width=.4 if net in ['/VDD_NRF','/VIN_5V','/VBAT','/VSYS'] else .3 if net=='/VIO_1V8' else .2
    if net in args.low_current_net:
        width=.2
    netpads=[p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname()==net]
    padcenters=[(*xy(p.GetPosition()),l) for p in netpads for l in layers if p.IsOnLayer(l)]
    # Narrow escapes are allowed only within 1 mm of an actual same-net pad.
    def route_width(x,y,layer):
        if width>.2 and any(l==layer and math.hypot(x-px,y-py)<=1.0 for px,py,l in padcenters):return .2
        return width
    cells=geometry()
    base_clear=clearance_checker(net,width,cells);memo={};via_memo={};hmemo={}
    def clear(x,y,layer,r=None,via=False):
        return base_clear(x,y,layer,route_width(x,y,layer)/2 if r is None else r,via)
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
    backend='native-python'
    request_sha=None
    if args.raster_python and width==.2:
        backend='shapely-raster'
        assert hashlib.sha256(raster_script.read_bytes()).hexdigest()==raster_sha, 'Raster helper changed during routing'
        unique={id(obj):obj for rows in cells.values() for obj in rows}
        objects=[(kind,layers.index(layer),other,data,box) for kind,layer,other,data,box in unique.values()]
        request=dict(bounds=[xmin,ymin,xmax,ymax],width=width,net=net,objects=objects,
                     layer_count=len(layers),
                     via_ground_radius_mm=args.via_ground_radius_mm,ground_points=ground_points,
                     starts=[(x,y,layers.index(l)) for x,y,l in starts_exact],
                     ends=[(x,y,layers.index(l)) for x,y,l in ends_exact],state_limit=600000)
        payload=json.dumps(request)
        request_sha=hashlib.sha256(payload.encode()).hexdigest()
        request_path=PCB.parent.parent/'build'/('raster-'+request_sha[:16]+'.json')
        request_path.write_text(payload+'\n')
        # Preserve the venv executable path: resolving its symlink would select
        # the base interpreter and discard the geometry environment.
        completed=subprocess.run([str(args.raster_python.absolute()),str(raster_script.resolve())],
                                 input=payload,text=True,capture_output=True)
        if completed.returncode:
            raise RuntimeError((net,'raster helper failed',completed.returncode,completed.stderr[-1000:]))
        proposal=json.loads(completed.stdout)
        print('raster',net,proposal['status'],'visited',proposal['visited'],
              'seconds',round(proposal.get('elapsed_seconds',0),3),flush=True)
        if proposal['status']!='found':
            raise RuntimeError((net,proposal['status'],proposal['visited'],request_sha))
        points=[(x,y,layers[l]) for x,y,l in proposal['points']]
        visited=proposal['visited']
        for aa,zz in zip(points,points[1:]):
            if aa[2]!=zz[2]:
                assert aa[:2]==zz[:2] and all(clear(aa[0],aa[1],l,.3,True) for l in layers), 'Raster via failed native-geometry planner check'
            else:
                assert all(clear(aa[0]+(zz[0]-aa[0])*t,aa[1]+(zz[1]-aa[1])*t,aa[2]) for t in [0,.25,.5,.75,1]), 'Raster segment failed native-geometry planner check'
    else:
        starts=nearby(starts_exact);targets=nearby(ends_exact)
        if not starts or not targets:raise RuntimeError((net,'no access',starts_exact,ends_exact))
        target_tree=point_tree(list({(p[0],p[1]) for p in ends_exact}))
        def h(s):
            key=s[:2]
            if key not in hmemo:hmemo[key]=math.sqrt(nearest_squared(target_tree,s[0]*STEP,s[1]*STEP))
            return hmemo[key]
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
        if found is None:
            bounds={b.GetLayerName(l):dict(states=len(rows),
                        x=[min(p[0] for p in rows)*STEP,max(p[0] for p in rows)*STEP],
                        y=[min(p[1] for p in rows)*STEP,max(p[1] for p in rows)*STEP])
                    for l in layers if (rows:=[p for p in dist if p[2]==l])}
            raise RuntimeError((net,'no route',visited,bounds))
        path=[];cur=found
        while cur is not None:path.append(cur);cur=parent[cur]
        path.reverse();points=[origin[found]]+[(x*STEP,y*STEP,l) for x,y,l in path]+[targets[found]]
    simplified=[]
    for p in points:
        if simplified and p==simplified[-1]:continue
        if len(simplified)>1 and p[2]==simplified[-1][2]==simplified[-2][2]:
            aa,zz=simplified[-2],simplified[-1]
            if (abs((zz[0]-aa[0])*(p[1]-zz[1])-(zz[1]-aa[1])*(p[0]-zz[0]))<1e-9 and route_width(*aa)==route_width(*zz)==route_width(*p)):simplified.pop()
        simplified.append(p)
    length=sum(math.dist(aa[:2],zz[:2]) for aa,zz in zip(simplified,simplified[1:]))
    if length>args.route_limit_mm:
        proposal=OUTPUT.with_suffix('.detour-proposal.json')
        proposal.write_text(json.dumps({'before_sha256':source_sha,'net':net,
            'length_mm':length,'starts':starts_exact,'ends':ends_exact,'points':simplified,
            'scope':'Rejected routing proposal; these points were not added to the board.'},indent=2)+'\n')
        raise RuntimeError((net,'detour needs topology review',round(length,3),visited))
    for via in list(b.GetTracks()):
        uid=via.m_Uuid.AsString()
        if uid not in relocatable:continue
        x,y=xy(via.GetPosition());radius=via.GetWidth(k.F_Cu)/2e6
        crosses=False
        for aa,zz in zip(simplified,simplified[1:]):
            if aa[2]!=zz[2]:
                crosses |= math.hypot(x-aa[0],y-aa[1])<radius+.3+.20001
            else:
                width_here=min(route_width(*aa),route_width(*zz))
                crosses |= point_segment(x,y,*aa[:2],*zz[:2])<radius+width_here/2+.20001
        if crosses:
            removed_returns.append(dict(id=uid,pos=[x,y],route_net=net,reason='Accepted route crosses return-only via clearance'))
            b.Delete(via)
    if ground_islands_before is not None:
        assert islands(b,{'/GND'})==ground_islands_before, 'Return relocation changed native local ground pad islands'
    for aa,zz in zip(simplified,simplified[1:]):
        if aa[2]!=zz[2]:addvia(aa[0],aa[1],net)
        else:
            t=k.PCB_TRACK(b);t.SetStart(vec(aa[0],aa[1]));t.SetEnd(vec(zz[0],zz[1]))
            t.SetLayer(aa[2]);t.SetWidth(round(min(route_width(*aa),route_width(*zz))*1e6));t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
    print(net,'visited',visited,'segments',len(simplified),flush=True)
    return {'net':net,'points':simplified,'visited':visited,'search_backend':backend,'raster_input_sha256':request_sha,'trunk_width_mm':width,'pad_escape_width_mm':.2,'escape_radius_mm':1.0}
results=[];failures=[];interrupted=False
print('Routing',len(d['unconnected_items']),'opens; footprint keepouts enabled',flush=True)
priority={net:i for i,net in enumerate(dict.fromkeys(args.first_net + ['/SPI_SCK','/SIM_IO','/SIM_CLK',
    '/ILIM_VSET','/ISET','/BAT_NTC','/VIN_5V','/VBAT','/CHG_STAT','/CHG_FAULT','/VSYS']))}
try:
    for opening in sorted(d['unconnected_items'],key=lambda op:priority.get(re.search(r'\[([^]]+)\]',op['items'][0]['description'])[1],len(priority))):
        if args.only_net and re.search(r'\[([^]]+)\]',opening['items'][0]['description'])[1] not in args.only_net:continue
        if any('Zone ' in item['description'] for item in opening['items']):continue
        try:results.append(route(opening))
        except RuntimeError as e:failures.append(str(e));print('FAILED',e,flush=True)
except KeyboardInterrupt:
    interrupted=True
    print('Interrupted; preserving completed routes for native review',flush=True)
k.ZONE_FILLER(b).Fill(b.Zones());assert k.SaveBoard(str(OUTPUT),b)
OUTPUT.with_suffix('.local-routing.json').write_text(json.dumps({'before_sha256':source_sha,
    'protected_sim_input_ids':sorted(sim_inputs),'route_anchors':anchors,'first_nets':args.first_net,
    'low_current_branch_nets':args.low_current_net,
    'existing_power_backbone_pins':branch_backbones,
    'only_nets':args.only_net,'router_script_sha256':script_sha,'raster_script_sha256':raster_sha,
    'routing_layers':[b.GetLayerName(l) for l in layers],
    'via_ground_radius_mm':args.via_ground_radius_mm,
    'relocatable_via_input_sha256':hashlib.sha256(args.relocatable_vias.read_bytes()).hexdigest() if args.relocatable_vias else None,
    'removed_return_vias':removed_returns,
    'route_limit_mm':args.route_limit_mm,'board_bounds_mm':[xmin,ymin,xmax,ymax],
    'source_sha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),'routes':results,
    'ground_stitches':stitches,'failed':failures,'interrupted':interrupted,
    'acceptance':'Pending native DRC and independent geometry audit'},indent=2)+'\n')
print('saved',str(OUTPUT),flush=True)
if interrupted:sys.exit(130)
