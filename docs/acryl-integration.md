# Fit for Acryl / ALLAGENT

ALLAGENT's promise is continuity across agents. Laya is a cheap (about 15-25 ms, local, free, offline) classifier for the decisions the room
makes constantly, where today an LLM call or a brittle regex would be used.

| Room decision | Primitive | Why Laya |
|---|---|---|
| Is this agent rate limited / logged out / crashed? Trigger a handoff | `agent_health` | reads messy terminal text, 6/6 on our cases; replaces per-vendor regex lists |
| Which agent should get this task | `pick_agent` | descriptions come from the agent registry |
| Does this change need a different agent's review | `needs_review` | enforces the self-review prohibition at the right times |
| Is a shell command safe to auto-approve | `shell_risk` | gate before PTY execution |
| Is a prompt or pasted content an injection | `guard` preset | screen room messages before compiling context packets |
| Small or large model for this request | `model_tier` / router preset | cost control |

## Integration options
1. **HTTP sidecar** (`make serve`): the Rust/Tauri backend calls `POST /v1/choice|yesno|decide` on 127.0.0.1:8780. Simplest, language agnostic.
2. **Python worker** for agent bridges (`from laya_agent import Engine`).
Keep model calls out of the room event path's critical section: Laya is fast but the first call compiles kernels (about 2 s), so warm at startup (`Engine().load()` does).

## Constraints to design around
- Apple Silicon only (MLX). A non-Mac deployment needs upstream `laya` (PyTorch/ONNX).
- Never send more than about 150 tokens per call without chunking ([capabilities.md](capabilities.md)).
- Laya returns probabilities: store them in the room event, keep a human-visible fallback when confidence is low (top probability below about 0.5).
- Recorded decisions should be room events (`agent_status_changed`, `review_requested`) with `decidedBy: "laya"` and the probabilities, so they are auditable.

## Next steps
- Wire `agent_health` to real captured terminal tails from Claude Code, Codex, OpenCode, Gemini (needs real samples, our 6 are hand-written).
- Evaluate `pick_agent` with the real agent registry.
- Fine-tuning path exists upstream (`laya/docs/finetune_browser_agent.md`) if generic accuracy is not enough.
