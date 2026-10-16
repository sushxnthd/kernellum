# Sign-anchor shifted study: first-run infrastructure failure

The frozen workflow at commit `69ff070bb2464d0584e030794f8a7ebf14f6cd6b`
stopped before writing a decision table or evaluating any test outcome.

Failure: one candidate leave-one-out nonlinear refit raised
`FloatingPointError: nonlinear optimizer failed`. The research runner treated a
single model attempt failure as fatal, whereas Kernellum's production model
bank records failed model attempts and selects among the remaining valid
sign/family models.

Correction boundary: wrap each frozen sign/family attempt independently,
record failures, and require at least one valid model in each candidate,
independent, and globalized bank for every path. No data, seeds, noise,
controls, arbitration rule, metric, threshold, or gate changes. The failed run
remains at https://github.com/sushxnthd/kernellum/actions/runs/38492645773.
