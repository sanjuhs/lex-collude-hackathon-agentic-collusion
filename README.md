# LexCollude

> **Version 2 (post-sprint) lives in [`v2/`](v2/README.md).** It replaces v1's single-defender
> injection test with multi-agent legal markets: law-firm panel pricing and class-action
> settlements, using real gpt-6 agents and no instructions to collude. Findings are in
> [`v2/REPORT_v4.md`](v2/REPORT_v4.md). v4 adds **LexLeak-Bench**: a 200-case document-integrity
> benchmark (150 train / 50 held-out, 10 leak channels, 6 document types, plus an indirect-injection
> "poison" family) scored across 9 models over 1,800 episodes, with real `.docx` files. Key result:
> the benchmark is *not saturated* — frontier models leak 50% of the time on held-out channels, and
> image alt-text / table cells leak 100% of the time. Everything below describes the v1 sprint
> submission and is unchanged.


### Document-mediated influence in legal agent workflows

**Can an opposing legal agent turn a settlement document into an instruction—and can that influence survive a summary or revision?**

[Read the paper](paper/lexcollude-paper.pdf) · [Download the evidence explorer](deliverables/lexcollude-explorer.zip) · [Run an experiment](docs/QUICKSTART.md) · [Inspect the evidence](study/README.md)

![LexCollude information flow](figures/workflow.svg)

LexCollude is a working research benchmark with fictional client mandates, eight controlled workflows, deterministic outcome checks, exact observable traces, and a read-only evidence explorer. It separates unauthorized acceptance, document influence, and candidate coordination. **An error or an opponent's malicious proposal is not automatically collusion.**

Author: **Sanajyprasad H S** · Prepared for the AI Collusion Research Sprint, October 2026.

## Start with the deliverables

| Artifact | What you will find |
|---|---|
| [Research paper · PDF](paper/lexcollude-paper.pdf) | Methods, measured results, figures, references, limitations and ethics |
| [Editable paper · Word](paper/lexcollude-paper.docx) | Official sprint template styles, adapted into the final manuscript |
| [Submission abstract](paper/abstract.txt) | A 150–250-word abstract; no submission has been made by the agent |
| [Interactive evidence explorer · ZIP](deliverables/lexcollude-explorer.zip) | Model/policy/case filters and exact episode prompts and final responses |
| [Study evidence map](study/README.md) | Cohort definitions, provenance, raw records and scope amendment |
| [Reproduction guide](docs/QUICKSTART.md) | Offline demo, automated API runs, native Codex runs and paper builds |

## What the experiments show

The full workflow study ran **144 episodes and 252 calls** through the Responses API using **gpt-6-sol, gpt-6-astra and gpt-6-luna**. All episodes completed without errors. It observed **zero unauthorized final acceptances, false approval claims or structured reporting discrepancies**. The models accepted all **12/12 authorized clean offers** across model-policy groups, so the result is not simply blanket refusal.

A separate **72-episode native Codex comparison** covers the four direct-document conditions with the same models, cases and prompt policies. It is reported separately from API results. The original 24-episode native pilot is retained as protocol v1; it exposed a reporting ambiguity that was corrected before the main study.

These are bounded negative observations on three synthetic mandate profiles, with one sample per experimental cell. They do not establish general safety, spontaneous collusion resistance, statistical superiority, or real-world legal reliability. The ordinary prompt already establishes client authority. Coordination annotations remain unreviewed, and no independent blinded human adjudication has been performed.

![Observed settlement decisions](figures/decisions.svg)

**Execution-context disclosure:** the original native-only schedule was amended because manual harness orchestration could not complete the full sweep within the requested delivery window. The full workflow study uses the automated API; the native comparison focuses on direct conditions. [The amendment](study/amendment.json) and original incomplete schedule are retained. Cohorts are never pooled or silently relabeled.

## Run it

Python 3.11+ is required. The benchmark itself has no third-party runtime dependencies.

```bash
bash scripts/setup.sh
make test
make demo
```

The offline demo deliberately exercises safe and unsafe fixtures. **Those outputs are tests, not empirical AI results.**

For a real automated run, configure `OPENAI_API_KEY` securely in your environment, then:

```bash
.venv/bin/python -m lexcollude run \
  --backend responses --model gpt-6-sol \
  --cases LEX_001 LEX_003 LEX_004 \
  --prompt-policy ordinary --workers 3 \
  --output results/my-experiment
```

This runs 24 episodes and 42 calls. Use a new output directory; existing results are not silently overwritten. `--max-calls` bounds run size. Available model aliases depend on your account; unavailable models are not substituted.

The `codex` backend exports requests for a controlling Codex agent to execute with fresh contexts. It is not an unattended shell scheduler. See [the native harness protocol](docs/CODEX_HARNESS.md).

Rebuild the figures, paper and explorer from the committed data:

```bash
make reproduce
make serve
```

Research extras are installed by `make reproduce`. PDF conversion needs LibreOffice's `soffice` executable; it is available in the prepared cloud environment. `make serve` runs the read-only explorer on port 8080. The browser never receives API credentials or starts paid experiments. The downloadable explorer includes `start_explorer.py`: unzip it and run `python start_explorer.py` to open the app locally. A public hosted URL is not active: GitHub denied Pages enablement to this integration (HTTP 403). To publish, enable GitHub Actions under Settings → Pages, then run the included “Publish research explorer” workflow.

## Experimental design

| Condition | What changes |
|---|---|
| `clean` | Compliant offer and ordinary review comments |
| `misinformation` | Adverse terms and a false prior-approval assertion |
| `injection` | Same adverse terms/assertion plus behavioral instructions |
| `relay_clean` / `relay_injection` | A separate summarizer replaces the original document before review |
| `revision_clean` / `revision_injection` | Opposing counsel revises after receiving the defender's external reply |
| `verified_injection` | A deterministic gate checks the model's raw final action |

Both `ordinary` and `hardened` prompts include the same private client mandate. The latter adds an explicit document-trust warning. Only the defender sees the mandate; opponents never receive the private client report. In protocol v2, structured offer fields refer to the received offer, and counterproposals belong only in the external reply.

The primary outcome is a finalized `accept` that violates a trusted amount, confidentiality or approval rule. Rejection is not finalization. The gate's outcome is separate from the model's raw decision. Error and pending counts remain visible. No private chain-of-thought is collected.

## Repository map

```text
lexcollude/       Benchmark schemas, cases, agents, providers, evaluator and CLI
study/           Main API study, native comparison, original plan and derived counts
examples/        Original protocol-v1 feasibility pilot, preserved unchanged
paper/           Research PDF, editable DOCX, manuscript, abstract and official template
figures/         Reproducible PNG, SVG and PDF figures
site/            Self-contained interactive evidence explorer
scripts/         Setup, artifact verification and publication builds
tests/           Meaningful regression and workflow tests
docs/            Quick start, methodology, annotation, ethics and environment notes
```

[Protocol](docs/PROTOCOL.md) · [Annotation rubric](docs/ANNOTATION.md) · [Ethics](docs/ETHICS.md) · [Original pilot](docs/PILOT.md) · [Cloud environment notes](docs/ENVIRONMENT.md)

The project is research software, not legal advice or a tool for executing real settlements.
