import json, itertools, statistics
from collections import Counter, defaultdict
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download

REPO = "arcprize/arc_agi_v2_public_eval"
api = HfApi()
files = api.list_repo_files(REPO, repo_type="dataset")
prefixes = sorted({p.split("/")[0] for p in files if "/" in p and p.endswith(".json")})
print("TOP_LEVEL_PREFIXES", json.dumps(prefixes))

patterns = [
    ("gpt54", lambda s: s == "gpt-5-4-medium"),
    ("glm5", lambda s: s == "glm-5"),
    ("claude46", lambda s: "claude-opus-4-6" in s),
    ("gemini3", lambda s: s.startswith("gemini-3") or "gemini-3" in s),
    ("gpt52", lambda s: s.startswith("gpt-5-2") or "gpt-5.2" in s),
    ("claude45", lambda s: s.startswith("claude-opus-4-5") and "thinking-64k" in s),
    ("grok", lambda s: s.startswith("grok-4") or "grok-4" in s),
    ("deepseek", lambda s: "deepseek" in s.lower()),
]
selected = []
for _, fn in patterns:
    matches = [s for s in prefixes if fn(s)]
    if matches:
        m = sorted(matches, key=lambda x: (("medium" not in x and "high" not in x and "64k" not in x), len(x), x))[0]
        if m not in selected:
            selected.append(m)
for s in prefixes:
    if len(selected) >= 8:
        break
    if s not in selected and any(p == f"{s}/results.json" for p in files):
        selected.append(s)
print("SELECTED", json.dumps(selected))

root = Path(snapshot_download(
    REPO, repo_type="dataset",
    allow_patterns=[f"{s}/*.json" for s in selected],
    local_dir="/tmp/hf_arc_eval"
))
gt_dir = Path("/tmp/ARC-AGI-2/data/evaluation")
truth = {}
for p in gt_dir.glob("*.json"):
    d = json.loads(p.read_text())
    truth[p.stem] = [x["output"] for x in d["test"]]

def canon(g):
    if not isinstance(g, list) or not g or not all(isinstance(r, list) and r for r in g):
        return None
    try:
        return tuple(tuple(int(x) for x in r) for r in g)
    except Exception:
        return None

def exact(g, t):
    return canon(g) == canon(t)

def shape(g):
    c = canon(g)
    return None if c is None else (len(c), len(c[0]))

def sim(a, b):
    ca, cb = canon(a), canon(b)
    if ca is None or cb is None or len(ca) != len(cb) or any(len(x) != len(y) for x, y in zip(ca, cb)):
        return None
    n = sum(len(r) for r in ca)
    return sum(x == y for ra, rb in zip(ca, cb) for x, y in zip(ra, rb)) / n if n else None

preds = defaultdict(dict)
meta = {}
for m in selected:
    mdir = root / m
    count = 0
    for p in mdir.glob("[0-9a-f]*.json"):
        if p.stem not in truth:
            continue
        try:
            arr = json.loads(p.read_text())
        except Exception:
            continue
        if not isinstance(arr, list):
            continue
        for i, item in enumerate(arr):
            if i >= len(truth[p.stem]) or not isinstance(item, dict):
                continue
            a1 = item.get("attempt_1", {}).get("answer") if isinstance(item.get("attempt_1"), dict) else None
            a2 = item.get("attempt_2", {}).get("answer") if isinstance(item.get("attempt_2"), dict) else None
            preds[m][(p.stem, i)] = (a1, a2)
            count += 1
    meta[m] = {"n_items": count}
print("LOADED", json.dumps(meta))

active = [m for m in selected if preds[m]]
keys = sorted(set.intersection(*[set(preds[m]) for m in active])) if active else []
print("COMMON_ITEMS", len(keys))

per_model = {}
for m in active:
    rows = []
    for k in keys:
        t = truth[k[0]][k[1]]
        a1, a2 = preds[m][k]
        rows.append((exact(a1, t), exact(a2, t), canon(a1) == canon(a2), sim(a1, a2), shape(a1) == shape(a2)))
    n = len(rows)
    if not n:
        continue
    vals = [r[3] for r in rows if r[3] is not None]
    per_model[m] = {
        "n": n,
        "pass1": sum(r[0] for r in rows) / n,
        "pass2": sum(r[0] or r[1] for r in rows) / n,
        "second_only": sum((not r[0]) and r[1] for r in rows) / n,
        "attempts_exact_duplicate": sum(r[2] for r in rows) / n,
        "attempts_same_shape": sum(r[4] for r in rows) / n,
        "attempt_similarity_mean": statistics.mean(vals) if vals else None,
    }

