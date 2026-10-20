#!/usr/bin/env python3
"""Cross-host comparison of scientific invariants, not float serialization."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


def main(expected_path: str, actual_path: str) -> None:
    expected = json.loads(Path(expected_path).read_text())
    actual = json.loads(Path(actual_path).read_text())
    checks = []
    checks.append(("source provenance", expected["source"] == actual["source"]))
    checks.append(("prediction", expected["frozen_prediction"] == actual["frozen_prediction"]))
    erows, arows = expected["records"], actual["records"]
    checks.append(("record count", len(erows) == len(arows)))
    for e, a in zip(erows, arows):
        label = f"{e['method']}/transform-{e['transform_id']}"
        checks.append((label + " identity",
                       (e["method"], e["seed"], e["transform_id"], e["split"], e["starts"]) ==
                       (a["method"], a["seed"], a["transform_id"], a["split"], a["starts"])))
        checks.append((label + " basin count", e["distinct_minima"] == a["distinct_minima"]))
        checks.append((label + " best objective",
                       np.isclose(e["best_objective"], a["best_objective"], rtol=1e-10, atol=1e-9)))
        checks.append((label + " evaluation stability",
                       abs(e["nfev"] - a["nfev"]) <= max(3, int(0.03 * e["nfev"]))))
    for label, passed in checks:
        if not passed:
            print("FAIL", label)
    print(f"{sum(p for _, p in checks)}/{len(checks)} cross-host invariants pass")
    if not all(p for _, p in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
