"""Latency and accuracy benchmark for the typed-decision API, on bench/cases.json.

Accuracy here is a small hand-written sanity set, not a benchmark of Laya in general.
Writes results/bench-<UTC timestamp>.json and prints a summary.
"""

import json
import platform
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def percentile(values, q):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(q * (len(ordered) - 1)))]


def run(engine, repeats=5):
    cases = json.loads((ROOT / "bench/cases.json").read_text())
    engine.load()
    latencies, report = [], {}
    for name, spec in cases.items():
        hits, rows = 0, []
        for item in spec["cases"]:
            if name == "yesno":
                state, proposition, expected = item
                result = engine.yesno(state, proposition)
                got, ok = result["answer"], result["answer"] == expected
                detail = {"p_true": result["p_true"]}
            else:
                state, expected = item
                result = engine.choice(state, spec["instructions"], spec["options"])
                got, ok = result["choice"], result["choice"] == expected
                detail = {"top_probability": max(result["probabilities"].values())}
            latencies.append(result["latency_ms"])
            hits += ok
            rows.append({"state": state, "expected": expected, "got": got, "ok": ok, **detail})
        report[name] = {"accuracy": round(hits / len(rows), 3), "correct": hits, "total": len(rows), "rows": rows}
    for _ in range(repeats):
        for spec in cases.values():
            for item in spec["cases"]:
                if "options" in spec:
                    latencies.append(engine.choice(item[0], spec["instructions"], spec["options"])["latency_ms"])
    summary = {
        "model": engine.model_id,
        "machine": f"{platform.machine()} {platform.platform()}",
        "when": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "calls": len(latencies),
        "latency_ms": {
            "p50": round(statistics.median(latencies), 2),
            "p95": round(percentile(latencies, 0.95), 2),
            "max": round(max(latencies), 2),
        },
        "suites": report,
    }
    out = ROOT / "results" / f"bench-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(summary, indent=2))
    return summary, out


def show(summary, path):
    print(f"model   {summary['model']}\nmachine {summary['machine']}")
    lat = summary["latency_ms"]
    print(f"latency p50 {lat['p50']} ms  p95 {lat['p95']} ms  ({summary['calls']} calls)")
    for name, suite in summary["suites"].items():
        print(f"{name:12s} {suite['correct']}/{suite['total']}")
        for row in suite["rows"]:
            if not row["ok"]:
                print(f"   miss: {row['state'][:60]!r} expected {row['expected']} got {row['got']}")
    print(f"saved {path}")
