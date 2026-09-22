#!/usr/bin/env python3
"""Standalone live bench for GitHub Actions. Stdlib only. Never prints secrets."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

URL = "https://ai-gateway.vercel.sh/typesafe/v1/systemone"
MODEL = "typesafe-ai/jev"
JEV_PER_M = 0.042

CASES = [
    {
        "id": "live-refund",
        "lane": "jev_only",
        "tools_available": 12,
        "tools_kept": 0,
        "history_tokens": 2500,
        "keep_ratio": 0.2,
        "state": "Customer charged twice for annual plan. Wants one refund today. Unpaid dispute.",
        "questions": {
            "needs_text": {"type": "noul", "instructions": "Does this turn require a drafted customer-facing reply right now?"},
            "risky": {"type": "noul", "instructions": "Is issuing the refund irreversible or above policy without a human?"},
            "already_done": {"type": "noul", "instructions": "Is the request already complete?"},
            "lane": {
                "type": "choice",
                "instructions": "Which lane?",
                "criteria": {
                    "skip": "Nothing left",
                    "jev_only": "Typed decision only",
                    "llm_fast": "Short generated text",
                    "llm_strong": "Frontier model",
                    "ask_human": "Ask a person",
                },
            },
        },
    },
    {
        "id": "live-already-done",
        "lane": "skip",
        "tools_available": 18,
        "tools_kept": 0,
        "history_tokens": 11000,
        "keep_ratio": 0.2,
        "state": "Dark-mode toggle already committed. Tests passed. User: looks good, thanks.",
        "questions": {
            "already_done": {"type": "noul", "instructions": "Is the requested work already complete?"},
            "needs_text": {"type": "noul", "instructions": "Does the agent still need to generate more code?"},
            "risky": {"type": "noul", "instructions": "Is this irreversible?"},
            "lane": {
                "type": "choice",
                "instructions": "Which lane?",
                "criteria": {
                    "skip": "Nothing left",
                    "jev_only": "Typed decision only",
                    "llm_fast": "Short generated text",
                    "llm_strong": "Frontier model",
                    "ask_human": "Ask a person",
                },
            },
        },
    },
    {
        "id": "live-deploy",
        "lane": "ask_human",
        "tools_available": 10,
        "tools_kept": 0,
        "history_tokens": 2800,
        "keep_ratio": 0.3,
        "state": "About to kubectl rollout restart deploy/payments -n prod. Unreviewed. Live traffic.",
        "questions": {
            "risky": {"type": "noul", "instructions": "Is this an irreversible production action that needs a human?"},
            "needs_text": {"type": "noul", "instructions": "Need generated prose?"},
            "already_done": {"type": "noul", "instructions": "Already done?"},
            "lane": {
                "type": "choice",
                "instructions": "Which lane?",
                "criteria": {
                    "skip": "Nothing left",
                    "jev_only": "Typed decision only",
                    "llm_fast": "Short generated text",
                    "llm_strong": "Frontier model",
                    "ask_human": "Ask a person",
                },
            },
        },
    },
    {
        "id": "live-explain",
        "lane": "llm_fast",
        "tools_available": 8,
        "tools_kept": 0,
        "history_tokens": 2600,
        "keep_ratio": 0.45,
        "state": "Explain why checkout retry can double-charge, plain English for a PM. No code.",
        "questions": {
            "needs_text": {"type": "noul", "instructions": "Does this need generated prose from a writer model?"},
            "risky": {"type": "noul", "instructions": "Irreversible?"},
            "already_done": {"type": "noul", "instructions": "Already done?"},
            "lane": {
                "type": "choice",
                "instructions": "Which lane?",
                "criteria": {
                    "skip": "Nothing left",
                    "jev_only": "Typed decision only",
                    "llm_fast": "Short generated text",
                    "llm_strong": "Frontier model",
                    "ask_human": "Ask a person",
                },
            },
        },
    },
    {
        "id": "live-arch",
        "lane": "llm_strong",
        "tools_available": 18,
        "tools_kept": 3,
        "history_tokens": 14000,
        "keep_ratio": 0.4,
        "state": "Redesign billing so invoices, tax, and dunning are separate bounded contexts. Propose split and migration.",
        "questions": {
            "needs_text": {"type": "noul", "instructions": "Does this need a long-form architecture write-up?"},
            "risky": {"type": "noul", "instructions": "Irreversible now?"},
            "already_done": {"type": "noul", "instructions": "Already done?"},
            "lane": {
                "type": "choice",
                "instructions": "Which lane?",
                "criteria": {
                    "skip": "Nothing left",
                    "jev_only": "Typed decision only",
                    "llm_fast": "Short generated text",
                    "llm_strong": "Frontier model",
                    "ask_human": "Ask a person",
                },
            },
        },
    },
    {
        "id": "live-tools",
        "lane": "llm_fast",
        "tools_available": 30,
        "tools_kept": 2,
        "history_tokens": 6000,
        "keep_ratio": 0.25,
        "state": "Look up invoice INV-4419 and email the PDF to finance@.",
        "questions": {
            "needs_text": {"type": "noul", "instructions": "After picking tools, does the model still need to write an email body?"},
            "risky": {"type": "noul", "instructions": "Irreversible?"},
            "already_done": {"type": "noul", "instructions": "Already done?"},
            "lane": {
                "type": "choice",
                "instructions": "Which lane?",
                "criteria": {
                    "skip": "Nothing left",
                    "jev_only": "Typed decision only",
                    "llm_fast": "Short generated text",
                    "llm_strong": "Frontier model",
                    "ask_human": "Ask a person",
                },
            },
        },
    },
]


def noul(ans):
    if not ans:
        return 0.5
    if "noul" in ans:
        return float(ans["noul"])
    if "probability" in ans:
        return float(ans["probability"])
    return 0.5


def pick_lane(answers):
    if noul(answers.get("already_done") or {}) >= 0.7:
        return "skip"
    if noul(answers.get("risky") or {}) >= 0.7:
        return "ask_human"
    lane = (answers.get("lane") or {}).get("choice")
    if lane in ("skip", "jev_only", "llm_fast", "llm_strong", "ask_human"):
        if noul(answers.get("needs_text") or {}) < 0.3 and lane in ("llm_fast", "llm_strong"):
            return "jev_only"
        return lane
    if noul(answers.get("needs_text") or {}) < 0.3:
        return "jev_only"
    return "llm_fast"


def estimate(case, lane):
    tool = 380
    system = 350
    naive_in = system + case["history_tokens"] + 180 + case["tools_available"] * tool
    naive_out = {"skip": 80, "jev_only": 120, "ask_human": 160, "llm_fast": 450, "llm_strong": 900}[case["lane"]]
    if lane in ("skip", "jev_only", "ask_human"):
        integ_in = 180 + 400
        integ_out = 0
    else:
        integ_in = system + int(case["history_tokens"] * case["keep_ratio"]) + 180 + case["tools_kept"] * tool
        integ_out = 280 if lane == "llm_fast" else 700
    return naive_in + naive_out, integ_in + integ_out


def post(key, state, questions):
    body = json.dumps({"state": state, "model": MODEL, "questions": questions}).encode()
    req = urllib.request.Request(
        URL,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode())


def main():
    key = (os.environ.get("AI_GATEWAY_API_KEY") or os.environ.get("TYPESAFE_API_KEY") or "").strip()
    if not key:
        print(json.dumps({"ok": False, "error": "no key in env"}))
        return 2
    rows = []
    jev_in = 0
    cost = 0.0
    errors = 0
    for case in CASES:
        t0 = time.perf_counter()
        try:
            raw = post(key, case["state"], case["questions"])
        except urllib.error.HTTPError as exc:
            errors += 1
            rows.append({"id": case["id"], "error": f"HTTP {exc.code}"})
            continue
        except Exception as exc:
            errors += 1
            rows.append({"id": case["id"], "error": type(exc).__name__})
            continue
        answers = raw.get("answers") or {}
        lane = pick_lane(answers)
        naive, integ = estimate(case, lane)
        usage = raw.get("usage") or {}
        inp = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
        jev_in += inp
        cost += inp / 1_000_000.0 * JEV_PER_M
        rows.append({
            "id": case["id"],
            "expected": case["lane"],
            "observed": lane,
            "match": lane == case["lane"],
            "jev_input": inp,
            "ms": int((time.perf_counter() - t0) * 1000),
            "naive": naive,
            "integrate": integ,
        })
    naive = sum(r.get("naive") or 0 for r in rows)
    integ = sum(r.get("integrate") or 0 for r in rows) + jev_in
    ok = [r for r in rows if "error" not in r]
    print(json.dumps({
        "ok": errors == 0,
        "backend": "vercel",
        "model": MODEL,
        "cases": len(CASES),
        "succeeded": len(ok),
        "errors": errors,
        "policy_matches": sum(1 for r in ok if r.get("match")),
        "jev_input_tokens": jev_in,
        "jev_cost_usd": round(cost, 6),
        "naive_writer_tokens": naive,
        "integrate_tokens_incl_jev": integ,
        "total_reduction_pct": round(100.0 * (1 - integ / naive), 1) if naive else 0.0,
        "rows": rows,
    }, indent=2))
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
