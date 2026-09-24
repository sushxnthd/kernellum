# SIMILARITY critical-bit replication: opened-data diagnostic plan

Status: **exploratory protocol fixed before candidate physical routing**.
This is not a confirmatory preregistration. The 5x8 and 8x5 geometries and
seeds 53, 71 and 89 were opened by the completed stride-two experiment and
are used only to decide whether a distinct intervention deserves a new,
prospective study.

## Evidence and intervention

The completed prospective stride-two experiment is a null because NanGate45
8x5 retained 52.94% of full-local's timing benefit, below the frozen 60%
gate. Across the 24 stride-two maximum-delay reports, launch registers were
usually A[7] or B[2:0]: the signed A sign bit and low B bits feeding the
multiplier. On the failing NanGate45 8x5 group, all three maximum paths
launched from shared A group registers with Q fanout 15, versus Q fanout
8, 9 and 8 for full-local. This is a hypothesis-generating association, not
a causal result.

The candidate keeps stride-two stages and shared valid signals. Inside each
two-PE group it replicates only A[7] and B[2:0]; the other eleven operand
bits remain shared. Keep attributes prevent synthesis from merging the
intended replicas. This adds exactly 68 explicit data flip-flops at 5x8 and
76 at 8x5 relative to the stride-two RTL, versus duplicating all operand
bits and valids as full-local does. Adding those counts to the previously
observed stride-two synthesis DFF totals predicts 1,899 versus 2,284 local
DFFs at 5x8, and 1,872 versus 2,232 at 8x5. Actual synthesis counts, not
these predictions, control the diagnostic gate.

## Fixed diagnostic corpus

Route only the candidate on the already-opened 5x8 and 8x5 shapes, on
NanGate45 and Sky130HD, at the already-opened seeds 53, 71 and 89: 12 routes.
Use the same immutable OpenROAD-flow-scripts image, platform corners, 20 ns
constraint, utilization, density, CAP/SLEW margins and final parsers as the
completed experiment. Reuse its published broadcast, full-local and
stride-two rows as fixed comparators. Before routing, compare signed GEMM
outputs with full-local on both shapes. No new geometry or seed is opened.

The candidate warrants a separate confirmatory preregistration only if every
condition below passes:

1. Functional equivalence passes on 5x8 and 8x5.
2. Exactly 12 unique candidate attempts exist and all 12 final routes are
   setup/hold/slew/fanout/capacitance/DRC clean with complete evidence.
3. All four platform/shape groups have all three matched seeds.
4. On every route, candidate DFFs are greater than stride-two but no more
   than 90% of full-local; candidate synthesis cell area is below full-local.
5. Each group has at least 5% median raw period benefit versus broadcast and
   retains at least 70% of the full-local period benefit.
6. Candidate period-times-synthesis-area beats both broadcast and full-local
   in at least three of four groups, with a win on each platform.
7. The targeted NanGate45 8x5 group improves median final period by at least
   0.02 ns relative to stride-two.

These thresholds are a continue/stop rule for research allocation, not a
scientific confirmation. A pass cannot be called a breakthrough. A failure
is published and the candidate stops; no seed is replenished and no gate is
weakened. If it passes, all shapes and seeds used in every earlier ASIC
study remain excluded. A new intervention, evaluator, fresh geometries and
fresh seeds must be frozen on main before a new confirmatory route starts.
