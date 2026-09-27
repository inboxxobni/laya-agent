.PHONY: setup weights doctor test serve bench browse fixtures clean-artifacts
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
