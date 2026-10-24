#!/usr/bin/env python3
"""Independent attribution of Kernellum's prospective quintic work savings.

Does not run solvers, alter frozen evidence, or claim novelty for symmetry.
Fails if headline savings are incorrectly attributed solely to orbit batching.
"""
import argparse
import json
from fractions import Fraction
from pathlib import Path

NAMES = ('orbit_batched_certified', 'unbatched_certified',
         'tensor_corners', 'optimized_lhs', 'greedy_maximin')


def audit(data):
    if not data.get('holdout_disjoint_from_pilot') or not data.get('gate_pass'):
        raise ValueError('primary holdout/gate is not valid')
    if set(NAMES) - set(data['summary']):
        raise ValueError('missing control')
    summaries = {}
    for name in NAMES:
        rows = [r for r in data['rows'] if r['method'] == name]
        if not rows or len(rows) != len(data['holdout_regimes']):
            raise ValueError('incomplete per-method coverage')
        summary = data['summary'][name]
        work = sum(r['total_work'] for r in rows)
        overhead = sum(r['construction_overhead'] for r in rows)
        solver = sum(r['full']['evaluations'] for r in rows)
        if work != solver + overhead or any(r['total_work'] != r['full']['evaluations'] + r['construction_overhead'] for r in rows):
            raise ValueError('work accounting inconsistent')
        if (work, overhead, solver) != (summary['total_work'], summary['construction_overhead'], summary['solver_evaluations']):
            raise ValueError('summary does not reproduce from raw rows')
        summaries[name] = summary
    batched = summaries['orbit_batched_certified']
    unbatched = summaries['unbatched_certified']
    complete_controls = [summaries[n] for n in NAMES[2:]
                         if summaries[n]['full_complete'] == len(data['holdout_regimes'])]
    if not complete_controls:
        raise ValueError('no full-complete simple control')
    best = min(x['total_work'] for x in complete_controls)
    b, u = batched['total_work'], unbatched['total_work']
    if best != data['best_complete_control_work'] or not (0 < b < u < best):
        raise ValueError('invalid cost ordering or control')
    if batched['solver_evaluations'] != unbatched['solver_evaluations']:
        raise ValueError('batching confounded by solver evaluations')
    if not data['batched_unbatched_behavior_identical']:
        raise ValueError('ablation changes behavior')
    paired = zip((r for r in data['rows'] if r['method'] == 'orbit_batched_certified'),
                 (r for r in data['rows'] if r['method'] == 'unbatched_certified'))
    if not all(a['weights_numerators'] == z['weights_numerators'] and a['full'] == z['full'] and a['capped'] == z['capped'] for a,z in paired):
        raise ValueError('paired ablation mismatch')
    total = Fraction(best-b, best)
    if total != Fraction(data['exact_work_reduction']):
        raise ValueError('published headline fraction inconsistent')
    batch_only = Fraction(u-b,u)
    structural_only = Fraction(best-u,best)
    contribution_share = Fraction(u-b,best-b)
    # A 40%+ end-to-end reduction is not a 40%+ batching-only reduction.
    if batch_only >= total or contribution_share >= Fraction(1,2):
        raise ValueError('decomposition no longer supports bounded claim')
    return {'headline_vs_best_simple_control':str(total),
            'incremental_batching_vs_unbatched_certified':str(batch_only),
            'structural_certification_vs_best_simple_control':str(structural_only),
            'batching_share_of_absolute_total_savings':str(contribution_share),
            'absolute_work':{'batched':b,'unbatched_certified':u,'best_simple_complete':best},
            'verdict':'40_PERCENT_IS_END_TO_END_NOT_BATCHING_ONLY',
            'evidence_tier':'INDEPENDENT_ACCOUNTING_OF_EXISTING_HOLDOUT_NOT_NEW_TRANSFER'}


def selftest():
    regimes=[[1],[2]]
    data={'holdout_disjoint_from_pilot':True,'gate_pass':True,'holdout_regimes':regimes,
          'batched_unbatched_behavior_identical':True,'best_complete_control_work':100,
          'exact_work_reduction':'2/5','summary':{},'rows':[]}
    for name, total, solver in [('orbit_batched_certified',60,50),
                                ('unbatched_certified',70,50),
                                ('tensor_corners',100,100),
                                ('optimized_lhs',120,120),('greedy_maximin',140,140)]:
        data['summary'][name]={'total_work':total,'solver_evaluations':solver,
                               'construction_overhead':total-solver,'full_complete':2}
        for i in range(2):
            data['rows'].append({'method':name,'weights_numerators':regimes[i],
                                 'full':{'evaluations':solver//2,'coverage':32},
                                 'capped':{'coverage':32},
                                 'construction_overhead':(total-solver)//2,
                                 'total_work':total//2})
    assert audit(data)['incremental_batching_vs_unbatched_certified']=='1/7'
    data['summary']['unbatched_certified']['total_work'] = 71
    try: audit(data)
    except ValueError: pass
    else: raise AssertionError('corrupt summary accepted')
    print('KERNELLUM_INCREMENTAL_ATTRIBUTION_SELFTEST_PASS')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--input',type=Path,default=Path('results/quintic_equivariance_transfer.json'))
    args=p.parse_args()
    if args.self_test: selftest()
    else: print(json.dumps(audit(json.loads(args.input.read_text())),indent=2,sort_keys=True))


if __name__=='__main__': main()
