"""laya-agent command line: doctor, serve, choice, score, yesno, bench."""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from .engine import Engine


def load_environment():
    path = Path.cwd() / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def doctor():
    import urllib.request

    ok = True

    def line(name, good, note=""):
        nonlocal ok
        ok &= bool(good)
        print(f"[{'ok' if good else 'FAIL'}] {name} {note}")

    import platform

    line("Apple Silicon", platform.machine() == "arm64", platform.machine())
    try:
        engine = Engine().load()
        result = engine.yesno("The build passed.", "Did the build pass?")
        line("Laya checkpoint", True, f"{engine.model_id} (warm call {result['latency_ms']} ms)")
    except Exception as error:  # report any load failure, including a missing download
        line("Laya checkpoint", False, f"{error}\n       run: make weights")
    base = os.environ.get("TEXT_MODEL_BASE_URL", "http://localhost:11434/v1").rstrip("/")
    try:
        with urllib.request.urlopen(base + "/models", timeout=3) as response:
            names = [m["id"] for m in json.load(response).get("data", [])]
        wanted = os.environ.get("TEXT_MODEL", "")
        line("Text model endpoint", True, f"{base} ({len(names)} models)")
        line("TEXT_MODEL available", wanted in names, wanted or "(unset)")
    except Exception as error:
        line("Text model endpoint", False, f"{base}: {error}")
    line("Chrome", shutil.which("google-chrome") or shutil.which("chrome") or True, "(open, with remote debugging on)")
    sys.exit(0 if ok else 1)


def main():
    parser = argparse.ArgumentParser(prog="laya-agent", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor", help="check the local setup")
    serve = sub.add_parser("serve", help="run the local HTTP decision service")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8780)
    choice = sub.add_parser("choice", help="pick one option")
    choice.add_argument("state")
    choice.add_argument("--q", required=True, help="the question")
    choice.add_argument("--options", nargs="+", required=True)
    score = sub.add_parser("score", help="rubric score")
    score.add_argument("state")
    score.add_argument("--q", required=True)
    score.add_argument("--levels", nargs="+", required=True, help="ordered low to high")
    yesno = sub.add_parser("yesno", help="P(true) for a proposition")
    yesno.add_argument("state")
    yesno.add_argument("--q", required=True, help="the proposition")
    bench = sub.add_parser("bench", help="latency + accuracy on bench/cases.json")
    bench.add_argument("--repeats", type=int, default=5)
    caps = sub.add_parser("capabilities", help="exercise every Laya capability, write results/capabilities-*.json")
    caps.add_argument("--only", nargs="+", help="suite names to run")
    sub.add_parser("usecases", help="run the labelled eval for coding / web / games / chat / acryl primitives")
    args = parser.parse_args()

    load_environment()
    if args.cmd == "doctor":
        doctor()
    if args.cmd == "capabilities":
        from .capabilities import run

        run(args.only)
        return
    engine = Engine()
    if args.cmd == "usecases":
        from .usecases import run as run_usecases

        report, path = run_usecases(engine)
        for name, r in report.items():
            if name != "_meta":
                print(f"{name:24s} {r['accuracy']:6s} {r.get('p50_ms', '')}")
                for m in r["misses"]:
                    print("    miss:", m)
        print("saved", path)
        return
    if args.cmd == "serve":
        from .server import serve as run_server

        run_server(engine, args.host, args.port)
    elif args.cmd == "bench":
        from .bench import run, show

        show(*run(engine, args.repeats))
    else:
        if args.cmd == "choice":
            result = engine.choice(args.state, args.q, args.options)
        elif args.cmd == "score":
            result = engine.score(args.state, args.q, args.levels)
        else:
            result = engine.yesno(args.state, args.q)
        print(json.dumps(result, indent=2))
