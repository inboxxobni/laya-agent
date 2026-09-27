# Terminal UI

```bash
uv run laya-agent tui
```

A [Textual](https://textual.textualize.io/) app, one process, no server needed (it loads the model directly). Tabs:

| Tab | What |
|---|---|
| Playground | pick choice / score / yes-no, type any text and question, see the probability bars |
| Use cases | the same registry as the web app; click a primitive, edit its sample input, run it |
| Chat | Laya guards and routes each message; a local text model (Ollama by default) answers |
| Status | the same checks as `laya-agent doctor`, live |

Keys: `q` or `ctrl+c` to quit, arrow keys / tab to move focus, enter to run or submit.
The model loads in the background on startup (about 2 s); the subtitle bar shows "ready" when it's warm.

Verified end to end on this machine (real model, no fakes): playground choice, a use-case run, a chat turn, and the status checks all worked (2026-09-27).
