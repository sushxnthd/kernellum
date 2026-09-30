"""Descriptive reporting only; does not alter any frozen outcome or gate."""
import gzip
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/model_revision'
s=json.loads((OUT/'frozen_run/summary.json').read_text())
r=[json.loads(line) for line in gzip.open(OUT/'frozen_run/traces.jsonl.gz','rt')]
ratios=s['model_revision_comparisons']['rbf_maximin']['by_equation']
ordered=sorted(ratios.items(),key=lambda z:z[1])
diagnostic={
    'status':'post-hoc descriptive diagnostic, not a new acceptance gate',
    'model_revision_vs_rbf_equations':{
        'wins':sum(v<1-1e-8 for v in ratios.values()),
        'ties_within_1e-8':sum(abs(v-1)<=1e-8 for v in ratios.values()),
        'losses':sum(v>1+1e-8 for v in ratios.values()),
        'best_five':ordered[:5],'worst_five':ordered[-5:],
        'ratio_after_removing_two_largest_gains':float(np.exp(np.mean(np.log([v for _,v in ordered[2:]])))),
        'median_equation_ratio':float(np.median(list(ratios.values())))},
    'selected_family_counts':{m:{family:sum(row['method']==m and row['metrics'][-1]['models'][0]['family']==family for row in r)
                                for family in ('linear','quadratic','cubic','rbf_short','rbf_medium','rbf_long')}
                              for m in ('maximin','mixture_ivr','rbf_maximin')}
}
(OUT/'diagnostics.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,'ps.fonttype':42,
                     'axes.spines.top':False,'axes.spines.right':False})
fig=plt.figure(figsize=(12,5.3),layout='constrained');gs=fig.add_gridspec(1,2,width_ratios=(1,1.45))
ax=fig.add_subplot(gs[0]);ax2=fig.add_subplot(gs[1])
legacy=1
revision=s['model_revision_comparisons']['quadratic_maximin']['ratio']
rbf=revision/s['model_revision_comparisons']['rbf_maximin']['ratio']
v=[legacy,rbf,revision]
labels=['Previous quadratic model','RBF-only model selection','Polynomial + RBF selection']
ax.barh(range(3),v,color=['#9ca3af','#64748b','#177854'],height=.52)
for i,z in enumerate(v):ax.text(z+.02,i,f'{z:.3f}',va='center',fontsize=10)
ax.set_yticks(range(3),labels);ax.invert_yaxis();ax.set_xlim(0,1.17)
ax.set_xlabel('Geometric mean NMSE, relative to previous model')
ax.set_title('A. Better model; identical measurements',loc='left',fontweight='bold',pad=18)
ax.text(0,-.16,'47 / 48 equation wins over the previous model',transform=ax.transAxes,fontsize=10)
methods=['winner_ivr','maximin','variance','ideal','committee','random']
labels2=['Single-model IVR','Space-filling / maximin','Marginal variance','IDEAL rule','Committee disagreement','Uniform random']
values=[s['comparisons'][m]['ratio'] for m in methods]
ax2.barh(range(len(methods)),values,height=.53,color=['#64748b' if z>.8 else '#177854' for z in values])
for i,(m,z) in enumerate(zip(methods,values)):
    ax2.text(z+.015,i,f'{z:.3f}  ({s["comparisons"][m]["wins"]}/48 wins)',va='center',fontsize=9)
ax2.set_yticks(range(len(methods)),labels2);ax2.invert_yaxis();ax2.set_xlim(0,1.28)
ax2.axvline(1,color='#555555',lw=1);ax2.axvline(.8,color='#b45309',lw=1,linestyle='--')
ax2.set_xlabel('Candidate / comparator prediction error; lower is better')
ax2.set_title('B. New acquisition; matched revised model',loc='left',fontweight='bold',pad=18)
ax2.text(0,-.16,'Dashed line: required 20% improvement. Full gate FAILED.',transform=ax2.transAxes,fontsize=10)
fig.suptitle('Kernellum | Model revision improves the old system; acquisition remains unproven',fontweight='bold',fontsize=13)
fig.savefig(OUT/'comparison.png',dpi=180,bbox_inches='tight')
fig.savefig(OUT/'comparison.pdf',bbox_inches='tight')
print(json.dumps(diagnostic,indent=2))
