# Adversarial boundary generator implementation addendum

**Frozen before any manifest execution:** 16 October 2026  
**Parent protocol:** `5d070a33ef124874c5e4c1db4b1cd838050e136b`

This addendum resolves one wording ambiguity in the parent protocol without
changing data, thresholds, perturbations, ranking features, caps, or gates.

The parent says a boundary event may include a change in the lower-CV solver
while also referring to “adjacent eligible perturbations.” Because eligibility
already requires the independent solver to have lower CV, that reading would
make the lower-solver clause vacuous.

The executable definition is therefore:

> For grid point `j`, compare against the immediately preceding successfully
> fitted grid point `j-1`, whether or not that predecessor is eligible. Mark a
> boundary event if either solver’s winning sign/family changes or the identity
> of the lower-CV solver changes. Only after boundary flags are computed, filter
> to points where independent has lower CV and apply the frozen ranking.

This is the only interpretation under which every preregistered boundary clause
can operate. No manifests or extrapolation outcomes existed when this
clarification was committed.

The generator is:
`scripts/generate_adversarial_boundary_manifest.py`.

Each of the four bases is executed independently and contributes its first six
eligible ranked cases. With exactly four bases and a cap of six per base, this
is algebraically identical to selecting 24 cases under the parent global cap;
the global lexicographic order affects presentation but not membership.
