#!/usr/bin/env python3
"""Generate a review schematic; unresolved interfaces are explicit, not fabricated parts."""
from pathlib import Path
import csv
import json
import math
import re
import shutil
import uuid

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / 'hardware'
NS = uuid.UUID('73f99f2a-9ba0-4fb3-ae04-7c01e649092b')
ROOT_UUID = str(uuid.uuid5(NS, 'schematic'))

def uid(s):
    return str(uuid.uuid5(NS, s))

def grid(value, step=1.27):
    return round(round(value / step) * step, 4)

def q(s):
    return json.dumps(str(s), ensure_ascii=False)

def effects(size=1.0, extra=''):
    return f'(effects (font (size {size} {size})) {extra})'

def prop(k, v, x, y, hide=False):
    return f'(property {q(k)} {q(v)} (at {x} {y} 0) {effects(1.0, "(hide yes)" if hide else "")})'

symbols = {}
parts = []
graphics = []
counter = 0

def wire(x1, y1, x2, y2):
    global counter
    counter += 1
    return f'(wire (pts (xy {x1:.4f} {y1:.4f}) (xy {x2:.4f} {y2:.4f})) (stroke (width 0) (type default)) (uuid {uid("wire"+str(counter))}))'

def text(value, x, y, size=1.25):
    global counter
    counter += 1
    graphics.append(f'(text {q(value)} (at {x} {y} 0) {effects(size, "(justify left top)")} (uuid {uid("text"+str(counter))}))')

def label(name, x, y, left=True):
    global counter
    counter += 1
    angle = 0 if left else 180
    return f'(label {q(name)} (at {x:.4f} {y:.4f} {angle}) {effects(0.9, "(justify left bottom)")} (uuid {uid("label"+str(counter))}))'

def chip(name, left, right, width=24, grounds=(), reserved=(), source=''):
    """Pins are (number, name, electrical type). Grounds stack on a single node."""
    width = grid(width, 2.54)
    height = max(len(left), len(right), 2) * 2.54 + 5.08
    pins = []
    for side, sequence in [('left', left), ('right', right)]:
        for index, (number, pin_name, pin_type) in enumerate(sequence):
            y = height / 2 - 5.08 - index * 2.54
            x = -width / 2 - 5.08 if side == 'left' else width / 2 + 5.08
            pins.append(dict(number=str(number), name=pin_name, type=pin_type,
                             x=x, y=y, angle=0 if side == 'left' else 180,
                             side=side, hidden=False))
    for index, number in enumerate(grounds):
        # Only the first stacked ground pin is a power input. Hidden passive
        # duplicates share its physical connection without implicit global nets.
        pins.append(dict(number=str(number), name='GND', type='power_in' if index == 0 else 'passive', x=0,
                         y=-height/2-5.08, angle=90, side='bottom', hidden=index>0))
    for number in reserved:
        pins.append(dict(number=str(number), name='RESERVED_NC', type='no_connect',
                         x=0, y=0, angle=0, side='none', hidden=True))
    body = f'(rectangle (start {-width/2} {height/2}) (end {width/2} {-height/2}) (stroke (width 0.254) (type default)) (fill (type background)))'
    pin_text = []
    for p in pins:
        pin_text.append(f'(pin {p["type"]} line (at {p["x"]} {p["y"]} {p["angle"]}) (length 5.08) '
                        f'{"(hide yes)" if p["hidden"] else ""} '
                        f'(name {q(p["name"])} {effects(0.9)}) (number {q(p["number"])} {effects(0.8)}))')
    symbol = f'''(symbol {q('Collar:'+name)} (pin_names (offset 0.8)) (in_bom yes) (on_board yes)
      {prop('Reference','U',0,height/2+5.08)} {prop('Value',name,0,height/2+2.54)}
      {prop('Datasheet',source,0,0,True)}
      (symbol {q(name+'_0_1')} {body}) (symbol {q(name+'_1_1')} {''.join(pin_text)}))'''
    symbols[name] = dict(text=symbol, pins=pins, width=width, height=height)

