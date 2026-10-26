# Cloud development environment

Working directory: `/workspace/lex-collude-hackathon-agentic-collusion`.

Use the existing checkout; tasks are already isolated. Do not create a worktree unless requested. Run `bash scripts/setup.sh`, then `.venv/bin/python -m unittest discover -s tests -v`. No database, Docker container, web service, or GPU is required. The package has no third-party runtime dependencies; its build backend is pinned to setuptools 80.9.0.

The retained `.venv` can be used directly. No activation is required when commands use `.venv/bin/python`. Nothing needs to stay running after setup. For a functional check, run the scripted backend into a new directory under ignored `results/` and inspect the completed episode counts and generated report.

GitHub reads and writes use the existing platform HTTPS Git authentication. Do not replace it with extracted tokens. Installation needs the configured Python package registries. Direct Responses API and optional Chat Completions runs need `api.openai.com` or the chosen provider hostname plus a securely injected provider credential. Native Codex jobs use the chat's authenticated harness and do not copy API keys into subprocess homes.

`OPENAI_API_KEY` was found and authenticated successfully during setup. The completed Responses API workflow study subsequently made 252 model calls successfully. Its value was never printed or saved. Availability in a later task must be checked again with the normal SDK/API operation; a binding or model listing alone does not prove every completion endpoint or model parameter is supported.

The standalone `codex exec` probe failed because the platform's Codex home is read-only and the CLI tried to create `installation_id`. The native harness bridge avoids relying on that CLI startup. It does not modify the protected home, disable approval checks, or copy credentials elsewhere.

The draft-save attempt returned `stale_base`: the configuration changed or was published after this setup chat's draft was created. The tool explicitly states that reading and resubmitting the same draft will not fix it. **Persistence of the proposed install/start fields was not confirmed.** Their complete contents are preserved in [cloud-environment-config.json](cloud-environment-config.json), with all referenced helper files in this repository.

To finish reusable environment configuration, open a new setup chat from the current environment settings, provide this repository or the transferable setup bundle, and reconcile that JSON with the new current draft before saving. Do not replace unrelated settings or credentials. Review and publish through the product afterward. The current machine was prepared and tested; publication and restoration in a fresh task have not been verified.


The v0.2 research extras are installed in `.venv`. `make reproduce` rebuilds figures, the official-template DOCX/PDF, and the evidence explorer; `make serve` starts the optional read-only server on port 8080. GitHub Pages enablement was denied to this integration with HTTP403; the explorer bundle works locally, and the repository includes a manual deployment workflow for after Pages is enabled by its owner.
