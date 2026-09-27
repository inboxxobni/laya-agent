"""Local HTTP decision service for other agents (stdlib only, JSON in / JSON out).

  GET  /health
  POST /v1/decide  {"state": str, "questions": {id: {type, instructions, criteria}}}   raw Laya call
  POST /v1/choice  {"state": str, "instructions": str, "options": [..] | {label: desc}}
  POST /v1/score   {"state": str, "instructions": str, "levels": [low, .., high]}
  POST /v1/yesno   {"state": str, "proposition": str}
  POST /v1/usecase/<name>  {"input": str}   ready-made primitives from usecases.py (see USECASES)

Binds to 127.0.0.1 by default: there is no authentication.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import usecases

MAX_BODY = 1_000_000

# name -> function(engine, input); each returns JSON-serializable data. Keep in step with docs/usecases.md.
USECASES = {
    "shell_risk": lambda e, x: usecases.shell_risk(e, x),
    "test_verdict": lambda e, x: usecases.test_verdict(e, x),
    "page_kind": lambda e, x: usecases.page_kind(e, x),
    "is_blocked": lambda e, x: usecases.is_blocked(e, x),
    "agent_health": lambda e, x: usecases.agent_health(e, x),
    "needs_review": lambda e, x: usecases.needs_review(e, x),
    "model_tier": lambda e, x: usecases.model_tier(e, x),
    "chat_route": lambda e, x: usecases.chat_route(e, x),
}


class BadRequest(ValueError):
    pass


def field(body, name, kind):
    value = body.get(name)
    if not isinstance(value, kind) or not value:
        raise BadRequest(f"'{name}' is required")
    return value


ROUTES = {
    "/v1/decide": lambda e, b: e.decide(field(b, "state", str), field(b, "questions", dict)),
    "/v1/choice": lambda e, b: e.choice(
        field(b, "state", str), field(b, "instructions", str), field(b, "options", (list, dict))
    ),
    "/v1/score": lambda e, b: e.score(field(b, "state", str), field(b, "instructions", str), field(b, "levels", list)),
    "/v1/yesno": lambda e, b: e.yesno(field(b, "state", str), field(b, "proposition", str)),
}


def make_handler(engine):
    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, payload):
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/health":
                self.reply(200, {"ok": True, "model": engine.model_id})
            else:
                self.reply(404, {"error": "not found"})

        def do_POST(self):
            route = ROUTES.get(self.path)
            if route is None and self.path.startswith("/v1/usecase/"):
                fn = USECASES.get(self.path.rsplit("/", 1)[1])
                if fn:
                    route = lambda e, b: {"result": fn(e, field(b, "input", str))}  # noqa: E731
            if route is None:
                return self.reply(404, {"error": "not found"})
            try:
                length = int(self.headers.get("Content-Length", 0))
                if length > MAX_BODY:
                    raise BadRequest("body too large")
                body = json.loads(self.rfile.read(length) or b"{}")
                if not isinstance(body, dict):
                    raise BadRequest("body must be a JSON object")
                self.reply(200, route(engine, body))
            except (BadRequest, json.JSONDecodeError, ValueError) as error:
                self.reply(400, {"error": str(error)})

        def log_message(self, fmt, *args):
            pass

    return Handler


def serve(engine, host="127.0.0.1", port=8780):
    engine.load()
    server = ThreadingHTTPServer((host, port), make_handler(engine))
    print(f"laya-agent decision server on http://{host}:{port}  (model {engine.model_id})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
