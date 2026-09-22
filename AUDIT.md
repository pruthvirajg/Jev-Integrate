# Audit notes

Verify before production:

```
python3 -m compileall -q jevintegrate scripts tests
python3 -m unittest discover -s tests -v
python3 -m jevintegrate.bench
echo '{"prompt":"/help"}' | python3 scripts/prompt_router.py; echo exit=$?
echo '' | python3 scripts/compact_hook.py
```

Hooks must exit 0. Bench policy match must stay 100% on the shipped corpus unless pick_lane changed on purpose. Version 0.2.0.
