#!/usr/bin/env python3
"""Generate the pre-outcome v27 amended benchmark manifest.

Historical v26 manifest is untouched. This file encodes only the explicitly
recorded 2026-11-14 feasibility amendment.
"""
from __future__ import annotations
import json
from pathlib import Path

SEEDS = range(5)
NY_METHODS = (
    ("ls", False, "linear"),
    ("mgda", True, "canonical-invariant"),
    ("nashmtl", False, "power-equilibrium"),
)
NY_PARENTS = {0: "segmentation", 1: "depth", 2: "normals"}
QM_TARGETS = [0, 1, 2, 3, 5, 6, 12, 13, 14, 15, 11]
NY_AUDIT_EPOCHS = [0, 49, 99, 149, 199]
QM_AUDIT_EPOCHS = [0, 74, 149, 224, 299]

def rid(*parts):
    return "__".join(str(x) for x in parts)

def build():
    cells = []
    for method, canonical_mgda, response_class in NY_METHODS:
        for seed in SEEDS:
            common = dict(
                tier="B",
                benchmark="nyuv2",
                method=method,
                canonical_mgda=canonical_mgda,
                response_class=response_class,
                seed=seed,
                epochs=200,
                batch_size=2,
                lr=1e-4,
                model="mtan",
                source_revision="OptMN-Lab/FairGrad@b58bce810e57288f7bf2c4c9effb7133b856739a",
            )
            cells.append(common | dict(
                run_id=rid("nyu", method, "canon" if canonical_mgda else "released", seed, "coarse"),
                arm="coarse", parent=0, parent_name="segmentation", k=4,
            ))
            for parent, parent_name in NY_PARENTS.items():
                cells.append(common | dict(
                    run_id=rid("nyu", method, "canon" if canonical_mgda else "released", seed, "exposed", parent, 4),
                    arm="exposed", parent=parent, parent_name=parent_name, k=4,
                ))
            cells.append(common | dict(
                run_id=rid("nyu", method, "canon" if canonical_mgda else "released", seed, "canonicalized", 0, 4),
                arm="canonicalized", parent=0, parent_name="segmentation", k=4,
            ))

    for seed in SEEDS:
        common = dict(
            tier="B",
            benchmark="qm9",
            method="nashmtl",
            canonical_mgda=False,
            response_class="power-equilibrium",
            seed=seed,
            epochs=300,
            batch_size=120,
            lr=1e-3,
            parent=0,
            parent_target_id=QM_TARGETS[0],
            parent_name="target_id_0",
            k=4,
            source_revision="OptMN-Lab/FairGrad@b58bce810e57288f7bf2c4c9effb7133b856739a",
            normalization="released_full_storage_path",
        )
        for arm in ("coarse", "exposed", "canonicalized"):
            cells.append(common | dict(
                run_id=rid("qm9", "nashmtl", seed, arm, 0, 4),
                arm=arm,
            ))

    tier_a = {
        "nyuv2": {
            "source_runs": [
                rid("nyu", "ls", "released", seed, "coarse") for seed in SEEDS
            ],
            "audit_epochs": NY_AUDIT_EPOCHS,
            "methods": ["ls", "mgda_released", "mgda_canonical", "cagrad", "nashmtl", "fairgrad_alpha2"],
            "parents": list(NY_PARENTS),
            "k": [2, 4, 8],
        },
        "qm9": {
            "source_runs": [
                rid("qm9", "nashmtl", seed, "coarse", 0, 4) for seed in SEEDS
            ],
            "audit_epochs": QM_AUDIT_EPOCHS,
            "methods": ["ls", "mgda_released", "mgda_canonical", "cagrad", "nashmtl", "fairgrad_alpha2"],
            "main_k4_parent_positions": list(range(len(QM_TARGETS))),
            "dose_target_ids": [0, 2, 12],
            "dose_parent_positions": [QM_TARGETS.index(x) for x in (0, 2, 12)],
            "dose_k": [2, 8],
        },
    }

    ids = [c["run_id"] for c in cells]
    assert len(cells) == 90, len(cells)
    assert len(ids) == len(set(ids)), "duplicate run IDs"
    assert sum(c["benchmark"] == "nyuv2" for c in cells) == 75
    assert sum(c["benchmark"] == "qm9" for c in cells) == 15
    assert sum(c["canonical_mgda"] for c in cells) == 25
    return cells, tier_a

def main():
    cells, tier_a = build()
    out = Path(__file__).with_name("AMENDED_MANIFEST_V27.jsonl")
    out.write_text("\n".join(json.dumps(x, sort_keys=True) for x in cells) + "\n")
    plan = Path(__file__).with_name("TIER_A_AUDIT_PLAN_V27.json")
    plan.write_text(json.dumps(tier_a, indent=2, sort_keys=True) + "\n")
    print(f"PASS: {len(cells)} Tier-B cells (75 NYUv2, 15 QM9), unique IDs")
    print(f"wrote {out}")
    print(f"wrote {plan}")

if __name__ == "__main__":
    main()