def passive(name, kind):
    p = [{'number':'1','name':'1','type':'passive','x':-5.08,'y':0,'angle':0,'side':'left','hidden':False},
         {'number':'2','name':'2','type':'passive','x':5.08,'y':0,'angle':180,'side':'right','hidden':False}]
    line = lambda a,b,c,d: f'(polyline (pts (xy {a} {b}) (xy {c} {d})) (stroke (width 0.254) (type default)) (fill (type none)))'
    if kind == 'C':
        body = line(-0.635,-1.9,-0.635,1.9)+line(0.635,-1.9,0.635,1.9)+line(-2.54,0,-0.635,0)+line(0.635,0,2.54,0)
    elif kind == 'L':
        body = '(rectangle (start -2.54 0.8) (end 2.54 -0.8) (stroke (width 0.254) (type default)) (fill (type none)))'
    elif kind == 'D':
        body = '(polyline (pts (xy -1.27 -1.27) (xy -1.27 1.27) (xy 1.27 0) (xy -1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))'+line(1.27,-1.27,1.27,1.27)+line(-2.54,0,-1.27,0)+line(1.27,0,2.54,0)
    else:
        body = '(rectangle (start -2.54 1.016) (end 2.54 -1.016) (stroke (width 0.254) (type default)) (fill (type none)))'
    pins=''.join(f'(pin passive line (at {x["x"]} 0 {x["angle"]}) (length 2.54) (name "~" {effects(0.8)}) (number {q(x["number"])} {effects(0.8)}))' for x in p)
    symbols[name]=dict(pins=p,width=5.08,height=2.54,text=f'(symbol {q("Collar:"+name)} (pin_names (offset 0) (hide yes)) (in_bom yes) (on_board yes) {prop("Reference",kind,0,3.81)} {prop("Value",name,0,-3.81)} (symbol {q(name+"_0_1")} {body}) (symbol {q(name+"_1_1")} {pins}))')

def add(ref, name, value, x, y, nets, footprint='', mpn='', status='candidate', dnp=False, onboard=True):
    sym=symbols[name]
    item=dict(ref=ref,symbol=name,value=value,x=grid(x),y=grid(y),nets={str(k):v for k,v in nets.items()},
              footprint=footprint,mpn=mpn,status=status,dnp=dnp,onboard=onboard)
    parts.append(item)
    return item

passive('R','R');passive('C','C');passive('L','L');passive('D','D')

# Power flags describe external power and continuity through the ferrite; they
# do not assert that the unresolved undervoltage/sequencing design is complete.
symbols['PWR_FLAG'] = dict(width=2.54, height=2.54,
    pins=[dict(number='1', name='pwr', type='power_out', x=0, y=0,
               angle=90, side='bottom', hidden=False)],
    text='''(symbol "Collar:PWR_FLAG" (power) (pin_numbers (hide yes))
      (pin_names (offset 0) (hide yes)) (in_bom no) (on_board no)
      (symbol "PWR_FLAG_0_1" (polyline (pts (xy 0 0) (xy 0 1.27)
        (xy -1.27 1.27) (xy 0 2.54) (xy 1.27 1.27) (xy 0 1.27))
        (stroke (width 0.254) (type default)) (fill (type none))))
      (symbol "PWR_FLAG_1_1" (pin power_out line (at 0 0 90) (length 0)
        (name "pwr" (effects (font (size 1 1))))
        (number "1" (effects (font (size 1 1)))))))''')

