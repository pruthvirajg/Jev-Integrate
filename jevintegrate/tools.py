"""Offer only the tools this turn needs. Most token waste is unused schemas."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .client import Jev
from .policies import NOUL_YES, tool_questions
from .types import Judgment


def pick_tools(
    jev: Jev,
    state: Any,
    tool_names: Sequence[str],
    *,
    extra_state: Mapping[str, Any] | None = None,
    threshold: float = NOUL_YES,
) -> tuple[list[str], Judgment]:
    if not tool_names:
        empty = jev.judge(
            {"note": "no tools registered", **(extra_state or {})},
            {"needs_any_tool": {"type": "noul", "instructions": "Are tools required?"}},
        )
        return [], empty

    payload: dict[str, Any] = {"turn": state, "available_tools": list(tool_names)}
    if extra_state:
        payload.update(extra_state)
    judgment = jev.judge(payload, tool_questions(tool_names))

    any_tool = judgment.get("needs_any_tool")
    if any_tool and any_tool.noul is not None and any_tool.noul < 0.4:
        return [], judgment

    picked: list[str] = []
    for name in tool_names:
        ans = judgment.get(f"offer_{name}")
        if ans and ans.noul is not None and ans.noul >= threshold:
            picked.append(name)
    return picked, judgment


def filter_schemas(
    schemas: Sequence[Mapping[str, Any]],
    picked_names: Sequence[str],
) -> list[dict[str, Any]]:
    allow = set(picked_names)
    out: list[dict[str, Any]] = []
    for schema in schemas:
        name = str(schema.get("name") or schema.get("tool") or "")
        if name in allow:
            out.append(dict(schema))
    return out
