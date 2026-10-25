#!/usr/bin/env python3
"""Apply the first JLC report corrections to the preserved 0.2 PCB.

This preserves pad copper dimensions, nets and antenna routing; J4 moves 0.2 mm.
It does not certify the unresolved circuit/RF design or emulate JLCDFM.
"""
from pathlib import Path
import hashlib,json,math
import pcbnew as k

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'snapshots/pre-dfm-fix-20261024/hardware/collar-tracker.kicad_pcb'
OUT=ROOT/'hardware/collar-tracker.kicad_pcb'
E=ROOT/'evidence/jlc-dfm-20261024'
b=k.LoadBoard(str(BASE)); changes=[]
def xy(v):return [v.x/1e6,v.y/1e6]
def polygons(poly):
    return [[xy(poly.COutline(n).CPoint(i)) for i in range(poly.COutline(n).PointCount())] for n in range(poly.OutlineCount())]

# Moving the connector row retains the already verified via/track geometry.
# Its existing track endpoints remain inside the shifted solder pads.
f=next(f for f in b.GetFootprints() if f.GetReference()=='J4')
old=f.GetPosition();new=k.VECTOR2I_MM(104.5,120.7);f.SetPosition(new)
changes.append({'ref':'J4','old':xy(old),'new':xy(new),'reason':'Increase same-net battery-pad/via gap from 0.025 to 0.225 mm; retain 0.5 mm edge clearance.'})

silk_count=0
for f in b.GetFootprints():
    if f.GetReference() in ['J1','J2']:
        for p in f.Pads():p.SetLocalSolderMaskMargin(k.FromMM(.05))
        f.SetAllowSolderMaskBridges(True)
        changes.append({'ref':f.GetReference(),'mask_expansion_mm':.05,'intentional_shared_mask_aperture':True,'reason':'Join the three pad apertures to the existing central copper-free connector opening; remove 0.01 mm mask slivers. Native footprint copper keepout remains intact; this is an explicit per-connector shared-aperture intent, not a global DRC rule exclusion.'})
    if f.GetReference()=='U2':
        p=next(p for p in f.Pads() if p.GetNumber()=='11')
        ls=k.LSET();ls.AddLayer(k.F_Cu);p.SetLayerSet(ls)
        p.SetLocalSolderMaskMargin(0);p.SetLocalSolderPasteMargin(0)
        changes.append({'ref':'U2.11','reason':'Use the already explicit mask/paste graphics; replace invalid negative-margin suppression with copper-only pad layers.'})
    for g in f.GraphicalItems():
        if g.GetLayer() in [k.F_SilkS,k.B_SilkS]:
            g.SetLayer(k.F_Fab if g.GetLayer()==k.F_SilkS else k.B_Fab)
            silk_count+=1
changes.append({'component_silk_graphics_moved_to_fab':silk_count,'reason':'Dense component outlines overlap pads/holes. Assembly geometry and orientation marks remain in Fab.'})

silks=[]
for g in b.GetDrawings():
    if g.GetClass()=='PCB_TEXT' and g.GetLayer() in [k.F_SilkS,k.B_SilkS]:
        if g.GetText().startswith('COLLAR'):g.SetText('COLLAR 0.2.1')
        g.SetTextSize(k.VECTOR2I_MM(1,1));g.SetTextThickness(k.FromMM(.15))
        poly=k.SHAPE_POLY_SET();g.TransformTextToPolySet(poly,0,1000,k.ERROR_OUTSIDE)
        silks.append({'id':g.m_Uuid.AsString(),'text':g.GetText(),'pos':xy(g.GetPosition()),'layer':b.GetLayerName(g.GetLayer()),'poly':polygons(poly)})

b.GetTitleBlock().SetRevision('0.2.1-DFM')
k.ZONE_FILLER(b).Fill(b.Zones());assert k.SaveBoard(str(OUT),b)
(E/'silk-candidates.json').write_text(json.dumps(silks,indent=2)+'\n')
(E/'patch-stage1.json').write_text(json.dumps({'input_sha256':hashlib.sha256(BASE.read_bytes()).hexdigest(),'changes':changes,'output_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest()},indent=2)+'\n')
print(json.dumps(changes,indent=2))
