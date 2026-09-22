# Jev-Integrate

**One decision layer in front of every famous LLM.**

Jev (TypeSafe System One) makes the typed call — yes/no, pick a label, score a rubric. Claude, Grok, GPT, Gemini, Mistral, DeepSeek, and the rest **only write when that call says they must**. That is how tokens drop.

```
                    +---------------+
   user turn  --->  | Jev-Integrate |
                    |  Router.plan  |
                    +-------+-------+
           skip / jev_only / ask_human
                            |
               llm_fast / llm_strong
                            |
          +-----------------+------------------+
          v                 v                  v
       Claude             Grok               GPT
       Gemini            Mistral           DeepSeek
       Groq / Together / Fireworks / OpenRouter
       Azure / Bedrock / Ollama / any /v1
```

```python
from jevintegrate import Router, connect

plan = Router(provider="xai").plan(state, messages=messages, tools=ALL_TOOLS)
if not plan.call_llm:
    handle(plan)                          # zero writer tokens
else:
    text, usage = connect(plan.provider, model=plan.model_tier).complete(
        messages, tools=[s for s in schemas if s["name"] in plan.tools]
    )
```

Swap `"xai"` for `"anthropic"`, `"openai"`, `"google"`, `"mistral"`, `"deepseek"`, `"groq"`, `"ollama"`, `"openrouter"`, `"compat"`.

## Measured token reduction

```bash
python3 -m jevintegrate.bench
```

| | Naive (always-strong LLM + every tool + full history) | Jev-Integrate |
| --- | ---: | ---: |
| Input tokens | 315,040 | 63,560 |
| Output tokens | 21,600 | 7,640 |
| **Total** | **336,640** | **71,200** |
| Writer calls | 24 / 24 | 13 / 24 |
| Tools offered (mean) | 13.5 | 0.8 |

**78.8% fewer tokens. 45.8% of turns never call a writer.** Policy match: **24 / 24**.

Full numbers: eval/RESULTS.json. Architecture estimate (chars/4 + fixed schema cost), not an invoice.

## Install

Python 3.10+. Zero PyPI dependencies.

```bash
git clone https://github.com/pruthvirajg/Jev-Integrate
cd Jev-Integrate
export TYPESAFE_API_KEY=...          # https://console.typesafe.ai
python3 -m jevintegrate providers
python3 -m jevintegrate bench
python3 -m unittest discover -s tests -v
```

Writer keys (only after plan.call_llm): ANTHROPIC_API_KEY, OPENAI_API_KEY, XAI_API_KEY, GEMINI_API_KEY, MISTRAL_API_KEY, DEEPSEEK_API_KEY, COHERE_API_KEY, GROQ_API_KEY, TOGETHER_API_KEY, FIREWORKS_API_KEY, OPENROUTER_API_KEY, AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT, LLM_API_KEY + LLM_BASE_URL, OLLAMA_HOST.

Claude Code:

```bash
claude plugin marketplace add pruthvirajg/Jev-Integrate
claude plugin install jev-integrate@jev-integrate
```

## Safety

Stdlib only. Payloads redacted before Jev. Hooks fail open. See SECURITY.md and AUDIT.md.

MIT. Inspired by 0x7067/claude-jev; code here is original.
