---
name: jev-integrate-grok
description: >
  Before an expensive or irreversible Grok action, ask Jev. Skip the LLM
  when the lane is skip or jev_only. Use XAI_API_KEY only after plan.call_llm.
---

# Grok path

```python
from jevintegrate import Router
from jevintegrate.llm import grok

plan = Router(provider="xai").plan(state, messages=messages, tools=tool_names)
if not plan.call_llm:
    return plan.lane, plan.reason
text, usage = grok(plan.model_tier).complete(messages, model=plan.model_tier)
```

Irreversible actions (`risky` high) come back as `ask_human`. Do not send
mail, spend money, or push from a `jev_only` lane.
