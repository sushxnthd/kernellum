"""Independent stdlib-only check of the frozen pilot archives and policy results.

Imports no Kernellum modules or original evaluator. Run from any directory.
"""
import csv
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def cycles(w, a):
    r,c,t = a
    return ((w['m']+r-1)//r)*((w['n']+c-1)//c)*(2*w['k']+3*((w['k']+t-1)//t)+2)


def features(a):
    r,c,t=a
    return r*c/120,math.log2(t)/6,math.log2(r/c),abs(r-c)/14


def estimate(a, observations):
    x=features(a)
    neighbors=sorted((math.dist(x,features(b)),i,f) for i,(b,f) in enumerate(observations))
    if neighbors[0][0]<1e-12:return neighbors[0][2]
    selected=neighbors[:4]
    weights=[1/(d+.03)**2 for d,_,_ in selected]
    return sum(w*f for w,(_,_,f) in zip(weights,selected))/sum(weights)


def main():
    spec_bytes=(ROOT/'experiments/pilot_search/spec.json').read_bytes()
    spec=json.loads(spec_bytes)
    manifest=json.loads((ROOT/'results/pilot_search/artifact_manifest.json').read_text())
    official=json.loads((ROOT/'results/pilot_search/summary.json').read_text())
    pool={f"r{a['rows']:02d}_c{a['cols']:02d}_k{a['k_tile']:03d}":(a['rows'],a['cols'],a['k_tile']) for a in spec['candidates']}
    records={};versions=set();files_checked=0
    for artifact in manifest['artifacts']:
        p=ROOT/'evidence/pilot_search/original_zips'/(artifact['name']+'.zip')
        raw=p.read_bytes()
        assert sha(raw)==artifact['digest'].split(':')[1],str(p)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if artifact['name']=='pilot-search-summary':
                assert z.read('summary.json')==(ROOT/'results/pilot_search/summary.json').read_bytes()
            for name in z.namelist():
                if not name.endswith('/result.json'):continue
                r=json.loads(z.read(name));prefix=name.rsplit('/',1)[0]+'/'
                key=r['seed'],r['name']
                assert key not in records and r['name'] in pool and r['seed'] in spec['seeds']
                assert r['spec_sha256']==sha(spec_bytes)
                assert r['runner_sha256']==sha((ROOT/'kernellum/pilot.py').read_bytes())
                for dep,digest in r['dependency_hashes'].items():
                    assert sha((ROOT/dep).read_bytes())==digest
                for f,digest in r['file_sha256'].items():
                    assert sha(z.read(prefix+f))==digest,(key,f)
                    files_checked+=1
                assert r['eligible'] and r['route_ok'] and r['synth_ok'] and r['functional_ok']
                assert len(r['commands'])==4 and all(x['returncode']==0 for x in r['commands'])
                assert 'KERNELLUM_PILOT_SIM_PASS' in z.read(prefix+'functional.log').decode()
                cells={}
                for line in z.read(prefix+'synthesis.log').decode().splitlines():
                    fields=line.split()
                    if len(fields)==2 and fields[1].isdigit():cells[fields[0]]=int(fields[1])
                for key_resource,cell in [('dsp','MULT18X18D'),('bram','DP16KD'),('lut4','LUT4'),('ff','TRELLIS_FF')]:
                    assert r['resources'][key_resource]==cells[cell]
                    assert cells[cell]<=spec['limits'][key_resource]
                geometry=pool[r['name']]
                assert (r['rows'],r['cols'],r['k_tile'])==geometry
                assert cells['MULT18X18D']==geometry[0]*geometry[1]
                timing=json.loads(z.read(prefix+'timing.json'))
                observed=min(float(v['achieved']) for v in timing['fmax'].values() if v.get('achieved') is not None)
                assert math.isfinite(observed) and observed>0 and observed==r['fmax_mhz']
                versions.add(json.dumps(r['tool_versions'],sort_keys=True))
                records[key]=r
    assert len(versions)==1
    assert set(records)==set(itertools.product(spec['seeds'],pool))
    prior=[]
    for f in spec['prior_files']:
        for r in csv.DictReader((ROOT/f).open()):
            assert r['route_ok']=='True' and r['timing_metric']=='post_route_report_json'
            prior.append(((int(r['rows']),int(r['cols']),int(r['k_tile'])),float(r['fmax_mhz']),r['name']))
    prior.sort(key=lambda x:(7/(x[1]*1000),x[2]))
    initial=[(a,f) for a,f,_ in prior]
    cases=[]
    for seed,w in itertools.product(spec['seeds'],spec['workloads']):
        lat={name:cycles(w,a)/(records[seed,name]['fmax_mhz']*1000) for name,a in pool.items()}
        case={'seed':seed,'workload':w['name'],'oracle_ms':min(lat.values()),'policies':{}}
        expected=next(c for c in official['cases'] if c['seed']==seed and c['workload']==w['name'])
        for policy in ['analytic','static','adaptive']:
            obs=list(initial);remaining=list(pool);trace=[]
            for _ in range(spec['budget']):
                def score(name):
                    f=1 if policy=='analytic' else estimate(pool[name],obs if policy=='adaptive' else initial)
                    return cycles(w,pool[name])/f,name
                selected=min(remaining,key=score);remaining.remove(selected);trace.append(selected)
                obs.append((pool[selected],records[seed,selected]['fmax_mhz']))
            best=min(lat[x] for x in trace)
            regret=100*(best/case['oracle_ms']-1)
            e=expected['policies'][policy]
            assert trace==[x['candidate'] for x in e['trace']]
            assert abs(e['best_ms']-best)<1e-10 and abs(e['oracle_regret_pct']-regret)<1e-10
            case['policies'][policy]={'best_ms':best,'regret_pct':regret,'trace':trace}
        vals=[min(lat[x] for x in pair) for pair in itertools.combinations(pool,spec['budget'])]
        case['random_ms']=sum(vals)/len(vals)
        assert abs(case['random_ms']-expected['expected_random_best_ms'])<1e-10
        cases.append(case)
    mean=lambda xs:sum(xs)/len(xs)
    gains={p:mean([100*(1-c['policies']['adaptive']['best_ms']/(c['random_ms'] if p=='random' else c['policies'][p]['best_ms'])) for c in cases]) for p in ['analytic','static','random']}
    regret=mean([c['policies']['adaptive']['regret_pct'] for c in cases])
    gates={'mean_regret':regret<=spec['gate']['max_mean_regret_pct'],
           **{f'gain_vs_{p}':gains[p]>=spec['gate'][f'min_gain_vs_{p}_pct'] for p in gains},
           'never_worse_than_analytic':all(c['policies']['adaptive']['best_ms']<=c['policies']['analytic']['best_ms']+1e-12 for c in cases)}
    assert gates==official['flags']
    assert all(gates.values())==official['claim_supported']
    for p in gains:assert abs(gains[p]-official['mean_gain_pct'][p])<1e-10
    result={'audit_passed':True,'archives':len(manifest['artifacts']),'routes':len(records),
            'hashed_files_checked':files_checked,'policy_traces_reproduced':len(cases)*3,
            'mean_gain_pct':gains,'mean_adaptive_regret_pct':regret,
            'analytic_oracle_hits':sum(c['policies']['analytic']['regret_pct']==0 for c in cases),
            'adaptive_oracle_hits':sum(c['policies']['adaptive']['regret_pct']==0 for c in cases),
            'flags':gates,'claim_supported':all(gates.values())}
    (ROOT/'results/pilot_search/independent_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
