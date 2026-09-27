"""One process-wide Laya model behind three typed helpers: choice, score, yes/no.

Laya answers narrow, constrained questions (a choice among named options, a rubric score, P(true)) in a
single forward pass with zero generated tokens. It is a System 1 classifier/router, not a planner or
a text generator. MLX is not safe to call from several threads at once, so every call takes a lock.
"""

import os
import threading
import time

DEFAULT_MODEL = "aac6fef/laya-typed-decisions-mlx"


class Engine:
    def __init__(self, model=None, loader=None):
        self.model_id = model or os.environ.get("LAYA_MODEL", DEFAULT_MODEL)
        self._loader = loader
        self._model = None
        self._lock = threading.Lock()

    def load(self):
        with self._lock:
            if self._model is None:
                if self._loader:
                    self._model = self._loader(self.model_id)
                else:
                    import laya_mlx

                    self._model = laya_mlx.load(self.model_id)
                # The first forward pass compiles Metal kernels; pay for it here, not on a request.
                self._model.system_one("Warm up.", {"q": {"type": "noul", "instructions": "Warm up."}})
        return self

    def decide(self, state, questions):
        """Raw Laya call: `questions` is {id: {type, instructions, criteria}}. Returns answers plus timing."""
        self.load()
        started = time.perf_counter()
        with self._lock:
            result = self._model.system_one(state, questions)
        result["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
        return result

    def choice(self, state, instructions, options):
        """`options` is a list of labels or a {label: description} dict. Returns choice + probabilities."""
        answer = self.decide(state, {"q": {"type": "choice", "instructions": instructions, "criteria": options}})
        a = answer["answers"]["q"]
        return {"choice": a["choice"], "probabilities": a["probabilities"], "latency_ms": answer["latency_ms"]}

    def score(self, state, instructions, levels):
        """`levels` is an ordered list of rubric labels, low to high. Returns expected score in [0, len-1]."""
        answer = self.decide(state, {"q": {"type": "score", "instructions": instructions, "criteria": levels}})
        a = answer["answers"]["q"]
        return {
            "score": a["score"],
            "level": levels[min(len(levels) - 1, max(0, round(a["score"])))],
            "probabilities": {levels[int(k)]: v for k, v in a["probabilities"].items()},
            "latency_ms": answer["latency_ms"],
        }

    def yesno(self, state, proposition):
        """P(true) for a proposition about `state`."""
        answer = self.decide(state, {"q": {"type": "noul", "instructions": proposition}})
        p = answer["answers"]["q"]["noul"]
        return {"answer": p >= 0.5, "p_true": p, "latency_ms": answer["latency_ms"]}
