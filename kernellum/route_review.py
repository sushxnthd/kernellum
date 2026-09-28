"""Offline decision report for the existing K1 INT8 GEMM architecture family.

This reviews supplied observations; it does not route designs or measure hardware.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import math
from pathlib import Path

from kernellum.k1.model import K1Architecture, predicted_cycles

VERSION = "0.1.0"
RESOURCES = ("dsp", "bram", "lut4", "ff")
REQUIRED = {"name", "rows", "cols", "k_tile", "synth_ok", "route_ok",
            "fmax_mhz", "timing_metric", "nextpnr_returncode"} | {
                "synth_" + r for r in RESOURCES}
BOUNDARY = (
    "K1 INT8 GEMM model only. Latency = modeled kernel cycles / supplied final-route Fmax. "
    "Resource counts are synthesis counts. No board timing, host I/O, model inference, "
    "power, new routing, functional verification, or customer savings were measured. "
    "Input labels are checked, but raw tool reports and RTL equivalence are not independently verified. "
    "Comparisons are descriptive over the supplied observations, not held-out validation."
)


def positive_int(value):
    try:
        n = int(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"expected positive integer, got {value!r}") from exc
    if str(n) != str(value).strip() or n <= 0:
        raise ValueError(f"expected positive integer, got {value!r}")
    return n


def count(value):
    n = float(value)
    if not math.isfinite(n) or n < 0 or not n.is_integer():
        raise ValueError(f"invalid resource count {value!r}")
    return int(n)


def review(paths, *, m, n, k, baseline, max_resources, min_observations=1):
    m, n, k = (positive_int(x) for x in (m, n, k))
    min_observations = positive_int(min_observations)
    limits = {r: count(max_resources[r]) for r in RESOURCES}
    sources, groups, errors, seen = [], {}, [], set()
    for path in map(Path, paths):
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest in seen:
            raise ValueError("duplicate input contents cannot count as new observations")
        seen.add(digest)
        sources.append({"file": path.name, "sha256": digest})
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        if not REQUIRED.issubset(reader.fieldnames or []):
            raise ValueError(f"{path.name}: missing columns {sorted(REQUIRED - set(reader.fieldnames or []))}")
        for line, row in enumerate(reader, 2):
            name = (row.get("name") or "").strip()
            if not name:
                raise ValueError(f"{path.name}:{line}: missing candidate name")
            g = groups.setdefault(name, {"name": name, "records": [], "reasons": [], "keys": set()})
            location = {"file": path.name, "source_sha256": digest, "line": line}
            try:
                if None in row or any(row[c] is None for c in REQUIRED):
                    raise ValueError("malformed CSV row")
                geometry = tuple(positive_int(row[c]) for c in ("rows", "cols", "k_tile"))
                transport = row.get("transport", "broadcast").strip()
                if transport not in ("broadcast", "local"):
                    raise ValueError("unknown transport")
                signature = (*geometry, transport)
                if "signature" in g and g["signature"] != signature:
                    raise ValueError("candidate name maps to conflicting architectures")
                g["signature"] = signature
                # Seed IDs must be explicit for repeated observations. Identical rows
                # and unlabeled repeats must not inflate the evidence count.
                seed = (row.get("seed") or "").strip()
                if seed in g["keys"]:
                    raise ValueError("duplicate seed or repeated unseeded observation")
                g["keys"].add(seed)
                if row["synth_ok"].lower() != "true" or row["route_ok"].lower() != "true":
                    raise ValueError("synthesis or routing failed")
                if row["nextpnr_returncode"].strip() != "0":
                    raise ValueError("nonzero router return code")
                if row["timing_metric"] != "post_route_report_json":
                    raise ValueError("timing is not labeled final post-route JSON")
                fmax = float(row["fmax_mhz"])
                if not math.isfinite(fmax) or fmax <= 0:
                    raise ValueError("Fmax must be finite and positive")
                resources = {r: count(row["synth_" + r]) for r in RESOURCES}
                g["records"].append({**location, "seed": seed or None,
                                     "fmax_mhz": fmax, "resources": resources})
            except (ValueError, TypeError, KeyError) as exc:
                reason = f"{path.name}:{line}: {exc}"
                g["reasons"].append(reason)
                errors.append({"candidate": name, **location, "reason": str(exc)})
    eligible, rejected = [], []
    for name, g in sorted(groups.items()):
        records = g["records"]
        reasons = g["reasons"]
        if len(records) < min_observations:
            reasons.append(f"requires {min_observations} observations; has {len(records)} valid")
        peak = {r: max((x["resources"][r] for x in records), default=0) for r in RESOURCES}
        reasons.extend(f"synthesis {r} {peak[r]} exceeds {limits[r]}" for r in RESOURCES if peak[r] > limits[r])
        if reasons:
            rejected.append({"name": name, "reasons": reasons})
            continue
        rows, cols, kt, transport = g["signature"]
        arch = K1Architecture(name, rows, cols, kt, transport)
        cycles = predicted_cycles(m, n, k, arch)
        fmax = min(x["fmax_mhz"] for x in records)
        eligible.append({"name": name, "rows": rows, "cols": cols, "k_tile": kt,
                         "transport": transport, "observations": len(records),
                         "worst_observed_fmax_mhz": fmax, "modeled_cycles": cycles,
                         "worst_observed_latency_ms": cycles / (fmax * 1000),
                         "peak_synthesis_resources": peak, "evidence": records})
    eligible.sort(key=lambda x: (x["worst_observed_latency_ms"], x["name"]))
    for a in eligible:
        av = [a["worst_observed_latency_ms"], *a["peak_synthesis_resources"].values()]
        a["pareto"] = not any(
            all(x <= y for x, y in zip(bv, av)) and any(x < y for x, y in zip(bv, av))
            for b in eligible if b is not a
            for bv in [[b["worst_observed_latency_ms"], *b["peak_synthesis_resources"].values()]]
        )
    base = next((x for x in eligible if x["name"] == baseline), None)
    best = eligible[0] if eligible else None
    return {
        "schema_version": VERSION, "evidence_kind": "descriptive_existing_route_review",
        "boundary": BOUNDARY,
        "workload": {"m": m, "n": n, "k": k, "precision": "signed INT8"},
        "limits": limits, "min_observations": min_observations, "sources": sources,
        "candidate_count": len(groups), "eligible_count": len(eligible),
        "status": "comparison_available" if base else "baseline_unavailable",
        "baseline": baseline, "baseline_eligible": base is not None,
        "best_supplied_candidate": best["name"] if best else None,
        "latency_reduction_vs_baseline_pct": (
            100 * (1 - best["worst_observed_latency_ms"] / base["worst_observed_latency_ms"])
            if base and best else None),
        "ranking": eligible, "rejected": rejected, "row_errors": errors,
        "aggregation": "minimum observed Fmax and maximum resource counts per candidate; any invalid row rejects its candidate",
        "sampling_note": "Seed sets and observation counts may differ. Worst observed is not a statistical guarantee or paired comparison.",
    }


def render_html(report):
    esc = lambda x: html.escape(str(x), quote=True)
    rows = "".join(
        "<tr>" + "".join(f"<td>{esc(v)}</td>" for v in (
            a["name"], f'{a["worst_observed_latency_ms"]:.4f}',
            f'{a["worst_observed_fmax_mhz"]:.2f}', a["observations"],
            *(a["peak_synthesis_resources"][r] for r in RESOURCES),
            "Yes" if a["pareto"] else "No")) + "</tr>" for a in report["ranking"])
    rejects = "".join(f'<li><b>{esc(a["name"])}</b>: {esc("; ".join(a["reasons"]))}</li>' for a in report["rejected"])
    reduction = report["latency_reduction_vs_baseline_pct"]
    comparison = (f"{reduction:.2f}% modeled latency reduction versus {report['baseline']}"
                  if reduction is not None else "No eligible baseline; no comparative improvement claimed")
    provenance = "".join(f'<li>{esc(s["file"])}<br><code>{esc(s["sha256"])}</code></li>' for s in report["sources"])
    return f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kernellum | Route review</title>
<style>body{{margin:0;background:#101713;color:#e5eee7;font:16px/1.6 system-ui,sans-serif}}main{{max-width:1100px;margin:auto;padding:48px 24px}}h1{{font-size:42px;line-height:1.1}}h2{{margin-top:40px}}.eyebrow{{color:#a4ef87;letter-spacing:.12em;font-size:12px}}.card{{padding:24px;background:#1b2820;border:1px solid #364d3b;border-radius:8px}}.table{{overflow:auto}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{text-align:left;padding:12px;border-bottom:1px solid #364d3b;white-space:nowrap}}code{{overflow-wrap:anywhere;font-size:12px}}.muted{{color:#afc1b4}}li{{margin:10px 0}}</style>
<main><p class="eyebrow">KERNELLUM / ENGINEERING PREVIEW {VERSION}</p>
<h1>Architecture route review</h1><p class="muted">GEMM {report['workload']['m']} × {report['workload']['n']} × {report['workload']['k']} / signed INT8 / K1 model</p>
<div class="card"><strong>{esc(report['best_supplied_candidate'] or 'No eligible candidate')}</strong><p>{esc(comparison)}</p><p>{report['eligible_count']} eligible of {report['candidate_count']} supplied candidates</p></div>
<h2>Observed tradeoffs</h2><p>Synthesis limits: {esc(report['limits'])}</p><div class="table"><table><thead><tr><th>Architecture</th><th>Modeled ms</th><th>Min MHz</th><th>Observations</th><th>DSP</th><th>BRAM</th><th>LUT4</th><th>FF</th><th>Pareto</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="muted">{esc(report['aggregation'])}. {esc(report['sampling_note'])}</p>
<h2>Excluded candidates</h2><ul>{rejects or '<li>None</li>'}</ul>
<h2>Interpretation</h2><p>{esc(report['boundary'])}</p>
<h2>Input provenance</h2><ul>{provenance}</ul><p class="muted">The companion JSON contains exact values and source row references. Hashes establish input identity, not correctness.</p></main></html>'''


def add_arguments(parser):
    parser.add_argument("--routes", nargs="+", required=True, type=Path)
    for dim in ("m", "n", "k"):
        parser.add_argument("--" + dim, required=True, type=int)
    parser.add_argument("--baseline", required=True)
    for r in RESOURCES:
        parser.add_argument("--max-" + r, type=int, required=True)
    parser.add_argument("--min-observations", type=int, default=1)
    parser.add_argument("--out", type=Path, required=True)


def run(args):
    report = review(args.routes, m=args.m, n=args.n, k=args.k, baseline=args.baseline,
                    max_resources={r: getattr(args, "max_" + r) for r in RESOURCES},
                    min_observations=args.min_observations)
    outputs = [args.out / "report.json", args.out / "report.html"]
    if any(p.resolve() in {q.resolve() for q in args.routes} for p in outputs):
        raise ValueError("output would overwrite an input")
    args.out.mkdir(parents=True, exist_ok=True)
    outputs[0].write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    outputs[1].write_text(render_html(report))
    print(json.dumps({"status": report["status"], "best": report["best_supplied_candidate"],
                      "eligible": report["eligible_count"], "json": str(outputs[0]), "html": str(outputs[1])}))
    return 0 if report["baseline_eligible"] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    args = parser.parse_args()
    try:
        return run(args)
    except (ValueError, OSError, UnicodeError, csv.Error) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
