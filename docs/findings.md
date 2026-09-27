# Findings log

Newest last. One entry per experiment: what we tried, what happened, the rule we took from it.

## 2026-09-27: first pass
- Setup works offline: 53 vendored tests pass, checkpoints load, 15 ms typed decisions. `results/bench-*.json`, `results/capabilities-*.json`, `results/usecases-*.json`.
- **Laya does not plan.** "What should the coding agent do next?" gave probabilities 0.1-0.3 across five options, 2/5 correct, even with structured JSON progress state. Rules on counters got 5/5. Rule: planning = rules or LLM.
- **Concrete phrasing beats abstract.** "Is this change high risk?" gave p_true 0.34 / 0.15 for risky / safe. "Does the diff touch security, payments, or data deletion?" gave 0.57-0.62 / 0.07-0.13. Name the categories.
- **noul is conservative.** True cases sit at 0.5-0.6. Use per-question thresholds (we use 0.4 for `needs_review`, tuned on 4 cases: needs a real validation set).
- **Long input silently degrades.** Correct at 155 tokens, wrong at 469 and above, no error raised (see capabilities.md). Chunk + max-pool got 5/5 positives and 0.0 p_true on same-length negative controls.
- **Spatial games fail.** Tic-tac-toe 0/6, same cell every time.
- **English checkpoint is weak on some non-Latin text** (Arabic p=0.38, Hindi p=0.44); the Router's language detection handles this automatically.
- **Dependency:** PyPI `laya-mlx` 0.1.0 has no `predict_shortlist` or `embed_fn_from_agent`; we pin the git revision (0.2.0).
- **Not yet done:** running the vendored browser agent end to end here (needs Chrome remote debugging; not attempted so the user's live browser was left alone), `model_tier` and `link_relevance` evals, Ollama-backed chat REPL, MCP/LangChain/hooks integrations from upstream `laya` (PyTorch package in `../laya`).

## 2026-09-27: browser agent, pi, Snake
- **Browser agent, fully local** (Laya + Ollama `qwen2.5` + private headless Chrome via `BU_CDP_URL`): local travel fixture 3/3 (27.6 s cold, then 5.1 s and 3.4 s, 8 actions). Live Wikipedia 1/5: three `Runtime.evaluate` IPC timeouts, one wrong page (donate site), one success (9.9 s). Diagnosed run: query typed correctly, then clicks at probability 0.24 / confidence 0.03 and wandering. Rule: the policy needs a confidence floor that stops or asks instead of clicking; we do not have that yet. Data: `results/browser-*.json`.
- **Private Chrome recipe** avoids touching your browser: `make chrome`, then `BU_CDP_URL=http://127.0.0.1:9333 ...`.
- **pi integration works** (tools callable, bash gate blocks destructive, allows safe). Interactive confirm dialog not exercised.
- **Snake**: Laya plays with 0 deaths over 6 x 1,000 moves. See usecases.md.
- **Thresholds warning:** `model_tier`, `link_relevance` and `needs_review` thresholds were fitted on the very cases used to evaluate them. Their 100% is optimistic.
- **Open:** confidence floor for the browser policy; IPC timeouts on real sites; agent_health on real captured terminal output; fine-tuning.
