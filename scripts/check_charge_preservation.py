#!/usr/bin/env python3
"""Compare r05l to the immutable r05k source, allowing only reviewed changes."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from build_power_r05 import parse, child

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'experiments/power-r05k-selected-parts'
TRIAL = ROOT / 'experiments/power-r05l-charge-interlock'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
NEW = {'U10', 'U11', 'U12', *('R'+str(i) for i in range(24,31)),
       *('C'+str(i) for i in range(31,37))}
RF = {'/LTE_RF', '/LTE_ANT', '/GPS_RF', '/GNSS_ANT',
      '/GNSS_FEM_IN', '/GNSS_FEM_OUT', '/FILT_OUT', '/AMP_IN'}


def items(root, tags):
    return {child(x,'uuid')[1]: x for x in root
            if isinstance(x,list) and x[0] in tags}


def footprints(root):
    return {next(p[2] for p in x if isinstance(p,list) and p[:2]==['property','Reference']): x
            for x in root if isinstance(x,list) and x[0]=='footprint'}


def compute():
    before, after = [p/'hardware/collar-tracker.kicad_pcb' for p in [BASE,TRIAL]]
    assert sha(before)=='bea6c52a7f045b5fb21ac9714f3db0c70207f150aab3e9587b891f08e4e2b4d3'
    a,b=[parse(p.read_text()) for p in [before,after]]
    af,bf=footprints(a),footprints(b)
    assert set(bf)-set(af)==NEW and not set(af)-set(bf)
    for ref in af:
        old,new=copy.deepcopy(af[ref]),copy.deepcopy(bf[ref])
        if ref=='U3':
            pin=next(x for x in new if isinstance(x,list) and x[:2]==['pad','4'])
            assert child(pin,'net')[1]=='/CHARGE_DISABLE'
            child(pin,'net')[1]='/GND'
        assert old==new, 'Unreviewed original footprint change: '+ref
    for tag in ['general','layers','setup']:
        assert child(a,tag)==child(b,tag), 'Stack or setup changed: '+tag
    for suffix in ['kicad_pro','kicad_dru']:
        assert sha(BASE/'hardware'/('collar-tracker.'+suffix))==sha(TRIAL/'hardware'/('collar-tracker.'+suffix))
    seed=json.loads((TRIAL/'evidence/pcb-seed.json').read_text())
    vin=json.loads((TRIAL/'evidence/vin-escape-rework.json').read_text())
    expected_removed={x['uuid'] for x in seed['removed_ce_ground_branch']+vin['removed']}
    old,new=items(a,{'segment','via','arc'}),items(b,{'segment','via','arc'})
    assert set(old)-set(new)==expected_removed and len(expected_removed)==8
    assert all(old[i]==new[i] for i in old.keys()&new.keys()), 'Original copper edited'
    preserved_copper_count=len(old)-len(expected_removed)
    added=[new[i] for i in sorted(new.keys()-old.keys())]
    allowed={'/VSYS','/GND','/VIN_5V','/BAT_NTC','/CHARGE_DISABLE',
             '/CHG_HOT_OK','/CHG_HOT_LIMIT','/CHG_HOT_REF',
             '/CHG_COLD_OK','/CHG_COLD_LIMIT','/CHG_COLD_REF'}
    assert all(child(x,'net')[1] in allowed for x in added)
    assert all(child(old[i],'net')[1] not in RF for i in expected_removed)
    # Entire original RF segment objects, including width and endpoints, survive.
    rf=[i for i,x in old.items() if child(x,'net')[1] in RF]
    assert len(rf)==27 and all(new[i]==old[i] for i in rf)
    graphics_a,graphics_b=items(a,{'gr_text','gr_line','gr_arc','gr_rect','gr_poly'}),items(b,{'gr_text','gr_line','gr_arc','gr_rect','gr_poly'})
    assert graphics_a.keys()==graphics_b.keys()
    labels=[]
    for uid,old in graphics_a.items():
        new=copy.deepcopy(graphics_b[uid])
        if new==old:continue
        assert old[0]==new[0]=='gr_text'
        if old[1]=='CT 0.5K':
            assert new[1]=='CT 0.5L';new[1]=old[1]
        else:
            assert old[1] in {'SWD','5V','BAT+'}
            new[new.index(child(new,'at'))]=child(old,'at')
        assert old==new, 'Label size or unrelated graphics changed'
        labels.append(old[1])
    assert set(labels)=={'CT 0.5K','SWD','5V','BAT+'}
    old_zones,new_zones=items(a,{'zone'}),items(b,{'zone'})
    assert old_zones.keys()==new_zones.keys()
    strip_fill=lambda z:[x for x in z if not (isinstance(x,list) and x[0] in {'filled_polygon','fill_segments'})]
    assert all(strip_fill(old_zones[i])==strip_fill(new_zones[i]) for i in old_zones), 'Plane or keepout definition changed'
    return dict(source_sha256=sha(after),baseline_sha256=sha(before),
        preserved_original_footprints=len(af),only_original_pin_net_change='U3.4: GND -> CHARGE_DISABLE',
        original_copper_items_preserved=preserved_copper_count,
        removed_original_items=sorted(expected_removed),added_copper_items=len(added),
        unchanged_rf_segments=len(rf),unchanged_rules_stack_lands_and_keepouts=True,
        repositioned_full_size_labels=['5V','BAT+','SWD'],
        added_refs=sorted(NEW),checker_sha256=sha(Path(__file__)),
        scope='Source identity and bounded geometry differences. New routing has its own native DRC, ground, power, RF-reference, fit and supplier evidence; this comparison is not functional qualification.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true')
    args=p.parse_args();result=compute()
    if args.write:(TRIAL/'evidence/source-preservation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
