# Frozen NIST transfer and certified-fit check

Use the unchanged additive-response predictor from public freeze
f606378c8c474d40b803330af322491956b313c9. No result from this check changes it.
Freeze this protocol and runner publicly before comparative prediction scores.
The datasets were selected for their publicly described exponential or rational
regression families, including clear model mismatch. This is a targeted
external transfer check, not an unselected benchmark or SOTA comparison.

Six NIST StRD datasets: Eckerle4, Gauss1, Gauss2, Lanczos3, Hahn1 and Bennett5.
Eckerle4 is observed circular-interference transmittance; Hahn1 is observed
copper thermal expansion; other provenance is preserved in the retrieved NIST
headers. Exact numeric rows, source URLs and extraction hashes are saved in
experiments/additive_response/nist_data. NIST URLs were accessed through the
web retrieval service because direct shell downloads returned HTTP 403.
The saved source text is line-indexed web extraction rather than wire-identical
original .dat bytes. Numeric row counts are checked against the source headers.

Ten predetermined seeds 104401..104410. Coverage selection uses the entire
unlabeled x pool with eight initial random points and budget min(64, n//2).
Each method receives exactly those labels; all remaining rows are held out.
No extra noise is added. Test NMSE measures prediction of held-out measured
responses, including their existing noise, rather than latent noiseless truth.
Repeated splits overlap; do not treat sixty paths as independent physical
experiments. Holdouts enter no fitting, initialization or model selection.

Eight methods match the expanded synthetic test. Frozen primary is augmented
adaptive. Report all 60 paths × 8 methods = 480 scores, geometric ratios with
the existing 1e-8 floor, per-dataset wins, worst raw NMSE, failures and selections.
Transfer criterion: <=.8 geometric ratio versus original adaptive and wins on
at least 4/6 datasets. Other comparisons and regressions remain visible even
if this restricted criterion passes. This criterion does not replace the
general synthetic or scoped Gaussian criteria.

A separate numerical diagnostic fits the positive concave exponential to all
35 Eckerle4 observations and checks the known NIST certified solution:
b1=1.5543827178, b2=4.0888321754, b3=451.54121844,
residual sum of squares=0.0014635887487. Demand RSS relative error <=1e-6 and
parameters relative error <=1e-5. This diagnostic is a third-party numerical
reference check, not a held-out prediction result or external reproduction.
It is isolated from every predictive split and performed after those fits.

Data-source reference:
https://www.itl.nist.gov/div898/strd/nls/data/LINKS/DATA/Eckerle4.dat
and the corresponding NIST URLs saved per dataset in the extraction manifest.
Prior knowledge of these model forms is disclosed; no claim of novel Gaussian
regression is supported by recovering a certified nonlinear fit.
