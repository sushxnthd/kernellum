# Transition-constrained batch acquisition: decisive negative result

**Date:** 17 October 2026  
**Classification:** opened-cohort development falsification  
**Frozen protocol commit:** `441de576a32128f53f353587799cc7cdbadc6882`

## Smallest supported claim

On the frozen 48-cell shifted synthetic cohort, neither a three-point
disagreement-diversity batch, a three-point farthest-support batch, nor locking
the pre-acquisition sign/model family made exact-LOO selection tail-safe. The
transition-locked arm produced 13 catastrophes versus 11 without acquisition,
including 9 far-shell catastrophes versus 7, and was unavailable in four cells.

This kills these exact mechanisms and the broader heuristic
abstention/acquisition intervention line after its third discriminating failure.
It is not a universal impossibility theorem, an external validation, or evidence
against active learning in general.

## Frozen outcomes

| Arm | Total catastrophes | Far-shell catastrophes | Model-class transitions | Unavailable cells |
|---|---:|---:|---:|---:|
| No acquisition | 11 | 7 | 0 | 0 |
| One-point disagreement | 9 | 8 | 11 | 0 |
| Three-point disagreement-diversity | 10 | 9 | 12 | 0 |
| Three-point farthest support | 9 | 7 | 12 | 0 |
| Transition-locked three-point batch | **13** | **9** | **0** | **4** |

Only the truth-blind decision/prehash gate passed. Every terminal scientific gate
for the transition-locked mechanism failed: completeness, catastrophe halving,
control superiority, per-domain safety, far-shell safety, inside non-inferiority,
and near/far geometric-error gates.

## Mechanism interpretation

The earlier one-point result showed that an acquisition can trigger a worse
discontinuous class transition. This matched experiment now separates that
failure from the stronger claim that preventing the transition is sufficient.
It is not: the locked arm had zero class transitions yet performed worse than
baseline and sometimes could not refit its frozen class at all. Meanwhile, adding
three points did not rescue either unrestricted batch. Thus both ingredients are
implicated:

1. class switching can create catastrophic extrapolators; and
2. within-class parameter revision and class infeasibility can remain catastrophic
   even when switching is forbidden.

The result rules out treating more labels, maximum disagreement, geometric
support expansion, or identity locking as stand-alone tail-safety certificates.

## Reproducibility and independent check

- 48 truth-blind decision rows, covering five arms and 240 arm/cell outcomes;
- decision artifact SHA-256:
  `e9d0fcd70ecd227055bd0d1e551f373bd04d579ada32f03469c4666f9db34750`;
- canonical result digest:
  `840286b5adfa6a0723a718dc7a25f5308173c30f72464d39eb5a18cd85fdcaf4`;
- result-file SHA-256:
  `92f647327ef46d4c637e557b4f6c52c63bcd767f276c8dd6a9f8c45463f29ef8`;
- independently written full-refit audit: 336 checks, zero failures;
- audit-file SHA-256:
  `a8a8f7cff89097a7a096f31eff5e19cbac168df872e9610e1717c0638dacf0e6`;
- a fresh rerun produced byte-identical decision and result artifacts.

## Preserved infrastructure failure

Commit `27fea1c437f49cbb24df3412e85598d7aef5b785` intentionally preserves the
first workflow implementation. Four legitimate locked-fit failures were counted
as catastrophes, yielding an internal infinity for the geometric mean; strict
JSON serialization then rejected that value before writing the result. The
follow-up fix changes only serialization: unavailable geometric means are stored
as `null`, while the frozen gate arithmetic still treats them as infinity and the
cells as catastrophes. No acquisition rule, fit, score, threshold, or outcome was
changed.

## SCIENCE ledger

- **Falsified:** discontinuous sign/family transitions are the sole cause of the
  catastrophic post-acquisition tail.
- **Falsified:** a three-point disagreement-diversity or farthest-support batch is
  sufficient to rescue the opened cohort.
- **Supported, scoped:** measurement can destabilize extrapolation both through
  between-class switches and within-class parameter revision/infeasibility.
- **Not claimed:** novelty beyond this exact matched causal dissection; universal
  impossibility; performance on external data.

## CONSEQUENCE ledger

- Do not ship nearest-support abstention, one-point disagreement acquisition,
  batch disagreement-diversity, farthest-support batching, or model-identity
  locking as safety mechanisms.
- Do not spend an untouched holdout on another heuristic acquisition variant.
- Exact-LOO selection must be treated as uncertified outside an explicit
  model-class validity region.
- The next runtime capability must return a proof-bearing prediction envelope or
  refuse, rather than return another heuristic risk score or measurement point.

## Active successor kernel: version-space envelope certification

- **Precise question:** can Kernellum compute the worst-case prediction range over
  every training-compatible model in an explicit class and authorize a request
  only when that range is below a user-set tolerance?
- **Best-known frontier:** stability, conformal, and active-learning heuristics do
  not by themselves certify out-of-support extrapolation under misspecification;
  the current exact-LOO pipeline has no version-space bound.
- **Exact objective:** zero catastrophic errors among certified cells while
  certifying strictly more cells than the static observed-support box.
- **Strongest alternative:** envelope width is only a costly proxy for support
  distance/domain order and adds no useful coverage.
- **Cheapest decisive falsification:** exact or interval enumeration on the opened
  candidate family, compared with static support-box, shell-order, and oracle
  hindsight controls; no holdout.
- **Publishable success condition:** a sound finite-sample envelope theorem plus
  prospective untouched and external-oracle validation with nontrivial coverage.
- **Project-relevance threshold:** a machine-checkable certificate/refusal object
  integrated at prediction time.
- **Kill condition:** any certified catastrophe, an unsound numerical bound, or
  coverage no better than the static support baseline.

No backup kernel is activated by this result.

## Limitations

The cohort contains 16 synthetic paths, three request domains, noiseless acquired
responses, two model families, two signs, one batch size, and one fixed optimizer.
All outcomes are development evidence. The negative result justifies a project
pivot; it does not justify a field-level claim without broader theory and data.
