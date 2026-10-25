#!/usr/bin/env python3
"""Reproduce the supplier-request stack and native r05l/r08 fit variant.

This checks a requested envelope, not a supplier-approved battery. Never turn
the result into purchasing, electrical, retention or ingress acceptance.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from shapely.geometry import box
import check_antenna_assembly as antenna
from audit_populated_fit import solid_distance
from check_charge_r05l import validate_topology

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/swim-r09-pack-request'
REQUEST = ROOT / 'assembly/pack-r03/request.json'
BASE = ROOT / 'mechanical/swim-r08-antennas'
SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def stack(request):
    m = request['mechanical']
    ntc = m['ntc']
    pack_top = m['body_bottom_z_mm'] + m['maximum_complete_pack_body_mm'][2]
    sensor_bottom = pack_top + ntc['bond_thickness_budget_mm']
    sensor_top = sensor_bottom + ntc['body_maximum_mm'][2]
    cover_top = sensor_top + ntc['cover_thickness_budget_mm']
    reservation_top = m['assembly_envelope_bottom_z_mm'] + m['assembly_envelope_mm'][2]
    return dict(pack_top_mm=pack_top, sensor_bottom_mm=sensor_bottom,
                sensor_top_mm=sensor_top, cover_top_mm=cover_top,
                remaining_envelope_mm=reservation_top-cover_top)


def validate_request(request):
    if request['status'] != 'SUPPLIER_REQUEST_NOT_AN_APPROVED_PART' or request['manufacturer_confirmed']:
        raise ValueError('This calculation cannot approve a supplier part')
    if request['lead_and_connector_drawing_approved']:
        raise ValueError('No lead drawing is qualified by this study')
    if stack(request)['remaining_envelope_mm'] < 0:
        raise ValueError('Sensor/bond stack exceeds the requested assembly envelope')
    expected = [('J4.1', 'VBAT'), ('J4.2', 'GND'), ('J4.3', 'BAT_NTC')]
    if [(r['pin'], r['signal']) for r in request['factory_interface']] != expected:
        raise ValueError('Factory battery pinout changed')


def build():
    request = json.loads(REQUEST.read_text())
    validate_request(request)
    paths = [BASE/n for n in ('parameters.json', 'components.native.json',
                              'fit-profile.json', 'routing-controls.json')]
    base_p, native, profile, controls = [json.loads(p.read_text()) for p in paths]
    base_hashes = {str(p.relative_to(ROOT)): SHA(p) for p in paths}
    if native['source_sha256'] != SHA(ROOT/native['source']):
        raise ValueError('Native PCB source changed')
    netlist_path = ROOT/base_p['pcb']['trial']/'evidence/native-netlist.json'
    inv = json.loads(netlist_path.read_text())
    validate_topology(inv['nets'])
    for row in request['factory_interface']:
        if row['pin'] not in inv['nets']['/'+row['signal']]:
            raise ValueError('Factory pinout does not match native schematic')

    p = copy.deepcopy(base_p)
    p['revision'] = OUT.name
    p['status'] = 'Supplier-request fit study; no approved battery, harness or production release'
    p['pcb']['bottom_z'] += .4
    p['body']['size'][2] += .4
    for a in p['antenna_reservations']:
        a['center'][2] += .4
    for points in controls.values():
        for point in points:
            point[2] += .4
    m = request['mechanical']
    p['battery_reservation'] = dict(size=m['assembly_envelope_mm'],
        bottom_z=m['assembly_envelope_bottom_z_mm'],
        nominal_cell=m['maximum_complete_pack_body_mm'],
        note='CT-BAT-001-A requested complete-pack/NTC envelope; not an approved EEMB substitution.')
    OUT.mkdir(exist_ok=True)
    for name, value in [('parameters.json', p), ('components.native.json', native),
                        ('fit-profile.json', profile), ('routing-controls.json', controls)]:
        (OUT/name).write_text(json.dumps(value, indent=2)+'\n')

    # The original checker remains byte-preserved; only its output destination
    # is selected for this process. Its own source hashes are retained.
    old = antenna.OUT
    try:
        antenna.OUT = OUT
        receipt = antenna.build()
    finally:
        antenna.OUT = old
    nominal = receipt['scenarios'][2]
    s = stack(request)
    checks = []
    pack_w, pack_d, _ = m['maximum_complete_pack_body_mm']
    envelope_w, envelope_d, _ = m['assembly_envelope_mm']
    checks.append(dict(name='Requested body inside assembly XY allowance',
        pass_=pack_w < envelope_w and pack_d < envelope_d))
    checks.append(dict(name='Requested sensor stack inside assembly',
        pass_=s['remaining_envelope_mm'] >= 0, margin_mm=s['remaining_envelope_mm']))
    # The complete reservation is checked against populated bodies in all four
    # thickness cases. Also inspect the carrier legs and physical contact shaft,
    # whose complete-pack interference cannot be inferred from component fit.
    batt = (box(-envelope_w/2, -envelope_d/2, envelope_w/2, envelope_d/2),
            m['assembly_envelope_bottom_z_mm'],
            m['assembly_envelope_bottom_z_mm']+m['assembly_envelope_mm'][2])
    for x, y in p['carrier_leg_centers_mm']:
        distance = solid_distance(batt, (box(x-.5, y-1, x+.5, y+1),
                                         p['body']['floor'], p['pcb']['bottom_z']-1.5))
        checks.append(dict(name='Pack to carrier leg', center_mm=[x,y],
                           gap_mm=distance, pass_=distance >= .2))
    for y in p['contacts']['centers_y']:
        c = p['contacts']; x = p['body']['cavity'][0]/2-c['thread_length']
        distance = solid_distance(batt, (box(x, y-c['thread_major']/2,
                                               p['body']['cavity'][0]/2, y+c['thread_major']/2),
                                         c['center_z']-c['thread_major']/2,
                                         c['center_z']+c['thread_major']/2))
        checks.append(dict(name='Pack to contact thread', y_mm=y,
                           gap_mm=distance, pass_=distance >= .2))
    if not all(c['pass_'] for c in checks):
        raise ValueError([c for c in checks if not c['pass_']])
    study = dict(result='REQUESTED_ENVELOPE_GEOMETRY_PASS',
        supplier_part_selected=False, electrical_release=False,
        physical_thermal_qualified=False, physical_ingress_qualified=False,
        request_sha256=SHA(REQUEST), checker_sha256=SHA(Path(__file__)),
        pcb_sha256=native['source_sha256'], base_inputs=base_hashes,
        native_netlist_sha256=SHA(netlist_path), stack=s, checks=checks,
        rigid_size_mm=[*p['body']['size'][:2], p['body']['size'][2]+p['body']['lid_thickness']],
        change_from_r08_mm=[0,0,.4],
        scope='Dimensional study of a supplier request. Existing EEMB PCM is not electrically approved. Leads, attachment strength, thermal lag, service swelling and retention remain open.')
    (OUT/'pack-fit.json').write_text(json.dumps(study, indent=2)+'\n')
    scad = '// Requested pack and NTC stack. No approved supplier part.\n'
    scad += 'module pack_request_stack() {\n'
    scad += f'  color([.65,.68,.72])translate([-{pack_w/2},-{pack_d/2},{m["body_bottom_z_mm"]}])cube({json.dumps(m["maximum_complete_pack_body_mm"])});\n'
    ntc = m['ntc']; w,d,h = ntc['body_maximum_mm']
    scad += f'  color([.95,.55,.1])translate([-{w/2},-{d/2},{s["sensor_bottom_mm"]}])cube([{w},{d},{h}]);\n'
    scad += f'  color([.85,.7,.2,.4])translate([-{w/2+1},-{d/2+1},{s["sensor_top_mm"]}])cube([{w+2},{d+2},{ntc["cover_thickness_budget_mm"]}]);\n'
    scad += '}\n'
    (OUT/'pack.scad').write_text(scad)
    cad = (BASE/'enclosure.scad').read_text()
    cad = cad.replace('// Swim enclosure r08-antennas.', '// Swim enclosure r09 pack request study.')
    cad = cad.replace('include <cables.scad>', 'include <cables.scad>\ninclude <pack.scad>')
    old = 'color([.85,.65,.17,.8])translate([-battery_size[0]/2,-battery_size[1]/2,battery_z])cube(battery_size);'
    if old not in cad:
        raise ValueError('Review changed r08 CAD before deriving pack study')
    cad = cad.replace(old, 'pack_request_stack();')
    (OUT/'enclosure.scad').write_text(cad)
    assert all(SHA(ROOT/name)==digest for name,digest in base_hashes.items())
    print(json.dumps(study, indent=2))
    return study


if __name__ == '__main__':
    build()
