#!/usr/bin/env python3
"""Check r05l net topology, fault logic and conservative temperature corners.

This is a source-bound design calculation. Thermal coupling, startup waveforms,
full-temperature input leakage and actual assembly remain bench requirements.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TRIAL=ROOT/'experiments/power-r05l-charge-interlock'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def enabled(hot_ok, cold_ok, por=False):
    return bool(hot_ok and cold_ok and not por)


def validate_topology(nets):
    pins={pin:net for net,items in nets.items() for pin in items}
    expected={
        'U3.4':'/CHARGE_DISABLE', 'U3.6':'/BAT_NTC', 'J4.3':'/BAT_NTC',
        'U10.1':'/CHG_HOT_OK','U10.2':'/GND','U10.3':'/BAT_NTC',
        'U10.4':'/CHG_HOT_LIMIT','U10.5':'/CHG_HOT_REF','U10.6':'/VSYS',
        'U11.1':'/CHG_COLD_OK','U11.2':'/GND','U11.3':'/CHG_COLD_LIMIT',
        'U11.4':'/BAT_NTC','U11.5':'/CHG_COLD_REF','U11.6':'/VSYS',
        'U12.1':'/CHG_HOT_OK','U12.2':'/CHG_COLD_OK','U12.3':'/GND',
        'U12.4':'/CHARGE_DISABLE','U12.5':'/VSYS',
        'R24.1':'/CHG_HOT_REF','R24.2':'/CHG_HOT_LIMIT',
        'R25.1':'/CHG_HOT_LIMIT','R25.2':'/GND',
        'R26.1':'/CHG_COLD_REF','R26.2':'/CHG_COLD_LIMIT',
        'R27.1':'/CHG_COLD_LIMIT','R27.2':'/GND',
        'R28.1':'/VSYS','R28.2':'/CHARGE_DISABLE',
        'R29.1':'/CHG_HOT_OK','R29.2':'/GND',
        'R30.1':'/CHG_COLD_OK','R30.2':'/GND',
        'C31.1':'/VSYS','C31.2':'/GND','C32.1':'/VSYS','C32.2':'/GND',
        'C33.1':'/VSYS','C33.2':'/GND','C34.1':'/CHG_HOT_REF','C34.2':'/GND',
        'C35.1':'/CHG_COLD_REF','C35.2':'/GND','C36.1':'/BAT_NTC','C36.2':'/GND'}
    for pin,net in expected.items():
        if pins.get(pin)!=net:raise ValueError(f'Unexpected {pin}: {pins.get(pin)} != {net}')
    assert set(nets['/CHARGE_DISABLE'])=={'U3.4','U12.4','R28.2'}
    assert set(nets['/BAT_NTC'])=={'J4.3','U3.6','U10.3','U11.4','C36.1'}
    original=json.loads((ROOT/'experiments/power-r05k-selected-parts/evidence/native-netlist.json').read_text())['nets']
    for net,items in original.items():
        for pin in items:
            if pin!='U3.4' and pins[pin]!=net:raise ValueError('Unrelated original net changed: '+pin)
    return len(expected)


def threshold(top, bottom):
    # Initial resistance, 25 ppm/C over -40..85 C and an explicitly assumed
    # additional 0.5% drift screen. Full hysteresis is included conservatively.
    rt=.001+25e-6*65+.005
    refs=[1.223*(1-100e-6*65)-100e-6*3.85-.00002,
          1.260*(1+100e-6*65)+100e-6*3.85+.00002]
    values=[v*b/(a+b) for v,a,b in itertools.product(
        refs,[top*(1-rt),top*(1+rt)],[bottom*(1-rt),bottom*(1+rt)])]
    # 100 nA per input is an engineering leakage allowance, not the datasheet's
    # 25 C-only 10 pA specification. Add common-mode, PSRR and input noise bounds.
    error=.009+.008+.001*3.85+1/(10**(54/20))+.0005+100e-9*(top*bottom/(top+bottom))
    return dict(nominal_V=1.242*bottom/(top+bottom), range_V=[min(values)-error,max(values)+error],
                comparator_error_allowance_V=error)


def ntc_voltage(temp):
    # Nominal curve is interpolated in inverse-K/log-R between actual published
    # points. R25/B variations plus 1% curve allowance are sensitivity assumptions.
    points=[(0,27700),(10,18070),(20,12110),(25,10000),(30,8301),(40,5811),(50,4147),(60,3011)]
    a,b=next((a,b) for a,b in zip(points,points[1:]) if a[0]<=temp<=b[0])
    fraction=(1/(temp+273.15)-1/(a[0]+273.15))/(1/(b[0]+273.15)-1/(a[0]+273.15))
    r=math.exp(math.log(a[1])+fraction*math.log(b[1]/a[1]))
    delta=3435*.01*abs(1/(temp+273.15)-1/298.15)
    return dict(nominal_V=r*38e-6,
                range_V=[r*.99*.99*math.exp(-delta)*(36.5e-6-200e-9),
                         r*1.01*1.01*math.exp(delta)*(39.5e-6+200e-9)])


def calculate():
    hot,cold=threshold(196000,49900),threshold(27400,49900)
    # Cell at 45 C may have a sensor at 43 C; at 0 C it may read 2 C. This
    # two-degree thermal-coupling allocation must be demonstrated on the assembly.
    at43,at2,at25,at50=[ntc_voltage(t) for t in [43,2,25,50]]
    hot_margin=hot['range_V'][0]-at43['range_V'][1]
    cold_margin=at2['range_V'][0]-cold['range_V'][1]
    normal_margin=min(at25['range_V'][0]-hot['range_V'][1],cold['range_V'][0]-at25['range_V'][1])
    temperatures=[i/100 for i in range(1,6000)]
    nominal=[t for t in temperatures if hot['nominal_V']<ntc_voltage(t)['nominal_V']<cold['nominal_V']]
    possible=[t for t in temperatures if ntc_voltage(t)['range_V'][1]>=hot['range_V'][0]
              and ntc_voltage(t)['range_V'][0]<=cold['range_V'][1]]
    guaranteed=[t for t in temperatures if ntc_voltage(t)['range_V'][0]>hot['range_V'][1]
                and ntc_voltage(t)['range_V'][1]<cold['range_V'][0]]
    assert hot_margin>0 and cold_margin>0 and normal_margin>0
    assert at50['range_V'][1]<hot['range_V'][0]
    assert not enabled(False,True) and not enabled(True,False) and not enabled(True,True,por=True)
    return dict(result='CONDITIONAL_DESIGN_PASS',electrical_release=False,
        hot_threshold=hot,cold_threshold=cold,
        nominal_sensor_window_C=[min(nominal),max(nominal)],
        possible_enable_sensor_window_C=[min(possible),max(possible)],
        guaranteed_normal_sensor_window_C=[min(guaranteed),max(guaranteed)],
        cell_sensor_offset_assumption_C=2,
        cell_45C_cutoff_margin_V=hot_margin,cell_0C_cutoff_margin_V=cold_margin,
        room_temperature_margin_V=normal_margin,
        original_50C_regression=dict(ts=at50,charge_enabled=False),
        fault_truth_table=[dict(hot_ok=h,cold_ok=c,charge_enabled=enabled(h,c))
                           for h,c in itertools.product([False,True],repeat=2)],
        battery_only_branch_estimate_uA=2*3.6+10+1.242/245900*1e6+1.242/77300*1e6+3.6/100000*1e6,
        current_estimate_scope='Illustrative 3.6 V battery-only state, one comparator output high. Not a total-current maximum or a runtime claim. NAND partial-input delta-ICC, transients, CE loading and the rest of the board are excluded; measure actual levels and current.',
        assumptions=['NTC R/T interpolation, B variation and additional 1% curve uncertainty require full-curve verification.',
          'Cell-to-sensor error including lag must remain within 2 C at 100 mA charging.',
          'Comparator input leakage is screened at 100 nA each over temperature; only 25 C is guaranteed in the table.',
          'Comparator output swing away from its 5 V test condition and CE input loading require measurement.',
          'VSYS/TS/POR startup, slow ramp, battery absence, brownout and sensor insertion transient waveforms require bench qualification.',
          'No single-component-fault safety certification or physical battery/RF/IP68 qualification is asserted.'])


def compute():
    native=TRIAL/'evidence/native-netlist.json'
    inv=json.loads(native.read_text())
    assert inv['schematic_sha256']==sha(TRIAL/'hardware/collar-tracker.kicad_sch')
    count=validate_topology(inv['nets'])
    design=json.loads((TRIAL/'hardware/design.json').read_text())
    parts={p['ref']:p for p in design['parts']}
    expected={'R24':'RT0402BRD07196KL','R25':'RT0402BRD0749K9L',
              'R26':'RT0402BRD0727K4L','R27':'RT0402BRD0749K9L',
              'U10':'TLV3012BIDCKR','U11':'TLV3012BIDCKR','U12':'SN74LVC1G00DCKR'}
    for ref,mpn in expected.items():assert parts[ref]['mpn']==inv['mpns'][ref]==mpn
    result=calculate()
    result.update(checked_pin_assignments=count,schematic_sha256=inv['schematic_sha256'],
                  netlist_sha256=sha(native),checker_sha256=sha(Path(__file__)))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');a=p.parse_args()
    result=compute()
    if a.write:(TRIAL/'evidence/charge-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
