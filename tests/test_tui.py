"""Headless smoke test for the Textual UI: it mounts, all tabs render, and the playground runs
against a fake engine (no real model, no download, no network)."""

import pytest

from laya_agent.tui import LayaApp


class FakeModel:
    def system_one(self, state, questions):
        answers = {}
        for key, q in questions.items():
            if q["type"] == "choice":
                labels = list(q["criteria"])
                answers[key] = {"choice": labels[0], "probabilities": dict.fromkeys(labels, 1 / len(labels))}
            elif q["type"] == "score":
                answers[key] = {"score": 1.0, "probabilities": {str(i): 0.5 for i in range(len(q["criteria"]))}}
            else:
                answers[key] = {"noul": 0.9}
        return {"answers": answers, "usage": {"input_tokens": 1, "output_tokens": 0}}


@pytest.mark.asyncio
async def test_app_mounts_and_runs_playground():
    app = LayaApp()
    app.engine._loader = lambda _: FakeModel()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.query_one("#pg-run") is not None
        assert app.query_one("#uc-list") is not None
        assert app.query_one("#chat-log") is not None
        app.run_playground()
        await pilot.pause(0.2)
        result = app.query_one("#pg-result").renderable
        assert "billing" in str(result)
