"""Local HTTP decision service for other agents (stdlib only, JSON in / JSON out).

  GET  /health
  POST /v1/decide  {"state": str, "questions": {id: {type, instructions, criteria}}}   raw Laya call
  POST /v1/choice  {"state": str, "instructions": str, "options": [..] | {label: desc}}
  POST /v1/score   {"state": str, "instructions": str, "levels": [low, .., high]}
  POST /v1/yesno   {"state": str, "proposition": str}
  GET  /v1/usecases        catalog of ready-made primitives (name, group, help, example)
  POST /v1/usecase/<name>  {"input": str}   run one primitive (see registry.py)
  POST /v1/chat            {"history": [{"role","content"}, ...], "message": str}   one chat turn

Serves the bundled single-page web app (web/index.html and its assets) at "/" when `static_dir` is set
(the CLI passes the packaged web/ directory; see `laya-agent web`).
Binds to 127.0.0.1 by default: there is no authentication.
"""

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import registry

MAX_BODY = 1_000_000


class BadRequest(ValueError):
    pass


def field(body, name, kind):
    value = body.get(name)
    if not isinstance(value, kind) or not value:
        raise BadRequest(f"'{name}' is required")
    return value


def chat_turn(engine, body):
    from .chat import system_prompt, turn

    history = [dict(m) for m in body.get("history") or []]
    if not history:
        history.append({"role": "system", "content": system_prompt(os.environ.get("TEXT_MODEL", "qwen2.5:latest"))})
    answer, route = turn(engine, history, field(body, "message", str))
    return {"answer": answer, "route": route, "history": history}


ROUTES = {
    "/v1/decide": lambda e, b: e.decide(field(b, "state", str), field(b, "questions", dict)),
    "/v1/choice": lambda e, b: e.choice(
        field(b, "state", str), field(b, "instructions", str), field(b, "options", (list, dict))
    ),
    "/v1/score": lambda e, b: e.score(field(b, "state", str), field(b, "instructions", str), field(b, "levels", list)),
    "/v1/yesno": lambda e, b: e.yesno(field(b, "state", str), field(b, "proposition", str)),
    "/v1/chat": chat_turn,
}


def make_handler(engine, static_dir=None):
    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, payload):
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def serve_static(self):
            rel = "index.html" if self.path in ("/", "") else self.path.lstrip("/").split("?", 1)[0]
            path = (static_dir / rel).resolve()
            inside = path == static_dir or static_dir in path.parents
            if not inside or not path.is_file():
                return self.reply(404, {"error": "not found"})
            content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/health":
                self.reply(200, {"ok": True, "model": engine.model_id})
            elif self.path == "/v1/usecases":
                self.reply(200, registry.catalog())
            elif static_dir is not None:
                self.serve_static()
            else:
                self.reply(404, {"error": "not found"})

        def do_POST(self):
            route = ROUTES.get(self.path)
            if route is None and self.path.startswith("/v1/usecase/"):
                name = self.path.rsplit("/", 1)[1]
                if name in registry.PRIMITIVES:
                    route = lambda e, b, name=name: {"result": registry.run(name, e, field(b, "input", str))}  # noqa: E731
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


def serve(engine, host="127.0.0.1", port=8780, static_dir=None):
    engine.load()
    static_dir = Path(static_dir).resolve() if static_dir else None
    try:
        server = ThreadingHTTPServer((host, port), make_handler(engine, static_dir))
    except OSError as error:
        if error.errno == 48:  # EADDRINUSE
            raise SystemExit(
                f"Port {port} is already in use, probably another laya-agent still running.\n"
                f"Find it with:  lsof -iTCP:{port} -sTCP:LISTEN\n"
                f"Stop it with:  kill <PID>\n"
                f"Or use a different port:  --port {port + 1}"
            ) from None
        raise
    where = f" and the web app at http://{host}:{port}/" if static_dir else ""
    print(f"laya-agent decision server on http://{host}:{port}{where}  (model {engine.model_id})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
