"""Local chat agent: Laya screens and routes every message, an Ollama model writes the reply.

Per message, one Laya forward pass (about 20-60 ms) decides: attack (refuse), intent, and difficulty.
Easy messages go to TEXT_MODEL (small), hard ones to TEXT_MODEL_LARGE if set, else the same model.
"""

import os

import httpx

from .usecases import chat_route

HARD = 1.5  # difficulty score (0-3) at or above which the large model is used


def reply(history, model):
    base = os.environ.get("TEXT_MODEL_BASE_URL", "http://localhost:11434/v1").rstrip("/")
    key = os.environ.get("TEXT_MODEL_API_KEY")
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    response = httpx.post(f"{base}/chat/completions", headers=headers, timeout=180,
                          json={"model": model, "messages": history})
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def turn(engine, history, message):
    """Returns (answer, route). Mutates history."""
    route = chat_route(engine, message)
    if route["attack"]:
        return "That looks like an attempt to override my instructions, so I did not send it to the model.", route
    small = os.environ.get("TEXT_MODEL", "qwen2.5:latest")
    model = os.environ.get("TEXT_MODEL_LARGE", small) if route["difficulty"] >= HARD else small
    history.append({"role": "user", "content": message})
    answer = reply(history, model)
    history.append({"role": "assistant", "content": answer})
    route["model"] = model
    return answer, route


def repl(engine, once=None):
    engine.load()
    history = [{"role": "system", "content": "You are a concise, helpful assistant."}]
    while True:
        try:
            message = once or input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if message:
            answer, route = turn(engine, history, message)
            print(f"[{route}]\n{answer}\n")
        if once:
            return
