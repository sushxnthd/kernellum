#!/usr/bin/env python3
"""Independent arithmetic and evidence audit of the opened B-local route ZIPs.

Reads the original eight Actions artifacts. It does not import the frozen
candidate evaluator, so agreement is a separate implementation check.
"""

import argparse
import csv
import hashlib
import json
import re
import statistics
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path


SHA = "f2b2c59fb75e1753e49c3f99e488cc5bf91855f5"
SEEDS = {53, 71, 89}
SHAPES = {(5, 8): 1979, (8, 5): 1972}
PLATFORMS = {"nangate45", "sky130hd"}
VIOLATIONS = ("setup_violations", "hold_violations", "max_slew_violations",
              "max_fanout_violations", "max_cap_violations", "drc_count")


def read_rows(root, pattern):
    return [row for path in sorted(root.rglob(pattern))
            for row in csv.DictReader(path.open(newline="", encoding="utf-8"))]


def key(row):
    return (row["platform"], int(row["seed"]), int(row["rows"]), int(row["cols"]))


def med(rows, field):
    return statistics.median(row[field] for row in rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--artifacts", type=Path, required=True)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--prior", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    files = sorted(args.artifacts.glob("*.zip"))
    assert len(files) == 8, f"expected eight original ZIPs, got {len(files)}"
    digests = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for artifact in files:
            with zipfile.ZipFile(artifact) as archive:
                assert all(not Path(n).is_absolute() and ".." not in Path(n).parts
                           for n in archive.namelist())
                archive.extractall(root)
        assert (root / "source_sha.txt").read_text().strip() == SHA
        assert "KERNELLUM_BLOCAL_EQUIVALENCE_PASS rows=5 cols=8" in (root / "tb_5x8.log").read_text()
        assert "KERNELLUM_BLOCAL_EQUIVALENCE_PASS rows=8 cols=5" in (root / "tb_8x5.log").read_text()
        assert (root / "similarity_blocal_functional_passed").exists()

        candidates = read_rows(root, "similarity_blocal_*.csv")
        prior = {key(row): row for row in read_rows(args.prior, "similarity_criticalbit_*.csv")}
        references = {(key(row), row["topology"]): row
                      for row in read_rows(args.baseline, "similarity_stride2_*.csv")}
        expected = {(platform, seed, *shape) for platform in PLATFORMS
                    for seed in SEEDS for shape in SHAPES}
        assert len(candidates) == 12 and {key(row) for row in candidates} == expected
        assert len({key(row) for row in candidates}) == 12
        summary_path = root / "similarity_blocal_summary.json"
        summary = json.loads(summary_path.read_text())
        assert summary["attempted"] == summary["clean"] == summary["complete_matched_sets"] == 12

        reports = list(root.rglob("6_finish.rpt"))
        drcs = list(root.rglob("5_route_drc.rpt"))
        assert len(reports) == len(drcs) == 12
        assert all(not f.read_bytes() for f in drcs), "nonempty DRC report"
        path_evidence = {}
        for f in reports:
            hit = re.search(r"(nangate45|sky130hd)/blocal/s(\d+)/r(\d+)_c(\d+)/reports/6_finish.rpt$", f.as_posix())
            assert hit
            platform, seed, rows, cols = hit.groups()
            report = f.read_text()
            assert "finish report_checks -path_delay min" in report
            section = report.split("finish report_checks -path_delay max", 1)[1]
            start = re.search(r"Startpoint: (.+)", section)
            end = re.search(r"Endpoint: (.+)", section)
            q = re.search(r"^\s*(\d+)\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+[\^v]\s+.*?/Q\s+\(", section, re.M)
            assert start and end and q, f"unreadable critical path {f}"
            path_evidence[(platform, int(seed), int(rows), int(cols))] = (start.group(1), end.group(1), int(q.group(1)))
        assert set(path_evidence) == expected
        for path in summary["critical_paths"]:
            assert path_evidence[(path["platform"], path["seed"], path["rows"], path["cols"])] == (
                path["startpoint"], path["endpoint"], path["launch_q_fanout"])

        groups = defaultdict(list)
        for row in candidates:
            k = key(row)
            assert row["topology"] == "blocal" and row["split"] == "opened_diagnostic"
            assert row["attempted"] == row["route_ok"] == "True"
            assert all(int(row[field]) == 0 for field in VIOLATIONS), k
            b, l, s = (references[k, t] for t in ("broadcast", "local", "stride2"))
            n = prior[k]
            bp, lp, sp, np, cp = (float(x["period_min_ns"]) for x in (b, l, s, n, row))
            ba, la, ca = (float(x["cell_area_um2"]) for x in (b, l, row))
            assert bp > lp
            assert int(row["dff_cells"]) == SHAPES[k[2:]]
            assert int(row["dff_cells"]) <= .9 * int(l["dff_cells"])
            assert ca < la
            groups[(k[0], k[2], k[3])].append({
                "period_ns": cp, "q": (bp-cp)/bp, "retention": (bp-cp)/(bp-lp),
                "density_b": bp*ba/(cp*ca), "density_l": lp*la/(cp*ca),
                "stride_ns": sp, "noop_ns": np,
            })
        assert len(groups) == 4 and all(len(v) == 3 for v in groups.values())
        points = []
        for k, rows in sorted(groups.items()):
            m = {field: med(rows, field) for field in rows[0]}
            m.update(platform=k[0], rows=k[1], cols=k[2])
            points.append(m)
        target = next(x for x in points if (x["platform"], x["rows"], x["cols"]) == ("nangate45", 8, 5))
        fanouts = [path_evidence[("nangate45", seed, 8, 5)][2] for seed in sorted(SEEDS)]
        density_wins = [x for x in points if x["density_b"] > 1 and x["density_l"] > 1]
        gates = {
            "complete_functional_electrical_cost_evidence": True,
            "all_groups_q_at_least_5pct": all(x["q"] >= .05 for x in points),
            "all_groups_retention_at_least_70pct": all(x["retention"] >= .70 for x in points),
            "three_joint_density_wins_both_platforms": len(density_wins) >= 3 and
                {x["platform"] for x in density_wins} == PLATFORMS,
            "target_improves_stride_by_0p04ns": target["period_ns"] <= target["stride_ns"]-.04,
            "target_improves_noop_by_0p02ns": target["period_ns"] <= target["noop_ns"]-.02,
            "target_median_launch_q_fanout_at_most_10": med([{"f": x} for x in fanouts], "f") <= 10,
        }
        assert all(gates.values()), gates
        assert all(summary["gates"].values()) and summary["prospective_study_warranted"]
        result = {"status": "EXPLORATORY_PASS_NOT_CONFIRMATION", "source_sha": SHA,
                  "original_zip_sha256": digests,
                  "summary_sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
                  "attempts": 12, "clean_routes": 12, "reports": len(reports),
                  "fanouts_nangate45_8x5": fanouts, "gates": gates, "groups": points}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"status": result["status"], "gates": gates}, indent=2))


if __name__ == "__main__":
    main()