# Pin identity is transcribed from Nordic's product documentation, not the community symbol.
gpio_numbers=[56,57,58,59,61,62,63,64,67,68,69,70,72,73,74,75,77,78,79,80,2,5,6,8,11,12,44,45,47,48,49,50]
gpio=[(n,f'P0.{i:02d}','bidirectional') for i,n in enumerate(gpio_numbers)]
core=[(14,'VDD','power_in'),(65,'VDD_GPIO','power_in'),(24,'DEC0','power_out'),
      (10,'ENABLE','input'),(9,'nRESET_2V2','bidirectional'),(3,'SWDCLK','input'),(4,'SWDIO','bidirectional'),
      (19,'SIM_1V8','power_out'),(16,'SIM_RST','output'),(18,'SIM_CLK','output'),(17,'SIM_IO','bidirectional'),
      (26,'SIM_DET_UNUSED','no_connect'),(35,'ANT','passive'),(42,'GPS','input'),(37,'AUX','passive'),
      (52,'COEX0','bidirectional'),(53,'COEX1','bidirectional'),(54,'COEX2','bidirectional'),
      (21,'MAGPIO0','bidirectional'),(22,'MAGPIO1','bidirectional'),(23,'MAGPIO2','bidirectional'),
      (27,'SDATA','bidirectional'),(28,'SCLK','output'),(29,'VIO','power_out')]
grounds=[1,7,13,15,20,25,30,34,36,38,39,40,41,43,46,51,55,60,66,71,76]+list(range(105,114))
reserved=[31,32,33]+list(range(81,105))
chip('nRF9151-LACA',gpio,core,56,grounds,reserved,'https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/pinout.html')
chip('BQ25185',[(10,'IN','power_in'),(4,'nCE','input'),(7,'ILIM_VSET','input'),(8,'ISET','input'),(6,'TS_MR','input')],
     [(1,'SYS','power_out'),(2,'BAT','passive'),(9,'STAT1','open_collector'),(3,'STAT2','open_collector')],24,[5,11],source='https://www.ti.com/lit/ds/symlink/bq25185.pdf')
chip('TPS7A0218-DBV',[(1,'IN','power_in'),(3,'EN','input')],[(5,'OUT_1V8','power_out'),(4,'NC','no_connect')],24,[2],source='https://www.ti.com/lit/ds/symlink/tps7a02.pdf')
chip('SKY65943-11',[(5,'RF_IN','input'),(3,'VCC','power_in'),(2,'VEN','input')],[(10,'RF_OUT','output'),(7,'FILT_OUT','output'),(8,'AMP_IN','input')],24,[1,4,6,9,11],source='https://www.skyworksinc.com/-/media/SkyWorks/Documents/Products/2801-2900/SKY65943-11_204404H.pdf')
chip('LIS2DW12',[(9,'VDD','power_in'),(10,'VDD_IO','power_in'),(1,'SCL','input'),(4,'SDA','bidirectional'),(2,'CS','input'),(3,'SA0','input')],[(12,'INT1','output'),(11,'INT2','output'),(5,'NC','no_connect')],24,[6,7,8],source='https://www.st.com/resource/en/application_note/an5038-lis2dw12-alwayson-3d-accelerometer-stmicroelectronics.pdf')
for name,n in [('Port2',2),('Port3',3),('Port5',5),('Port6',6),('Port12',12)]:
    chip(name,[(i,str(i),'passive') for i in range(1,n+1)],[],12)

FP_R='Resistor_SMD:R_0402_1005Metric'
FP_C='Capacitor_SMD:C_0402_1005Metric'
def r(ref,val,x,y,a,b,fp=FP_R,status='candidate',dnp=False):
    return add(ref,'R',val,x,y,{1:a,2:b},fp,status=status,dnp=dnp)
def c(ref,val,x,y,a,b='GND',fp=FP_C,mpn='',dnp=False):
    return add(ref,'C',val,x,y,{1:a,2:b},fp,mpn=mpn,dnp=dnp)

core_nets={14:'VDD_NRF',65:'VIO_1V8',24:'DEC0',10:'NRF_ENABLE',9:'NRF_RESET',3:'SWDCLK',4:'SWDIO',
           19:'SIM_1V8',16:'SIM_RST',18:'SIM_CLK',17:'SIM_IO',35:'LTE_RF',42:'GPS_RF',52:'COEX0'}
gpio_nets=['I2C_SDA','I2C_SCL','ACC_INT','HEALTH_INT','SPI_SCK','SPI_MOSI','SPI_MISO','HEALTH_CS',
           'HEALTH_RESET','HEALTH_EN','CHG_STAT','CHG_FAULT',None,'BAT_ADC']
