# Profile-critical-root transfer protocol (frozen before outcomes)

## Active KERNELLUM kernel

**Question.** Does the positive structural-start mechanism transfer from the
handcrafted FTrig factor lattice to an unrelated, classical nonlinear
least-squares problem when the exploitable structure is different?

**External system.** Freudenstein--Roth is used exactly as a two-residual
least-squares benchmark:

\[
r_1(x,y)=x-13+5y^2-y^3-2y,\qquad
r_2(x,y)=x-29+y^3+y^2-14y.
\]

The benchmark predates and is unrelated to FTrig. Its two minima are not used
to construct the candidate starts.

**Pre-solver diagnostic.** Both residuals are affine in `x` with the same
coefficient. Eliminate `x` exactly:

\[
x_*(y)=-\tfrac12(p_1(y)+p_2(y)),\qquad
V(y)=\tfrac12(p_1(y)-p_2(y))^2.
\]

Enumerate all real roots of `V'(y)`, retain only roots with positive profile
curvature, and lift each retained root to `(x_*(y),y)`. This is a different
certificate from residual-factor Cartesian products: it is conditional linear
elimination followed by exact univariate critical-root classification.

## Frozen prediction and objective

The diagnostic will emit exactly two strict-minimum candidates. With an
equal two-local-solve budget, those candidates will recover both distinct
strict minima under the identity problem and eight fixed affine coordinate
metamorphs. Random, Latin-hypercube, and a fixed maximin two-point control will
not achieve two-minimum coverage in every matched trial.

- Domain for generic controls: `x in [-20,20]`, `y in [-5,5]` in latent
  coordinates.
- Confirmation transform seed: `20261020`.
- Random/LHS repetitions: 64 per problem regime.
- A catastrophe is failure to recover both independently verified strict
  minima with the two-start budget.
- Ordinary performance is retaining the lowest objective found by the
  structured candidates.

## Gates

**Success.** Two certified candidates; complete coverage and the lowest
objective in every structured trial; strictly fewer catastrophes than every
matched generic control; independent algebra/Hessian audit passes.

**Failure.** Kill this transfer if the candidate count is not two, any
structured regime misses a strict minimum, any candidate is not a strict
minimum, or a simple control achieves universal coverage.

**Publishable threshold.** This is external transfer 1 of 2 required by the
parent FTrig protocol. Even a pass is not a general solver-instability
breakthrough. A second unrelated external system and a priority audit remain
mandatory.

**Project consequence.** On a pass, generalize KERNELLUM's guarded structural
start synthesizer from factor-root lattices to a second certificate:
shared-affine-variable elimination plus real critical-root classification.
Fail closed outside the certified form.

## Strongest alternative explanation

The method may simply be classical variable projection plus polynomial root
enumeration on a tiny benchmark. That explanation is accepted as the priority
boundary: the scientific question here is prospective transfer and system
scope, not mathematical novelty.
