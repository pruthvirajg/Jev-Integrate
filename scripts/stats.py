#!/usr/bin/env python3
"""Summarize ~/.jev-integrate/router.jsonl."""

from __future__ import annotations

import json
import os
import sys
from collections import Counter

LOG = os.path.expanduser("~/.jev-integrate/router.jsonl")


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else LOG
    if not os.path.isfile(path):
        print(f"no log at {path}")
        return 0
    kinds: Counter[str] = Counter()
    intents: Counter[str] = Counter()
    n = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            n += 1
            kinds[row.get("kind") or "prompt"] += 1
            choice = ((row.get("answers") or {}).get("intent") or {}).get("choice")
            if choice:
                intents[choice] += 1
    print(json.dumps({"rows": n, "kinds": dict(kinds), "intents": dict(intents)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
