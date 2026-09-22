# Security

Jev-Integrate sends sanitized state plus typed questions to https://api.typesafe.ai/v1/systemone. LLM backends are contacted only after plan.call_llm.

Controls live in jevintegrate/security.py: secret redaction, 48k state cap, refuse live sk- keys, block .env/.ssh/.pem paths, 240-char redacted logs, fail-open hooks, Jev never executes side effects, stdlib-only supply chain.

Cap TYPESAFE_API_KEY in the TypeSafe console. Report issues via GitHub private advisory on pruthvirajg/Jev-Integrate.
