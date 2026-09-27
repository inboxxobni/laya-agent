# laya-agent

Local, open-weight typed decisions with [Laya](https://github.com/NandhaKishorM/laya) on Apple Silicon (MLX).
One forward pass, about 15 ms, no cloud, no API key, no generated tokens: choose, score, or answer yes/no about
a short text. It's the free, open, offline alternative to hosted typed-decision APIs like TypeSafe's Jev, for the
part of an agent that just needs to classify, route, or gate, not generate.

Three ways in, pick whichever fits:

```bash
make setup weights doctor     # once: install, ~1 GB checkpoint, environment check

uv run laya-agent tui         # terminal UI: click around, no HTTP, no browser
uv run laya-agent web         # opens a page in your browser: same thing, point and click
uv run laya-agent choice "I was billed twice" --q "Which team?" --options billing technical sales
```

**New here? Start with [docs/testing-guide.md](docs/testing-guide.md)** — a numbered walkthrough of every feature with
the exact command and what you should see.

## What's in the box

| | |
|---|---|
| `laya_agent/` | the decision engine (`Engine`), HTTP API, TUI, web app, local chat agent, use-case primitives |
| `laya_ultrafast/` | a fully local browser agent (from [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast), MIT) |
| `pi-package/` | tools and a bash safety gate for the [pi](https://pi.dev) coding agent |
| `docs/` | guides, and a dated findings log of what actually worked (see [docs/findings.md](docs/findings.md)) |
| `results/` | every benchmark run this project has produced, as JSON |

## Honest summary

Strong at classification, routing and gating (support triage, shell-command safety, page-type detection, agent
health from terminal output). Not a planner, not a text generator, and not reliable on long text without chunking
or on live sites without more work yet — see [docs/findings.md](docs/findings.md) for the failures too, not just the wins.

MIT licensed. Contributions welcome, see [CONTRIBUTING.md](CONTRIBUTING.md).
