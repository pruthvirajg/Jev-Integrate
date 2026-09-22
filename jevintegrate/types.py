"""Typed Jev questions, answers, and routing plans."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Sequence

QuestionType = Literal["noul", "choice", "score"]
Lane = Literal["skip", "jev_only", "llm_fast", "llm_strong", "ask_human"]
Provider = Literal["none", "anthropic", "openai", "xai", "openrouter"]


def noul(
    instructions: str,
    *,
    true: str | None = None,
    false: str | None = None,
) -> dict[str, Any]:
    q: dict[str, Any] = {"type": "noul", "instructions": instructions}
    if true is not None or false is not None:
        q["criteria"] = {k: v for k, v in (("true", true), ("false", false)) if v is not None}
    return q


def choice(instructions: str, criteria: Mapping[str, str | None]) -> dict[str, Any]:
    return {"type": "choice", "instructions": instructions, "criteria": dict(criteria)}


def score(instructions: str, criteria: Sequence[str]) -> dict[str, Any]:
    levels = list(criteria)
    if not 2 <= len(levels) <= 10:
        raise ValueError("score criteria must have 2-10 ordered levels")
    return {"type": "score", "instructions": instructions, "criteria": levels}


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    ms: int = 0
    cost_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class Answer:
    id: str
    type: QuestionType
    raw: dict[str, Any]

    @property
    def noul(self) -> float | None:
        if self.type != "noul":
            return None
        return float(self.raw.get("noul", 0.0))

    @property
    def choice(self) -> str | None:
        if self.type != "choice":
            return None
        return self.raw.get("choice")

    @property
    def score(self) -> float | None:
        if self.type != "score":
            return None
        return float(self.raw["score"]) if "score" in self.raw else None

    @property
    def probabilities(self) -> dict[str, float]:
        raw = self.raw.get("probabilities") or {}
        return {str(k): float(v) for k, v in raw.items()}

    @property
    def confidence(self) -> float | None:
        if self.type == "noul":
            p = self.noul if self.noul is not None else 0.5
            return abs(p - 0.5) * 2.0
        if "confidence" in self.raw:
            return float(self.raw["confidence"])
        return None

    @property
    def legend(self) -> dict[str, Any]:
        return dict(self.raw.get("legend") or {})

    def yes(self, threshold: float = 0.7) -> bool:
        if self.type != "noul" or self.noul is None:
            raise TypeError(f"{self.id} is not a noul answer")
        return self.noul >= threshold

    def peaked(self, threshold: float = 0.6) -> bool:
        c = self.confidence
        return c is not None and c >= threshold


@dataclass
class Judgment:
    model: str
    answers: dict[str, Answer]
    usage: Usage
    raw: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Answer:
        return self.answers[key]

    def get(self, key: str) -> Answer | None:
        return self.answers.get(key)


@dataclass
class Plan:
    lane: Lane
    reason: str
    model_tier: str = "none"
    provider: Provider = "none"
    tools: list[str] = field(default_factory=list)
    keep_message_ids: list[str] = field(default_factory=list)
    dropped_messages: int = 0
    answers: dict[str, Answer] = field(default_factory=dict)
    usage: Usage = field(default_factory=Usage)
    escalate: bool = False

    @property
    def call_llm(self) -> bool:
        return self.lane in ("llm_fast", "llm_strong")
