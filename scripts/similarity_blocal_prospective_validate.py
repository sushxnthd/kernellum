#!/usr/bin/env python3
"""All-required frozen gates for unopened B-local physical confirmations."""

import argparse
import csv
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

from scripts.similarity_asic_transfer_route import FIELDS
from scripts.similarity_blocal_prospective_route import GEOMETRIES, PLATFORMS, SEEDS, TOPOLOGIES
from scripts.similarity_stride2_validate import good_route

ROOT = Path(__file__).resolve().parents[1]


def identity(row):
    return (row["platform"], row["topology"], int(row["seed"]),
            int(row["rows"]), int(row["cols"]))


def path_evidence(root):
    paths = []
    expected = {(p, t, s, r, c) for p in PLATFORMS for t in TOPOLOGIES
                for s in SEEDS for _, r, c in GEOMETRIES}
    pattern = re.compile(r"(nangate45|sky130hd)/(broadcast|local|blocal)/s(101|131|157)/r(6|8|9)_c(6|8|9)/reports/6_finish.rpt$")
    for path in root.rglob("6_finish.rpt"):
        match = pattern.search(path.as_posix())
        if not match:
            continue
        platform, topology, seed, rows, cols = match.groups()
        key = platform, topology, int(seed), int(rows), int(cols)
        if key not in expected:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        parts = text.split("finish report_checks -path_delay max", 1)
        if len(parts) != 2:
            continue
        start = re.search(r"Startpoint: (.+)", parts[1])
        endpoint = re.search(r"Endpoint: (.+)", parts[1])
        launch = re.search(r"^\s*(\d+)\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+[\^v]\s+.*?/Q\s+\(", parts[1], re.M)
        paths.append({"platform": platform, "topology": topology,
                      "seed": int(seed), "rows": int(rows), "cols": int(cols),
                      "startpoint": start.group(1) if start else None,
                      "endpoint": endpoint.group(1) if endpoint else None,
                      "launch_q_fanout": int(launch.group(1)) if launch else None})
    return sorted(paths, key=lambda x: (x["platform"], x["topology"], x["seed"], x["rows"]))


