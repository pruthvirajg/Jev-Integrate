---
name: jev
description: >
  Offload a snap decision to TypeSafe Jev. Use when picking among a known
  set of options, answering yes/no, or rating on a rubric. Do not use Jev
  to generate text, code, or plans.
---

# Jev-Integrate skill

Jev evaluates `state` against typed questions and returns values, not prose.

Requires `TYPESAFE_API_KEY` and `python3`. If the key is missing, make the
judgment yourself and continue. Never block the session.

## CLI

From the repo root:

```bash
python3 scripts/jev.py choose "Which tool?" "find the retry timeout" \
  --opt 'Grep=search file contents' \
  --opt 'Glob=find files by name'

python3 scripts/jev.py noul "Does this diff keep the public API?" @diff.patch

python3 scripts/jev.py score "How risky is this command?" "rm -rf build/" \
  --level 'safe — reversible' \
  --level 'moderate — recoverable' \
  --level 'dangerous — hard to undo'

echo '{"state":"...","questions":{...}}' | python3 scripts/jev.py ask
python3 scripts/jev.py intent "add a dark-mode toggle"
python3 scripts/jev.py smoke
```

## Library

```python
from jevintegrate import Jev, Router, noul, choice

plan = Router(provider="xai").plan(state, messages=messages, tools=["bash"])
if plan.call_llm:
    # only now call Grok / Claude
    ...
```

## Using the number

Read `confidence` before you act. Below ~0.55 treat it as a coin flip.
A noul is a probability to threshold — pick the threshold before you see it.
Jev is advice, not permission.
