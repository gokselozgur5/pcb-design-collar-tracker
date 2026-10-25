#!/usr/bin/env python3
"""Seed charge-interlock PCB parts; preserve all unrelated r05k copper."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pcbnew as k
from build_charge_r05l import TARGET, SOURCE, BASE_PCB, sha
from seed_power_r05_pcb import export_placement, polys


def main():
    hw = TARGET/'hardware'
    pcb = hw/'collar-tracker.kicad_pcb'
    assert sha(pcb) == BASE_PCB, 'Seed may only be applied once'
    netlist = ET.parse(TARGET/'evidence/netlist.xml').getroot()
    nets = {n.attrib['name']:sorted(p.attrib['ref']+'.'+p.attrib['pin'] for p in n.findall('node'))
            for n in netlist.find('nets')}
    pin_nets = {p:n for n,pins in nets.items() for p in pins}
    design = json.loads((hw/'design.json').read_text())
    parts = {p['ref']:p for p in design['parts'] if not p['ref'].startswith('#')}
    assert len(parts) == 87
    native = dict(schematic_sha256=sha(hw/'collar-tracker.kicad_sch'),
                  exporter='KiCad CLI XML netlist',
                  parts={p['ref']:p['value'] for p in parts.values()},
                  mpns={p['ref']:p['mpn'] for p in parts.values()}, nets=nets)
    (TARGET/'evidence/native-netlist.json').write_text(json.dumps(native,indent=2)+'\n')
    board = k.LoadBoard(str(pcb))
    settings = json.loads(pcb.with_suffix('.kicad_pro').read_text())
    fps={f.GetReference():f for f in board.GetFootprints()}
    added=set(parts)-set(fps)
    ce=next(p for p in fps['U3'].Pads() if p.GetNumber()=='4')
    removed=[]
    for t in list(board.GetTracks()):
        if t.GetClass()=='PCB_TRACK' and t.GetNetname()=='/GND' and (
                ce.HitTest(t.GetStart()) or ce.HitTest(t.GetEnd())):
            removed.append(dict(uuid=t.m_Uuid.AsString(),start=[t.GetStart().x/1e6,t.GetStart().y/1e6],
                                end=[t.GetEnd().x/1e6,t.GetEnd().y/1e6]))
            board.Delete(t)
    assert len(removed)==1, 'Review the CE-ground branch before removing different copper'
    io=k.PCB_IO_KICAD_SEXPR()
    for i,ref in enumerate(sorted(added)):
        p=parts[ref];lib,name=p['footprint'].split(':')
        f=io.FootprintLoad(str(hw/(lib+'.pretty')),name)
        assert f is not None
        board.Add(f)
        f.SetReference(ref); f.SetValue(p['value']); f.SetFPIDAsString(p['footprint'])
        f.SetPath(k.KIID_PATH('/'+design['root_uuid']+'/'+p['uuid']))
        f.Reference().SetVisible(False);f.Value().SetVisible(False)
        f.SetField('MPN',p['mpn']);f.GetField('MPN').SetVisible(False)
        f.SetField('Design status',p['status']);f.GetField('Design status').SetVisible(False)
        f.SetPosition(k.VECTOR2I(round((150+5*(i%4))*1e6),round((102+5*(i//4))*1e6)))
        fps[ref]=f
    for ref,f in fps.items():
        for p in f.Pads():
            if not p.GetNumber() or not p.IsOnCopperLayer():continue
            n=pin_nets[ref+'.'+p.GetNumber()]
            if ref not in added and (ref,p.GetNumber())!=('U3','4'):
                assert p.GetNetname()==n,(ref,p.GetNumber(),p.GetNetname(),n)
            net=board.FindNet(n)
            if net is None or net.GetNetCode()<0:
                net=k.NETINFO_ITEM(board,n);board.Add(net)
            p.SetNet(net)
    for text in board.GetDrawings():
        if text.GetClass()=='PCB_TEXT' and text.GetText()=='CT 0.5K':text.SetText('CT 0.5L')
    board.GetTitleBlock().SetRevision('0.5l-charge-WIP')
    board.BuildConnectivity()
    assert k.SaveBoard(str(pcb),board)
    after=json.loads(pcb.with_suffix('.kicad_pro').read_text())
    assert settings['board']['design_settings']==after['board']['design_settings']
    assert settings['net_settings']==after['net_settings']
    export_placement(board,added,output=pcb,trial=TARGET)
    # The old four-layer export groups all non-front tracks as B. Correct the
    # new placement model to include only real outer-layer copper obstacles.
    path=TARGET/'evidence/placement-input.json'; data=json.loads(path.read_text())
    data['tracks']=[dict(start=[t.GetStart().x/1e6,t.GetStart().y/1e6],
                         end=[t.GetEnd().x/1e6,t.GetEnd().y/1e6],width=t.GetWidth()/1e6,
                         side='F' if t.GetLayer()==k.F_Cu else 'B',net=t.GetNetname())
                    for t in board.GetTracks() if t.GetClass()=='PCB_TRACK' and t.GetLayer() in [k.F_Cu,k.B_Cu]]
    path.write_text(json.dumps(data,indent=2)+'\n')
    keepouts=[dict(layer=board.GetLayerName(z.GetLayer()),tracks=z.GetDoNotAllowTracks(),
                   vias=z.GetDoNotAllowVias(),poly=polys(z.Outline()))
              for z in [*board.Zones(),*(z for f in board.GetFootprints() for z in f.Zones())]
              if z.GetIsRuleArea()]
    (TARGET/'evidence/placement-extra.json').write_text(json.dumps(dict(keepouts=keepouts),indent=2)+'\n')
    receipt=dict(base_pcb_sha256=BASE_PCB,source_sha256=sha(pcb),added_refs=sorted(added),
                 removed_ce_ground_branch=removed,changed_original_pins=['U3.4'],
                 scope='Unplaced/unrouted candidate. No new DFM acceptance.')
    (TARGET/'evidence/pcb-seed.json').write_text(json.dumps(receipt,indent=2)+'\n')
    assert sha(SOURCE/'hardware/collar-tracker.kicad_pcb')==BASE_PCB
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
