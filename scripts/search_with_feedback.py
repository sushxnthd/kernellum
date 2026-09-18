from __future__ import annotations

import argparse
import json
from pathlib import Path

from kernellum.compiler import search_architecture
from kernellum.pnr_feedback import load_feedback


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-run Kernellum architecture search using post-route feedback")
    parser.add_argument("--feedback", default="artifacts/digits_int8/pnr_ulx3s/implementation_feedback.json")
    parser.add_argument("--out", default="artifacts/digits_int8/pnr_ulx3s/feedback_search.json")
    parser.add_argument("--latency-us", type=float, default=10.0)
    args = parser.parse_args()

    feedback = load_feedback(args.feedback)
    selected, candidates = search_architecture(
        (64, 32, 16, 10),
        latency_target_us=args.latency_us,
        implementation_feedback=feedback,
    )

    payload = {
        "schema": "kernellum.feedback_search.v1",
        "evidence_level": "post-route implementation feedback; not physical measurement",
        "latency_target_us": args.latency_us,
        "selected": selected,
        "candidates": list(candidates),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
