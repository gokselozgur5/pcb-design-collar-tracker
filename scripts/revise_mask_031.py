#!/usr/bin/env python3
"""Prepare (Shapely) then apply (KiCad) a bounded 0.3.1 mask/land revision.

Does not overwrite 0.3 or imply production/supplier approval. Sources and
the remaining fixed-pitch exceptions are recorded in the revision report.
"""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT/'experiments/35x28-in2/hardware/collar-tracker.kicad_pcb'
TRIAL = ROOT/'experiments/35x28-mask-r031'
PCB = TRIAL/'hardware/collar-tracker.kicad_pcb'
E = TRIAL/'evidence'
BASE_HASH = 'e43296f852e2b1f9a789794bd66c97c7418bf79f2dd2b295e2a6412c608d19d2'
assert hashlib.sha256(OLD.read_bytes()).hexdigest() == BASE_HASH

if sys.argv[1] == 'plan':
    from shapely.ops import unary_union
    from shapely.affinity import affine_transform
    from audit_release_mask import read_gerber
    shapes, _ = read_gerber(ROOT/'release/collar-tracker-0.3-35x28-dfm/collar-tracker-F_Mask.gts')
    result = {}
    for ref in ['J1','J2']:
        g = unary_union([g for owner,g in shapes if owner == ref])
        assert g.geom_type == 'Polygon' and not g.interiors and g.is_valid
        native = affine_transform(g, [1,0,0,-1,100,128])
        result[ref] = {'points_mm':list(native.exterior.coords)[:-1], 'area_mm2':g.area}
    (E/'ufl-mask-plan.json').write_text(json.dumps(result,indent=2)+'\n')
    print({r:len(p['points_mm']) for r,p in result.items()})
elif sys.argv[1] == 'apply':
    import pcbnew as k
    b = k.LoadBoard(str(OLD))
    plan = json.loads((E/'ufl-mask-plan.json').read_text())
    changes = []
    for f in b.GetFootprints():
        ref = f.GetReference()
        if ref in ['J1','J2']:
            for p in f.Pads():
                ls = p.GetLayerSet(); ls.RemoveLayer(k.F_Mask); p.SetLayerSet(ls)
            for g in list(f.GraphicalItems()):
                if g.GetLayer() == k.F_Mask:
                    f.Remove(g); g.thisown = False
            poly = k.SHAPE_POLY_SET(); poly.NewOutline()
            for x,y in plan[ref]['points_mm']: poly.Append(k.FromMM(x),k.FromMM(y))
            shape = k.PCB_SHAPE(f); shape.SetShape(k.SHAPE_T_POLY)
            shape.SetLayer(k.F_Mask); shape.SetWidth(0); shape.SetFilled(True)
            shape.SetPolyShape(poly); f.Add(shape)
            changes.append({'ref':ref,'change':'One union mask polygon, same aperture geometry within polygon tolerance; copper/paste/keepout unchanged.'})
        if ref in ['J3','J4','J5','J6','J7']:
            for p in f.Pads():p.SetLocalSolderMaskMargin(k.FromMM(.05))
            changes.append({'ref':ref,'change':'Add 0.05 mm mask expansion to exposed contact copper; no component or copper geometry change.'})
        if ref in ['C1','C2','C5','C8']:
            copper = [p for p in f.Pads() if p.IsOnLayer(k.F_Cu) or p.IsOnLayer(k.B_Cu)]
            paste = [p for p in f.Pads() if p not in copper]
            assert len(copper)==2 and len(paste)==2
            old_positions = {p.GetNumber():p.GetPosition() for p in copper}
            center = f.GetPosition()
            for p in copper:
                old = p.GetPosition()
                dx,dy = old.x-center.x,old.y-center.y
                assert abs((dx*dx+dy*dy)**.5/1e6-.32)<1e-5
                p.SetPosition(k.VECTOR2I(round(center.x+dx*.275/.32),round(center.y+dy*.275/.32)))
                p.SetSize(k.VECTOR2I_MM(.30,.35))
                p.SetRoundRectRadiusRatio(.15)
                p.SetLocalSolderMaskMargin(k.FromMM(.025))
            for p in paste:
                pos = p.GetPosition()
                q = min(copper,key=lambda q:(old_positions[q.GetNumber()].x-pos.x)**2+(old_positions[q.GetNumber()].y-pos.y)**2)
                p.SetPosition(q.GetPosition());p.SetSize(q.GetSize())
                p.SetShape(k.PAD_SHAPE_ROUNDRECT);p.SetRoundRectRadiusRatio(.15)
                p.SetOrientation(q.GetOrientation())
                p.SetLocalSolderPasteMargin(0);p.SetLocalSolderPasteMarginRatio(0.0)
            changes.append({'ref':ref,'change':'GRM03 family reflow candidate: a=0.25 gap, b=0.30 land length, c=0.35 land width; pitch 0.55. Matched paste-only pads, +0.025 mask.'})
    # Move only the control-signal dogleg, preserving all joints/angles.
    oldpoint1 = (124.7017,117.0); oldpoint2 = (124.7017,119.2778)
    replacements = {oldpoint1:(124.76,117.0),oldpoint2:(124.76,119.2195)}
    track_changes = []
    for t in b.GetTracks():
        if t.GetClass()=='PCB_VIA' or t.GetNetname()!='/GNSS_LNA_EN' or t.GetLayer()!=k.F_Cu:continue
        before = [[t.GetStart().x/1e6,t.GetStart().y/1e6],[t.GetEnd().x/1e6,t.GetEnd().y/1e6]]
        for getter,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
            v=getter();pt=(round(v.x/1e6,4),round(v.y/1e6,4))
            if pt in replacements:setter(k.VECTOR2I_MM(*replacements[pt]))
        after = [[t.GetStart().x/1e6,t.GetStart().y/1e6],[t.GetEnd().x/1e6,t.GetEnd().y/1e6]]
        if before!=after:track_changes.append({'id':t.m_Uuid.AsString(),'before':before,'after':after})
    assert len(track_changes)==3
    changes.append({'net':'/GNSS_LNA_EN','tracks':track_changes})
    for z in b.Zones():
        if not z.GetIsRuleArea(): z.SetLocalClearance(k.FromMM(.25))
    changes.append({'zone_clearance_mm':.25,'reason':'Leave >=0.20 mm nominal mask-to-foreign-pour margin for +0.05 mm apertures. Refill/connectivity must pass.'})
    for g in b.GetDrawings():
        if g.GetClass()=='PCB_TEXT' and g.GetText().startswith('COLLAR'):
            g.SetText('COLLAR 0.3.1 TEST')
    b.GetTitleBlock().SetRevision('0.3.1-DFM')
    k.ZONE_FILLER(b).Fill(b.Zones())
    assert k.SaveBoard(str(PCB),b)
    (E/'changes.json').write_text(json.dumps({'base_sha256':BASE_HASH,'initial_output_sha256':hashlib.sha256(PCB.read_bytes()).hexdigest(),'changes':changes},indent=2)+'\n')
    print(json.dumps(changes,indent=2))
else:raise ValueError(sys.argv[1])
