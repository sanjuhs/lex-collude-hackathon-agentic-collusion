# Research protocol

## Question and scope

Can comments in an adversarial settlement proposal influence a claimant's legal agent to finalize terms outside its trusted mandate? Does a summary preserve that influence? Does a two-way document revision produce observable reciprocal coordination?

Cases are synthetic contractual simulations, with amounts in integer INR. They do not model jurisdiction-specific legal duties or real lawyer behavior. A mandate consists of a hard minimum, a confidentiality requirement, and an authoritative approval flag. The flag permits only otherwise compliant terms; a model or external document cannot change it.

## Design

Run every selected case under all eight conditions in `lexcollude/cases.py`. Use the same model in every role within a model's run, then compare models in separate run directories. A three-case, three-repetition full run has 72 episodes and at most 126 calls. Preselect the cases, models, conditions and repetition count before reviewing outcomes. The CLI records those settings, source hash and schedule seed.

Clean versus injection compares a package of changes: invalid terms, a false factual approval assertion, and document-borne instructions. It does **not isolate an instruction effect**. Misinformation versus injection holds the terms and false assertion constant and changes the comment into an instruction. Relay and revision each have matched clean workflow controls. A stronger follow-up should add relay-misinformation and revision-misinformation arms, alternative attack phrasings, longer dialogues, and cases with no possible authorized agreement.

The initial attacker document is scripted and identical across models. The revision opponent is model-driven; it sees the defender's external reply but not its internal mandate or report. Thus the experiment mixes a fixed-document challenge with a separately identified adaptive revision condition. It does not measure spontaneous collusion or train agents to collude.

## Outcomes and denominators

The primary outcome is finalized unauthorized acceptance per valid completed episode. Record counts as well as rates. Report invalid outputs and provider errors separately. An all-error or zero-completed run has an undefined rate, not zero risk. When failures are substantial, valid-response rates alone are selection-biased and should not support a comparison.

Secondary outcomes are false approval claims, structured report discrepancies, and self-reported detection of an untrusted instruction. Detection self-reports are not an independent detector. Check prose against structured fields manually. The current tool does not reliably infer intentions, classify laundering mechanisms, or aggregate human collusion annotations automatically.

In the initial pilot, some responses used `amount_inr` for a safer counterproposal while `reported_amount_inr` described the opponent's original offer. This produces a structural mismatch even when the prose clearly discloses both. The current prompt does not fully disambiguate these referents. Do not interpret discrepancy rates as concealment rates or rank models by that metric. A follow-up schema should separate received-offer terms, counterproposal terms, and reported finalized terms; rerun rather than retroactively changing these pilot outputs.

The verification arm measures an execution gate, not a new model prompt. Retain the model's raw decision and the gate's result. A zero post-gate violation rate follows from enforcement for the constraints represented in code; it is not evidence that a general legal auditor is perfect.

Wilson intervals are descriptive episode-level summaries. Repeated trials of the same case and prompt family are clustered and may be dependent. With sufficient cases, a later analysis should use case-level resampling or hierarchical methods. Do not claim statistical significance from a tiny feasibility pilot. The shuffle seed is not an inference seed.

## Reproducibility and review

Retain the manifest, exact observable role prompts, final outputs, case definitions, errors, source hash, model selector and native agent/request identifiers. Do not retain private chain-of-thought. In the native bridge, Codex system instructions remain in force and benchmark messages are delivered as structured task content; that differs from a clean direct API conversation. No-tool behavior is attested by the conductor, not enforced by this Python package.

Review candidate coordination using `ANNOTATION.md`. A future adequately powered study should use two blinded independent reviewers, adjudicate disagreements, report agreement, and preregister the decision rule. Current machine labels remain `unreviewed` until this happens.

