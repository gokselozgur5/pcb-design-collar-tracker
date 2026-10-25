#!/usr/bin/env python3
"""Apply the bounded SKY65943-11 mask revision to an isolated copy of 0.3.1.

Run with scripts/kicad-python. Source: Skyworks 204404H, 2025-09-04,
Figure 7. Copper, routing and stencil are deliberately unchanged.
"""
from pathlib import Path
import hashlib
import json
import shutil
import pcbnew as k

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'experiments/35x28-mask-r031'
NEW = ROOT / 'experiments/35x28-mask-r032'
BASE_HASH = 'a7e596b58e7e32e75886a4b711d0680cc23c1b5abfe2d4a14a947072b90c495c'
source = OLD / 'hardware/collar-tracker.kicad_pcb'
assert hashlib.sha256(source.read_bytes()).hexdigest() == BASE_HASH
assert not NEW.exists(), 'Refuse to reset an existing revision'
shutil.copytree(OLD / 'hardware', NEW / 'hardware')
E = NEW / 'evidence'
E.mkdir()
b = k.LoadBoard(str(source))
f = next(f for f in b.GetFootprints() if f.GetReference() == 'U2')
assert f.GetValue() == 'SKY65943-11'

def mask_rectangle(x, y, width, height):
    poly = k.SHAPE_POLY_SET()
    poly.NewOutline()
    for px, py in [(x-width/2,y-height/2), (x+width/2,y-height/2),
                   (x+width/2,y+height/2), (x-width/2,y+height/2)]:
        # FromMM truncates floating-point near-integers in this KiCad build.
        poly.Append(round(px*1e6), round(py*1e6))
    shape = k.PCB_SHAPE(f)
    shape.SetShape(k.SHAPE_T_POLY)
    shape.SetLayer(k.F_Mask)
    shape.SetWidth(0)
    shape.SetFilled(True)
    shape.SetPolyShape(poly)
    f.Add(shape)

old_center = [g for g in f.GraphicalItems() if g.GetLayer() == k.F_Mask]
assert len(old_center) == 1
f.Remove(old_center[0])
old_center[0].thisown = False
# Full-size center opening in Figure 7: 1.55 x 2.90 mm. The specified
# 60-100% option includes this full opening; stencil windows are unchanged.
mask_rectangle(123, 116.5, 1.55, 2.90)
for p in f.Pads():
    if p.GetNumber() in ['1', '5', '6', '10']:
        assert p.GetSize() == k.VECTOR2I_MM(.425, .515)
        layers = p.GetLayerSet()
        layers.RemoveLayer(k.F_Mask)
        p.SetLayerSet(layers)
        # Figure 7 specifies X=0.525, Y=0.515 for these four apertures,
        # rather than adding 0.05 mm on all four edges of the copper pad.
        mask_rectangle(k.ToMM(p.GetPosition().x), k.ToMM(p.GetPosition().y), .525, .515)

for g in b.GetDrawings():
    if g.GetClass() == 'PCB_TEXT' and g.GetText() == 'COLLAR 0.3.1 TEST':
        g.SetText('COLLAR 0.3.2 TEST')
b.GetTitleBlock().SetRevision('0.3.2-DFM')
target = NEW / 'hardware/collar-tracker.kicad_pcb'
assert k.SaveBoard(str(target), b)
assert hashlib.sha256(source.read_bytes()).hexdigest() == BASE_HASH
(E/'source.json').write_text(json.dumps({'inner2_signal':True, 'base':str(source),
    'base_sha256':BASE_HASH, 'source':'0.3.1 unchanged copper/routing/paste; U2 mask only'},indent=2)+'\n')
(E/'changes.json').write_text(json.dumps({
    'base_sha256':BASE_HASH,
    'source_url':'https://www.skyworksinc.com/-/media/C1965FC4C165469FAEED1BA276874AF1.pdf',
    'source_document':'204404H, 2025-09-04, Figure 7, page 9; drawing visually inspected',
    'changes':[
        {'ref':'U2','pin':'11','layer':'F.Mask','before_mm':[1.55,2.487], 'after_mm':[1.55,2.90],
         'reason':'Select full center opening from manufacturer 60-100% range; expose entire unchanged copper land.'},
        {'ref':'U2','pins':['1','5','6','10'],'layer':'F.Mask','before_mm':[.525,.615], 'after_mm':[.525,.515],
         'reason':'Match the four large terminal mask apertures in Figure 7; copper and paste unchanged.'},
        {'layer':'B.Silkscreen','legend':'COLLAR 0.3.2 TEST'}],
    'supplier_dfm':'NOT RUN; no assertion that two supplier negative-mask occurrences are this center pad.',
    'open_findings':'0.3.1 report has 45 warnings. Fixed-pitch U2/U5 and three mask/trace occurrences still require disposition.'
},indent=2)+'\n')
print(target)
