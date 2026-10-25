#!/usr/bin/env python3
"""Replace single-layer via junctions with tracks and validate their copper.

Plan with geometry Python; apply with KiCad Python. By default replacements stay
inside existing copper. Optional extensions must meet the inherited clearance.
No attached track is narrowed; native terminal groups must remain identical.
"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def plan(args):
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import unary_union
    g=json.loads((args.trial/'evidence/route-geometry.json').read_text())
    assert g['source_sha256']==sha(args.trial/'hardware/collar-tracker.kicad_pcb')
    drc=json.loads(args.drc.read_text())
    ids={v['items'][0]['uuid'] for v in drc['violations'] if v['type']=='via_dangling'}
    vias={v['id']:v for v in g['vias']}
    assert ids<=vias.keys()
    tracks=[(t,LineString([t['start'],t['end']]),LineString([t['start'],t['end']]).buffer(t['width']/2,quad_segs=64)) for t in g['tracks']]
    pads=[(p,unary_union([Polygon(q) for q in p['poly']])) for p in g['pads']]
    accepted,rejected=[],[]
    protected={'/GND','/LTE_RF','/LTE_ANT','/GPS_RF','/GNSS_ANT','/GNSS_FEM_IN','/GNSS_FEM_OUT','/FILT_OUT','/AMP_IN','/SIM_1V8','/SIM_CLK','/SIM_IO','/SIM_RST'}
    for uid in sorted(ids):
        v=vias[uid];assert v['net'] not in protected
        center=Point(v['pos']);circle=center.buffer(v['diameter']/2,quad_segs=64)
        touching=[(t,line,s) for t,line,s in tracks if t['net']==v['net'] and s.distance(circle)<.00001]
        pp=[p for p,s in pads if p['net']==v['net'] and s.distance(circle)<.00001]
        layers={t['layer'] for t,_,_ in touching}
        if len(layers)!=1 or not touching or pp:
            rejected.append({'id':uid,'net':v['net'],'reason':'Not a simple single-layer track junction','layers':sorted(layers),'tracks':len(touching),'pads':[p['ref']+'.'+p['pin'] for p in pp]});continue
        layer=next(iter(layers));old=unary_union([circle]+[s for t,_,s in touching])
        paths=[];added=[]
        # A single-track leaf needs no junction: leave its native track intact.
        for t,line,s in touching if len(touching)>1 else []:
            q=line.interpolate(line.project(center));point=[q.x,q.y]
            if center.distance(q)<1e-7:continue
            assert t['width']>=.2
            paths.append({'start':v['pos'],'end':point,'width':t['width'],'layer':layer,'net':v['net']})
            added.append(LineString([v['pos'],point]).buffer(t['width']/2,quad_segs=64))
        outside=unary_union(added).difference(old).area
        clearance=None
        if outside>1e-7 and args.allow_clear_extension:
            foreign=[s for t,_,s in tracks if t['net']!=v['net'] and t['layer']==layer]
            foreign += [s for p,s in pads if p['net']!=v['net'] and layer in p['layers']]
            foreign += [Point(other['pos']).buffer(other['diameter']/2,quad_segs=64) for other in g['vias'] if other['net']!=v['net']]
            extra=json.loads((args.trial/'evidence/placement-extra.json').read_text())
            foreign += [Polygon(poly) for zone in extra['keepouts'] if zone['layer']==layer and zone['tracks'] for poly in zone['poly']]
            clearance=min(unary_union(added).distance(s) for s in foreign)
        if outside>1e-7 and (clearance is None or clearance<.20001):
            rejected.append({'id':uid,'net':v['net'],'reason':'Replacement would add copper outside the source','outside_mm2':outside});continue
        accepted.append({'via':v,'paths':paths,'outside_mm2':outside,'extension_clearance_mm':clearance,'touching_track_ids':[t['id'] for t,_,_ in touching]})
    assert not args.output.exists()
    args.output.write_text(json.dumps({'source_sha256':g['source_sha256'],'drc_sha256':sha(args.drc),
        'accepted':accepted,'rejected':rejected,'scope':'Geometric proposal only; native terminal-group and DRC checks remain required.'},indent=2)+'\n')
    print('Single-layer junction replacements:',len(accepted),'; retained:',len(rejected))


def apply(args):
    import pcbnew as k
    from trim_power_r05_tails import islands
    data=json.loads(args.output.read_text());pcb=args.trial/'hardware/collar-tracker.kicad_pcb'
    assert sha(pcb)==data['source_sha256']
    receipt=args.output.with_name(args.output.stem+'-applied.json');assert not receipt.exists()
    b=k.LoadBoard(str(pcb));nets={p.GetNetname() for f in b.GetFootprints() for p in f.Pads()};before=islands(b,nets)
    items={t.m_Uuid.AsString():t for t in b.GetTracks()};added=[]
    vector=lambda p:k.VECTOR2I(*(round(v*1e6) for v in p))
    for row in data['accepted']:
        v=items[row['via']['id']];assert v.GetClass()=='PCB_VIA' and v.GetNetname()==row['via']['net']
        for path in row['paths']:
            t=k.PCB_TRACK(b);t.SetStart(vector(path['start']));t.SetEnd(vector(path['end']))
            t.SetWidth(round(path['width']*1e6));t.SetLayer(b.GetLayerID(path['layer']));t.SetNet(v.GetNet());b.Add(t)
            added.append(t.m_Uuid.AsString())
        b.Delete(v)
    assert islands(b,nets)==before,'Replacement changed native terminal groups; not saved'
    k.ZONE_FILLER(b).Fill(b.Zones());assert k.SaveBoard(str(pcb),b)
    receipt.write_text(json.dumps({'before_sha256':data['source_sha256'],'source_sha256':sha(pcb),
        'plan_sha256':sha(args.output),'removed_vias':[r['via']['id'] for r in data['accepted']],
        'added_tracks':added,'native_terminal_groups_preserved':len(before),
        'scope':'Junctions replaced with native terminal groups preserved. Fresh DRC and return checks required.'},indent=2)+'\n')
    print('Replaced',len(data['accepted']),'unused via junctions')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trial',type=Path)
    p.add_argument('--drc',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--allow-clear-extension',action='store_true')
    p.add_argument('--apply',action='store_true');a=p.parse_args()
    assert a.trial.name in {'power-r05f-return-reset', 'power-r05l-charge-interlock'}
    if a.apply:apply(a)
    else:
        assert a.drc is not None
        plan(a)
