#!/usr/bin/env python3
"""Place revision and NTC legends outside masked lands without shrinking text."""
import hashlib
import json
import math
from pathlib import Path
import shutil
import pcbnew as k

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'experiments/power-r05b-pin-exits'
PCB = TRIAL / 'hardware/collar-tracker.kicad_pcb'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def bbox(item):
    b = item.GetBoundingBox()
    return [b.GetLeft() / 1e6, b.GetTop() / 1e6, b.GetRight() / 1e6, b.GetBottom() / 1e6]


def gap(a, b):
    return math.hypot(max(a[0] - b[2], b[0] - a[2], 0),
                      max(a[1] - b[3], b[1] - a[3], 0))


def main():
    receipt = TRIAL / 'evidence/legend-placement.json'
    assert not receipt.exists()
    before = sha(PCB)
    assert json.loads(PCB.with_suffix('.local-routing.json').read_text())['source_sha256'] == before
    board = k.LoadBoard(str(PCB))
    texts = [t for t in board.GetDrawings() if t.GetClass() == 'PCB_TEXT']
    targets = {t.GetText(): t for t in texts if t.GetText() in {'NTC', 'CT 0.4'}}
    assert set(targets) == {'NTC', 'CT 0.4'}
    pads = [bbox(p) for f in board.GetFootprints() for p in f.Pads() if p.IsOnLayer(k.B_Mask)]
    pads += [bbox(g) for f in board.GetFootprints() for g in f.GraphicalItems() if g.GetLayer() == k.B_Mask]
    changed = []
    for old, new in [('NTC', 'NTC'), ('CT 0.4', 'CT 0.5B')]:
        text = targets[old]
        assert text.GetLayer() == k.B_SilkS
        origin = [text.GetPosition().x / 1e6, text.GetPosition().y / 1e6]
        text.SetText(new)
        choices = [(dx * dx + dy * dy + (20 if angle else 0), dx, dy, angle)
                   for dx in range(-24, 25) for dy in range(-24, 25) for angle in [0, 90]
                   if dx * dx + dy * dy <= 24 ** 2]
        others = [bbox(t) for t in texts if t != text and t.GetLayer() == k.B_SilkS]
        for _, dx, dy, angle in sorted(choices):
            pos = [origin[0] + dx * .25, origin[1] + dy * .25]
            text.SetPosition(k.VECTOR2I(*(round(x * 1e6) for x in pos)))
            text.SetTextAngle(k.EDA_ANGLE(angle, k.DEGREES_T))
            box = bbox(text)
            if box[0] < 98.4 or box[1] < 98.4 or box[2] > 137.6 or box[3] > 129.6:
                continue
            if any(gap(box, p) < .30 for p in pads) or any(gap(box, p) < .25 for p in others):
                continue
            changed.append({'before_text': old, 'after_text': new, 'before_position_mm': origin,
                            'position_mm': pos, 'angle_degrees': angle,
                            'minimum_copper_box_clearance_mm': min(gap(box, p) for p in pads)})
            break
        else:
            raise RuntimeError('No local label position: ' + old)
    shutil.copy2(PCB, TRIAL / 'build/before-legends.kicad_pcb')
    assert k.SaveBoard(str(PCB), board)
    receipt.write_text(json.dumps({'before_sha256': before, 'source_sha256': sha(PCB), 'changes': changed,
                                  'acceptance': 'Conservative label placement only; native DRC and actual JLC analysis remain required.'}, indent=2) + '\n')
    print(json.dumps(changed))


if __name__ == '__main__':
    main()
