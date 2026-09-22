# Jev-Integrate

Jev makes the decisions. Claude, Grok, or any other LLM only writes.

Inspired by [0x7067/claude-jev](https://github.com/0x7067/claude-jev) — fail-open hooks that hand small judgments to [TypeSafe Jev](https://docs.typesafe.ai) — this repo is a standalone integration for **Claude Code, Grok, and any OpenAI-compatible chat model**, plus a Python library you can call from your own loop.

```
user turn
   |
   v
Jev  -- skip / jev_only / ask_human -->  no LLM tokens
   |
   +-- cheapest model tier that can write
   +-- drop tool schemas that will not be used
   +-- drop stale history (kept rows stay verbatim)
   |
   v
Claude / Grok / OpenAI writes the text
```

Jev is a System One model. It does not generate prose. You send a `state` plus typed questions to `POST https://api.typesafe.ai/v1/systemone` and get probabilities back in ~70-500 ms at **$0.042 / million input tokens**, output free.

## What it does

| Surface | Job |
| --- | --- |
| `UserPromptSubmit` | Classify the prompt, inject a routing hint |
| `PreToolUse` (`Agent\|Task`) | Set the subagent model tier unless one was named |
| `PostToolUse` + `Stop` | Score the edit against bullets in `AGENTS.md` / `CLAUDE.md` |
| `session.compact` | Keep/drop rows with Jev; no LLM summary |
| `jevintegrate.Router` | Same decisions from any Python agent (Grok included) |

Hooks **fail open**. A missing key, timeout, or exception prints nothing and exits 0. Compaction answers `{"fallback": ...}` so the host summarizer can run.

Slash commands, `#` memorize lines, and prompts under 3 characters are skipped locally.

## Setup

```bash
git clone https://github.com/pruthvirajg/Jev-Integrate
cd Jev-Integrate
export TYPESAFE_API_KEY=...          # https://console.typesafe.ai
python3 scripts/jev.py smoke
python3 -m unittest discover -s tests -v
```

### Claude Code plugin

```bash
claude plugin marketplace add pruthvirajg/Jev-Integrate
claude plugin install jev-integrate@jev-integrate
```

From a checkout: `claude plugin marketplace add .` then install `jev-integrate@jev-integrate`.

### Library (Claude, Grok, OpenAI)

```python
from jevintegrate import Router
from jevintegrate.llm import grok, AnthropicMessages

plan = Router(provider="xai").plan(
    {"user": "Refund the duplicate charge on INV-2041."},
    messages=messages,
    tools=["refund_api", "lookup_invoice", "send_email"],
)
if not plan.call_llm:
    print(plan.lane, plan.reason)     # zero LLM tokens
else:
    text, usage = grok(plan.model_tier).complete(messages, model=plan.model_tier)
```

`provider="anthropic"` or `"openai"` swaps the tier table. Optional keys `ANTHROPIC_API_KEY` / `XAI_API_KEY` / `OPENAI_API_KEY` are only read when a plan actually calls an LLM.

## CLI

```bash
python3 scripts/jev.py smoke
python3 scripts/jev.py intent "add a dark-mode toggle"
python3 scripts/jev.py noul "Does this ask for a refund?" @examples/state/ticket.json
python3 -m jevintegrate route --state examples/state/ticket.json --provider xai
python3 scripts/stats.py
```

## Token cuts

| Cut | What Jev does | LLM tokens you stop paying |
| --- | --- | --- |
| Lane | `skip` / `jev_only` / `ask_human` | the entire completion |
| Tier | fast vs strong vs hardest | Opus-class turns that were actually a lookup |
| Tools | keep 1-2 schemas | unused tool dumps in the prompt |
| History | drop stale rows, keep the rest verbatim | long-tail context |

The no-tools hint is gated harder than intent: it fires only on a near-certain yes/no, because skipping needed work is the expensive mistake.

## Layout

```
jevintegrate/     library (client, router, compact, tools, meter, llm)
scripts/          hook entrypoints + jev CLI
hooks/            Claude Code hook map + compact bridge
skills/           /jev and /stats
plugins/          Claude install notes, Grok skill
examples/
tests/            no network; hooks must exit 0 on bad input
```

## Invariants

- Python 3 stdlib only. `urllib.request` is the HTTP client.
- One required env var: `TYPESAFE_API_KEY`.
- Thresholds live in `jevintegrate/policies.py` and the hook modules, with comments. Do not hide them in a system prompt.
- Jev never executes a side effect. `ask_human` stops the agent.

## License

MIT. Jev is a product of TypeSafe. This repo calls their public System One API. Architecture inspired by 0x7067/claude-jev; the code here is original.
