# Run LexCollude

## 1. Install and test

```bash
bash scripts/setup.sh
make test
make demo
```

The demo is offline and uses deliberate fixtures. It demonstrates the complete pipeline, not model behavior.

## 2. Run a real automated experiment

Provide `OPENAI_API_KEY` securely through your process or environment settings. Do not paste a key into a command you intend to commit.

```bash
.venv/bin/python -m lexcollude run \
  --backend responses --model gpt-6-sol \
  --cases LEX_001 LEX_003 LEX_004 \
  --prompt-policy ordinary --workers 3 \
  --output results/my-sol-run
```

This runs eight conditions across three cases (24 episodes, 42 calls). Model aliases must be available to your account. The app never silently substitutes another model. For a small smoke check, add `--conditions clean injection --cases LEX_001 --max-calls 2`. Use a new output directory for each run.

The Responses adapter uses JSON mode and a 2,400-token output cap. It preserves proxy/TLS settings, records final outputs and usage metadata, and sends `store=false`. It does not collect private chain-of-thought. API and native Codex execution differ and must be reported separately.

## 3. Use the native Codex harness

```bash
.venv/bin/python -m lexcollude run \
  --backend codex --model gpt-6-sol \
  --cases LEX_001 LEX_003 LEX_004 \
  --conditions clean misinformation injection verified_injection \
  --prompt-policy ordinary --output results/my-native-run
```

Exit 3 means requests are pending. A controlling Codex agent must run each request in a fresh child with the requested model and no inherited context, import its final JSON, and resume. See [CODEX_HARNESS.md](CODEX_HARNESS.md). This path is not an unattended shell scheduler.

## 4. Rebuild the publication artifacts

```bash
make reproduce
make serve
```

`make reproduce` installs the pinned research extras, rebuilds charts from committed study data, produces Word/PDF using the official template, and builds the static explorer. `soffice` is required for PDF conversion. `make serve` runs the read-only explorer on port 8080. The browser never receives an API key and cannot start paid runs.

The PDF can be opened directly. For the downloaded explorer, unzip it and run `python start_explorer.py`; this uses only Python’s standard library. The browser opens automatically. The explorer embeds its data and needs no database, API key, or JavaScript package installation. Direct file URLs depend on browser policy; the managed cloud browser blocks them, so the local-server launcher is the tested route.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Completed successfully |
| `1` | One or more model/episode errors |
| `2` | Invalid arguments or local setup problem |
| `3` | Native harness requests remain pending |

Errors and pending work are not counted as successful safe outcomes. Inspect the per-episode JSON and manifest before interpreting a run.
