# accudist -- notes for coding agents

Read `AGENTS.md`. Generated files (`src/_ufuncs_generated.c`, `accudist/_api.py`,
`accudist/rmath.py`, `docs/api-reference.md`) come from `functions.toml` via
`python tools/regen.py`; never edit them by hand. Never edit `vendor/nmath/` in
place; change `vendor/patches/` and re-run `python tools/sync_rmath.py`.
