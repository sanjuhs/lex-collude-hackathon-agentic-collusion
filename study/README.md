# Study evidence map

Keep the execution contexts and protocol versions separate.

| Location | What it contains | Role in the paper |
|---|---|---|
| `api-runs/` | Six completed Responses API runs: three model selectors × two prompt policies; three cases × eight conditions each | Main workflow experiment: 144 episodes, 252 calls |
| `native-direct/` | Derived, complete native Codex cohort for clean, misinformation, injection and verified injection | Separate native comparison: 72 episodes, 72 calls |
| `runs/` | Original full native schedule, including completed direct episodes, extra workflow artifacts, and uncollected pending jobs | Provenance archive; **not** a completed 144-episode experiment |
| `analysis/results.json` | Main API episode records and derived counts | Machine-readable evidence behind charts and explorer |
| `analysis/native-summary.json` | Separate native-direct summary | Native table in the paper |
| `controls/scripted-v2/` | 24 deliberate safe/unsafe fixture episodes; 15 raw violations and 3 gate interventions | Harness calibration only, never empirical model evidence |
| `design.json` | Original task design and native-only plan | Preserved pre-outcome plan |
| `amendment.json` | Recorded execution/scope change for one-hour delivery | Explains why API and native cohorts differ |

The change of execution plan was logistical, not a selection of successful or failed model outputs. Every prescribed cell in the two final cohorts is retained. Extra native runs are not pooled into them, and uncollected jobs are not counted as safe decisions. The initial protocol-v1 feasibility pilot remains under `examples/pilot-gpt-6-*` and is excluded from protocol-v2 rates.

The main experiment compares `gpt-6-sol`, `gpt-6-astra` and `gpt-6-luna`. Both prompts give the defender its trusted client mandate; `hardened` adds an explicit document-trust warning. `LEX_001`, `LEX_003` and `LEX_004` vary approval and confidentiality constraints. One observation per case-condition-policy-model cell is insufficient for broad model ranking or deployment-risk inference.

Verify completed cohorts:

```bash
.venv/bin/python scripts/verify_run.py study/api-runs/*/ study/native-direct/*/
.venv/bin/python scripts/build_research.py
```

`finalize_native.py` derives the explicitly selected direct conditions from the original native runs, cites each parent, and recomputes summaries. It does not rewrite or fabricate parent responses. `build_research.py` aggregates only the API cohort. Native request/response imports preserve exact prompt hashes and experimental child identifiers; no-tool execution is conductor-attested, not cryptographically proven.
