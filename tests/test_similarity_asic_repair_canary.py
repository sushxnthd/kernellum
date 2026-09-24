from scripts.similarity_asic_repair_canary import evaluate


def row(platform, topology, seed, max_cap=0):
    return {
        "platform": platform, "topology": topology, "seed": str(seed),
        "rows": "7", "cols": "7", "route_ok": "True",
        "setup_violations": "0", "hold_violations": "0",
        "max_slew_violations": "0", "max_fanout_violations": "0",
        "max_cap_violations": str(max_cap), "drc_count": "0",
        "gds_sha256": "a", "odb_sha256": "b",
        "spef_sha256": "c", "netlist_sha256": "d",
    }


def test_complete_clean_matrix_passes():
    rows = [row(p, t, s) for p in ("nangate45", "sky130hd")
            for t in ("broadcast", "local") for s in (11, 29, 47)]
    assert evaluate(rows)["all_final_routes_electrically_clean"]
    rows[0]["max_cap_violations"] = "1"
    assert not evaluate(rows)["all_final_routes_electrically_clean"]
    rows[0]["max_cap_violations"] = "0"
    assert not evaluate(rows[:-1])["all_final_routes_electrically_clean"]
    assert not evaluate(rows + rows[:1])["all_final_routes_electrically_clean"]
