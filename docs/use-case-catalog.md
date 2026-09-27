# Every use case, in one list

Status: **works** = measured on this machine and good enough to use; **partial** = works with caveats; **no** = measured failing; **untested**.
Numbers and cases: [usecases.md](usecases.md), [capabilities.md](capabilities.md), `../results/`.

## Coding
| # | Use case | Status | How |
|---|---|---|---|
| C1 | Gate shell commands before an agent runs them | partial (7/8) | pi bash gate, `shell_risk` |
| C2 | Test/build log verdict: passed / failed / tooling error | works (6/6) | `test_verdict` |
| C3 | Pick the next action for a coding agent | no for Laya; rules 5/5 | `next_step(progress)` |
| C4 | Route request to small / large model | partial (5/5, fitted thresholds) | `model_tier` |
| C5 | Decide when a change needs independent review | partial (4/4, fitted threshold) | `needs_review` |
| C6 | Screen pasted content / prompts for injection | works on obvious cases | `guard` preset |
| C7 | Run as tools inside the pi coding agent | works | [pi.md](pi.md) |
| C8 | Long diff/log analysis | works with chunking | max-pool over chunks |

## Web agent and scraping
| # | Use case | Status | How |
|---|---|---|---|
| W1 | Full browser agent, fully local | partial: local fixture 3/3, live Wikipedia 1/5 | `laya_ultrafast`, `scripts/run_fixture.py` |
| W2 | Classify page type | partial (6/7) | `page_kind` |
| W3 | Detect robot check / access denial and hand off to a human | partial (3/4) | `is_blocked` |
| W4 | Rank links for a crawler | works (5/5, fitted threshold) | `link_relevance` |
| W5 | Pick an element for a goal from a large list | works with shortlist | `predict_shortlist` (200 options in 364 ms) |
| W6 | Multilingual pages | works | multilingual checkpoint, Router |

## Games
| # | Use case | Status | How |
|---|---|---|---|
| G1 | Snake | works: 0 deaths in 6 runs of 1,000 moves; score 32/35/31 with the safety layer, 3/18/31 without | `laya-snake` (laya-mlx), `scripts/snake_bench.py` |
| G2 | Board games (tic-tac-toe) | no (0/6) | needs rule engine, Laya only for semantic questions |

## Chat
| # | Use case | Status | How |
|---|---|---|---|
| H1 | Local chat agent: Laya guard + route, Ollama answers | works | `uv run laya-agent chat` |
| H2 | Attack/jailbreak detection | works on obvious cases | `chat_route.attack` |
| H3 | Small-talk vs question vs code vs action intent | partial (3/4) | `chat_route.intent` |
| H4 | Multilingual routing (10 languages) | works (10/10) | multilingual checkpoint |
| H5 | Moderation, triage, email presets | ran; not accuracy-tested | laya-mlx presets |

## Acryl / ALLAGENT
| # | Use case | Status | How |
|---|---|---|---|
| A1 | Agent health from terminal tail (rate limit / auth / crash / done) | works (6/6, hand-written samples) | `agent_health` |
| A2 | Assign a task to the right agent | works (4/4) | `pick_agent` |
| A3 | Reviewer trigger | partial | `needs_review` |
| A4 | Cheap decisions as room events with probabilities | untested design | [acryl-integration.md](acryl-integration.md) |

## Platform
| # | Use case | Status |
|---|---|---|
| P1 | Local HTTP decision service | works |
| P2 | Batch many questions in one pass | works (about 6 ms per question) |
| P3 | Fine-tune for your domain | untested (upstream docs exist) |
| P4 | Non-Apple hardware | not supported by this repo (MLX) |
