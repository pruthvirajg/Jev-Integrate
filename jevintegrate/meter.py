"""Cost and latency accounting for Jev vs LLM calls."""

from __future__ import annotations

from dataclasses import dataclass, field

from .types import Usage

JEV_INPUT_PER_MTOK = 0.042

DEFAULT_LLM_PRICES: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-opus-5": (15.00, 75.00),
    "grok-4-fast": (0.20, 0.50),
    "grok-4": (3.00, 15.00),
    "gpt-5.6-luna": (0.15, 0.60),
    "gpt-5.6-terra": (1.25, 10.00),
    "default": (3.00, 15.00),
}

TIER_TO_MODEL = {
    "anthropic": {
        "fast": "claude-haiku-4-5",
        "strong": "claude-sonnet-5",
        "hardest": "claude-opus-5",
    },
    "xai": {
        "fast": "grok-4-fast",
        "strong": "grok-4",
        "hardest": "grok-4",
    },
    "openai": {
        "fast": "gpt-5.6-luna",
        "strong": "gpt-5.6-terra",
        "hardest": "gpt-5.6-terra",
    },
    "openrouter": {
        "fast": "claude-haiku-4-5",
        "strong": "claude-sonnet-5",
        "hardest": "claude-opus-5",
    },
}


def jev_cost(input_tokens: int) -> float:
    return (input_tokens / 1_000_000.0) * JEV_INPUT_PER_MTOK


def llm_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    inn, out = DEFAULT_LLM_PRICES.get(model, DEFAULT_LLM_PRICES["default"])
    return (input_tokens / 1_000_000.0) * inn + (output_tokens / 1_000_000.0) * out


def resolve_model(provider: str, tier: str) -> str:
    table = TIER_TO_MODEL.get(provider, TIER_TO_MODEL["anthropic"])
    return table.get(tier, table["strong"])


@dataclass
class SessionMeter:
    jev_calls: int = 0
    llm_calls: int = 0
    jev_input_tokens: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    jev_ms: int = 0
    events: list[Usage] = field(default_factory=list)

    def add_jev(self, usage: Usage) -> None:
        self.jev_calls += 1
        self.jev_input_tokens += usage.input_tokens
        self.jev_ms += usage.ms
        self.events.append(usage)

    def add_llm(self, usage: Usage) -> None:
        self.llm_calls += 1
        self.llm_input_tokens += usage.input_tokens
        self.llm_output_tokens += usage.output_tokens
        self.events.append(usage)

    @property
    def jev_usd(self) -> float:
        return jev_cost(self.jev_input_tokens)

    @property
    def llm_usd(self) -> float:
        total = 0.0
        for ev in self.events:
            if ev.model.startswith("jev"):
                continue
            total += llm_cost(ev.input_tokens, ev.output_tokens, ev.model or "default")
        return total

    @property
    def total_usd(self) -> float:
        return self.jev_usd + self.llm_usd

    def naive_llm_usd(self, assumed_input: int, assumed_output: int, model: str) -> float:
        turns = max(self.jev_calls, 1)
        return turns * llm_cost(assumed_input, assumed_output, model)

    def summary(self, *, naive_model: str = "claude-sonnet-5", naive_in: int = 4000, naive_out: int = 600) -> dict:
        naive = self.naive_llm_usd(naive_in, naive_out, naive_model)
        saved = max(0.0, naive - self.total_usd)
        return {
            "jev_calls": self.jev_calls,
            "llm_calls": self.llm_calls,
            "jev_input_tokens": self.jev_input_tokens,
            "llm_input_tokens": self.llm_input_tokens,
            "llm_output_tokens": self.llm_output_tokens,
            "jev_usd": round(self.jev_usd, 6),
            "llm_usd": round(self.llm_usd, 6),
            "total_usd": round(self.total_usd, 6),
            "naive_all_llm_usd": round(naive, 6),
            "estimated_saved_usd": round(saved, 6),
            "jev_ms": self.jev_ms,
        }