def summarize(rows, functional, paths):
    expected = {(p, t, s, r, c) for p in PLATFORMS for t in TOPOLOGIES
                for s in SEEDS for _, r, c in GEOMETRIES}
    keys = [identity(row) for row in rows]
    exact = len(rows) == 72 and len(set(keys)) == 72 and set(keys) == expected
    clean = exact and all(row["attempted"].lower() == "true" and good_route(row)
                          for row in rows)
    lookup = {identity(row): row for row in rows if good_route(row)}
    matched = []
    for p in PLATFORMS:
        for split, r, c in GEOMETRIES:
            for s in SEEDS:
                trio = [lookup.get((p, t, s, r, c)) for t in TOPOLOGIES]
                if any(x is None for x in trio):
                    continue
                b, l, candidate = trio
                bp, lp, cp = [float(x["period_min_ns"]) for x in trio]
                ba, la, ca = [float(x["cell_area_um2"]) for x in trio]
                matched.append({
                    "platform": p, "split": split, "rows": r, "cols": c,
                    "seed": s, "broadcast_period_ns": bp,
                    "local_period_ns": lp, "blocal_period_ns": cp,
                    "q_local": (bp-lp)/bp, "q_candidate": (bp-cp)/bp,
                    "retention": (bp-cp)/(bp-lp) if bp>lp else None,
                    "density_vs_broadcast": bp*ba/(cp*ca),
                    "density_vs_local": lp*la/(cp*ca),
                    "broadcast_dffs": int(b["dff_cells"]),
                    "local_dffs": int(l["dff_cells"]),
                    "blocal_dffs": int(candidate["dff_cells"]),
                    "local_area_um2": la, "blocal_area_um2": ca,
                })
    groups = defaultdict(list)
    for row in matched:
        groups[(row["platform"], row["split"], row["rows"], row["cols"])].append(row)
    points = []
    for (p, split, r, c), group in sorted(groups.items()):
        if len(group) != 3:
            continue
        fields = ("broadcast_period_ns", "local_period_ns", "blocal_period_ns",
                  "q_local", "q_candidate", "density_vs_broadcast", "density_vs_local",
                  "local_dffs", "blocal_dffs", "local_area_um2", "blocal_area_um2")
        points.append({"platform": p, "split": split, "rows": r, "cols": c,
                       **{f"median_{field}": statistics.median(float(x[field]) for x in group)
                          for field in fields},
                       "median_retention": statistics.median(float(x["retention"]) for x in group
                                                              if x["retention"] is not None)
                       if all(x["retention"] is not None for x in group) else None})
    holdouts = [x for x in points if x["split"] == "holdout"]
    winners = [x for x in holdouts if x["median_density_vs_broadcast"] >= 1.01
               and x["median_density_vs_local"] >= 1.01]
    target_paths = [x for x in paths if x["platform"] == "nangate45"
                    and x["topology"] == "blocal" and (x["rows"],x["cols"]) in ((6,9),(9,6))]
    fanouts = defaultdict(list)
    for x in target_paths:
        if x["launch_q_fanout"] is not None:
            fanouts[(x["rows"],x["cols"])].append(x["launch_q_fanout"])
    all_reports = len(paths) == 72 and len({(x["platform"],x["topology"],x["seed"],x["rows"],x["cols"]) for x in paths}) == 72
    gates = {
        "signed_gemm_functional_on_all_four_shapes": functional,
        "exactly_72_unique_attempted_routes": exact and all(x["attempted"].lower()=="true" for x in rows),
        "all_72_final_routes_electrically_and_drc_clean": clean,
        "all_72_final_critical_path_reports_present": all_reports and all(x["startpoint"] and x["endpoint"] and x["launch_q_fanout"] is not None for x in paths),
        "all_eight_groups_three_complete_matched_seeds": len(points) == 8 and len(matched)==24,
        "full_local_positive_each_group": len(points)==8 and all(x["median_q_local"]>0 for x in points),
        "all_24_candidate_dffs_at_most_90pct_local_and_above_broadcast": len(matched)==24 and all(x["broadcast_dffs"]<x["blocal_dffs"]<=.9*x["local_dffs"] for x in matched),
        "all_24_candidate_synthesis_areas_below_local": len(matched)==24 and all(x["blocal_area_um2"]<x["local_area_um2"] for x in matched),
        "all_four_holdouts_raw_benefit_at_least_5pct": len(holdouts)==4 and all(x["median_q_candidate"]>=.05 for x in holdouts),
        "all_four_holdouts_retention_at_least_70pct": len(holdouts)==4 and all(x["median_retention"] is not None and x["median_retention"]>=.70 for x in holdouts),
        "holdout_joint_density_wins_at_least_3_of_4_at_1pct": len(winners)>=3,
        "holdout_joint_density_wins_on_both_platforms": all(any(x["platform"]==p for x in winners) for p in PLATFORMS),
        "nangate45_holdout_launch_q_fanout_at_most_10": len(fanouts)==2 and all(len(fanouts[shape])==3 and statistics.median(fanouts[shape])<=10 for shape in ((6,9),(9,6))),
    }
    return {"schema_version":1,"planned":72,"attempted":len(rows),
            "clean":sum(good_route(x) for x in rows),"matched":len(matched),
            "gates":gates,"frozen_claim_supported":all(gates.values()),
            "points":points,"matched_rows":matched,"critical_paths":paths,"raw_rows":rows}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,default=ROOT/"results/similarity_blocal_prospective_summary.json")
    args=p.parse_args()
    rows=[]
    for path in sorted(args.input.rglob("similarity_blocal_prospective_*.csv")):
        with path.open(newline="",encoding="utf-8") as handle:
            reader=csv.DictReader(handle)
            if reader.fieldnames != list(FIELDS):
                raise ValueError(f"route schema mismatch: {path}")
            rows.extend(reader)
    data=summarize(rows,any(args.input.rglob("similarity_blocal_prospective_functional_passed")),path_evidence(args.input))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2,allow_nan=False)+"\n")
    print(json.dumps({key:data[key] for key in ("planned","attempted","clean","matched","gates","frozen_claim_supported")},indent=2))
    return 0 if data["frozen_claim_supported"] else 1


if __name__=="__main__":
    raise SystemExit(main())
