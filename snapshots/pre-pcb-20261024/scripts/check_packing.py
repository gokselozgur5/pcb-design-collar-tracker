#!/usr/bin/env python3
"""Check proposed envelopes, not real PCB routing or RF performance."""
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical'

def inside_round_rect(x,y,length,width,radius):
    # Signed distance to an axis-aligned rounded rectangle.
    qx=abs(x)-(length/2-radius)
    qy=abs(y)-(width/2-radius)
    return math.hypot(max(qx,0),max(qy,0))+min(max(qx,qy),0)-radius <= 1e-7

def envelope(size,center,z):
    return dict(size=size,center=center,z=z)

def fits(part,body,wall=1.2):
    size=part['size']; cx,cy=part['center']
    return (part['z'] >= wall-1e-7 and
            part['z']+size[2] <= body[2]-wall+1e-7 and
            all(inside_round_rect(cx+sx*size[0]/2,cy+sy*size[1]/2,
                                 body[0]-2*wall,body[1]-2*wall,4-wall)
                for sx,sy in itertools.product([-1,1],repeat=2)))

def overlap(a,b):
    aa=[a['center'][0]-a['size'][0]/2,a['center'][1]-a['size'][1]/2,a['z']]
    bb=[b['center'][0]-b['size'][0]/2,b['center'][1]-b['size'][1]/2,b['z']]
    return all(min(aa[i]+a['size'][i],bb[i]+b['size'][i])-max(aa[i],bb[i])>1e-7 for i in range(3))

def check_variant(name,body,cell):
    antenna_y=body[1]/2-1.2-1.2
    parts={
        'battery_example': envelope(cell,[0,-0.5],3),
        'pcb_envelope': envelope([30,22,0.8],[1,0],8.9),
        'nrf9151_body': envelope([12.1,11.1,1.2],[-6,0],9.7),
        'power_esim_passives_reservation': envelope([12,8,2.5],[8,-5],9.7),
        'sensor_circuit_reservation': envelope([6,4,1.2],[9,5],9.7),
        'lte_antenna_reservation': envelope([30,1,7],[0,antenna_y],3.3),
        'gnss_antenna_reservation': envelope([14,5,1],[6,antenna_y-2.1],11),
        'health_head_reservation': envelope([10,10,1.3],[0,0],1.4),
    }
    outside=[key for key,value in parts.items() if not fits(value,body)]
    overlaps=[(ka,kb) for (ka,a),(kb,b) in itertools.combinations(parts.items(),2) if overlap(a,b)]
    assert not outside, (name,'outside',outside)
    assert not overlaps, (name,'overlap',overlaps)
    # A larger 500mAh example must be rejected by the small case, not just
    # scaled visually to make an attractive but impossible packing image.
    if name=='compact_250':
        assert not fits(envelope([36,29,4.75],[0,-0.5],3),body)
    return dict(name=name,body_mm=body,total_height_with_contact_reservation_mm=body[2]+0.6,
                parts=parts,outside=outside,overlaps=overlaps)

variants=[check_variant('compact_250',[38,30,14],[32,20.5,5.3]),
          check_variant('reference_500',[44,36,14],[36,29,4.75])]
result=dict(status='PASS for the specified envelopes only',variants=variants,
    checks=['rounded inner wall clearance','floor/lid clearance','pairwise volume overlap',
            'oversized 500mAh example rejected from compact case'],
    unverified=['real placement of all BOM footprints and routing',
                'battery pack protection/NTC/lead exit and swelling specification',
                'LTE/GNSS antenna selection, ground plane, isolation, matching and body effects',
                'heart-rate method, contact head and real sensor dimensions',
                'sealing, fasteners, retention, charging contacts and collar attachment',
                'device weight, battery life and physical prototype fit'],
    sources={'battery_250_example':'https://eemb.store/products/lp502030',
             'battery_250_bare_cell':'https://www.eemb.com/product-130',
             'battery_500_example':'https://www.adafruit.com/product/1578',
             'nrf9151':'https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_054/physical_characteristics.html'})
(OUT/'packing-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({v['name']:dict(body_mm=v['body_mm'],overlaps=len(v['overlaps'])) for v in variants}))
