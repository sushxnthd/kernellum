#!/usr/bin/env python3
"""Independent, read-only check of frozen B-local replication artifacts."""
import csv
import hashlib
import json
import math
import pathlib
import re
import statistics

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / 'extracted'
V = ('setup_violations','hold_violations','max_slew_violations','max_fanout_violations','max_cap_violations','drc_count')
P = ('period_min_ns','fmax_mhz','critical_path_delay_ns','total_cells','dff_cells','cell_area_um2','wire_length_um')
H = ('gds_sha256','odb_sha256','spef_sha256','netlist_sha256')
SHAPES = {(5,10),(10,5),(7,8),(8,7)}
SEEDS = {181,211,239}
PLATFORMS = {'nangate45','sky130hd'}
TOPOLOGIES = {'broadcast','local','blocal'}

def key(x):
    return x['platform'],x['topology'],int(x['rows']),int(x['cols']),int(x['seed'])

def clean(x):
    return x['attempted'].lower() == x['route_ok'].lower() == 'true' and not x['error_stage'] and all(int(x[k]) == 0 for k in V) and all(math.isfinite(float(x[k])) and float(x[k]) > 0 for k in P) and all(re.fullmatch('[0-9a-f]{64}',x[k]) for k in H)

def main():
    dl=json.loads((ROOT/'artifact_digests.json').read_text())
    assert len(dl)==20
    for x in dl:
        z=ROOT/'original_zips'/(x['name']+'.zip')
        assert hashlib.sha256(z.read_bytes()).hexdigest()==x['digest'].removeprefix('sha256:'),z
    csvs=list(DATA.rglob('similarity_blocal_replication_*.csv'))
    assert len(csvs)==18
    rows=[row for path in csvs for row in csv.DictReader(path.open())]
    expected={(p,t,r,c,s) for p in PLATFORMS for t in TOPOLOGIES for r,c in SHAPES for s in SEEDS}
    assert len(rows)==72 and {key(r) for r in rows}==expected
    dirty=[x for x in rows if not clean(x)]
    indexed={key(x):x for x in rows if clean(x)}
    matched=[]
    for platform in sorted(PLATFORMS):
        for rr,cc in sorted(SHAPES):
            for seed in sorted(SEEDS):
                trio=[indexed.get((platform,t,rr,cc,seed)) for t in ('broadcast','local','blocal')]
                if None in trio: continue
                b,l,c=trio
                bp,lp,cp=(float(x['period_min_ns']) for x in trio)
                ba,la,ca=(float(x['cell_area_um2']) for x in trio)
                matched.append(dict(platform=platform,shape=f'{rr}x{cc}',seed=seed,q_local=(bp-lp)/bp,q_candidate=(bp-cp)/bp,retention=(bp-cp)/(bp-lp) if bp>lp else None,density_b=bp*ba/(cp*ca),density_l=lp*la/(cp*ca),dff_b=int(b['dff_cells']),dff_l=int(l['dff_cells']),dff_c=int(c['dff_cells']),area_c=ca,area_l=la))
    groups=[]
    for platform in sorted(PLATFORMS):
        for rr,cc in sorted(SHAPES):
            ss=f'{rr}x{cc}'
            bunch=[x for x in matched if x['platform']==platform and x['shape']==ss]
            if len(bunch)!=3: continue
            groups.append(dict(platform=platform,shape=ss,holdout=(rr,cc) in {(7,8),(8,7)},raw=statistics.median(x['q_candidate'] for x in bunch),retention=statistics.median(x['retention'] for x in bunch),density_b=statistics.median(x['density_b'] for x in bunch),density_l=statistics.median(x['density_l'] for x in bunch),local_raw=statistics.median(x['q_local'] for x in bunch)))
    reports=list(DATA.rglob('6_finish.rpt'));drivers=list(DATA.rglob('driver.log'));manifests=list(DATA.rglob('flow_patch_*.json'));logs=list(DATA.rglob('tb_*.log'))
    patch_records=[json.loads(p.read_text()) for p in manifests]
    patch_ok=len(manifests)==18 and all(x['workflow_source_sha']=='e70fee7455876ad08c670df727338a6edbb86cc1' and x['replacement_count']==1 and x['target']=='flow/scripts/final_outputs.tcl' and x['before_sha256']!=x['after_sha256'] for x in patch_records)
    driver_ok=len(drivers)==72 and all('===== native finish' in (s:=p.read_text()) and 'Signal 11 received' not in s and 'make: ***' not in s for p in drivers)
    qfan=[]
    for p in reports:
        path=p.as_posix()
        if '/nangate45/blocal/' not in path or not any('/'+shape+'/' in path for shape in ('r7_c8','r8_c7')):continue
        s=p.read_text().split('finish report_checks -path_delay max',1)
        body=s[1] if len(s)==2 else ''
        m=re.search(r'^\s*(\d+)\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+[\^v]\s+.*?/Q\s+\(',body,re.MULTILINE)
        if m:qfan.append((path,int(m.group(1))))
    fanout_ok=len(qfan)==6 and all(statistics.median(v for path,v in qfan if '/'+shape+'/' in path)<=10 for shape in ('r7_c8','r8_c7'))
    gates=dict(function=len(logs)==4 and all('PASS' in p.read_text() for p in logs),patch_manifests=patch_ok,all_evidence=len(reports)==len(drivers)==72,drivers=driver_ok,all_attempted=len(rows)==72 and all(x['attempted'].lower()=='true' for x in rows),all_clean=len(dirty)==0,all_groups=len(groups)==8 and len(matched)==24,local_positive=len(groups)==8 and all(x['local_raw']>0 for x in groups),dff=len(matched)==24 and all(x['dff_b']<x['dff_c']<=.9*x['dff_l'] for x in matched),area=len(matched)==24 and all(x['area_c']<x['area_l'] for x in matched),fanout=fanout_ok)
    hold=[x for x in groups if x['holdout']]
    gates.update(raw=len(hold)==4 and all(x['raw']>=.05 for x in hold),retention=len(hold)==4 and all(x['retention']>=.70 for x in hold),density=sum(x['density_b']>=1.01 and x['density_l']>=1.01 for x in hold)>=3,density_both_platforms=all(any(x['platform']==p and x['density_b']>=1.01 and x['density_l']>=1.01 for x in hold) for p in PLATFORMS))
    result=dict(artifact_count=len(dl),rows=len(rows),clean=len(rows)-len(dirty),dirty=[{k:x[k] for k in ('platform','topology','rows','cols','seed',*V)} for x in dirty],matched=len(matched),groups=groups,gates=gates,all_required_pass=all(gates.values()))
    (ROOT/'independent_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
