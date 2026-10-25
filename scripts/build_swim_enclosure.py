#!/usr/bin/env python3
"""Generate the prototype CAD parameters and bound checks from one source.

These checks cover declared envelopes and seal dimensions, not physical ingress,
RF, material compatibility, lid stiffness, load qualification or supplier approval.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--parameters',type=Path,default=ROOT/'mechanical/swim-r01/parameters.json')
parser.add_argument('--output',type=Path,default=ROOT/'mechanical/swim-r01')
args=parser.parse_args()
OUT=args.output.resolve()
assert OUT.is_relative_to(ROOT), 'Keep generated artifacts in this checkout'
OUT.mkdir(parents=True,exist_ok=True)
p = json.loads(args.parameters.read_text())
b, g, c, pcb = (p[k] for k in ['body', 'gland', 'contacts', 'pcb'])
trial = ROOT / pcb['trial']
source = trial / 'hardware/collar-tracker.kicad_pcb'
geometry = json.loads((trial / 'evidence/route-geometry.json').read_text())
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash == geometry['source_sha256'], 'Export current PCB geometry first'
assert geometry['board_bounds_mm'] == [98.0, 98.0, 138.0, 130.0]


def perimeter(w, h, r):
    return 2 * (w + h) - 8 * r + 2 * math.pi * r


def rounded_contains(x, y, w, h, r):
    return math.hypot(max(abs(x) - w / 2 + r, 0), max(abs(y) - h / 2 + r, 0)) <= r + 1e-9


def rounded_distance(x,y,w,h,r):
    qx,qy=abs(x)-w/2+r,abs(y)-h/2+r
    return math.hypot(max(qx,0),max(qy,0))+min(max(qx,qy),0)-r


checks = []
def check(name, ok, **values):
    checks.append(dict(name=name, pass_=bool(ok), **values))

native_thickness = re.search(r'\(general\s+\(thickness\s+([0-9.]+)\)', source.read_text())
assert native_thickness, 'Cannot read native PCB thickness'
bounds = geometry['board_bounds_mm']
native_size = [bounds[2]-bounds[0], bounds[3]-bounds[1], float(native_thickness[1])]
check('PCB reservation matches native outline and thickness',
      all(abs(a-z) < 1e-6 for a,z in zip(pcb['size'],native_size)), native_size_mm=native_size)
# Include nominal rectangular PCB corners, not just width/height inequalities.
for sx, sy in itertools.product([-1, 1], repeat=2):
    x, y = sx * pcb['size'][0] / 2, sy * pcb['size'][1] / 2
    check('PCB corner inside cavity', rounded_contains(x,y,*b['cavity'],b['cavity_radius']), corner=[x,y])
batt = p['battery_reservation']
board_bottom_parts = pcb['bottom_z'] - pcb['bottom_component_budget']
battery_top = batt['bottom_z'] + batt['size'][2]
check('Battery reservation below bottom components', board_bottom_parts-battery_top >= .39, gap_mm=board_bottom_parts-battery_top)
check('Battery reservation above floor', batt['bottom_z']-b['floor'] >= .19, gap_mm=batt['bottom_z']-b['floor'])
for sx, sy in itertools.product([-1, 1], repeat=2):
    check('Battery corner inside cavity', rounded_contains(sx*batt['size'][0]/2,sy*batt['size'][1]/2,*b['cavity'],b['cavity_radius']))
component_top = pcb['bottom_z'] + pcb['size'][2] + pcb['top_component_budget']
for a in p['antenna_reservations']:
    low, high = a['center'][2]-a['size'][2]/2, a['center'][2]+a['size'][2]/2
    check('Antenna reservation vertical clearance', low-component_top>=.5 and b['size'][2]-high>=.29,
          name_of_reservation=a['label'], component_gap_mm=low-component_top, lid_gap_mm=b['size'][2]-high)
    for sx, sy in itertools.product([-1,1],repeat=2):
        check('Antenna reservation inside cavity',rounded_contains(a['center'][0]+sx*a['size'][0]/2,a['center'][1]+sy*a['size'][1]/2,*b['cavity'],b['cavity_radius']))
# Main seal: conservative combinations of declared section, ID and gland tolerances.
P = perimeter(*g['centerline_size'],g['corner_radius'])
rows=[]
for di, cs, depth, width in itertools.product(
    [g['id']-g['id_tolerance'],g['id']+g['id_tolerance']],
    [g['cross_section']-g['cross_section_tolerance'],g['cross_section']+g['cross_section_tolerance']],
    [g['depth']-g['depth_tolerance']-g['flatness_budget'],g['depth']+g['depth_tolerance']+g['flatness_budget']],
    [g['width']-g['width_tolerance'],g['width']+g['width_tolerance']]):
    stretch=P/(math.pi*(di+cs))
    section=cs/math.sqrt(stretch)
    gland_area=depth*width-2*(1-math.pi/4)*g['bottom_radius']**2
    rows.append(dict(stretch=stretch-1,squeeze=1-depth/section,fill=math.pi*section**2/4/gland_area))
main_ranges={k:[min(t[k] for t in rows),max(t[k] for t in rows)] for k in rows[0]}
check('Main seal declared tolerance screen', main_ranges['stretch'][0]>0 and main_ranges['stretch'][1]<.06 and main_ranges['squeeze'][0]>=.15 and main_ranges['squeeze'][1]<=.30 and main_ranges['fill'][1]<=.85, **main_ranges)
# Outside water pressure presses the seal toward its inner wall.
inner_perimeter=P-math.pi*g['width']
check('Main seal nominal inner circumference stretched', inner_perimeter>math.pi*g['id'], inner_perimeter_mm=inner_perimeter, nominal_free_id_circumference_mm=math.pi*g['id'])
# Contact seal: all declared dimension corners; radial geometry, not face seal.
rows=[]
for di,cs,root,bore,width in itertools.product(
    [c['oring_id']-c['oring_id_tolerance'],c['oring_id']+c['oring_id_tolerance']],
    [c['oring_cs']-c['oring_cs_tolerance'],c['oring_cs']+c['oring_cs_tolerance']],
    [c['groove_root']-c['groove_root_tolerance'],c['groove_root']+c['groove_root_tolerance']],
    [c['bore']-c['bore_tolerance'],c['bore']+c['bore_tolerance']],
    [c['groove_width']-c['groove_width_tolerance'],c['groove_width']+c['groove_width_tolerance']]):
    stretch=root/di
    section=cs/math.sqrt(stretch)
    depth=(bore-root)/2
    # Exact torus volume / annular groove volume, excluding tiny specified edge radii.
    rubber_volume=(math.pi*cs*cs/4)*math.pi*(di+cs)
    gland_volume=math.pi/4*(bore*bore-root*root)*width
    rows.append(dict(stretch=stretch-1,squeeze=1-depth/section,fill=rubber_volume/gland_volume))
contact_ranges={k:[min(t[k] for t in rows),max(t[k] for t in rows)] for k in rows[0]}
check('Contact seal declared tolerance screen',contact_ranges['stretch'][0]>=0 and contact_ranges['stretch'][1]<=.06 and contact_ranges['squeeze'][0]>=.15 and contact_ranges['squeeze'][1]<=.30 and contact_ranges['fill'][1]<=.85,**contact_ranges)
corner_center=[g['centerline_size'][0]/2-g['corner_radius'],g['centerline_size'][1]/2-g['corner_radius']]
webs=[]
for x,y in p['fasteners']['centers']:
    web=math.dist([abs(x),abs(y)],corner_center)-(g['corner_radius']+g['width']/2)-p['fasteners']['hole']/2
    webs.append(web)
check('Fastener holes outside main seal',min(webs)>=.8,minimum_web_mm=min(webs))
web=[]
for angle in range(91):
    a=math.radians(angle)
    x=b['cavity'][0]/2-b['cavity_radius']+b['cavity_radius']*math.cos(a)
    y=b['cavity'][1]/2-b['cavity_radius']+b['cavity_radius']*math.sin(a)
    web.append(-rounded_distance(x,y,g['centerline_size'][0]-g['width'],g['centerline_size'][1]-g['width'],g['corner_radius']-g['width']/2))
check('Cavity-to-groove corner web',min(web)>=.8,minimum_sampled_web_mm=min(web))
outer_nut_web=min(-rounded_distance(x,y,*b['size'][:2],b['corner_radius'])-p['fasteners']['nut_across_flats']/math.sqrt(3) for x,y in p['fasteners']['centers'])
check('Captive nut pockets inside shell',outer_nut_web>=.8,minimum_conservative_web_mm=outer_nut_web)
check('Contact shaft spans side wall',abs(c['stem_length']-(b['size'][0]-b['cavity'][0])/2)<1e-6)
check('Contact threads clear battery reservation',b['cavity'][0]/2-c['thread_length']-batt['size'][0]/2>=.49,
      gap_mm=b['cavity'][0]/2-c['thread_length']-batt['size'][0]/2)
check('Contact retaining nut clears PCB edge',pcb['bottom_z']-c['center_z']-7/math.sqrt(3)>=.15,
      minimum_gap_mm=pcb['bottom_z']-c['center_z']-7/math.sqrt(3))
pressure=1000*9.80665*p['target']['depth_m']
area=b['cavity'][0]*b['cavity'][1]-(4-math.pi)*b['cavity_radius']**2
report=dict(source_sha256=source_hash,parameter_sha256=hashlib.sha256(args.parameters.read_bytes()).hexdigest(),
    checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),checks=checks,
    all_declared_geometry_checks_pass=all(x['pass_'] for x in checks),
    external_size_mm=[*b['size'][:2],b['size'][2]+b['lid_thickness']],
    docking_key_adds_to_positive_x_mm=1.3,
    overall_without_mount_mm=[b['size'][0]+1.3,b['size'][1],b['size'][2]+b['lid_thickness']],
    hydrostatic_design_pressure_kPa=pressure/1000,approx_inward_lid_force_N=pressure*area/1e6,
    scope='Analytical checks of declared CAD envelopes and seal tolerances. Does not prove component heights, selected pack/antennas, groove surface finish, seal compatibility, deformation, retention, physical fit, RF, swimming or IP68.')
(OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
# One generated include supplies CAD dimensions; no independent copy to drift.
variables={
 'body_w':b['size'][0],'body_d':b['size'][1],'body_h':b['size'][2],'body_r':b['corner_radius'],
 'cavity_w':b['cavity'][0],'cavity_d':b['cavity'][1],'cavity_r':b['cavity_radius'],'floor_t':b['floor'],'lid_t':b['lid_thickness'],
 'gland_w':g['centerline_size'][0],'gland_d':g['centerline_size'][1],'gland_r':g['corner_radius'],'gland_width':g['width'],'gland_depth':g['depth'],'gland_bottom_r':g['bottom_radius'],
 'gasket_cs':g['cross_section'],'gasket_id':g['id'],'gasket_perimeter':P,
 'screw_centers':p['fasteners']['centers'],'screw_hole':p['fasteners']['hole'],'head_d':p['fasteners']['head_recess_diameter'],'head_depth':p['fasteners']['head_recess_depth'],'nut_af':p['fasteners']['nut_across_flats'],'nut_depth':p['fasteners']['nut_pocket_depth'],
 'pcb_size':pcb['size'],'pcb_z':pcb['bottom_z'],'top_budget':pcb['top_component_budget'],'bottom_budget':pcb['bottom_component_budget'],
 'battery_size':batt['size'],'battery_z':batt['bottom_z'],
 'antenna_centers':[a['center'] for a in p['antenna_reservations']],'antenna_sizes':[a['size'] for a in p['antenna_reservations']],
 'contact_y':c['centers_y'],'contact_z':c['center_z'],'contact_head_d':c['head_diameter'],'contact_head_t':c['head_thickness'],'contact_bore':c['bore'],'contact_shaft':c['shaft'],'contact_root':c['groove_root'],'contact_groove_w':c['groove_width'],'contact_groove_center':c['groove_center_from_face'],'contact_length':c['stem_length'],'contact_thread_d':c['thread_major'],'contact_thread_length':c['thread_length'],'contact_oring_cs':c['oring_cs'],'contact_oring_id':c['oring_id'],
 'magnet_y':p['magnets']['centers_y'],'magnet_z':p['magnets']['center_z'],'magnet_d':p['magnets']['diameter'],'magnet_t':p['magnets']['thickness'],'magnet_pocket_d':p['magnets']['pocket_diameter'],'magnet_wall':p['magnets']['outer_wall']}
(OUT/'parameters.scad').write_text('// Generated by scripts/build_swim_enclosure.py; edit parameters.json.\n'+''.join(f'{key} = {json.dumps(value)};\n' for key,value in variables.items()))
print(json.dumps({k:report[k] for k in ['source_sha256','all_declared_geometry_checks_pass','external_size_mm','hydrostatic_design_pressure_kPa']},indent=2))
for item in checks:
 if not item['pass_']:print('FAILED',item)
raise SystemExit(not report['all_declared_geometry_checks_pass'])
