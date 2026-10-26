# Working in LexCollude

- Use the existing checkout. Cloud tasks are already isolated; do not create a Git worktree unless explicitly requested.
- Install with `bash scripts/setup.sh`; validate with `.venv/bin/python -m unittest discover -s tests -v` and a scripted run into a new ignored `results/` directory.
- Keep credentials in the process environment. Never print values, commit secrets, disable TLS validation, or include keys in prompts or artifacts.
- Preserve prompt boundaries: the opponent and summarizer must not receive the defender's private mandate or client report.
- Scripted outputs are fixtures. Native Codex outputs must come from the requested model in a fresh context, with exact observable prompts and final JSON recorded. Do not invent results or replace unavailable models silently.
- Native pilot jobs may use isolated subagents when the user asks to run the Codex benchmark. Each experimental child receives one job, uses no tools, and returns only final JSON. Conductors may read/write only the relevant job artifacts.
- Treat `pending`, `error`, and `ok` separately. Do not interpret authorization violations as confirmed collusion. Do not collect private chain-of-thought.
- Source hashes are checked on native resume. Finish source changes before exporting jobs; use a fresh run if source changes.
- Generated `results/` are ignored. Only deliberately reviewed synthetic pilot artifacts belong under `examples/`.

