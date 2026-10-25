#!/usr/bin/env python3
"""Conditional linear-expansion bounds for the collar's mechanical interfaces.

The coefficients are engineering acceptance requirements, not guaranteed values
from the material sheets. Independent part temperatures include thermal gradients.
No stress, moisture, creep, seal compression or physical acceptance is inferred.
"""
import itertools
import math


def scales(spec, material):
    limits = spec['materials'][material]['cte_ppm_per_K']
    temperatures = spec['temperature_C']
    assert len(limits) == len(temperatures) == 2
    assert 0 <= limits[0] <= limits[1] and temperatures[0] < temperatures[1]
    rows = [dict(scale=1 + alpha * 1e-6 * (temperature-spec['reference_C']),
                 temperature_C=temperature, cte_ppm_per_K=alpha)
            for temperature, alpha in itertools.product(temperatures, limits)]
    assert min(row['scale'] for row in rows) > 0
    return min(rows, key=lambda row: row['scale']), max(rows, key=lambda row: row['scale'])


def evaluate(p, r, spec, frame_material='pc'):
    states = {name: scales(spec, material) for name, material in
              [('body','pc'),('carrier','pc'),('lid','pc'),('frame',frame_material),
               ('board_xy','board_xy'),('board_z','board_z')]}
    d = r['dimension_requirements']
    tol = d['frame_and_carrier_overall_tolerance_mm']
    pcb_tol = d['pcb_outline_overall_tolerance_mm']
    rows = []

    def linear(name, terms, minimum=0, extra_tolerance=0):
        # Each part contributes one signed length. Combining body height/floor
        # first preserves their shared temperature instead of inventing two bodies.
        low = high = 0.
        witness = {}
        for part, length in terms.items():
            lo, hi = states[part]
            low += length * (lo if length >= 0 else hi)['scale']
            high += length * (hi if length >= 0 else lo)['scale']
            witness[part] = lo if length >= 0 else hi
        scale_max = max(s[1]['scale'] for s in states.values())
        low -= extra_tolerance * scale_max
        high += extra_tolerance * scale_max
        row = dict(name=name, minimum_mm=low, maximum_mm=high,
                   required_minimum_mm=minimum, pass_=low >= minimum-1e-9,
                   minimum_witness=witness)
        rows.append(row)
        return row

    rails, ribs = r['guide_rails_xy_mm'], r['locator_ribs_xy_mm']
    apertures = [rails[1][0]-rails[0][2], rails[3][1]-rails[2][3]]
    carrier_size = [rails[1][2]-rails[0][0], rails[3][3]-rails[2][1]]
    locator_size = [ribs[1][0]-ribs[0][2], ribs[3][1]-ribs[2][3]]
    pcb_shift, carrier_shift = [], []
    for axis, label in enumerate(['X','Y']):
        board = p['pcb']['size'][axis]
        linear('Guide/PCB '+label,
               {'carrier':apertures[axis]-tol,'board_xy':-(board+pcb_tol)}, .05)
        linear('Locator/carrier '+label,
               {'body':locator_size[axis]-d['body_locator_aperture_overall_tolerance_mm'],
                'carrier':-(carrier_size[axis]+tol)}, .05)
        linear('Cavity/frame '+label,
               {'body':p['body']['cavity'][axis]-d['body_cavity_overall_tolerance_mm'],
                'frame':-(r['frame']['outer_mm'][axis]+tol)}, .05)
        pcb_shift.append(((apertures[axis]+tol)*states['carrier'][1]['scale']
                          -(board-pcb_tol)*states['board_xy'][0]['scale'])/2+spec['corner_rotation_allowance_mm'])
        carrier_shift.append(((locator_size[axis]+d['body_locator_aperture_overall_tolerance_mm'])
                              *states['body'][1]['scale']
                              -(carrier_size[axis]-tol)*states['carrier'][0]['scale'])/2)
    floor = p['body']['floor']; body_h = p['body']['size'][2]
    axial = d['axial_feature_tolerance_mm']
    linear('Lid closure', {'body':body_h-floor,
                          'lid':-(body_h-r['lid_post_bottom_z_mm']),
                          'carrier':-(r['guide_top_z_mm']-floor),
                          'frame':-r['frame']['height_mm']}, 0, 3*axial)
    max_scale = max(s[1]['scale'] for s in states.values())
    pcb_top_min = (floor*states['body'][0]['scale']
                   +(p['pcb']['bottom_z']-floor)*states['carrier'][0]['scale']
                   -axial*max_scale+.71*states['board_z'][0]['scale'])
    pcb_top_max = (body_h*states['body'][1]['scale']
                   -(body_h-r['lid_post_bottom_z_mm'])*states['lid'][0]['scale']
                   -r['frame']['height_mm']*states['frame'][0]['scale']+2*axial*max_scale)
    frame_min = (floor*states['body'][0]['scale']
                  +(r['guide_top_z_mm']-floor)*states['carrier'][0]['scale']-axial*max_scale)
    key_gap = None
    key_points = []
    for key in r.get('radial_keys', []):
        b, slot = key['xy_mm'], key['slot_xy_mm']
        radial_axis = 0 if key['axis']=='x' else 1
        tangent_axis = 1-radial_axis
        key_length = b[tangent_axis+2]-b[tangent_axis]
        slot_length = slot[tangent_axis+2]-slot[tangent_axis]
        linear(key['name']+' key tangential fit',
               {'carrier':slot_length-tol,'frame':-(key_length+tol)}, .05,2*d['key_position_tolerance_per_axis_mm'])
        position = d['key_position_tolerance_per_axis_mm']
        g = (((slot_length+tol)*states['carrier'][1]['scale']
              -(key_length-tol)*states['frame'][0]['scale'])/2+2*position*max_scale)
        radius = abs((b[radial_axis]+b[radial_axis+2])/2)
        key_points.append(dict(name=key['name'],tangential_motion_mm=g,
                               radius_min_mm=radius*states['frame'][0]['scale']))
        # Check both ends; preserve signed coordinates on west/south keys.
        linear(key['name']+' key radial low',
               {'frame':b[radial_axis]-tol/2,
                'carrier':-(slot[radial_axis]+tol/2)}, .05,2*position)
        linear(key['name']+' key radial high',
               {'carrier':slot[radial_axis+2]-tol/2,
                'frame':-(b[radial_axis+2]+tol/2)}, .05,2*position)
    if key_points:
        assert len(key_points)==4 and {k['name'] for k in key_points}=={'west','east','north','south'}, 'Four opposed keys are required'
        g = max(k['tangential_motion_mm'] for k in key_points)
        radius_min = min(k['radius_min_mm'] for k in key_points)
        # Opposed radial slots give |dx|+ry*|sin(yaw)|<=gx and the analogous
        # Y constraint. The outer contour is slightly outside the key centers.
        ratio = max(max(r['frame']['outer_mm'])/2/max(k['radius_min_mm'] for k in key_points),
                    min(r['frame']['outer_mm'])/2/radius_min)
        angle = math.asin(min(1,g/radius_min))
        key_gap = g*ratio+max(r['frame']['outer_mm'])/2*(1-math.cos(angle))
        for key in r['radial_keys']:
            axis = 0 if key['axis']=='x' else 1
            inner = min(abs(key['xy_mm'][axis]),abs(key['xy_mm'][axis+2]))
            linear(key['name']+' key remains engaged',
                   {'carrier':carrier_size[axis]/2-tol/2,'frame':-(inner+tol/2)},
                   .1,r['motion_screen']['retainer_to_carrier_pointwise_mm'])
            linear(key['name']+' key/PCB centered clearance',
                   {'frame':inner-tol/2,'board_xy':-(p['pcb']['size'][axis]/2+pcb_tol/2)},.05)
        linear('Key bottom/slot floor',
               {'body':0,'carrier':r['guide_top_z_mm']-r['key_slot_bottom_z_mm'],
                'frame':-(r['frame']['bottom_z_mm']-r['key_bottom_z_mm'])}, .05,2*axial)
        linear('Keys remain vertically engaged',
               {'body':floor-body_h,'carrier':r['guide_top_z_mm']-floor,
                'lid':body_h-r['lid_post_bottom_z_mm'],
                'frame':r['frame']['height_mm']+r['frame']['bottom_z_mm']-r['key_bottom_z_mm']},
               .2,3*axial)
    return dict(result='CONDITIONAL_INTERFACE_BOUNDS_PASS' if all(row['pass_'] for row in rows) else 'THERMAL_ASSEMBLY_HOLD',
                checks=rows, states=states, pcb_to_carrier_pointwise_mm=max(pcb_shift),
                carrier_to_body_xy_mm=max(carrier_shift),
                pcb_to_body_pointwise_mm=max(a+b for a,b in zip(pcb_shift,carrier_shift)),
                pcb_top_z_mm=[pcb_top_min,pcb_top_max],retainer_bottom_z_mm=[frame_min,pcb_top_max],
                radial_key_pointwise_bound_mm=key_gap,radial_keys=key_points,
                physical_thermal_qualified=False,
                scope='Affine dimensional sensitivity under declared CTE bounds and independent part temperatures. No moisture, stress/creep, sealed assembly or physical qualification.')
