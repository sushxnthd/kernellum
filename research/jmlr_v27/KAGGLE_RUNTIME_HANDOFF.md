# JMLR Project Zero v27 — Kaggle runtime-calibration handoff

This handoff is **runtime-only**. It must not launch any Tier-A/Tier-B outcome-bearing benchmark cell.

## User action

1. Open the authenticated Kaggle notebook created for this campaign.
2. In Notebook settings, enable the fastest available NVIDIA GPU and enable Internet.
3. Paste the single cell below and run it.

```bash
%%bash
set -euo pipefail
rm -rf /kaggle/working/kernellum
git clone -q -b research/jmlr-v27-completion https://github.com/sushxnthd/kernellum.git /kaggle/working/kernellum

python /kaggle/working/kernellum/research/jmlr_v27/kaggle_bootstrap.py \
  --work-root /kaggle/working \
  --download-nyuv2

python /kaggle/working/kernellum/research/jmlr_v27/runtime_probe.py \
  --fairgrad-root /kaggle/working/fairgrad_v27 \
  --nyuv2-data /kaggle/working/nyuv2 \
  --output-root /kaggle/working/jmlr_v27_runtime_probes
```

## Required outputs

Do not interpret model metrics from these one-epoch runs. Only inspect:
- `/kaggle/working/jmlr_v27_environment.json`
- `/kaggle/working/jmlr_v27_runtime_probes/runtime_probe_summary.json`
- runtime probe logs if any probe fails

The environment record must show CUDA available and record the actual GPU/PyTorch/CUDA/PyG/CVXPY/ECOS versions.

## Stop condition

After the runtime probes finish, **stop**. Do not run `run_amended_batch.py` yet.

The runtime measurements are used to decide whether the currently frozen 90-cell Tier-B amendment is computationally feasible. If it is not, a final pre-outcome amendment must be committed to GitHub issue #120 and the branch before any eligible standard-benchmark cell is launched.

## Outcome-bearing command

Intentionally omitted from this handoff. It is released only after runtime feasibility is adjudicated.
