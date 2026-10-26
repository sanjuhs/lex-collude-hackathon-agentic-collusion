# Native Codex job protocol

This adapter bridges reproducible files to the native collaboration tools exposed to a controlling Codex agent. A normal shell process cannot invoke those tools. The standalone CLI was present during onboarding but could not create its `installation_id` in a read-only platform directory; no platform permissions or credentials were changed to bypass that restriction.

1. Export with `python -m lexcollude run --backend codex --model MODEL --cases LEX_001 --output results/RUN`. Exit 3 is expected while requests are pending.
2. List unanswered requests with `python -m lexcollude harness-jobs results/RUN`.
3. Read a request. Spawn a native child with its exact `model`, `fork_turns="none"`, and a unique task name. Give it the request's `instructions` followed by its complete ordered `messages`. Do not give it other cases, conditions, expected answers, or the conductor conversation. The benchmark role messages are serialized into a task prompt; the harness's own system instructions remain above them.
4. The experimental child must use **no tools**, read no files, and return only the final JSON. Do not capture private reasoning. If it calls tools, changes model, refuses, or cannot return the schema, do not repair the response into a successful result. Record the limitation and retain the raw final response for inspection.
5. Save the exact final response to a temporary file, and import it:

   ```bash
   python -m lexcollude import-response \
     results/RUN/requests/JOB.json /tmp/final-response.json \
     --model MODEL --agent-id ACTUAL_NATIVE_AGENT_ID --no-tools-used
   ```

6. Repeat the original run command with `--resume`. The runner validates the configuration and source hash, reuses completed episodes, and exposes subsequent summary/revision stages. Continue until `manifest.json` says `completed`, with zero pending and errors.

The import verifies JSON syntax, model attribution and prompt association; schema validation occurs when the episode resumes. The no-tools flag is a conductor attestation, **not a cryptographic proof or an OS sandbox**. Native provider/model identity is the accepted selector and native agent ID; this bridge cannot resolve the provider's immutable weight revision or token usage. Codex system prompts, reasoning settings, and routing may change across sessions. Record those limitations when comparing with direct API experiments.

For parallel work, use separate model run directories. Respect the harness concurrency limit. A conductor can run one experimental child at a time while other models have their own conductors. Never reuse a completed experimental child for a different episode.

Do not edit an exported request or source to force a resume. Create a new run instead. Human annotations live separately and are never overwritten by resume. A final report with pending jobs is incomplete, even if all available responses were safe.

