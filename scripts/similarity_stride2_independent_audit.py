#!/usr/bin/env python3
"""Independently check the frozen stride-two gate against raw route archives.

Usage: python scripts/similarity_stride2_independent_audit.py \
    --archives /path/to/downloaded/action-zips \
    --summary results/similarity_stride2_summary.json

The 18 route ZIPs and functional ZIP must be from the *same* frozen run.
The actual GDS/ODB/SPEF/netlist bytes are not in those archives; their
recorded SHA-256 values cannot be independently rehashed here.
"""

import argparse
import csv
import io
import json
import math
import re
import statistics
import zipfile
from collections import defaultdict
from pathlib import Path

PLATFORMS = ("nangate45", "sky130hd")
TOPOLOGIES = ("broadcast", "local", "stride2")
SEEDS = (53, 71, 89)
SHAPES = (("discovery", 4, 7), ("discovery", 7, 4),
          ("holdout", 5, 8), ("holdout", 8, 5))
CSV_RE = re.compile(r"results/similarity_stride2_(nangate45|sky130hd)_"
                    r"(broadcast|local|stride2)_s(53|71|89)\.csv$")
VIOLATIONS = ("setup_violations", "hold_violations", "max_slew_violations",
              "max_fanout_violations", "max_cap_violations", "drc_count")


def must(test, message):
    if not test:
        raise AssertionError(message)


def report_number(pattern, text, description):
    match = re.search(pattern, text, re.MULTILINE)
    must(match is not None, f"missing {description}")
    return float(match.group(1))


