import json
from pathlib import Path

from kernellum.compiler import search_architecture
from kernellum.pnr_feedback import load_feedback, parse_nextpnr_report, write_feedback


def test_parse_nextpnr_report_and_feedback_search(tmp_path: Path):
    report = {
        "fmax": {"clk": {"achieved": 86.5, "constraint": 100.0}},
        "utilization": {
            "TRELLIS_SLICE": {"used": 4200, "available": 41820},
            "MULT18X18D": {"used": 4, "available": 156},
        },
    }
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report))

    point = parse_nextpnr_report(report_path, lanes=4)
    assert point.lanes == 4
    assert point.cycles == 680
    assert point.achieved_fmax_mhz == 86.5
    assert point.board_clock_core_latency_us == 27.2
    assert point.slices_used == 4200
    assert point.multipliers_used == 4

    feedback_path = tmp_path / "feedback.json"
    write_feedback([point], feedback_path)
    feedback = load_feedback(feedback_path)
    selected, _ = search_architecture(
        (64, 32, 16, 10),
        implementation_feedback=feedback,
    )
    assert selected["lanes"] == 4
    assert selected["latency_source"] == "post_route_fmax"


def test_feedback_can_change_selected_lane_count():
    feedback = {
        4: {"achieved_fmax_mhz": 50.0, "slices_used": 4000, "multipliers_used": 4},
        8: {"achieved_fmax_mhz": 95.0, "slices_used": 6200, "multipliers_used": 8},
    }
    selected, candidates = search_architecture(
        (64, 32, 16, 10),
        implementation_feedback=feedback,
    )
    assert selected["lanes"] == 8
    by_lane = {candidate["lanes"]: candidate for candidate in candidates}
    assert not by_lane[4]["meets_latency"]
    assert by_lane[8]["meets_latency"]
