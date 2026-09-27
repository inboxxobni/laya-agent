# Laya capabilities, measured

M1 Max, macOS 26.7, FP16, `laya-mlx` 0.2.0 (git). Raw data: `results/capabilities-*.json`. Re-run: `uv run laya-agent capabilities`.

**What Laya is:** a 322M-421M bidirectional encoder that answers *typed* questions about a text in one forward pass, no generated tokens:
`choice` (probabilities over named options), `score` (expected level of an ordered rubric), `noul` (P(true)).
It is a System 1 classifier/router/scorer. It is not a planner, extractor, or text generator.

| Capability | Result here |
|---|---|
| Latency, 1 question | 14-15 ms (English / typed-decisions), 10 ms (multilingual) |
| Batching (many questions, one state, one call) | 1q 14.9 ms, 8q 52.6 ms, 32q 190 ms: about 6 ms per question beyond 8 |
| Checkpoints, 6 English routing cases | 6/6 on all three |
| Multilingual (10 languages, en zh hi es de ja ar ru fr pt) | multilingual 10/10; English checkpoint 9/10 with p=0.38-0.44 on Arabic and Hindi. Router detects the language and picks the checkpoint |
| State shapes (text / JSON dict / chat list) | all three worked |
| Presets (`triage`, `guard`, `moderation`, `router`) | all run; guard flagged "ignore all previous instructions" (jailbreak 1.0, injection 1.0) and the benign question 0.0-0.002. 5-question presets take 55-220 ms |
| Shortlist (200 options) | plain call fails ("too many options for the token budget"); `predict_shortlist` (k=20) works, 364 ms, picked a correct-topic tool |
| `compile=True, cache_prompts=True` | p50 14.3 ms vs 15.5 eager: marginal for this workload |
| Long input | **Hard limit in practice**, see below |

## Long input: the important limit
Needle test with `max_len=8192` on the multilingual checkpoint (one fact buried in filler):

| Filler | Tokens | Whole document | Chunked + max-pool |
|---|---|---|---|
| 100 words | 155 | correct (code and semantic) | correct |
| 400-5000 words | 469-5,405 | **wrong at every length** (both needle kinds) | correct at all lengths (p_true 0.63-0.84) |

Latency for a whole 5,400-token document was 580-630 ms, so the extra length costs time and returns nothing useful.
Rule: never hand Laya long text. Split into ~120-word overlapping chunks and max-pool `noul`, or shortlist first.
The chunk experiment had no negative-control document yet (a long text without the fact); treat 0.63-0.84 as a signal, not a calibrated probability. Tracked in `findings.md`.

## Calibration
`noul` P(true) is conservative: real positives came out 0.5-0.6, negatives 0.05-0.15. A 0.5 threshold misses positives; choose a threshold per question and validate it on your own labelled cases.