def audit_report(zfile, row):
    p, t, s, r, c = (row["platform"], row["topology"], row["seed"],
                     row["rows"], row["cols"])
    root = f"build/similarity_stride2_study/{p}/{t}/s{s}/r{r}_c{c}/"
    finish = zfile.read(root + "reports/6_finish.rpt").decode()
    synth = zfile.read(root + "reports/synth_stat.txt").decode()
    drc = zfile.read(root + "reports/5_route_drc.rpt").decode().strip()
    route_log = zfile.read(root + "logs/5_2_route.log").decode()
    period = report_number(r"^clk period_min =\s*([0-9.]+)", finish, "period")
    area = report_number(r"Chip area for module '[^']+':\s*([0-9.eE+-]+)",
                         synth, "synthesis area")
    wire = list(re.finditer(r"^Total wire length =\s*([0-9.eE+-]+)\s+um\.",
                            route_log, re.MULTILINE))
    must(wire, f"missing wire length {p}/{t}/{s}/{r}x{c}")
    must(float(row["period_min_ns"]) == period, f"period mismatch {root}")
    must(float(row["cell_area_um2"]) == area, f"area mismatch {root}")
    must(float(row["wire_length_um"]) == float(wire[-1].group(1)),
         f"wire-length mismatch {root}")
    must(int(row["drc_count"]) == (len(drc.splitlines()) if drc else 0),
         f"DRC mismatch {root}")
    for label, field in (("setup", "setup_violations"),
                         ("hold", "hold_violations"),
                         ("max slew", "max_slew_violations"),
                         ("max fanout", "max_fanout_violations"),
                         ("max cap", "max_cap_violations")):
        value = report_number(rf"^{label} violation count\s+(\d+)\s*$",
                              finish, field)
        must(int(row[field]) == value, f"{field} mismatch {root}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archives", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    expected_shards = {(p, t, s) for p in PLATFORMS
                       for t in TOPOLOGIES for s in SEEDS}
    expected_rows = {(p, t, s, r, c) for p, t, s in expected_shards
                     for _, r, c in SHAPES}
    found_shards = set()
    records = {}
    functional = False
    source_sha = "0b3fd3c58385bd8158ac2e7bbad55cfdaa9be897"
    for path in args.archives.rglob("*.zip"):
        try:
            zfile = zipfile.ZipFile(path)
        except zipfile.BadZipFile:
            continue
        with zfile:
            names = zfile.namelist()
            matches = [name for name in names if CSV_RE.fullmatch(name)]
            if "similarity_stride2_functional_passed" in names:
                must(zfile.read("source_sha.txt").decode().strip() == source_sha,
                     "functional evidence from wrong source")
                for _, r, c in SHAPES:
                    log = zfile.read(f"tb_{r}x{c}.log").decode()
                    must(f"KERNELLUM_STRIDED_EQUIVALENCE_PASS rows={r} cols={c}"
                         in log, f"functional check missing for {r}x{c}")
                functional = True
            for name in matches:
                must(len(matches) == 1, f"multiple CSVs in {path}")
                match = CSV_RE.fullmatch(name)
                shard = (match.group(1), match.group(2), int(match.group(3)))
                must(shard not in found_shards, f"duplicate archive for {shard}")
                found_shards.add(shard)
                rows = list(csv.DictReader(io.StringIO(zfile.read(name).decode())))
                must(len(rows) == 4, f"bad row count {shard}")
                for row in rows:
                    key = (row["platform"], row["topology"], int(row["seed"]),
                           int(row["rows"]), int(row["cols"]))
                    must(key in expected_rows and key not in records,
                         f"missing/duplicate/wrong route key {key}")
                    must(key[:3] == shard, f"CSV row in wrong artifact {key}")
                    must(row["split"] == next(split for split, r, c in SHAPES
                                              if (r, c) == key[3:]),
                         f"incorrect split {key}")
                    must(row["route_ok"] == row["attempted"] == "True",
                         f"failed route {key}")
                    must(all(int(row[field]) == 0 for field in VIOLATIONS),
                         f"electrical/DRC failure {key}")
                    must(all(math.isfinite(float(row[field])) and float(row[field]) > 0
                             for field in ("period_min_ns", "cell_area_um2",
                                           "wire_length_um", "dff_cells", "total_cells")),
                         f"invalid cost {key}")
                    must(all(re.fullmatch(r"[0-9a-f]{64}", row[field])
                             for field in ("gds_sha256", "odb_sha256",
                                           "spef_sha256", "netlist_sha256")),
                         f"missing physical hash {key}")
                    audit_report(zfile, row)
                    records[key] = row
    must(found_shards == expected_shards, f"missing shards: {expected_shards-found_shards}")
    must(set(records) == expected_rows and len(records) == 72,
         "72-route matrix mismatch")
    must(functional, "functional artifact missing")
    summary = json.loads(args.summary.read_text())
    must(summary["attempted"] == summary["successful"] == summary["clean"] == 72,
         "summary count mismatch")
    must(summary["complete_triples"] == 24, "summary triple count mismatch")
    must(len(summary["all_raw_routes"]) == 72, "summary raw row count mismatch")
    must({(x["platform"], x["topology"], int(x["seed"]),
           int(x["rows"]), int(x["cols"])): x
          for x in summary["all_raw_routes"]} == records,
         "summary does not reproduce independent CSV contents")
    grouped = defaultdict(list)
    for p in PLATFORMS:
        for split, r, c in SHAPES:
            for s in SEEDS:
                b, l, t = [records[p, topology, s, r, c]
                           for topology in TOPOLOGIES]
                B, L, S = [float(x["period_min_ns"]) for x in (b, l, t)]
                Ab, Al, As = [float(x["cell_area_um2"]) for x in (b, l, t)]
                Db, Dl, Ds = [int(x["dff_cells"]) for x in (b, l, t)]
                must(B > L, f"full local failed to benefit {p}/{r}x{c}/s{s}")
                must(Db < Ds <= 0.9 * Dl, f"DFF gate failed {p}/{r}x{c}/s{s}")
                must(As < Al, f"area gate failed {p}/{r}x{c}/s{s}")
                grouped[p, r, c].append(((B-L)/B, (B-S)/B, (B-S)/(B-L),
                                          B*Ab/(S*As), L*Al/(S*As)))
    rows = []
    for (p, r, c), triples in sorted(grouped.items()):
        med = [statistics.median(t[i] for t in triples) for i in range(5)]
        rows.append((p, r, c, *med))
        point = next(x for x in summary["points"]
                     if (x["platform"], x["rows"], x["cols"]) == (p, r, c))
        for i, field in enumerate(("median_local_q", "median_stride2_q",
                                   "median_retained_benefit",
                                   "median_stride2_vs_broadcast_density",
                                   "median_stride2_vs_local_density")):
            must(math.isclose(med[i], point[field], rel_tol=1e-12),
                 f"summary median mismatch {p}/{r}x{c}/{field}")
    hold = [row for row in rows if (row[1], row[2]) in ((5, 8), (8, 5))]
    density = [row for row in hold if row[6] > 1 and row[7] > 1]
    checks = {
        "functional_equivalence": functional,
        "exactly_72_unique_attempts": len(records) == 72,
        "all_72_final_routes_clean": True,
        "all_eight_geometries_have_two_complete_seeds": len(grouped) == 8,
        "full_local_positive_on_all_eight": all(row[3] > 0 for row in rows),
        "stride2_transport_register_reduction": True,
        "stride2_area_below_full_local": True,
        "holdout_stride2_raw_benefit_at_least_5pct": all(row[4] >= .05 for row in hold),
        "holdout_retains_at_least_60pct_full_local_benefit": all(row[5] >= .60 for row in hold),
        "holdout_density_wins_at_least_three_of_four": len(density) >= 3,
        "holdout_density_win_on_each_platform": all(any(x[0] == p for x in density)
                                                    for p in PLATFORMS),
    }
    must(checks == summary["gates"], "independent gate vector differs")
    must(all(checks.values()) == summary["claim_supported"],
         "independent claim decision differs")
    print(json.dumps({"rows": len(records), "shards": len(found_shards),
                      "route_reports_checked": len(records),
                      "functional_shapes_checked": 4,
                      "gates": checks, "claim_supported": all(checks.values()),
                      "holdout_medians": hold}, indent=2))


if __name__ == "__main__":
    main()
