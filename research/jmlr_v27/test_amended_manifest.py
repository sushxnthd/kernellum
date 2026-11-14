#!/usr/bin/env python3
from generate_amended_manifest import build, QM_TARGETS

cells, tier_a = build()
assert len(cells) == 90
assert len({c["run_id"] for c in cells}) == 90
assert {c["method"] for c in cells if c["benchmark"] == "nyuv2"} == {"ls","mgda","nashmtl"}
assert {c["arm"] for c in cells if c["benchmark"] == "qm9"} == {"coarse","exposed","canonicalized"}
assert all(c["parent_target_id"] == 0 for c in cells if c["benchmark"] == "qm9")
assert tier_a["qm9"]["dose_parent_positions"] == [QM_TARGETS.index(0), QM_TARGETS.index(2), QM_TARGETS.index(12)]
assert tier_a["nyuv2"]["audit_epochs"] == [0,49,99,149,199]
assert tier_a["qm9"]["audit_epochs"] == [0,74,149,224,299]
print("PASS: amended manifest invariants")
