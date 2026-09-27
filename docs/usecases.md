# Use cases

Primitives are in `laya_agent/usecases.py` (import them into any agent); labelled evals run with `uv run laya-agent usecases`
and save to `results/usecases-*.json`. Eval sets are 4-8 hand-written cases per primitive: sanity checks, not benchmarks.
Numbers below are from the latest run; see `findings.md` for how each design was reached.

## Rule that decides everything
Laya is strong at **reading text and putting it in a category** and weak at **deciding what to do next or reasoning over structure**.
Use it for classification, gating, routing and scoring. Use rules (or an LLM) for planning, arithmetic, spatial reasoning.

## Coding agent
| Primitive | Job | Eval |
|---|---|---|
| `shell_risk(cmd)` | safe / needs_approval / destructive gate before an agent runs a command | 7/8 (missed: `cargo test` judged needs_approval; conservative side) |
| `test_verdict(log)` | passed / failed / tooling error from test output | 6/6 |
| `next_step(progress)` | next action from counters | 5/5 **by rules**: Laya's text version scored 2/5 with near-uniform probabilities, so it is not used |
| `model_tier(request)` | small / medium / large model from a difficulty score | 5/5, thresholds (small below 1.5, large from 1.8) fitted on the same 5 cases: trivial requests scored about 1.3, hard ones 2.0-2.1 |
| `needs_review(diff)` | independent-review trigger (ALLAGENT reviewer rule) | 4/4, threshold tuned on the same 4 cases: re-validate |

## Web agent and scraping
| Primitive | Job | Eval |
|---|---|---|
| `page_kind(text)` | search_form / results / article / login / captcha / cookie_banner / error | 6/7 (a bare form-label string was called `results`) |
| `is_blocked(text)` | robot check or access denial: hand to a human, never bypass | 3/4 (missed "Are you a person or a robot? Verify to continue.", P below 0.5) |
| `pick_element(goal, elements)` | choose the element for a goal | used inside the vendored browser agent |
| `link_relevance(goal, link)` | 0-3 crawl-priority score | 5/5 at threshold 1.5 ("Pricing plans" 1.83, "Buy now" 1.95 vs "Contact us" 1.14, "Privacy policy" 0.45, "Careers" 0.38); threshold chosen after seeing these scores |

The full browser agent (`laya_ultrafast/`, `make browse`) is the Jev-ultrafast loop with Laya in place of the hosted model, plus one
text-model call per task. Upstream reports Google Flights 5/5 (7.5-12.1 s); we have not reproduced that from this repo yet.
For scraping, combine `page_kind` + `is_blocked` + `link_relevance` to drive a crawler without any LLM call per page.

## Games
`laya-mlx` ships `laya-snake` (Laya drives Snake with three questions per move plus a visible safety layer: 75 moves/s in their test).
Measured here (`scripts/snake_bench.py`, 1,000 moves x 3 seeds, multilingual checkpoint, about 15-20 ms per move): **0 deaths in all 6 runs**; final score 32 / 35 / 31 with the safety layer and 3 / 18 / 31 without it. The safety layer helps most where Laya alone stalls, so treat it as part of the design. Our own tic-tac-toe probe scored **0/6**: Laya picked the same cell regardless of board. Pattern that works for games:
Laya proposes from a small set of *semantic* questions ("is there danger ahead?"), a rule layer enforces legality and safety.
Do not expect spatial reasoning from the encoder.

## Chat agent
`chat_route(msg)` runs guard, intent and difficulty in one forward pass (about 20-60 ms): block attacks, route small talk to a small model,
hard questions to a large one. Measured 3/4 on 4 cases (attack detection right; "hi there!" was mislabelled `action`). Run it as `uv run laya-agent chat` (Ollama answers; verified: a normal question was answered by `qwen2.5:latest`, an instruction-override prompt was refused before reaching the model). Use the `guard`
preset for injection screening; measured 1.0/1.0 on an obvious jailbreak and 0.0 on a benign question.

## Acryl / ALLAGENT (continuous mode)
| Primitive | Job | Eval |
|---|---|---|
| `agent_health(terminal_tail)` | working / waiting_for_input / rate_limited / auth_expired / crashed / finished | 6/6 |
| `pick_agent(task, agents)` | assign a task to the right registered agent | 4/4 |
| `needs_review(diff)` | require a different agent to review | 4/4 |

See [acryl-integration.md](acryl-integration.md).
