"""Minimal TypeSafe Jev client. Stdlib only."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping

from .meter import jev_cost
from .types import Answer, Judgment, Usage

DEFAULT_URL = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"
KEY_FILES = (
    Path.home() / ".typesafe" / "key",
    Path.home() / ".jev" / "key",
)


class JevError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None, body: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.body = body


def _read_key() -> str:
    for name in ("TYPESAFE_API_KEY", "JEV_API_KEY", "AI_GATEWAY_API_KEY"):
        val = os.environ.get(name)
        if val:
            return val.strip()
    for path in KEY_FILES:
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
    raise JevError(
        "No TypeSafe key. Set TYPESAFE_API_KEY or write the key to ~/.typesafe/key"
    )


class Jev:
    """POST /v1/systemone wrapper.

    Pack every independent question about the same state into one call.
    Output tokens are free; you pay $0.042 per million input tokens.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
        retries: int = 3,
    ) -> None:
        self.api_key = api_key or _read_key()
        self.model = model or os.environ.get("TYPESAFE_DEFAULT_MODEL") or DEFAULT_MODEL
        self.base_url = (base_url or os.environ.get("TYPESAFE_BASE_URL") or DEFAULT_URL).rstrip("/")
        if not self.base_url.endswith("/v1/systemone"):
            if self.base_url.endswith("/v1"):
                self.base_url = self.base_url + "/systemone"
            elif "openrouter.ai" in self.base_url:
                pass
            else:
                self.base_url = self.base_url + "/v1/systemone"
        self.timeout = timeout
        self.retries = retries

    def judge(
        self,
        state: Any,
        questions: Mapping[str, Mapping[str, Any]],
        *,
        model: str | None = None,
    ) -> Judgment:
        if not questions:
            raise ValueError("questions must not be empty")
        payload = {
            "state": state,
            "model": model or self.model,
            "questions": dict(questions),
        }
        raw, ms = self._post(payload)
        usage_raw = raw.get("usage") or {}
        input_tokens = int(usage_raw.get("input_tokens") or 0)
        output_tokens = int(usage_raw.get("output_tokens") or 0)
        used_model = str(raw.get("model") or payload["model"])
        usage = Usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=used_model,
            ms=ms,
            cost_usd=jev_cost(input_tokens),
        )
        answers: dict[str, Answer] = {}
        for key, val in (raw.get("answers") or {}).items():
            answers[key] = Answer(id=key, type=val.get("type", "noul"), raw=val)
        return Judgment(model=used_model, answers=answers, usage=usage, raw=raw)

    def check(self, state: Any, instructions: str, **more: Mapping[str, Any]) -> Judgment:
        questions: dict[str, Mapping[str, Any]] = {
            "check": {"type": "noul", "instructions": instructions}
        }
        questions.update(more)
        return self.judge(state, questions)

    def _post(self, payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "jev-integrate/0.1",
        }
        last_err: Exception | None = None
        for attempt in range(self.retries):
            req = urllib.request.Request(self.base_url, data=body, headers=headers, method="POST")
            started = time.perf_counter()
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw_bytes = resp.read()
                ms = int((time.perf_counter() - started) * 1000)
                return json.loads(raw_bytes.decode("utf-8")), ms
            except urllib.error.HTTPError as exc:
                err_body = exc.read().decode("utf-8", errors="replace")
                if exc.code in (429, 529, 500, 502, 503) and attempt < self.retries - 1:
                    retry_after = exc.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 0.4 * (2**attempt)
                    time.sleep(delay)
                    last_err = JevError(f"HTTP {exc.code}: {err_body[:300]}", status=exc.code, body=err_body)
                    continue
                raise JevError(f"HTTP {exc.code}: {err_body[:500]}", status=exc.code, body=err_body) from exc
            except urllib.error.URLError as exc:
                last_err = JevError(f"network error: {exc}")
                if attempt < self.retries - 1:
                    time.sleep(0.4 * (2**attempt))
                    continue
                raise last_err from exc
        raise last_err or JevError("request failed")
