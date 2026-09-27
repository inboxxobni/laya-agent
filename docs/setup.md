# Setup and daily use

Requirements: Apple Silicon Mac, macOS 14+, [uv](https://docs.astral.sh/uv/), Chrome (only for the browser agent),
optionally [Ollama](https://ollama.com) for a fully offline text model.

```bash
make setup      # uv sync, creates .env from .env.example
make weights    # downloads aac6fef/laya-typed-decisions-mlx (default)
make doctor     # checks arm64, checkpoint loads, Ollama endpoint, TEXT_MODEL present
```

Other checkpoints (downloaded on first use, or `uv run hf download <repo>`):

| Repo | Use |
|---|---|
| `aac6fef/laya-typed-decisions-mlx` | default; 1,024-token context |
| `aac6fef/laya-mlx` | English, 512-token context |
| `aac6fef/laya-multilingual-mlx` | 100+ languages, fastest (about 10 ms) |

Daily commands:

| Command | Does |
|---|---|
| `make serve` | local decision API on 127.0.0.1:8780 ([api.md](api.md)) |
| `uv run laya-agent choice "text" --q "question" --options a b c` | one-off typed decision |
| `uv run laya-agent yesno "text" --q "proposition"` | P(true) |
| `uv run laya-agent chat` | chat agent: Laya guards/routes each message, Ollama answers (`--once "msg"` for one shot) |
| `make browse` | browser agent inspector on :8766 (needs Chrome remote debugging, see below) |
| `make bench` / `uv run laya-agent capabilities` / `uv run laya-agent usecases` | measure and save to `results/` |
| `make test` | offline lint + tests (a fake model stands in for Laya) |

`laya_mlx` comes from the git repo (PyPI 0.1.x lacks `predict_shortlist`); the tested revision is pinned in `uv.lock`.

## Browser agent
Enable remote debugging at `chrome://inspect/#remote-debugging`, then `make browse` and open http://127.0.0.1:8766.
The text model defaults to local Ollama `qwen2.5:latest` (set in `.env`), so nothing leaves the machine.
This vendored copy (`laya_ultrafast/`) has not yet been run end to end from this repo; see `findings.md`.
