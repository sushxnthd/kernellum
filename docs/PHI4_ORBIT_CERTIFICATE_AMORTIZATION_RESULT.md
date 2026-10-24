# Phi4 orbit-certificate amortization: positive fleet mechanism

## Decision and smallest supported claim

**The frozen positive-mechanism gate passes locally; hosted CI is pending.**

For the certified five-site open-chain phi4 route, exact global sign symmetry
groups the 32 sign boxes into 16 antipodal orbits. Computing one Newton start
per orbit and reflecting it constructs exactly the same 32 starts as the
unbatched route while halving construction overhead. On 19 prospective rational
weight regimes disjoint from the predecessor experiment, this preserved zero
capped catastrophes and raised end-to-end savings versus the strongest
complete-coverage control to exactly `179/609 = 29.3924%`, above the unchanged
25% fleet gate.

## Mechanism

For the residual and Jacobian,

`F(-x)=-F(x)` and `J(-x)=J(x)`.

Consequently the Newton map is odd:

`N(-x)=-N(x)`.

The implementation chooses the 16 signs with positive first coordinate,
performs one residual and Jacobian evaluation for each, and reflects each start
into its antipodal box. This is an executable reduction in work, not a relaxed
certificate or post-hoc exclusion of difficult regimes.

## Frozen prospective evidence

| Route | Full complete | Capped complete | Capped catastrophes | End-to-end work |
|---|---:|---:|---:|---:|
| Orbit-batched certified | 19/19 | 19/19 | 0 | 5,160 |
| Unbatched certified ablation | 19/19 | 19/19 | 0 | 5,768 |
| Tensor corners | 19/19 | 0/19 | 19 | 7,308 |
| Optimized LHS | 0/19 | 0/19 | 19 | 8,774 |
| Greedy maximin | 0/19 | 0/19 | 19 | 8,016 |

The batched and unbatched routes had zero start mismatch, identical solver call
counts, identical basin coverage, identical objectives, and identical capped
decisions. Only charged construction overhead changed: 1,216 calls became 608.
The primary artifact reproduced byte-identically. Its SHA-256 is
`40826cd7e6a39ea4649288a069e6d51ad0b4ba1b350f1a0973a80a6461e0c294`.

## Independent falsification

The independent checker does not import the experiment. Using `Fraction`
arithmetic, it separately evaluates residual oddness and Jacobian evenness for
all 608 regime/sign cases, reconstructs every aggregate from raw rows, checks
that only overhead changed, verifies the complete-control boundary, recomputes
the primary digest, and derives the exact reduction `179/609`. All 8 checks
passed. Audit SHA-256:
`ad201bd73c398ed604774b1eca7c9dabb723fbb539727e98bc2f0c448b165a6f`.

The initial pre-outcome module-path failure and the later missing-local-pytest
infrastructure stop are preserved. Six focused test functions were executed
directly and passed; GitHub remains the authoritative pytest/full-suite gate.

## Priority and novelty boundary

Symmetry reduction, Newton iteration, interval existence/uniqueness methods,
and discrete phi4 lattices are established. The predecessor report records the
primary literature boundary. No new general theorem about these subjects is
claimed. The defensible KERNELLUM result is the exact antipodal cost law wired
into a frozen, prospective selector experiment that changes a previously
failed fleet decision while retaining every safety and ordinary-performance
gate.

## Project consequence and limits

Orbit batching should replace the unbatched construction in the certified phi4
route if hosted reproduction passes. This is the first coupled-family transfer
to exceed the fleet-value gate with zero catastrophic tails.

The result applies only where the residual is odd, the Jacobian is even, and
the existing sign-box certificate holds. Asymmetric forcing breaks the orbit
law. The 32 certified minima are not a global completeness theorem, and transfer
to unrelated objective families remains unproven.

