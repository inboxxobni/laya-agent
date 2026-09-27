"""Terminal UI for laya-agent (Textual). One process, no server required: it loads the Engine directly.

Tabs: Playground (choice/score/yesno on any text), Use cases (the registry, click to try), Chat
(Laya guard/route + a local text model), Status (the same checks as `laya-agent doctor`).

Run with `uv run laya-agent tui`.
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    RadioButton,
    RadioSet,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)

from . import registry
from .engine import Engine

CSS = """
Screen { background: $surface; }
.panel { border: round $panel-lighten-1; padding: 1 2; margin: 1 0; }
.hint { color: $text-muted; margin-bottom: 1; }
#pg-options, #uc-input { height: 5; }
.result { height: auto; max-height: 16; border: round $panel-lighten-1; padding: 1; margin-top: 1; }
#uc-list { height: 12; border: round $panel-lighten-1; }
#chat-log { height: 1fr; border: round $panel-lighten-1; padding: 0 1; }
.msg-user { color: $accent; }
.msg-assistant { color: $text; }
.msg-route { color: $text-muted; text-style: italic; }
"""


def bar(label, value, maximum, width=24):
    filled = int(width * value / maximum) if maximum else 0
    return f"{label:>16} [{'#' * filled}{'.' * (width - filled)}] {value:.3f}"


class Playground(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("Ask Laya to pick one option, score a rubric, or answer yes/no. About 15-25 ms, all local.", classes="hint")
        yield Label("Text to judge")
        yield TextArea("I was billed twice, please refund me.", id="pg-state")
        yield Label("Mode")
        with RadioSet(id="pg-mode"):
            yield RadioButton("choice", value=True)
            yield RadioButton("score")
            yield RadioButton("yes / no")
        yield Label("Question / instructions")
        yield Input("Which team should handle this?", id="pg-question")
        yield Label("Options, one per line (ignored for yes/no)")
        yield TextArea("billing\ntechnical\nsales", id="pg-options")
        yield Button("Run", id="pg-run", variant="success")
        yield Static("", id="pg-result", classes="result")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "pg-run":
            self.app.run_playground()


class UseCases(Horizontal):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Ready-made primitives. Pick one, edit the sample, run it.", classes="hint")
            yield ListView(
                *[ListItem(Label(f"[{g}] {name} - {h}"), name=name) for name, (g, h, _e, _f) in registry.PRIMITIVES.items()],
                id="uc-list",
            )
        with Vertical():
            yield Label("Input", id="uc-label")
            yield TextArea("", id="uc-input")
            yield Button("Run", id="uc-run", variant="success", disabled=True)
            yield Static("", id="uc-result", classes="result")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        name = event.item.name
        group, help_text, example, _fn = registry.PRIMITIVES[name]
        self.query_one("#uc-label", Label).update(f"{name}  ({group}) - {help_text}")
        self.query_one("#uc-input", TextArea).text = example
        self.query_one("#uc-run", Button).disabled = False
        self.app.selected_usecase = name

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "uc-run":
            self.app.run_usecase()


class Chat(Vertical):
    def compose(self) -> ComposeResult:
        yield Static(
            "Laya guards and routes every message (attack / intent / difficulty, one pass); "
            "a local text model (TEXT_MODEL_BASE_URL, default Ollama) writes the reply.",
            classes="hint",
        )
        yield VerticalScroll(id="chat-log")
        yield Input(placeholder="Type a message and press enter...", id="chat-input")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "chat-input" and event.value.strip():
            message = event.value
            event.input.value = ""
            self.app.send_chat(message)


class StatusPane(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("Checking Apple Silicon, the Laya checkpoint and the text model endpoint...", id="status-text", classes="panel")

    def on_mount(self) -> None:
        self.app.run_status()


class LayaApp(App):
    CSS = CSS
    TITLE = "laya-agent"
    SUB_TITLE = "local typed decisions, no cloud"
    BINDINGS = [("q", "quit", "Quit"), ("ctrl+c", "quit", "Quit")]
    engine_state = reactive("loading")
    selected_usecase: str | None = None

    def __init__(self):
        super().__init__()
        self.engine = Engine()

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Playground", id="tab-playground"):
                yield Playground()
            with TabPane("Use cases", id="tab-usecases"):
                yield UseCases()
            with TabPane("Chat", id="tab-chat"):
                yield Chat()
            with TabPane("Status", id="tab-status"):
                yield StatusPane()
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._warm_engine, thread=True, exclusive=True)

    def _warm_engine(self) -> None:
        try:
            self.engine.load()
            self.call_from_thread(self._set_subtitle, "ready")
        except Exception as error:  # surfaced in Status and on first use
            self.call_from_thread(self._set_subtitle, f"load failed: {error}")

    def _set_subtitle(self, text: str) -> None:
        self.sub_title = f"local typed decisions, no cloud - {text}"

    # -------------------------------------------------------------------------------- playground

    def run_playground(self) -> None:
        pg = self.query_one(Playground)
        state = pg.query_one("#pg-state", TextArea).text
        question = pg.query_one("#pg-question", Input).value
        options = [line.strip() for line in pg.query_one("#pg-options", TextArea).text.splitlines() if line.strip()]
        mode_index = pg.query_one("#pg-mode", RadioSet).pressed_index
        mode = ("choice", "score", "yesno")[mode_index if mode_index is not None else 0]
        result_box = pg.query_one("#pg-result", Static)
        result_box.update("running...")
        self.run_worker(lambda: self._playground_job(mode, state, question, options, result_box), thread=True)

    def _playground_job(self, mode, state, question, options, result_box) -> None:
        try:
            if mode == "choice":
                r = self.engine.choice(state, question, options)
                text = f"{r['choice']}   ({r['latency_ms']} ms)\n\n" + "\n".join(
                    bar(k, v, max(r["probabilities"].values())) for k, v in sorted(r["probabilities"].items(), key=lambda kv: -kv[1])
                )
            elif mode == "score":
                r = self.engine.score(state, question, options)
                text = f"{r['level']}  (score {r['score']:.2f}, {r['latency_ms']} ms)\n\n" + "\n".join(
                    bar(k, v, max(r["probabilities"].values())) for k, v in sorted(r["probabilities"].items(), key=lambda kv: -kv[1])
                )
            else:
                r = self.engine.yesno(state, question)
                text = f"{'yes' if r['answer'] else 'no'}  (p_true {r['p_true']:.3f}, {r['latency_ms']} ms)"
        except Exception as error:
            text = f"Error: {error}"
        self.call_from_thread(result_box.update, text)

    # -------------------------------------------------------------------------------- use cases

    def run_usecase(self) -> None:
        if not self.selected_usecase:
            return
        uc = self.query_one(UseCases)
        text = uc.query_one("#uc-input", TextArea).text
        result_box = uc.query_one("#uc-result", Static)
        result_box.update("running...")
        name = self.selected_usecase
        self.run_worker(lambda: self._usecase_job(name, text, result_box), thread=True)

    def _usecase_job(self, name, text, result_box) -> None:
        try:
            result = registry.run(name, self.engine, text)
            rendered = str(result)
        except Exception as error:
            rendered = f"Error: {error}"
        self.call_from_thread(result_box.update, rendered)

    # -------------------------------------------------------------------------------------- chat

    def send_chat(self, message: str) -> None:
        log = self.query_one("#chat-log", VerticalScroll)
        log.mount(Static(f"you> {message}", classes="msg-user"))
        log.scroll_end()
        if not hasattr(self, "_chat_history"):
            self._chat_history = [{"role": "system", "content": "You are a concise, helpful assistant."}]
        self.run_worker(lambda: self._chat_job(message, log), thread=True)

    def _chat_job(self, message, log) -> None:
        from .chat import turn

        try:
            answer, route = turn(self.engine, self._chat_history, message)
        except Exception as error:
            answer, route = f"Error: {error}", {}
        self.call_from_thread(self._show_chat_reply, log, answer, route)

    def _show_chat_reply(self, log, answer, route) -> None:
        log.mount(Static(answer, classes="msg-assistant"))
        if route:
            log.mount(Static(
                f"intent={route.get('intent')} difficulty={route.get('difficulty')} model={route.get('model', '-')}"
                + (" BLOCKED" if route.get("attack") else ""),
                classes="msg-route",
            ))
        log.scroll_end()

    # ------------------------------------------------------------------------------------ status

    def run_status(self) -> None:
        self.run_worker(self._status_job, thread=True)

    def _status_job(self) -> None:
        import os
        import platform
        import urllib.request

        lines = [f"Apple Silicon: {'ok' if platform.machine() == 'arm64' else 'no'} ({platform.machine()})"]
        try:
            self.engine.load()
            r = self.engine.yesno("The build passed.", "Did the build pass?")
            lines.append(f"Laya checkpoint: ok  {self.engine.model_id}  ({r['latency_ms']} ms)")
        except Exception as error:
            lines.append(f"Laya checkpoint: FAIL  {error}")
        base = os.environ.get("TEXT_MODEL_BASE_URL", "http://localhost:11434/v1").rstrip("/")
        try:
            with urllib.request.urlopen(base + "/models", timeout=3) as response:
                import json

                names = [m["id"] for m in json.load(response).get("data", [])]
            wanted = os.environ.get("TEXT_MODEL", "")
            lines.append(f"Text model endpoint: ok  {base}  ({len(names)} models)")
            lines.append(f"TEXT_MODEL '{wanted}': {'available' if wanted in names else 'NOT FOUND'}")
        except Exception as error:
            lines.append(f"Text model endpoint: FAIL  {base}: {error}")
        self.call_from_thread(self.query_one("#status-text", Static).update, "\n".join(lines))


def main() -> None:
    from .cli import load_environment

    load_environment()
    LayaApp().run()


if __name__ == "__main__":
    main()
