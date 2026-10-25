#!/usr/bin/env python3
"""Reproduce source-backed component calculations, with explicit physical limits.

The result is a conditional design screen, never powered or purchasing approval.
The original r05 report remains immutable.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'assembly/power-parts-r01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def resistor_interval(part, temperature, reference=25, drift=0):
    delta = max(abs(t-reference) for t in temperature)
    fraction = part['initial_tolerance_fraction'] + part['tcr_ppm_per_C'] * delta * 1e-6 + drift
    require(0 <= fraction < 1, 'Invalid resistance tolerance')
    return [part['ohm'] * (1-fraction), part['ohm'] * (1+fraction)]


def divider_current(rail, rt, rb, rh, rp=10000):
    """Nominal unloaded PG/SENSE KCL; excludes IC supply and input currents."""
    g = 1/rt + 1/rb + 1/rh
    a = 1/rp + 1/rh
    sense = (rail/rt + rail/(rp*rh*a)) / (g - 1/(rh*rh*a))
    pg = (rail/rp + sense/rh) / a
    return (rail-sense)/rt + (rail-pg)/rp


def model(config, drift=0):
    a = config['assumptions']
    resistors = {ref: resistor_interval(p, config['analysis_temperature_C'],
                    config['reference_temperature_C'], drift)
                 for ref, p in config['resistors'].items()}
    rail_max = a['maximum_valid_rail_V']
    rt, rb, rh = [resistors[ref] for ref in ('R17','R18','R19')]
    # Omit the MR pull-up's assistance. Bound feedback by Vrail/R19, even
    # though SENSE is positive. Include source leakage for the other sign.
    feedback_uA = rail_max/rh[0] * 1e6
    sink_uA = (a['u8_input_leak_abs_max_uA'] + a['u6_reset_high_leak_max_uA'] +
               a['enable_and_sense_load_max_uA'] + feedback_uA)
    source_uA = (a['u8_input_leak_abs_max_uA'] + a['u6_reset_high_leak_max_uA'] +
                 a['enable_source_leak_max_uA'])
    drop = [-source_uA*1e-6*resistors['R16'][1], sink_uA*1e-6*resistors['R16'][1]]
    falling, rising = [], []
    for top, bottom, feedback, vit, leakage in itertools.product(
            rt, rb, rh, [.405*.98,.405*1.02],
            [-a['u6_sense_leak_abs_max_nA']*1e-9, a['u6_sense_leak_abs_max_nA']*1e-9]):
        conductance = 1/top + 1/bottom + 1/feedback
        for d in drop:
            falling.append((vit*conductance + leakage + d/feedback)/(1/top+1/feedback))
        # No guaranteed minimum hysteresis is published. Do not use the
        # typical 1.5% as a minimum. RESET may be anywhere from 0 to VOLmax.
        for hysteresis, vol in itertools.product([0,.03], [0,a['u6_reset_vol_max_V']]):
            rising.append(top*(vit*(1+hysteresis)*conductance + leakage - vol/feedback))
    enable_min, enable_max = [n*1e-9 for n in config['capacitors']['C9']['effective_nF']]
    restart_min, restart_max = config['capacitors']['C25']['effective_nF']
    gpio_min, gpio_max = config['capacitors']['C26']['effective_nF']
    scale_min, scale_max = a['ct_delay_scale']
    reset_min = scale_min*(restart_min/175+.0005)
    reset_max = scale_max*(restart_max/175+.0005)
    gpio_delay_min = scale_min*(gpio_min/175+.0005)
    gpio_delay_max = scale_max*(gpio_max/175+.0005)
    series_max = resistors['R1'][1] + resistors['R16'][1]
    tau = series_max*enable_max
    # Conservative independent envelope: the PG drop already counts EN's
    # static load through R16; subtracting series_max*load counts it twice.
    # This widens the delay bound rather than understating the load.
    load_drop = series_max*a['enable_and_sense_load_max_uA']*1e-6
    gaps, latest, high_margins = [], [], []
    for rail in [min(falling),rail_max]:
        final = rail-drop[1]-load_drop
        high_margins.append(final-.89*rail)
        require(final > .89*rail, 'ENABLE cannot reach guaranteed HIGH')
        require(final > 2.79*1.015*1.025, 'U7 cannot release at worst SENSE threshold')
        enable_high = -tau*math.log(1-.89*rail/final)
        sense_early = -tau*math.log(1-2.79*.985/final)
        sense_late = -tau*math.log(1-2.79*1.015*1.025/final)
        gaps.append(gpio_delay_min-max(0,enable_high-sense_early))
        latest.append(sense_late+gpio_delay_max)
    # Both RC time differences are monotone in a fixed final-offset/rail
    # interval: their derivatives have a constant-sign numerator. Endpoints
    # bound this assumed stable-rail step response, not arbitrary supply ramps.
    low_final = a['u6_reset_vol_max_V'] + resistors['R1'][1]*a['enable_source_leak_max_uA']*1e-6
    low_threshold = .18*min(falling)
    require(low_final < low_threshold, 'ENABLE cannot reach guaranteed LOW')
    low_after = resistors['R1'][1]*enable_max*math.log((rail_max-low_final)/(low_threshold-low_final))
    high_departure = -resistors['R1'][0]*enable_min*math.log(.89)
    vio_cap = a['vio_cap_max_uF']*1e-6
    discharge = (resistors['R21'][1]+a['fet_hot_rds_bound_ohm'])*vio_cap*math.log(a['vio_initial_max_V']/.1)
    # Full capacitor-discharge current and MR pull-up current are included.
    reset_sink = (rail_max/resistors['R16'][0] + rail_max/resistors['R1'][0] +
                  rail_max/a['supervisor_mr_pullup_min_ohm'] + .405*1.02/rh[0] +
                  a['u8_input_leak_abs_max_uA']*1e-6)
    peak_power = a['vio_initial_max_V']**2/resistors['R21'][0]
    energy = .5*vio_cap*a['vio_initial_max_V']**2
    # The reviewed continuous-pulse graph (Vishay 20043, p5) exceeds 0.5 W
    # through 10 ms. Use that deliberately low graphical screen. The decay
    # tail is not treated as zero: average power uses the full stored energy.
    pulse_screen_W, pulse_window_s = .5,.010
    pulse_tail_power = peak_power*math.exp(-2*pulse_window_s/
                           ((resistors['R21'][1]+a['fet_hot_rds_bound_ohm'])*vio_cap))
    rated_at_85 = .2*(155-max(70,config['analysis_temperature_C'][1]))/(155-70)
    bounds = {
        'falling_threshold_V':[min(falling),max(falling)],
        'restart_threshold_V':[min(rising),max(rising)],
        'power_good_high_drop_V':drop,
        'enable_high_margin_min_V':min(high_margins),
        'recognized_fault_reset_delay_s':[reset_min,reset_max],
        'enable_low_hold_min_s':reset_min-low_after,
        'gpio_after_enable_high_min_s':min(gaps),
        'gpio_enable_latest_after_power_good_s':max(latest),
        'fully_on_enable_high_departure_min_s':high_departure,
        'vio_to_0p1V_estimate_max_s':discharge,
        'turnoff_latency_budget_s':high_departure-discharge,
        'rail_retention_for_strict_sequence_s':low_after,
        'reset_sink_max_mA':reset_sink*1000,
        'r21_peak_power_W':peak_power,
        'r21_full_discharge_energy_uJ':energy*1e6,
        'r21_average_power_bound_W':energy/reset_min,
        'r21_pulse_graph_screen_W':pulse_screen_W,
        'r21_screen_duration_s':pulse_window_s,
        'r21_tail_power_after_screen_W':pulse_tail_power,
        'r21_ambient_derated_continuous_W':rated_at_85,
    }
    checks = {
        'static_cutoff_above_3V':min(falling)>3,
        'restart_below_4p2V':max(rising)<4.2,
        'recognized_fault_enable_low_at_least_1s':reset_min-low_after>=1,
        'gpio_at_least_6ms_after_enable_high':min(gaps)>.006,
        'fully_on_discharge_positive_latency_budget':high_departure>discharge,
        'reset_sink_below_datasheet_test':reset_sink<a['reset_sink_test_mA']*1e-3,
        'firmware_wait_exceeds_modeled_gpio_enable':a['firmware_initial_vio_wait_s']>max(latest),
        'r21_peak_below_conservative_pulse_graph_screen':peak_power<pulse_screen_W,
        'r21_mean_and_tail_below_derated_rating':max(energy/reset_min,pulse_tail_power)<rated_at_85,
    }
    return dict(resistance_intervals_ohm=resistors, extra_drift_fraction=drift,
                bounds=bounds, conditional_checks=checks, all_pass=all(checks.values()))


def capacitance_screen(config, raw):
    results = {}
    for ref, cap in config['capacitors'].items():
        part = cap['mpn'][:-1]
        matches = [c for c in raw['curves'] if c['part']==part and
                   c['kind']=='c_temp_capacitance' and c['dc_V']==cap['curve_bias_V'] and
                   c['ac_Vrms']==.01 and c['capacitance_unit']=='nF']
        require(len(matches)==1, 'Missing or ambiguous capacitor curve: '+ref)
        minimum = min(y for x,y in matches[0]['data'])
        guarded = minimum*(1-cap['initial_tolerance_fraction'])*(1-config['assumptions']['cap_extra_loss_sensitivity_fraction'])
        results[ref] = dict(mpn=cap['mpn'], typical_sample_min_nF=minimum,
            with_tolerance_and_extra_loss_nF=guarded, model_min_nF=cap['effective_nF'][0],
            pass_=guarded>=cap['effective_nF'][0], guaranteed=False,
            scope='Typical 10 mVrms temperature samples at selected DC, then initial tolerance and additional 15% engineering loss. Not lot/age qualification.')
    return results


def report():
    paths = [DIRECTORY/n for n in ['selection.json','capacitor-curves.json','manufacturer-sources.json','murata-catalog-extract.json']]
    config, curves, sources, catalog = [json.loads(p.read_text()) for p in paths]
    require(len(config['resistors'])==9 and all(p['mpn'] for p in config['resistors'].values()), 'Nine resistors required')
    known_sources = {x['id'] for x in sources['sources']}
    require(all(p['source_id'] in known_sources for p in config['resistors'].values()), 'Missing resistor source')
    states = {x['part_number']:x['production_status_en-us'] for x in catalog['parts']}
    require(all(states[p['mpn'][:-1]]=='B' for p in config['capacitors'].values()), 'Selected timing capacitor is not recorded In Production')
    current = model(config)
    sensitivity = model(config,config['assumptions']['extra_resistor_drift_sensitivity_fraction'])
    caps = capacitance_screen(config,curves)
    draw = []
    values = [config['resistors'][r]['ohm'] for r in ['R17','R18','R19']]
    for rail in [3.6,4.2]:
        old = divider_current(rail,1e6,130e3,16.9e6)
        new = divider_current(rail,*values)
        draw.append(dict(rail_V=rail, previous_nominal_uA=old*1e6, selected_nominal_uA=new*1e6,
                         added_uA=(new-old)*1e6, added_mAh_per_day=(new-old)*24000))
    require(current['all_pass'] and sensitivity['all_pass'] and all(v['pass_'] for v in caps.values()), 'Conditional component screen failed')
    return dict(result='CONDITIONAL_COMPONENT_SCREEN_PASS', electrical_acceptance='HOLD',
        physical_test=False, purchase_release=False, operating_corner=current,
        additional_drift_sensitivity=sensitivity, capacitor_screen=caps,
        nominal_divider_current=draw,
        fault_pullup_current_note={
            'rail_V':3.3,'R16_plus_R20_nominal_max_uA':
                3.3*sum(1/config['resistors'][r]['ohm'] for r in ['R16','R20'])*1e6,
            'scope':'Ohmic 3.3 V / 10 kohm for each pull-up while PG and VIO_ENABLE are clamped near zero; excludes MR/divider/IC draw. UVLO stops the modem but is not a zero-current pack disconnect. Protected-cell cutoff and recharge behavior remain required.'},
        unresolved=config['unqualified'],
        sequencing_exception='Nordic permits VDD_GPIO to fall later when undefined GPIO states are acceptable; the strict-retention estimate is not an unconditional damage limit. See docs/power-sequence-followup.md.',
        scope='Fresh-component tolerance plus independent TCR extremes over an engineering temperature range. Stable-rail step/recognized-fault assumptions. No proof for arbitrary ramps, transients or physical hardware.',
        inputs={str(p.relative_to(ROOT)):sha(p) for p in paths+[Path(__file__).resolve()]})


def verify(write=False):
    result = report()
    path = DIRECTORY/'component-check.json'
    if write:
        path.write_text(json.dumps(result,indent=2)+'\n')
    else:
        require(json.loads(path.read_text())==result,'Saved component report is stale')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    print(json.dumps(verify(args.write),indent=2))