for n,net in zip(gpio_numbers,gpio_nets):
    if net:core_nets[n]=net
core_nets.update({n:'GND' for n in grounds})
add('U1','nRF9151-LACA','nRF9151-LACA',135,100,core_nets,'Collar:LGA_9151_12.1x11.1mm',mpn='NRF9151-LACA-R',status='candidate; LTE-M carrier unresolved')

text('01 / MODEM, GNSS AND APPLICATION MCU',65,22,2)
text('Reserved pins 31-33 and 81-104: electrically unconnected.\nSIM_DET is not supported. No external pull-up on nRESET.',65,163)
text('REFERENCE DECOUPLING / NOT A COMPLETE RF LAYOUT',225,22,1.6)
add('FB1','L','22R @100MHz',250,39,{1:'VSYS',2:'VDD_NRF'},'Inductor_SMD:L_0603_1608Metric',mpn='BLM18SD220SN1',status='Nordic recommended filter; verify rail impedance')
c('C1','1uF /10V',245,54,'VSYS',fp='Capacitor_SMD:C_0201_0603Metric',mpn='GRM033R61A105ME15')
c('C2','1uF /10V',310,54,'VSYS',fp='Capacitor_SMD:C_0201_0603Metric',mpn='GRM033R61A105ME15')
c('C3','47uF /10V',245,69,'VDD_NRF',fp='Capacitor_SMD:C_0805_2012Metric',mpn='GRM21BR61A476ME15')
c('C4','10uF /10V',310,69,'VDD_NRF',fp='Capacitor_SMD:C_0603_1608Metric',mpn='GRM188R61A106MAAL')
c('C5','100nF',245,84,'VIO_1V8',fp='Capacitor_SMD:C_0201_0603Metric',mpn='GRM033R60J104ME19')
c('C6','4.7uF',310,84,'VIO_1V8',mpn='GRM155R60J475ME47')
c('C7','4.7uF',245,99,'DEC0',mpn='GRM155R60J475ME47')
c('C8','100nF',310,99,'NRF_RESET',fp='Capacitor_SMD:C_0201_0603Metric')
r('R1','10k',245,114,'VDD_NRF','NRF_ENABLE')
c('C9','100nF',310,114,'NRF_ENABLE')
r('R2','1k',245,129,'NRF_RESET','DEBUG_RESET')
c('C10','100nF',310,129,'SIM_1V8')

text('02 / LTE AND GNSS FRONT END',390,22,2)
r('R3','0R / tune',425,42,'LTE_RF','LTE_ANT')
c('C11','DNP / tune',490,42,'LTE_RF',dnp=True)
c('C12','DNP / tune',490,57,'LTE_ANT',dnp=True)
add('J1','Port2','LTE antenna / 50R',550,45,{1:'LTE_ANT',2:'GND'},'Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical',mpn='U.FL-R-SMT-1(10)',status='bench connector; final FPC antenna TBD')
add('U2','SKY65943-11','SKY65943-11',435,105,{5:'GNSS_FEM_IN',3:'VIO_1V8',2:'GNSS_LNA_EN',10:'GNSS_FEM_OUT',7:'FILT_OUT',8:'AMP_IN',1:'GND',4:'GND',6:'GND',9:'GND',11:'GND'},mpn='SKY65943-11',status='candidate; footprint pending manufacturer land pattern review')
add('L1','L','9.1nH',505,93,{1:'FILT_OUT',2:'AMP_IN'},'Inductor_SMD:L_0402_1005Metric',mpn='LQW15AN9N1J00D')
c('C13','39pF RF',505,112,'GNSS_FEM_OUT','GPS_RF')
c('C14','39pF RF',505,131,'GNSS_ANT','GNSS_FEM_IN')
add('J2','Port2','GNSS antenna / passive',550,145,{1:'GNSS_ANT',2:'GND'},'Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical',mpn='U.FL-R-SMT-1(10)',status='bench connector; final antenna/ESD TBD')
r('R4','1k',425,145,'COEX0','GNSS_LNA_EN')
r('R5','100k',425,160,'GNSS_LNA_EN','GND')
c('C15','100nF',490,160,'VIO_1V8')
c('C16','1uF',550,177,'VIO_1V8')
text('GPS and cellular do not receive/transmit concurrently.\nGNSS RF ESD, matching and body/enclosure tuning remain open.\nNo NTN/B255 requirement in this draft.',390,189)

