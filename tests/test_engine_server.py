import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from laya_agent.engine import Engine
from laya_agent.server import make_handler


class FakeModel:
    def system_one(self, state, questions):
        answers = {}
        for key, q in questions.items():
            if q["type"] == "choice":
                labels = list(q["criteria"])
                answers[key] = {"choice": labels[0], "probabilities": dict.fromkeys(labels, 1 / len(labels))}
            elif q["type"] == "score":
                answers[key] = {"score": 1.2, "probabilities": {str(i): 0.5 for i in range(len(q["criteria"]))}}
            else:
                answers[key] = {"noul": 0.8}
        return {"answers": answers, "usage": {"input_tokens": 1, "output_tokens": 0}}


def engine():
    return Engine(model="fake", loader=lambda _: FakeModel())


def test_engine_helpers():
    e = engine()
    assert e.choice("x", "q", ["a", "b"])["choice"] == "a"
    assert e.score("x", "q", ["low", "mid", "high"])["level"] == "mid"
    assert e.yesno("x", "q")["answer"] is True


def call(port, path, body):
    request = urllib.request.Request(f"http://127.0.0.1:{port}{path}", json.dumps(body).encode(), method="POST")
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def test_server_routes_and_validation():
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(engine()))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    try:
        assert call(port, "/v1/choice", {"state": "s", "instructions": "q", "options": ["a", "b"]})[1]["choice"] == "a"
        assert call(port, "/v1/yesno", {"state": "s", "proposition": "p"})[1]["answer"] is True
        status, body = call(port, "/v1/choice", {"state": "s"})
        assert status == 400 and "instructions" in body["error"]
        status, body = call(port, "/v1/usecase/shell_risk", {"input": "ls"})
        assert status == 200 and body["result"] in {"safe", "needs_approval", "destructive"}
        assert call(port, "/v1/usecase/nope", {"input": "x"})[0] == 404
        assert call(port, "/v1/nope", {})[0] == 404
    finally:
        server.shutdown()
