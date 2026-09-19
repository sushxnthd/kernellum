# Kernellum K1 closed-loop physical-design search

Date frozen: 2026-09-19

This experiment begins only after the original nine-candidate K1 routed sweep passed.

## Question

Can routed physical-design observations be used to choose the next architectures more effectively than equal-budget random selection while physically implementing less than 10% of a larger search space?

## Search space

The frozen candidate pool uses:

- ROWS in {2,4,6,8,10,12,14}
- COLS in {2,4,6,8,10,12,14}
- K_TILE in {8,16,32,64}
- PE count ROWS*COLS <= 120
- INT8 MACs
- same ECP5-85K / CABGA381 flow as K1

This produces **172 architectures**.

The original nine routed K1 designs are the initial observations.

## Surrogate

The Fmax surrogate is a deterministic inverse-distance model over four architecture features:

1. PE count / 120
2. log2(K_TILE) / 6
3. signed log2(ROWS/COLS)
4. absolute ROWS-COLS / 14

Prediction uses up to four nearest routed architectures with inverse-square distance weighting.

Uncertainty is the nearest-neighbor feature distance.

## Active acquisition

For every unseen architecture, K1 predicts Fmax and computes routed-latency estimates for all 12 frozen Transformer GEMMs.

The acquisition score is the mean latency normalized to the best currently routed latency for each workload, using an optimistic Fmax equal to:

`predicted_fmax + 6 * nearest_feature_distance`

The four unseen architectures with the lowest acquisition scores are the **active** arm.

## Random control

Four unseen architectures are sampled with a fixed RNG seed of **20260919**, excluding active proposals.

The random arm therefore gets exactly the same physical-routing budget as active search.

## Physical-design budget

- initial routed observations: 9
- active routes: 4
- random-control routes: 4
- maximum total observed architectures: 17 / 172 = **9.88%**

No extra candidate may be routed because a result looks inconvenient.

## Predeclared gate

The closed-loop experiment passes if:

1. at least 7 of the 8 new candidates route successfully;
2. total observed architecture fraction remains <= 10%;
3. Fmax surrogate MAPE on successfully routed new candidates is <= 20%;
4. active search's mean final-best routed latency across the 12 workloads is no worse than the equal-budget random arm;
5. active search improves the initial routed optimum on at least as many workloads as random search.

Ties on criteria 4 or 5 are allowed.

## Interpretation

A pass is evidence that physical feedback can guide the next routing decisions in this limited ECP5 design family. It is not evidence of universal Bayesian optimization superiority, physical-board performance, or ASIC transfer.
