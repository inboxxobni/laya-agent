# laya-agent

Local, open-weight typed decisions with [Laya](https://github.com/NandhaKishorM/laya) on Apple Silicon (MLX):
a decision server other agents can call, a browser agent, per-use-case primitives, and measured results.
Work in progress: see `docs/` and `results/`.

```bash
make setup weights doctor   # deps, ~1 GB checkpoint, environment check
make test bench             # offline tests; latency + accuracy
uv run laya-agent capabilities   # exercise every Laya capability
uv run laya-agent usecases       # coding / web / games / chat / acryl evals
make serve                  # http://127.0.0.1:8780
```
