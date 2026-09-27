# API

## Python
```python
from laya_agent import Engine
e = Engine().load()                       # ~2 s cold (Metal compile), then ~15 ms per call
e.choice("I was billed twice", "Which team?", ["billing", "technical", "sales"])
e.score("URGENT!!", "How urgent?", ["low", "medium", "high"])   # expected level in [0, n-1]
e.yesno("Deploy finished", "Did it succeed?")                    # {"answer", "p_true"}
e.decide(state, {"a": {...}, "b": {...}})                         # many questions, ONE forward pass
```
`state` may be text, a dict, or a chat list. Options may be a list or `{label: description}`; descriptions help.
Calls are serialized by a lock (MLX is not thread-safe).

## HTTP (`make serve`, 127.0.0.1:8780, no auth: keep it local)
`GET /health`, `POST /v1/choice|score|yesno|decide` with JSON bodies:

```bash
curl -s localhost:8780/v1/choice -d '{"state":"Refund my duplicate charge","instructions":"Which team?","options":["billing","technical","sales"]}'
# {"choice": "billing", "probabilities": {...}, "latency_ms": 42.06}
```
Validation errors return 400 `{"error": ...}`.
