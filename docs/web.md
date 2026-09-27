# Web app

```bash
uv run laya-agent web            # opens http://127.0.0.1:8780 in your browser
uv run laya-agent web --no-open  # just start the server
```

A single HTML page (`laya_agent/web/`, no build step, no npm) served by the same stdlib HTTP server used for the API,
so the web app and `/v1/...` are on one port. Tabs: **Playground** (choice/score/yes-no with probability bars),
**Use cases** (click a card to load its sample input, edit, run), **Chat** (Laya guard/route + your text model), **About**.

Bind `--host 0.0.0.0` to reach it from another device on your network. There is no authentication, so do not expose it
to the internet. Verified end to end with curl against a running server: static files, `/v1/usecases`, `/v1/choice`,
and `/v1/chat` (both the blocked-attack path and a real Ollama reply) all worked (2026-09-27).
