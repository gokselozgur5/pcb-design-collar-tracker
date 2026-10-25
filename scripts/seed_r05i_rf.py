#!/usr/bin/env python3
"""Create a separate RF geometry trial from the immutable all-green r05h.

Run with KiCad Python. This is a one-shot source-bound edit, not RF acceptance.
The exact supplier stack and the two short module escapes need qualification.
"""
import hashlib
import json
from pathlib import Path
import shutil

import pcbnew as k
from trim_power_r05_tails import islands

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'experiments/power-r05h-six-layer'
TARGET = ROOT / 'experiments/power-r05i-rf-stack'
EXPECTED = 'aecb8e431819fa2aa23dfecc98ff1f6a064b5ae81afe7679a6e317f3571c3171'
RF = {'/LTE_RF', '/LTE_ANT', '/GPS_RF', '/GNSS_ANT',
      '/GNSS_FEM_IN', '/GNSS_FEM_OUT'}
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(SOURCE / 'hardware/collar-tracker.kicad_pcb') == EXPECTED
assert not TARGET.exists(), 'Never overwrite a previous experiment'
shutil.copytree(SOURCE / 'hardware', TARGET / 'hardware',
                ignore=shutil.ignore_patterns('*.local-routing.json', '*.detour-proposal.json', '*.kicad_prl'))
(TARGET / 'evidence').mkdir()
pcb = TARGET / 'hardware/collar-tracker.kicad_pcb'
b = k.LoadBoard(str(pcb))
nets = {p.GetNetname() for f in b.GetFootprints() for p in f.Pads()}
before = islands(b, nets)
v = lambda point: k.VECTOR2I(*(round(x * 1e6) for x in point))
xy = lambda p: [p.x / 1e6, p.y / 1e6]
changes = []

for t in list(b.GetTracks()):
    if t.GetNetname() not in RF:
        continue
    assert t.GetClass() == 'PCB_TRACK' and t.GetLayer() == k.F_Cu
    assert t.GetWidth() == 200000
    changes.append(dict(id=t.m_Uuid.AsString(), net=t.GetNetname(),
                        old_start=xy(t.GetStart()), old_end=xy(t.GetEnd()),
                        old_width_mm=.2))
    t.SetWidth(360000)

# Keep narrow, bounded escapes at the fixed 0.5 mm module pin pitch. Two steps
# spread the width transition. These discontinuities remain RF review items.
escapes = {
    '22d6dd2d-1fd0-41f6-a2ac-10b576bbee88':
        [(113.25003, 118.125), (113.25003, 118.475), (113.25003, 118.625)],
    '9406690b-d2da-4ce9-b30b-2d877d4e1765':
        [(116.625, 117.25), (116.975, 117.25), (117.125, 117.25)],
}
escape_rows = []
for t in list(b.GetTracks()):
    points = escapes.get(t.m_Uuid.AsString())
    if points is None:
        continue
    assert xy(t.GetStart()) == list(points[0])
    t.SetStart(v(points[-1]))
    for start, end, width in [(points[0], points[1], .2),
                              (points[1], points[2], .28)]:
        neck = k.PCB_TRACK(b)
        neck.SetLayer(k.F_Cu)
        neck.SetNetCode(t.GetNetCode())
        neck.SetStart(v(start)); neck.SetEnd(v(end))
        neck.SetWidth(round(width * 1e6)); neck.SetLocked(True)
        b.Add(neck)
        escape_rows.append(dict(id=neck.m_Uuid.AsString(), net=neck.GetNetname(),
                                start=start, end=end, width_mm=width))

# Move the GNSS elbow away from an existing SIM supply via's L2 antipad.
# Keep the connector, capacitor, all vias and all non-RF copper in place.
for t in b.GetTracks():
    if t.GetNetname() != '/GNSS_ANT':
        continue
    if xy(t.GetStart()) == [125.475, 113.1]:
        t.SetStart(v((125.9, 113.1)))
    if xy(t.GetEnd()) == [125.475, 113.1]:
        t.SetEnd(v((125.9, 113.1)))

assert islands(b, nets) == before, 'RF edit changed native terminal groups'
b.GetTitleBlock().SetRevision('0.5i-RF-stack-WIP')
for drawing in b.GetDrawings():
    if drawing.GetClass() == 'PCB_TEXT' and drawing.GetText() == 'CT 0.5H':
        drawing.SetText('CT 0.5I')
