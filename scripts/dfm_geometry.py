#!/usr/bin/env python3
"""Export actual KiCad copper/mask geometry for independent DFM measurements."""
import hashlib, json, sys
from pathlib import Path
import pcbnew as k

root=Path(__file__).resolve().parents[1]
source=Path(sys.argv[1]) if len(sys.argv)>1 else root/'hardware/collar-tracker.kicad_pcb'
target=Path(sys.argv[2]) if len(sys.argv)>2 else root/'evidence/jlc-dfm-20261024/geometry-before.json'
b=k.LoadBoard(str(source)); layers=[k.F_Cu,k.In1_Cu,k.In2_Cu,k.B_Cu]
def xy(v):return [v.x/1e6,v.y/1e6]
def polygons(poly):
    return [[xy(poly.COutline(n).CPoint(i)) for i in range(poly.COutline(n).PointCount())] for n in range(poly.OutlineCount())]

out={'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
     'pads':[],'vias':[],'tracks':[],'mask_graphics':[],'silks':[]}
edges=[item for item in b.GetDrawings() if item.GetLayer()==k.Edge_Cuts]
if len(edges)==4 and all(item.GetShape()==k.SHAPE_T_SEGMENT for item in edges):
    corners={tuple(xy(p)) for edge in edges for p in [edge.GetStart(),edge.GetEnd()]}
    xmin,ymin=min(p[0] for p in corners),min(p[1] for p in corners)
    xmax,ymax=max(p[0] for p in corners),max(p[1] for p in corners)
    if corners=={(xmin,ymin),(xmin,ymax),(xmax,ymin),(xmax,ymax)} and all(
        edge.GetStart().x==edge.GetEnd().x or edge.GetStart().y==edge.GetEnd().y for edge in edges
    ):
        out['board_bounds_mm']=[xmin,ymin,xmax,ymax]
out['zones']=[{'layer':b.GetLayerName(z.GetLayer()),'net':z.GetNetname(),'minimum_width_mm':z.GetMinThickness()/1e6,
               'clearance_mm':z.GetLocalClearance()/1e6}
              for z in b.Zones() if not z.GetIsRuleArea()]
for f in b.GetFootprints():
    for p in f.Pads():
        ls=[b.GetLayerName(l) for l in layers if p.IsOnLayer(l)]
        if not ls:continue
        poly=p.GetEffectivePolygon(layers[next(i for i,l in enumerate(layers) if p.IsOnLayer(l))])
        out['pads'].append({'id':p.m_Uuid.AsString(),'ref':f.GetReference(),'pin':p.GetNumber(),
                           'net':p.GetNetname(),'layers':ls,'pos':xy(p.GetPosition()),'poly':polygons(poly),
                           'mask':{b.GetLayerName(l):p.GetSolderMaskExpansion(l)/1e6 for l in [k.F_Mask,k.B_Mask] if p.IsOnLayer(l)}})
    for g in f.GraphicalItems():
        if g.GetLayer() in [k.F_Mask,k.B_Mask] and g.GetClass()=='PCB_SHAPE':
            poly=k.SHAPE_POLY_SET();g.TransformShapeToPolygon(poly,g.GetLayer(),0,1000,k.ERROR_OUTSIDE)
            out['mask_graphics'].append({'ref':f.GetReference(),'layer':b.GetLayerName(g.GetLayer()),'poly':polygons(poly)})
for t in b.GetTracks():
    item={'id':t.m_Uuid.AsString(),'net':t.GetNetname()}
    if t.GetClass()=='PCB_VIA':
        v=k.Cast_to_PCB_VIA(t)
        item.update(pos=xy(v.GetPosition()),diameter=v.GetWidth(k.F_Cu)/1e6,drill=v.GetDrill()/1e6,
                    layers=[b.GetLayerName(l) for l in layers if v.IsOnLayer(l)])
        out['vias'].append(item)
    else:
        item.update(start=xy(t.GetStart()),end=xy(t.GetEnd()),layer=b.GetLayerName(t.GetLayer()),width=t.GetWidth()/1e6)
        out['tracks'].append(item)
for g in b.GetDrawings():
    if g.GetLayer() in [k.F_SilkS,k.B_SilkS] and g.GetClass()=='PCB_TEXT':
        poly=k.SHAPE_POLY_SET();g.TransformTextToPolySet(poly,0,1000,k.ERROR_OUTSIDE)
        out['silks'].append({'id':g.m_Uuid.AsString(),'text':g.GetText(),'layer':b.GetLayerName(g.GetLayer()),'poly':polygons(poly)})
target.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({key:len(out[key]) for key in ['pads','vias','tracks','mask_graphics']}))
