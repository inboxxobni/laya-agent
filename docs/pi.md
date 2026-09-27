# Using Laya with pi (pi.dev)

Laya is a classifier, not a coding model. pi's own LLM still writes the code; Laya adds fast, local, offline decisions around it:
a bash safety gate, and tools the model can call to classify short text. This is the right split (see [findings.md](findings.md)).

The integration is a pi package in [`../pi-package`](../pi-package): an extension (`extensions/laya.ts`) and a skill (`skills/laya/SKILL.md`).
It talks to the local decision server over HTTP, so pi needs no Python.

## Install (one time)
```bash
cd laya-agent && make serve            # keep running: 127.0.0.1:8780
pi install /absolute/path/to/laya-agent/pi-package      # adds it to ~/.pi/agent/settings.json
# or try without installing:
pi -e /absolute/path/to/laya-agent/pi-package/extensions/laya.ts
```
Inside pi, `/laya` reports server status.

## What you get
| Piece | Behaviour |
|---|---|
| Bash gate | every `bash` tool call is rated `safe` / `needs_approval` / `destructive`. Destructive asks you first (blocked when pi has no UI, e.g. `-p`). `LAYA_GATE=strict` also asks on `needs_approval`; `LAYA_GATE=off` disables |
| `laya_choice` / `laya_yesno` | the model can route or judge short text in about 15 ms |
| `laya_classify` | ready-made primitives: `shell_risk`, `test_verdict`, `page_kind`, `is_blocked`, `agent_health`, `needs_review`, `model_tier`, `chat_route` |
| skill `laya` | tells the model when to use Laya and when not to |

Env: `LAYA_URL` (default `http://127.0.0.1:8780`), `LAYA_GATE`, `LAYA_GATE_FAIL=closed` (block commands if the server is down; default is fail open with no prompt).

## Verified on this machine (2026-09-27, `pi -ne -e ... -p`)
- `laya_classify shell_risk "rm -rf ~/projects"` called by the model: returned `destructive`.
- `rm -rf /tmp/<nonexistent>`: blocked by the gate ("rated this command destructive and there is no UI to confirm").
- `ls /tmp | head -3`: allowed and executed.
Not verified: interactive confirm dialog (needs a TTY), `pi install` (I did not modify `~/.pi`), long sessions.

## Limits
The gate is a safety net, not a sandbox: Laya missed nothing destructive in our 8-case set but judged `cargo test` "needs_approval". It also cannot see obfuscated commands (`sh -c "$(curl ...)"`). Keep pi's own permission model on.

## Laya as chat inside pi
`chat` = a conversation, which needs a generator. Use pi's model for replies and let Laya guard/route: ask pi to call `laya_classify chat_route` on the user message.
Standalone local chat (Laya screens, Ollama answers) is `uv run laya-agent chat`.
