# Jev-Integrate

**One decision layer in front of every famous LLM.**

See the checkout in artifacts/Jev-Integrate for the full README if this copy is trimmed. Clone and read README.md, SECURITY.md, AUDIT.md.

## Bench (reproducible, no live vendor calls)

```
python3 -m jevintegrate.bench
```

24 labeled turns: 78.8% fewer tokens vs always-strong LLM + every tool + full history. 45.8% of turns never call a writer. 24/24 policy match.

## Quick start

```python
from jevintegrate import Router, connect
plan = Router(provider="xai").plan(state, messages=messages, tools=ALL_TOOLS)
if not plan.call_llm:
    handle(plan)
else:
    connect(plan.provider, model=plan.model_tier).complete(messages)
```

Providers: anthropic, openai, xai, google, mistral, deepseek, cohere, groq, together, fireworks, openrouter, azure, bedrock, ollama, compat.

Zero PyPI dependencies. TYPESAFE_API_KEY required for live Jev.
