# Jev-Integrate

Integration of TypeSafe Jev with Claude, Grok, or any chat LLM. Jev returns typed answers. The LLM writes only when `Router.plan` says so.

Read `README.md` before changing behavior.

## Layout

| Path | What lives there |
| --- | --- |
| `jevintegrate/` | Library. Import this from your own agent. |
| `scripts/jev.py` | CLI + intent/subagent question bundles. |
| `scripts/prompt_router.py` | `UserPromptSubmit` |
| `scripts/subagent_router.py` | `PreToolUse` on Agent/Task |
| `scripts/rules.py` | `PostToolUse` + `Stop` |
| `scripts/compact_hook.py` | compact rows; fail-open `{"fallback"}` |
| `hooks/register.ts` | Claude function-hook bridge only |
| `hooks/hooks.json` | Hook registration |
| `skills/` | User-facing `/jev`, `/stats` |
| `tests/` | Unit + fail-open hook tests, no network |

## Invariants

- Hooks fail open. `except Exception: return` at the top of every hook `main`. Compaction prints `{"fallback": ...}` and exits 0.
- Python 3 standard library only inside `scripts/` and `jevintegrate/`.
- One required env var: `TYPESAFE_API_KEY`. Optional LLM keys are unused until `plan.call_llm`.
- A constant carries a comment saying why it has that value.
- User-facing entry points are skills, not a `commands/` directory.

## Verify

```bash
python3 -m compileall -q jevintegrate scripts tests
python3 -m unittest discover -s tests -v
echo '{"prompt":"hi","transcript_path":""}' | python3 scripts/prompt_router.py; echo exit=$?
echo '' | python3 scripts/compact_hook.py
```

Every hook must exit 0 on malformed or empty stdin.
