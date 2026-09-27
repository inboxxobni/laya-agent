# Contributing

This project measures before it claims. If you add a primitive, a checkpoint, or an integration:

1. Add 4-10 labelled cases to its eval (`laya_agent/usecases.py`'s `EVALS`, or `bench/cases.json`).
2. Run `make test usecases capabilities` and paste the numbers into a doc under `docs/`, including misses.
3. Prefer a rule over a Laya call for anything that needs planning, arithmetic, or spatial reasoning (see `docs/findings.md`).
4. Add a dated entry to `docs/findings.md` for anything you learn, especially a failure.
5. `make test` (ruff + pytest) must pass. New endpoints or UI need a test with a fake model (see `tests/test_engine_server.py`, `tests/test_tui.py`); do not require a real download or network in the test suite.

Style: explicit `git add <path>` (never `-A`/`.`), no em dashes, keep files under about 800 lines, name things plainly.
Issues and PRs welcome. Be specific about what you measured on your own machine; numbers here are from one M1 Max.
