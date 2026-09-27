.PHONY: setup weights doctor test serve bench browse chrome fixture snake chat usecases capabilities tui web
setup:        ## install deps and create .env
	uv sync
	@test -f .env || cp .env.example .env
weights:      ## one-time checkpoint download (~1 GB)
	uv run hf download aac6fef/laya-typed-decisions-mlx
doctor:       ## check Apple Silicon, weights, Ollama, model
	uv run laya-agent doctor
test:         ## offline unit tests + lint
	uv run ruff check . && uv run pytest -q
serve:        ## local decision API on 127.0.0.1:8780
	uv run laya-agent serve
bench:        ## latency + accuracy, writes results/bench-*.json
	uv run laya-agent bench
browse:       ## browser agent inspector on http://127.0.0.1:8766
	uv run laya
chrome:       ## private headless Chrome for the browser agent (does not touch your browser)
	"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --remote-debugging-port=9333 --user-data-dir=$$HOME/.laya-agent-chrome --no-first-run about:blank &
fixture:      ## browser agent on the local fixture page (needs `make chrome` first)
	BU_CDP_URL=http://127.0.0.1:9333 uv run python scripts/run_fixture.py --scenario travel
snake:        ## Snake benchmark: Laya with and without the safety layer
	uv run python scripts/snake_bench.py
chat:         ## local chat: Laya guards/routes, Ollama answers
	uv run laya-agent chat
usecases:     ## labelled evals for every primitive
	uv run laya-agent usecases
capabilities: ## every Laya capability
	uv run laya-agent capabilities
tui:          ## terminal UI: playground, use cases, chat, status
	uv run laya-agent tui
web:          ## web app on http://127.0.0.1:8780 (same port as the API)
	uv run laya-agent web
