# One-point disagreement acquisition: pre-outcome implementation addendum

**Frozen:** 16 October 2026, before any acquisition outcome was joined.

The acquired candidate point is excluded from that method's post-acquisition
evaluation batch. Thus each acquired method is scored on the remaining 255
points in its cell. This prevents a training point from receiving automatic
zero-error credit. No-acquisition remains scored on all 256 points because it
has not observed any requested-batch response.

Geometric NMSE uses the variance of the corresponding 255-point or 256-point
truth vector. Catastrophe remains log-NMSE greater than 5. This clarification
does not alter selection rules, controls, solvers, thresholds, or gates.
