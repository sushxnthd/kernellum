import json

import pytest

from kernellum.k1.routed_timing import post_route_fmax_mhz


def test_post_route_fmax_uses_slowest_achieved_clock(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(json.dumps({
        "fmax": {
            "clk": {"achieved": 91.25, "constraint": 25.0},
            "aux": {"achieved": 73.5, "constraint": 20.0},
        }
    }))
    assert post_route_fmax_mhz(report) == 73.5


def test_post_route_fmax_rejects_missing_measurement(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(json.dumps({"fmax": {"clk": {"achieved": None}}}))
    with pytest.raises(ValueError, match="no achieved Fmax"):
        post_route_fmax_mhz(report)

