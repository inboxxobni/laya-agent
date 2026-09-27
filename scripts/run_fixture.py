"""Run the Laya browser agent on the bundled local fixture pages and save a result to results/.

Uses its own Chrome (BU_CDP_URL) and its own static server, so your everyday browser is not touched:
  google-chrome --headless=new --remote-debugging-port=9333 --user-data-dir=/tmp/laya-profile about:blank &
  BU_CDP_URL=http://127.0.0.1:9333 uv run python scripts/run_fixture.py --scenario travel
The travel and research fixtures are checked by their final URL / page text (no model judges its own success).
"""

import argparse
import functools
import http.server
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from laya_ultrafast import Agent
from laya_ultrafast.demo import load_environment

ROOT = Path(__file__).resolve().parent.parent
GOALS = {
    "travel": "Use the destination search and filters to find Design stays in Lisbon with Free cancellation, "
    "then open Casa Flora.",
}
CHECKS = {"travel": lambda s, text: s["page"]["url"].endswith("#casa-flora")
          and "Design · Free cancellation enabled · Destination Lisbon" in text}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default="travel", choices=sorted(GOALS))
    parser.add_argument("--port", type=int, default=8788)
    parser.add_argument("--max-actions", type=int, default=20)
    args = parser.parse_args()
    load_environment()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT / "laya_ultrafast/static"))
    handler.log_message = lambda *a, **k: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{args.port}/fixture.html?scenario={args.scenario}"
    result = {"scenario": args.scenario, "when": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    with Agent(url, GOALS[args.scenario]) as agent:
        state = {}
        try:
            for state in agent.run():
                if len(state["history"]) >= args.max_actions:
                    raise RuntimeError(f"stopped at {args.max_actions} actions")
        except Exception as error:
            result["error"] = f"{type(error).__name__}: {error}"
        state = agent.snapshot()
        text = agent.browser.evaluate("document.body.innerText")
    result.update(status=state["status"], ms=state["elapsed_ms"], actions=len(state["history"]),
                  passed=state["status"] == "done" and CHECKS[args.scenario](state, text),
                  history=[h["action"] for h in state["history"]])
    out = ROOT / "results" / f"browser-{args.scenario}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps({k: v for k, v in result.items() if k != "history"}, indent=2), "\nsaved", out)
    server.shutdown()


if __name__ == "__main__":
    main()
