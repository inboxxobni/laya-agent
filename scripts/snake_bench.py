"""Headless Snake with and without laya-mlx's safety layer; saves results/snake-<UTC>.json.
Shows what Laya alone can do in a game versus Laya proposing and rules enforcing safety."""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL, STEPS = "aac6fef/laya-multilingual-mlx", 1000
runs = []
for seed in (1, 2, 3):
    for mode, flag in (("assisted", []), ("unassisted", ["--unassisted"])):
        command = ["uv", "run", "laya-snake", "--headless", "--steps", str(STEPS), "--max-speed",
                   "--seed", str(seed), "--model", MODEL, *flag]
        out = subprocess.run(command, capture_output=True, text=True, cwd=ROOT).stdout
        data = json.loads(out[out.index("{"):])
        keys = ("score", "length", "deaths", "interventions", "mean_inference_ms")
        runs.append({"seed": seed, "mode": mode, **{k: data[k] for k in keys}})
        print(runs[-1], flush=True)
path = ROOT / "results" / f"snake-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
path.write_text(json.dumps({"model": MODEL, "steps": STEPS, "runs": runs}, indent=2))
print("saved", path)