text('03 / POWER — FIRST CIRCUIT DRAFT',25,209,2)
add('J3','Port2','5V charging input',43,235,{1:'VIN_5V',2:'GND'},status='connector and input protection unresolved',onboard=False)
add('U3','BQ25185','BQ25185DLHR',108,245,{10:'VIN_5V',4:'GND',7:'ILIM_VSET',8:'ISET',6:'BAT_NTC',1:'VSYS',2:'VBAT',9:'CHG_STAT',3:'CHG_FAULT',5:'GND',11:'GND'},mpn='BQ25185DLHR',status='candidate; footprint, input protection and cell limits unresolved')
add('J4','Port3','Protected cell + NTC',190,239,{1:'VBAT',2:'GND',3:'BAT_NTC'},status='cell/NTC/connector not selected',onboard=False)
c('C17','1uF /10V',40,275,'VIN_5V')
c('C18','10uF /10V',110,285,'VSYS',fp='Capacitor_SMD:C_0603_1608Metric')
c('C19','1uF /10V',190,269,'VBAT')
r('R6','18k /1%',40,293,'ILIM_VSET','GND',status='4.2V / 500mA input limit per BQ25185 table')
r('R7','3k /1%',40,310,'ISET','GND',status='100mA provisional; battery approval required')
r('R8','10k',190,287,'CHG_STAT','VIO_1V8')
r('R9','10k',190,304,'CHG_FAULT','VIO_1V8')
add('U4','TPS7A0218-DBV','TPS7A0218PDBVR',110,329,{1:'VSYS',3:'VSYS',5:'VIO_1V8',2:'GND'},'Package_TO_SOT_SMD:SOT-23-5',mpn='TPS7A0218PDBVR',status='candidate; VIO sequencing unresolved')
c('C20','1uF',40,339,'VSYS')
c('C21','1uF',190,331,'VIO_1V8')
r('R10','2M',40,365,'VBAT','BAT_ADC')
r('R11','1M',110,365,'BAT_ADC','GND')
c('C22','10nF',190,365,'BAT_ADC')
text('HOLD: add/verify hardware undervoltage cutoff (VDD >=3.0V),\nVDD_GPIO startup/shutdown sequencing, charging-input protection,\nand battery/NTC ratings before layout release.\nBQ25185 internal battery cutoff alone is insufficient for nRF9151.\nBAT_ADC: allow divider/filter settling; do not sample immediately.',25,382,1.15)

text('04 / MOTION AND HEART-RATE EXPANSION',255,209,2)
add('U5','LIS2DW12','LIS2DW12TR',290,247,{9:'VIO_1V8',10:'VIO_1V8',1:'I2C_SCL',4:'I2C_SDA',2:'VIO_1V8',3:'VIO_1V8',12:'ACC_INT',6:'GND',7:'GND',8:'GND'},mpn='LIS2DW12TR',status='candidate; footprint pending; SA0 high prevents pull-up leakage')
c('C23','100nF',265,282,'VIO_1V8')
c('C24','100nF',330,282,'VIO_1V8')
r('R12','4.7k',265,299,'I2C_SDA','VIO_1V8')
r('R13','4.7k',330,299,'I2C_SCL','VIO_1V8')
health={1:'GND',2:'VIO_1V8',3:'VSYS',4:'I2C_SDA',5:'I2C_SCL',6:'HEALTH_INT',7:'SPI_SCK',8:'SPI_MOSI',9:'SPI_MISO',10:'HEALTH_CS',11:'HEALTH_RESET',12:'HEALTH_EN'}
add('J5','Port12','DIGITAL health sensor interface',405,264,health,status='interface only; sensor, connector and mechanics unresolved',onboard=False)
r('R14','100k',265,319,'HEALTH_CS','VIO_1V8')
r('R15','100k',330,319,'HEALTH_EN','GND')
text('Digital interface only — not an electrode connection.\nPPG/ECG measurement head, power switching and protection\nmust be designed and validated separately.\nNo heart-rate sensor selected; no heart-rate accuracy claim.',255,341,1.2)

