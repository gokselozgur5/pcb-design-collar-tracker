#!/usr/bin/env python3
"""Read actual RF tracks, pads and saved reference fills with one native load.

Contains probes bind the independent polygon interpretation to KiCad. No refill
or board save occurs. Run with KiCad Python; analysis uses geometry Python.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pcbnew as k

RF = {'/LTE_RF', '/LTE_ANT', '/GPS_RF', '/GNSS_ANT',
      '/GNSS_FEM_IN', '/GNSS_FEM_OUT', '/FILT_OUT', '/AMP_IN'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pcb', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    source = sha(args.pcb)
    board = k.LoadBoard(str(args.pcb))
    xy = lambda v: [v.x / 1e6, v.y / 1e6]

    def contour(chain):
        return [xy(chain.CPoint(i)) for i in range(chain.PointCount())]

    def polygons(poly):
        return [dict(outer=contour(poly.COutline(i)),
                     holes=[contour(poly.CHole(i, j)) for j in range(poly.HoleCount(i))])
                for i in range(poly.OutlineCount())]

    output = dict(source_sha256=source, exporter_sha256=sha(Path(__file__)),
                  board_thickness_mm=board.GetDesignSettings().GetBoardThickness()/1e6,
                  zones=[], pads=[], tracks=[], vias=[], contains_probes=[])
    planes = [z for z in board.Zones() if not z.GetIsRuleArea()
              and z.IsOnLayer(k.In1_Cu) and z.GetNetname() == '/GND']
    assert len(planes) == 1, 'This audit requires one In1.Cu GND zone'
    filled = planes[0].GetFilledPolysList(k.In1_Cu)
    output['zones'].append(dict(layer='In1.Cu', net='/GND', poly=polygons(filled)))
    probes = set()
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if pad.GetNetname() in RF:
                assert pad.IsOnLayer(k.F_Cu)
                output['pads'].append(dict(
                    id=pad.m_Uuid.AsString(), ref=footprint.GetReference(),
                    pin=pad.GetNumber(), net=pad.GetNetname(), pos=xy(pad.GetPosition()),
                    poly=polygons(pad.GetEffectivePolygon(k.F_Cu))))
                probes.add(tuple(pad.GetPosition()))
    for track in board.GetTracks():
        item = dict(id=track.m_Uuid.AsString(), net=track.GetNetname())
        if track.GetClass() == 'PCB_VIA':
            item.update(pos=xy(track.GetPosition()),
                        width=k.Cast_to_PCB_VIA(track).GetWidth(k.F_Cu)/1e6)
            output['vias'].append(item)
            # Via centers plus offsets cross both GND annuli and signal antipads.
            for dx, dy in [(0, 0), (400000, 0), (-400000, 0), (0, 400000), (0, -400000)]:
                p = track.GetPosition()
                probes.add((p.x + dx, p.y + dy))
        else:
            item.update(start=xy(track.GetStart()), end=xy(track.GetEnd()),
                        layer=board.GetLayerName(track.GetLayer()), width=track.GetWidth()/1e6)
            output['tracks'].append(item)
            if track.GetNetname() in RF:
                a, b = track.GetStart(), track.GetEnd()
                for i in range(21):
                    probes.add((round(a.x+(b.x-a.x)*i/20), round(a.y+(b.y-a.y)*i/20)))
    output['contains_probes'] = [dict(pos=[x/1e6, y/1e6],
                                          inside=filled.Contains(k.VECTOR2I(x, y)))
                                 for x, y in sorted(probes)]
    assert sha(args.pcb) == source
    args.output.write_text(json.dumps(output, separators=(',', ':'))+'\n')
    print(json.dumps(dict(source_sha256=source, rf_pads=len(output['pads']),
                          probes=len(probes), board_thickness_mm=output['board_thickness_mm'])))


if __name__ == '__main__':
    main()
