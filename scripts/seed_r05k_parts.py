#!/usr/bin/env python3
"""One-shot r05k component selection; preserve tested r05j and every copper item."""
import copy
import csv
import hashlib
import json
from pathlib import Path
import shutil

import pcbnew as k
from build_power_r05 import parse, emit, child, Quoted

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'experiments/power-r05j-rf-junctions'
TARGET = ROOT/'experiments/power-r05k-selected-parts'
SELECTION = ROOT/'assembly/power-parts-r01/selection.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED = '51fc05ccc66009995daa8c5d5466aa983436e00e7ff338f0ddfb0927c92b4580'


def main():
    assert sha(SOURCE/'hardware/collar-tracker.kicad_pcb') == EXPECTED
    assert not TARGET.exists(), 'Preserve previous candidates'
    selected = json.loads(SELECTION.read_text())
    profile_source = ROOT/'mechanical/swim-r06-six-layer-fit/fit-profile.json'
    profile = json.loads(profile_source.read_text())
    profile['revision'] = 'r05k-selected-parts-fit'
    profile['reviewed_date'] = '2026-10-25'
    by_ref = {p['ref']:p for p in profile['parts']}
    for ref, spec in {**selected['resistors'],**selected['capacitors']}.items():
        p = by_ref[ref]
        p.update(mpn=spec['mpn'],height_max_mm=spec['height_max_mm'],status='candidate_part')
        p['source_url'] = ('https://www.vishay.com/docs/20043/crcwhpe3.pdf' if ref=='R21'
            else 'https://www.yageogroup.com/component-documentation/download/specsheet/'+spec['mpn']
            if ref.startswith('R') else 'https://ds.murata.com/simsurfing/mlcc.html?partnumbers=%5B%22'+spec['mpn'][:-1]+'%22%5D&lcid=en-us')
        p['basis'] = ('Manufacturer part-specific dimensions and electrical selection; see assembly/power-parts-r01. '
                      'Prototype candidate, not powered/assembly approval.')
    profile['open_items'] = [s for s in profile['open_items'] if not s.startswith('R1/R16-R23 exact MPN')]
    profile['open_items'].append('Selected exact power parts and timing capacitor bounds require assembled electrical, aging and process validation; no unspecified resistor-height reservations remain.')
    shutil.copytree(SOURCE/'hardware',TARGET/'hardware',ignore=shutil.ignore_patterns('*.kicad_prl','*.local-routing.json','*.detour-proposal.json'))
    (TARGET/'evidence').mkdir()
    (TARGET/'assembly').mkdir()
    (TARGET/'assembly/fit-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    hardware = TARGET/'hardware'
    rows = list(csv.DictReader((hardware/'bom.csv').open()))
    old_rows = copy.deepcopy(rows)
    updates = {}
    for row in rows:
        ref = row['ref']
        if by_ref[ref]['mpn']:
            row['mpn'] = by_ref[ref]['mpn']
            row['status'] = 'Exact prototype candidate MPN; electrical, RF and assembly acceptance remain open'
            if ref in selected['changes']:
                assert row['value'] == selected['changes'][ref]['from']
                row['value'] = selected['changes'][ref]['to']
            updates[ref] = dict(value=row['value'],mpn=row['mpn'],status=row['status'])
    assert len(updates)==65
    with (hardware/'bom.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    design=json.loads((hardware/'design.json').read_text())
    for part in design['parts']:
        if part['ref'] in updates:part.update(updates[part['ref']])
    (hardware/'design.json').write_text(json.dumps(design,indent=2)+'\n')
    schematic=hardware/'collar-tracker.kicad_sch'
    root=parse(schematic.read_text())
    for item in root:
        if not isinstance(item,list) or not item:continue
        if item[0]=='symbol' and child(item,'lib_id'):
            props={str(p[1]):p for p in item if isinstance(p,list) and p and p[0]=='property'}
            ref=str(props['Reference'][2])
            if ref in updates:
                for field,key in [('Value','value'),('MPN','mpn'),('Design status','status')]:
                    props[field][2]=Quoted(updates[ref][key])
        elif item[0]=='text':
            text=str(item[1])
            if text.startswith('r05 POWER SCHEMATIC CANDIDATE'):
                item[1]=Quoted('r05k SELECTED COMPONENTS — PHYSICAL ELECTRICAL / RF QUALIFICATION OPEN')
            elif text.startswith('Existing RF, SIM and digital circuits'):
                item[1]=Quoted('Circuit topology retains r05; PCB routing retains r05j.\nR17/R18/R19: 200k / 26.1k / 3.4M; C25: 1uF.\nAll 65 fitted component references have exact candidate MPNs.')
    title=child(root,'title_block')
    child(title,'title')[1]=Quoted('Collar tracker — r05k selected component candidate')
    child(title,'rev')[1]=Quoted('0.5k-components-WIP')
    child(title,'comment')[2]=Quoted('Native and supplier evidence belong to this exact revision; see STATUS')
    schematic.write_text(emit(root)+'\n')
    board=k.LoadBoard(str(hardware/'collar-tracker.kicad_pcb'))
    assert len(list(board.GetFootprints()))==71
    for f in board.GetFootprints():
        if f.GetReference() not in updates:continue
        row=updates[f.GetReference()]
        f.SetValue(row['value'])
        f.SetField('MPN',row['mpn']);f.GetField('MPN').SetVisible(False)
        f.SetField('Design status',row['status']);f.GetField('Design status').SetVisible(False)
    board.GetTitleBlock().SetRevision('0.5k-components-WIP')
    labels=0
    for drawing in board.GetDrawings():
        if drawing.GetClass()=='PCB_TEXT' and drawing.GetText()=='CT 0.5J':
            drawing.SetText('CT 0.5K');labels+=1
    assert labels==1
    # No refill: this mutation never changes copper, mask, paste or placement.
    assert k.SaveBoard(str(hardware/'collar-tracker.kicad_pcb'),board)
    assert sha(SOURCE/'hardware/collar-tracker.kicad_pcb')==EXPECTED
    for suffix in ['kicad_pro','kicad_dru']:
        assert sha(hardware/('collar-tracker.'+suffix))==sha(SOURCE/'hardware'/('collar-tracker.'+suffix))
    receipt=dict(source_revision='r05j',source_sha256=EXPECTED,
        candidate_sha256=sha(hardware/'collar-tracker.kicad_pcb'),
        selection_sha256=sha(SELECTION), profile_source_sha256=sha(profile_source),
        value_changes=selected['changes'], exact_fitted_mpn_count=len(updates),
        changes=[dict(ref=a['ref'],before=a,after=b) for a,b in zip(old_rows,rows) if a!=b],
        scope='Component values/metadata and CT 0.5K silk label only; fresh native and supplier checks required.')
    (TARGET/'evidence/component-seed.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('Created r05k: 65 fitted candidate MPNs; four value changes; native checks pending.')


if __name__=='__main__':main()