text('05 / eSIM AND DEBUG INTERFACES',465,209,2)
add('J6','Port5','eSIM interface / SKU TBD',515,245,{1:'SIM_1V8',2:'SIM_RST',3:'SIM_CLK',4:'SIM_IO',5:'GND'},status='logical interface; NOT a physical eSIM pinout',onboard=False)
text('J6 is NOT a purchasable eSIM or its footprint.\nSelect 1.8V eUICC + carrier profile, then map\nthese signals to its actual package pins.\nSIM_1V8 must remain separate from VIO_1V8.',465,273,1.15)
add('J7','Port6','SWD / debug',515,321,{1:'VIO_1V8',2:'SWDIO',3:'GND',4:'SWDCLK',5:'DEBUG_RESET',6:'VSYS'},status='pogo pad geometry TBD; debug must sense 1.8V VTref',onboard=False)
text('Reset has an internal 2.2V pull-up.\nDebug reset driver: open drain, compatible voltage.\nNo external reset pull-up.',465,349,1.15)
text('ENGINEERING DRAFT 0.1 — NOT FOR FABRICATION\nTurkey / shared lightweight body / heart-rate feasibility pending',255,382,1.7)
add('#FLG01','PWR_FLAG','PWR_FLAG',250,151,{1:'VDD_NRF'},onboard=False)
add('#FLG02','PWR_FLAG','PWR_FLAG',40,252,{1:'VIN_5V'},onboard=False)
add('#FLG03','PWR_FLAG','PWR_FLAG',190,351,{1:'GND'},onboard=False)

def instance(p):
    s=symbols[p['symbol']]
    body=[f'(symbol (lib_id {q("Collar:"+p["symbol"])}) (at {p["x"]} {p["y"]} 0) (unit 1) '
          f'(in_bom {"no" if p["ref"].startswith("#") else "yes"}) (on_board {"yes" if p["onboard"] else "no"}) (dnp {"yes" if p["dnp"] else "no"}) (uuid {uid(p["ref"])})',
          prop('Reference',p['ref'],p['x'],p['y']-s['height']/2-3.81,p['ref'].startswith('#')),
          prop('Value',p['value'],p['x'],p['y']-s['height']/2-1.27),
          prop('Footprint',p['footprint'],p['x'],p['y'],True),
          prop('MPN',p['mpn'],p['x'],p['y'],True),
          prop('Design status',p['status'],p['x'],p['y'],True),
          f'(instances (project "collar-tracker" (path "/{ROOT_UUID}" (reference {q(p["ref"])}) (unit 1))))',')']
    connections=[]; seen=set()
    for pin in s['pins']:
        net=p['nets'].get(pin['number'])
        x=p['x']+pin['x'];y=p['y']-pin['y']
        key=(x,y)
        if pin['side']=='none':
            continue
        if key in seen:
            continue
        seen.add(key)
        if net:
            if pin['side']=='bottom':
                x2,y2=x,y+5.08
            elif pin['side']=='left':
                x2,y2=x-7.62,y
            else:
                x2,y2=x+7.62,y
            connections.extend([wire(x,y,x2,y2),label(net,x2,y2,pin['side']!='right')])
        else:
            connections.append(f'(no_connect (at {x:.4f} {y:.4f}) (uuid {uid(p["ref"]+"-nc-"+pin["number"])}))')
    return '\n'.join(body+connections)

