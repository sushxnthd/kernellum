from __future__ import annotations

import json
from pathlib import Path


def post_route_fmax_mhz(report_path: str | Path) -> float:
    """Return the slowest achieved clock from nextpnr's final report JSON."""
    data = json.loads(Path(report_path).read_text())
    values = [
        float(item["achieved"])
        for item in data.get("fmax", {}).values()
        if item.get("achieved") is not None
    ]
    if not values:
        raise ValueError("nextpnr post-route report contains no achieved Fmax")
    return min(values)

