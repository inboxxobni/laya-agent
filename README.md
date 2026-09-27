# laya-agent

Local, open-weight typed decisions with [Laya](https://github.com/NandhaKishorM/laya) on Apple Silicon (MLX). One forward pass, about 15 ms,
no cloud, no generated tokens: choose, score, or answer yes/no about a short text. Use it as a fast classifier and gate around agents.

Contents: decision engine and HTTP server (`laya_agent/`), use-case primitives with evals (coding, web, games, chat, Acryl),
a local browser agent (`laya_ultrafast/`, from browser-use/jev-ultrafast, MIT), a pi package (`pi-package/`), measured results (`results/`).

```bash
make setup weights doctor     # once
make test                     # offline
make serve                    # decision API on 127.0.0.1:8780
```
**Start with [docs/testing-guide.md](docs/testing-guide.md).** Everything measured, including failures, is in [docs/findings.md](docs/findings.md).
Honest summary: strong on classification and gating; not a planner; local browsing works on the fixture but is unreliable on live sites so far.
