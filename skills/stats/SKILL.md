---
name: stats
description: Summarize Jev-Integrate routing decisions from the local log.
---

```bash
python3 scripts/stats.py
python3 scripts/stats.py ~/.jev-integrate/router.jsonl
```

Prints counts by hook kind and predicted intent. Does not call the API.
