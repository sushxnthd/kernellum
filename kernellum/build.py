"""Usable K1 build entrypoint; analytical selection is the evidence-backed default."""
import argparse
import contextlib
import csv
import io
import json
from pathlib import Path

from kernellum.pilot import load_spec, prior, simulate_policy, route, digest, dump, audit
from kernellum.route_review import review, render_html


def build(spec_path, out, *, workload, seed, policy='analytic', replay=None):
    spec_path, out = Path(spec_path), Path(out)
    s,pool=load_spec(spec_path)
    w=next((w for w in s['workloads'] if w['name']==workload),None)
    if w is None or seed not in s['seeds']:raise ValueError('workload and seed must exist in spec')
    if out.exists():raise ValueError('use a new output directory to preserve previous evidence')
    if policy not in ('analytic','static','adaptive'):raise ValueError('unknown policy')
    observed={}
    if replay is not None:
        with contextlib.redirect_stdout(io.StringIO()):
            checked=audit(spec_path,replay,out/'replay-audit.json')
        if not checked['complete_and_eligible']:raise ValueError('replay evidence failed integrity checks')
        for p in Path(replay).rglob('result.json'):
            r=json.loads(p.read_text());observed[r['seed'],r['name']]=r
    rows=[]
    def evaluate(a):
        r=observed[seed,a.name] if replay is not None else route(a,seed,s,digest(spec_path),out/'evidence')
        row={k:r[k] for k in ('name','rows','cols','k_tile','seed','synth_ok','route_ok','fmax_mhz')}
        row.update(timing_metric=r.get('timing_metric','unavailable'),
                   nextpnr_returncode=0 if r['route_ok'] else 1)
        row.update({'synth_'+k:v for k,v in r.get('resources',dict(dsp=0,bram=0,lut4=0,ff=0)).items()})
        rows.append(row);return r
    initial=[] if policy=='analytic' else prior(s)
    result=simulate_policy(pool,initial,w,policy,s['budget'],evaluate)
    out.mkdir(parents=True,exist_ok=True)
    csv_path=out/'selected_routes.csv'
    with csv_path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    report=review([csv_path],m=w['m'],n=w['n'],k=w['k'],baseline=rows[0]['name'],max_resources=s['limits'])
    mode='recorded_evidence_replay' if replay is not None else 'live_toolchain_execution'
    report['execution_mode']=mode
    report['selection_policy']=policy
    report['boundary'] = ('RECORDED REPLAY: no new route was executed. Archived functional, synthesis and routing records were used. '
                          if replay is not None else 'LIVE EXECUTION: functional checks, synthesis and routing were attempted for each selected candidate; inspect the recorded outcomes. ')
    report['boundary'] += ('K1 INT8 GEMM only. Latency is modeled kernel cycles divided by final routed Fmax. '
                           'Resources are synthesis counts. No board latency, host I/O, full-model inference, power or customer savings were measured. '
                           'The baseline is the first selected candidate. This comparison does not establish superiority over other selection policies.')
    dump(out/'report.json',report)
    label='Recorded routing replay' if replay is not None else 'Live toolchain execution'
    (out/'report.html').write_text(render_html(report).replace('<h1>Architecture route review</h1>',f'<h1>Architecture route review</h1><p class="eyebrow">{label}</p>'))
    result.update(execution_mode=mode,policy=policy,workload=w,spec_sha256=digest(spec_path),
                  new_route_calls=0 if replay is not None else len(rows),
                  selection_note='Analytical policy chosen after the frozen pilot; further generalization is unvalidated.')
    dump(out/'selection.json',result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--workload',default='expand')
    p.add_argument('--seed',type=int,default=1103)
    p.add_argument('--policy',choices=['analytic','static','adaptive'],default='analytic')
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument('--execute',action='store_true')
    modes.add_argument('--replay',type=Path)
    args=p.parse_args()
    try:
        result=build(args.spec,args.out,workload=args.workload,seed=args.seed,policy=args.policy,replay=args.replay)
        print(json.dumps(result,indent=2));return 0 if result['best_ms'] is not None else 2
    except (ValueError,OSError,KeyError,TypeError) as exc:p.error(str(exc))


if __name__=='__main__':raise SystemExit(main())
