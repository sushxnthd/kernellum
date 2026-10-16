# High-dimensional adversarial boundary generator: decisive failure

**Protocol commit:** `b9f1b892e33c5d37144e969d44e20eef610f4ea7`  
**Generator commit:** `9754fa2263529e6cdb11a1a44e6513611b25e3c0`  
**Corrected workflow commit:** `b39d0c438adc61e03716c9e7be0ddcaff35f38ca`  
**Workflow run:** https://github.com/sushxnthd/kernellum/actions/runs/38842592777  
**Classification:** prospective truth-blind generator failure  
**Outcome truth opened:** no

## Decision

The second and final opportunity generator fails its preregistered manifest gate.
The active pairwise prediction-envelope kernel is retired without opening any
requested-input truth.

The frozen design required six eligible cases from each of four bases, hence
exactly 24 selected cases. The untouched 7-D/seed-6101 base produced zero
eligible perturbations among all 97 grid points. Therefore no completion of the
remaining shards can satisfy the protocol.

## Immutable evidence available at decision time

| Dimension | Seed | Eligible / 97 | Selected | Gate |
|---:|---:|---:|---:|---|
| 5 | 6101 | 70 | 6 | PASS |
| 7 | 6101 | 0 | 0 | FAIL |
| 5 | 6107 | 60 | 6 | PASS |
| 7 | 6107 | still running | — | non-decisive |

The complete factorial should remain running for descriptive preservation, but
its remaining results cannot repair this preregistered study.

Artifact receipts:

- 5-D/6101 canonical manifest SHA-256:
  `eeca09d0a8b648f80b011175a10928f3e74a79de83487d6e6a8bf181075c0136`
- 5-D/6101 workflow artifact digest:
  `sha256:bf988fc52126f9125e40e87b38da6dd2ac3726d0879b90bc79df1366a3361f79`
- 5-D/6107 canonical manifest SHA-256:
  `b14330c88cebd6ddee2811fbfe18a3f4f3cd5f3fbd038238de9e49c958324b5c`
- 5-D/6107 workflow artifact digest:
  `sha256:8fe6eb0a36a7be8bf6aac39e0bfff6fbb08df8e5982ce339a85f2d5d67bfcae8`
- 7-D/6101 canonical manifest SHA-256:
  `f069eca3eddc7b5c9420d44df4fc4a5344685a0001b3049010949a0fa9e39561`
- 7-D/6101 workflow artifact digest:
  `sha256:2459b433343f0f236ad576d4bb3b4848e7a1814a71850c6b687e6a2022a02743`

Generation was executed twice per completed shard. The 5-D shard passed byte
identity and the exact selected-count gate. The 7-D shard reached the scientific
selected-count assertion, failed it as preregistered, and uploaded its manifest.

## Falsified prediction

The mechanism-derived prediction that eligible independent-lower-CV crossings
persist or increase monotonically with dimension is false. Combined with the
first generator, observed eligible frequencies include:

- original 3-D bases: 0/194;
- original 5-D bases: 86/194;
- new 5-D seeds: 130/194 (70/97 and 60/97);
- new 7-D seed 6101: 0/97.

The boundary-opportunity regime is not a simple increasing function of
dimension. It is sharply base-dependent. Dimension is not a prospective
diagnostic for whether exact-LOO arbitration becomes solver-dependent.

## Strongest supported claim

Two independently frozen truth-blind generators failed to create the required
opportunity set. Prediction-envelope disagreement may remain a useful receipt
for descriptive solver invariance, but this research line has not shown that it
can prospectively identify or safely arbitrate catastrophic lower-CV switches.
No safety claim is supported.

## SCIENCE ledger

- **TRUE:** the fixed perturbation produces abundant eligible crossings in some
  5-D bases and none in at least one untouched 7-D base.
- **FALSIFIED:** increasing dimension predicts crossing availability.
- **UNTESTED:** envelope rejection of prospectively selected harmful switches,
  because neither generator produced its required frozen manifest.
- **LIMITATION:** this is a generator/mechanism falsification, not evidence that
  harmful solver switches do not exist.

## CONSEQUENCE ledger

Retire the pairwise-envelope kernel as a flagship KERNELLUM claim. Do not open
the partial manifests' outcome truth and do not retune seeds, caps, perturbation
directions, or thresholds.

The single successor kernel is robust optimization rather than risk scoring:

> Can a deterministic globalized multi-start/ensemble solver remove
> solver-dependent catastrophic tails on frozen boundary sweeps while keeping
> ordinary-regime error and compute within preregistered bounds?

The successor must compare single-start, multi-start, globalized, ensemble, and
stability-penalized controls on untouched regimes; expose compute cost; and
derive a prospective basin diagnostic before any external holdout is opened.
