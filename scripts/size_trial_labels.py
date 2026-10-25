#!/usr/bin/env python3
"""plan with Shapely Python, then apply with KiCad Python; actual glyph geometry."""
import hashlib,json,sys
from pathlib import Path
mode=sys.argv[1];OUT=Path(sys.argv[2]).resolve();E=OUT/'evidence'
PCB=OUT/'hardware/collar-tracker.kicad_pcb'
source_sha=hashlib.sha256(PCB.read_bytes()).hexdigest()
if mode=='plan':
    import itertools,math
    from shapely.geometry import Polygon,Point,box
    from shapely.ops import unary_union
    from shapely.affinity import translate
    from shapely.prepared import prep
    data=json.loads((E/'geometry.json').read_text())
    assert data['source_sha256']==source_sha, 'Regenerate geometry before planning labels'
    def geom(polys):return unary_union([Polygon(p) for p in polys])
    obstacles={l:[] for l in ['F.Silkscreen','B.Silkscreen']}
    for p in data['pads']:
        for silk,mask,cu in [('F.Silkscreen','F.Mask','F.Cu'),('B.Silkscreen','B.Mask','B.Cu')]:
            if cu in p['layers']:obstacles[silk].append(geom(p['poly']).buffer(max(0,p['mask'].get(mask,0))+.21))
    for v in data['vias']:
        for l in obstacles:obstacles[l].append(Point(v['pos']).buffer(v['drill']/2+.31))
    for m in data['mask_graphics']:obstacles['F.Silkscreen' if m['layer']=='F.Mask' else 'B.Silkscreen'].append(geom(m['poly']).buffer(.21))
    bounds=data['board_bounds_mm']
    allowed=box(*bounds).buffer(-.3,join_style=2);result=[]
    deltas=sorted(itertools.product(range(-50,51),repeat=2),key=lambda d:(d[0]*d[0]+d[1]*d[1],abs(d[0])))
    for t in data['silks']:
        original=geom(t['poly']);obs=prep(unary_union(obstacles[t['layer']]));chosen=None
        for ix,iy in deltas:
            dx,dy=ix*.1,iy*.1;moved=translate(original,dx,dy)
            if allowed.covers(moved) and not obs.intersects(moved):chosen=(dx,dy,moved);break
        if chosen is None:raise RuntimeError('No legible position for '+t['text'])
        dx,dy,moved=chosen;obstacles[t['layer']].append(moved.buffer(.21))
        result.append({'id':t['id'],'text':t['text'],'delta_mm':[dx,dy],'distance_mm':math.hypot(dx,dy)})
    report=dict(source_sha256=source_sha,board_bounds_mm=bounds,items=result,
                scope='Actual glyph/mask/drill placement only; inspect interface association and native checks.')
    (E/'silk-placement.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
elif mode=='apply':
    import pcbnew as k
    plan=json.loads((E/'silk-placement.json').read_text())
    assert plan['source_sha256']==source_sha, 'Source changed after label planning'
    b=k.LoadBoard(str(PCB));drawings={g.m_Uuid.AsString():g for g in b.GetDrawings()}
    for item in plan['items']:
        g=drawings[item['id']];assert g.GetText()==item['text'];p=g.GetPosition();dx,dy=item['delta_mm']
        g.SetPosition(k.VECTOR2I(round(p.x+dx*1e6),round(p.y+dy*1e6)))
    assert k.SaveBoard(str(PCB),b)
    (E/'silk-applied.json').write_text(json.dumps(dict(before_sha256=source_sha,
        source_sha256=hashlib.sha256(PCB.read_bytes()).hexdigest(),items=plan['items']),indent=2)+'\n')
else:raise ValueError(mode)