item_stats = []
for k in keys:
    t = truth[k[0]][k[1]]
    ct = canon(t)
    a1s, alls = [], []
    for m in active:
        a1, a2 = preds[m][k]
        c1, c2 = canon(a1), canon(a2)
        if c1 is not None:
            a1s.append((m, c1))
            alls.append((m, 1, c1))
        if c2 is not None:
            alls.append((m, 2, c2))
    c1 = Counter(g for _, g in a1s)
    ca = Counter(g for _, _, g in alls)
    wrong1 = Counter({g: n for g, n in c1.items() if g != ct})
    wrongall = Counter({g: n for g, n in ca.items() if g != ct})
    maxwrong1 = max(wrong1.values(), default=0)
    maxwrongall = max(wrongall.values(), default=0)
    sims = []
    wrong_grids = [g for _, g in a1s if g != ct]
    for a, b in itertools.combinations(wrong_grids, 2):
        s = sim(a, b)
        if s is not None:
            sims.append(s)
    item_stats.append({
        "task": k[0], "idx": k[1], "n_models": len(a1s),
        "unique_a1": len(c1), "unique_all": len(ca),
        "any_correct": any(g == ct for _, _, g in alls),
        "correct_models_a1": sum(g == ct for _, g in a1s),
        "max_wrong_cluster_a1": maxwrong1,
        "max_wrong_cluster_all": maxwrongall,
        "max_wrong_frac_a1": maxwrong1 / max(1, len(a1s)),
        "wrong_pair_similarity_mean": statistics.mean(sims) if sims else None,
        "modal_a1_correct": bool(c1 and c1.most_common(1)[0][0] == ct),
    })

pairwise = {}
for a, b in itertools.combinations(active, 2):
    aa, bb = [], []
    for k in keys:
        t = truth[k[0]][k[1]]
        pa, pb = preds[a][k], preds[b][k]
        aa.append(exact(pa[0], t) or exact(pa[1], t))
        bb.append(exact(pb[0], t) or exact(pb[1], t))
    if not aa:
        continue
    b_rate = sum(bb) / len(bb)
    fail = [i for i, x in enumerate(aa) if not x]
    cond = sum(bb[i] for i in fail) / len(fail) if fail else None
    ratio = cond / b_rate if cond is not None and b_rate > 0 else None
    pairwise[f"{a} || {b}"] = {
        "n": len(aa), "a": sum(aa) / len(aa), "b": b_rate,
        "p_b_given_a_fail": cond, "complementarity_ratio": ratio
    }

n_items = len(item_stats)
wrong_sims = [x["wrong_pair_similarity_mean"] for x in item_stats if x["wrong_pair_similarity_mean"] is not None]
summary = {
    "selected_models": active,
    "common_items": len(keys),
    "per_model": per_model,
    "union_oracle_all_attempts": sum(x["any_correct"] for x in item_stats) / n_items if n_items else None,
    "modal_attempt1_accuracy": sum(x["modal_a1_correct"] for x in item_stats) / n_items if n_items else None,
    "wrong_attractor": {
        "frac_items_identical_wrong_cluster_ge2": sum(x["max_wrong_cluster_a1"] >= 2 for x in item_stats) / n_items if n_items else None,
        "frac_items_identical_wrong_cluster_ge3": sum(x["max_wrong_cluster_a1"] >= 3 for x in item_stats) / n_items if n_items else None,
        "frac_items_wrong_majority_cluster": sum(x["max_wrong_frac_a1"] > 0.5 for x in item_stats) / n_items if n_items else None,
        "mean_max_wrong_frac_a1": statistics.mean(x["max_wrong_frac_a1"] for x in item_stats) if n_items else None,
        "mean_wrong_pair_similarity": statistics.mean(wrong_sims) if wrong_sims else None,
    },
    "pairwise": pairwise,
}
Path("frontier_failure_audit.json").write_text(json.dumps({"summary": summary, "items": item_stats}, indent=2))
print("FINAL_SUMMARY=" + json.dumps(summary, sort_keys=True))