k.ZONE_FILLER(b).Fill(b.Zones())
assert k.SaveBoard(str(pcb), b)

# SWIG does not expose BOARD_STACKUP methods. Insert the documented native
# stack syntax, then let a separate native process parse/refill and validate it.
# Catalog copper+dielectric sum is 0.8104 mm. Adding the calculator's 0.01524 mm
# copper-surface mask each side gives 0.84088 mm for this CAD model. This differs
# from the catalog's rounded finished-thickness label (0.81 +/- 0.10 mm); do not
# change catalog dielectric thicknesses to hide that unresolved convention.
layers = [
    ('F.SilkS', 'Top Silk Screen', None, None, None),
    ('F.Paste', 'Top Solder Paste', None, None, None),
    ('F.Mask', 'Top Solder Mask', .01524, None, 3.8),
    ('F.Cu', 'copper', .035, None, None),
    ('dielectric 1', 'prepreg', .2104, 'NP-155F 7628 RC49%', 4.4),
    ('In1.Cu', 'copper', .0152, None, None),
    ('dielectric 2', 'core', .075, 'NP-155F H/H', 3.99),
    ('In2.Cu', 'copper', .0152, None, None),
    ('dielectric 3', 'prepreg', .1088, 'NP-155F 2116 RC54%', 4.16),
    ('In3.Cu', 'copper', .0152, None, None),
    ('dielectric 4', 'core', .075, 'NP-155F H/H', 3.99),
    ('In4.Cu', 'copper', .0152, None, None),
    ('dielectric 5', 'prepreg', .2104, 'NP-155F 7628 RC49%', 4.4),
    ('B.Cu', 'copper', .035, None, None),
    ('B.Mask', 'Bottom Solder Mask', .01524, None, 3.8),
    ('B.Paste', 'Bottom Solder Paste', None, None, None),
    ('B.SilkS', 'Bottom Silk Screen', None, None, None),
]
stack = ['\t\t(stackup']
for name, kind, thickness, material, er in layers:
    stack.append('\t\t\t(layer %s (type %s)' % (json.dumps(name), json.dumps(kind)))
    if thickness is not None:
        stack.append('\t\t\t\t(thickness %s)' % thickness)
    if material:
        stack.append('\t\t\t\t(material %s)' % json.dumps(material))
    if er:
        stack.append('\t\t\t\t(epsilon_r %s)' % er)
    stack.append('\t\t\t)')
stack += ['\t\t\t(dielectric_constraints yes)', '\t\t)']
text = pcb.read_text()
assert '(stackup' not in text
text = text.replace('\t(setup\n', '\t(setup\n' + '\n'.join(stack) + '\n', 1)
assert text.count('(thickness 0.8)') == 1
text = text.replace('(thickness 0.8)', '(thickness 0.84088)', 1)
pcb.write_text(text)

project = pcb.with_suffix('.kicad_pro')
settings = json.loads(project.read_text())
rf_class = next(c for c in settings['net_settings']['classes'] if c['name'] == 'RF')
assert rf_class['track_width'] == .2
rf_class['track_width'] = .36
# The FEM filter-to-amplifier matching network is not a 50-ohm port route.
for entry in settings['net_settings']['netclass_patterns']:
    if entry['pattern'] in ['/FILT_OUT', '/AMP_IN']:
        entry['netclass'] = 'Default'
project.write_text(json.dumps(settings, indent=2) + '\n')
assert sha(SOURCE / 'hardware/collar-tracker.kicad_pcb') == EXPECTED
(TARGET / 'evidence/rf-seed.json').write_text(json.dumps(dict(
    baseline_sha256=EXPECTED, source_sha256=sha(pcb),
    schematic_sha256=sha(pcb.with_suffix('.kicad_sch')),
    changed_original_tracks=changes, added_escapes=escape_rows,
    native_terminal_groups_preserved=len(before),
    supplier_stack_candidate='JLC06081H-7628', target_port_impedance_ohms=50,
    prototype_track_width_mm=.36, calculator_width_mm=.3586,
    catalog_copper_and_dielectric_mm=.8104, cad_with_mask_mm=.84088,
    catalog_finished_mm=.81, catalog_finished_tolerance_mm=.10,
    scope='RF geometry trial only. Supplier parameter discrepancies, escapes, pad capacitance, matching stubs and physical RF remain unqualified.'
), indent=2) + '\n')
print('Created r05i RF trial; r05h unchanged. Fresh native checks required.')
