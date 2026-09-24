# SIMILARITY: a lower-register transport candidate

Status: RTL and functional preflight, no routed performance claim.

## Design question

Full registered-local operand transport improved raw routed timing in the
ECP5 study, but added about 70% more flip-flops in the deployment corpus.
The ASIC archive also shows that faster raw period does not imply better
cell-area-normalized throughput in every clean pair. A stride-two transport
places one registered operand stage per two PE positions along each axis.
Each such stage serves at most two adjacent PEs.

For an R-by-C array, the operand-network group registers have
`R*ceil(C/2) + C*ceil(R/2)` data words, compared with `2*R*C` for
full local transport. Edge skew and valid registers also contribute;
these formulas are not total synthesis-cell counts. The compiler should
choose stride from measured timing *and* cost, not register count alone.

The functional invariant is explicit: operands for PE(r,c) arrive after
`floor(r/2) + floor(c/2) + 1` registered group stages from the same
input time step. A and B use complementary edge skew. The accumulator
therefore sees matching signed products despite the different schedule.

## Preflight and scientific firewall

The initial preflight checks two independent signed-GEMM transactions,
including clearing between them, against both broadcast and full local
implementations on six even/odd and transposed geometries. It is a
functional test only. No area, frequency, power or breakthrough follows
from an RTL pass.

The prior ASIC flow's 7x7 canary must finish clean before a new physical
study begins. Then freeze the entire physical matrix and all gates before
routing any new shape: same pinned image and final-report parser, the
qualified repair margins, both original topologies and stride two, explicit
discovery/holdout split, new seeds, complete electrical checks, and
paired cost and timing metrics. The principal target is whether stride two
can recover most of full-local raw period benefit with a smaller area
penalty and improve area-normalized throughput on *unseen* geometries.
Negative outcomes will be retained.

Prior work on registered relays failed to recover the ECP5 local benefit;
see `docs/SIMILARITY_RELAY_HIERARCHY_REPORT.md`. This is a different
communication graph and requires independent physical evidence. None of
the old routes are confirmation data for this new candidate.