def main():
    HW.mkdir(exist_ok=True)
    # Copy the third-party land pattern, preserving its license and provenance.
    vendor=ROOT/'references/nordic-lib-kicad'
    lib=HW/'Collar.pretty';lib.mkdir(exist_ok=True)
    src=vendor/'footprints/nordic-lib-kicad-nrf9.pretty/LGA_9151_12.1x11.1mm.kicad_mod'
    fp=src.read_text()
    # Avoid an unresolved model path; 3D model is added only after its local copy exists.
    start=fp.find('\n\t(model ')
    if start>=0:
        fp=fp[:start]+'\n)\n'
    (lib/src.name).write_text(fp)
    shutil.copy2(vendor/'LICENSE',HW/'NORDIC_LIBRARY_LICENSE.txt')
    (HW/'NORDIC_LIBRARY_NOTICE.txt').write_text('Source: https://github.com/hlord2000/nordic-lib-kicad\nCommit: 05a4dae2427fde6be0e190d6c9169eae1b3dae51\nLicense: CERN-OHL-P-2.0\nChange: removed non-local 3D model reference. Footprint geometry remains unmodified and needs dimensional verification.\nSymbols in this project are separately generated from manufacturer pin descriptions.\n')
    content=f'''(kicad_sch (version 20250114) (generator "collar_tracker_draft")
      (uuid {ROOT_UUID}) (paper "A2")
      (title_block (title "Collar tracker — schematic review draft") (date "2026-10-24") (rev "0.1-DRAFT")
      (comment 1 "Not for fabrication — unresolved power, eSIM, RF and heart-rate interfaces"))
      (lib_symbols {''.join(s['text'] for s in symbols.values())})
      {''.join(instance(p) for p in parts)}
      {''.join(graphics)}
      (sheet_instances (path "/" (page "1"))))'''
    (HW/'collar-tracker.kicad_sch').write_text(content)
    (HW/'Collar.kicad_sym').write_text('(kicad_symbol_lib (version 20250114) (generator "collar_tracker_draft")\n'+
       '\n'.join(s['text'].replace('(symbol "Collar:', '(symbol "',1) for s in symbols.values())+'\n)\n')
    (HW/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Collar") (type "KiCad") (uri "${KIPRJMOD}/Collar.kicad_sym") (options "") (descr "Project draft symbols")))\n')
    standard_libraries = ['Resistor_SMD', 'Capacitor_SMD', 'Inductor_SMD',
                          'Connector_Coaxial', 'Package_TO_SOT_SMD']
    footprint_libraries = ['(lib (name "Collar") (type "KiCad") (uri "${KIPRJMOD}/Collar.pretty") (options "") (descr "Candidate Nordic footprint; see notice"))']
    footprint_libraries += [f'(lib (name "{name}") (type "KiCad") (uri "${{KICAD10_FOOTPRINT_DIR}}/{name}.pretty") (options "") (descr "KiCad standard library"))' for name in standard_libraries]
    (HW/'fp-lib-table').write_text('(fp_lib_table (version 7)\n'+'\n'.join(footprint_libraries)+')\n')
    (HW/'collar-tracker.kicad_pro').write_text(json.dumps({'meta':{'filename':'collar-tracker.kicad_pro','version':1}},indent=2)+'\n')
    with (HW/'bom.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=['ref','value','mpn','footprint','dnp','onboard','status'])
        writer.writeheader()
        for p in parts:
            if not p['ref'].startswith('#'):
                writer.writerow({k:p[k] for k in writer.fieldnames})
    data={'schema':'draft-v1','root_uuid':ROOT_UUID,'parts':parts,'symbols':{k:{a:b for a,b in v.items() if a!='text'} for k,v in symbols.items()}}
    (HW/'design.json').write_text(json.dumps(data,indent=2)+'\n')
    pinmap={p['number']:p['name'] for p in symbols['nRF9151-LACA']['pins']}
    assert len(pinmap)==113 and set(pinmap)=={str(x) for x in range(1,114)}, 'nRF pin coverage mismatch'
    for ref in [p['ref'] for p in parts]:
        assert sum(p['ref']==ref for p in parts)==1
    print(json.dumps({'schematic':str(HW/'collar-tracker.kicad_sch'),'parts':len(parts),'nrf_pins':len(pinmap),'status':'draft; electrical/manufacturing checks pending'}))

if __name__=='__main__':main()
