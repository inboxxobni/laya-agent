---
name: laya
description: Use the local Laya classifier for fast, offline routing, triage and gating decisions on short text (shell command risk, test log verdicts, page type, agent health, review need). Use when a choice among named categories is needed and an LLM call would be slow or costly.
---

# Laya typed decisions

Laya answers one constrained question about a short text in about 15-25 ms, locally. Tools: `laya_choice`, `laya_yesno`, `laya_classify`.

Use it for: categorising text, gating commands, deciding pass/fail from logs, detecting rate limits or bot checks, routing to a model tier.
Do not use it for: planning next steps, arithmetic, spatial or game reasoning, extracting exact values, or text longer than about 150 tokens (split into chunks and take the highest `p_true`).

Rules of thumb (measured, see laya-agent/docs/findings.md):
- Name concrete categories in the question ("touch security, payments, or data deletion?") rather than abstract ones ("is it risky?").
- `p_true` is conservative. Positives often land at 0.4-0.6. Use a threshold you validated, and verify anything consequential yourself.
- If the top choice probability is under about 0.5, treat the answer as unsure and decide another way.
- Requires the server: `make serve` in the laya-agent repo (127.0.0.1:8780).
