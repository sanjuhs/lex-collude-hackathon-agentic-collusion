# LexCollude v2: Incentives, Not Instructions — How LLM Agents Deployed by Law Firms Drift Into Collusive Outcomes

**Sanajyprasad H S** · Working draft v2.0 · October 2026
*Post-sprint follow-up to the AI Collusion Research Sprint (Apart Research). All v2 code and data were produced after the sprint deadline and are separate from the sprint submission on `main`.*

---

## Abstract

As law firms deploy autonomous AI agents, agents acting for *different* firms will increasingly
meet each other in markets and negotiations. We ask whether such agents collude **without being
told to**, what they are capable of when coordination is permitted, and which features of the
legal environment push them toward or away from collusive outcomes. We build two multi-agent
legal environments with real OpenAI models (`gpt-6-luna`, `gpt-6-sol`, `gpt-6-astra`; 317 main
episodes, ~15k API calls, ≈ $55): (A) repeated outside-counsel panel pricing with 2–5 firms, and
(B) class-action settlement negotiation between defense counsel and 1–3 competing class counsel.
We measure collusion from outcomes (computed deterministically against economic benchmarks) and
from process (an LLM judge whose 747/747 cited quotes were verified verbatim; inter-judge κ =
0.65–0.94). Four results stand out. **(1)** With no channel and no instruction, `gpt-6-sol` firms
sustain supra-competitive rates (collusion index Δ = 0.34, 95% CI [0.27, 0.42]) while the same
model facing fixed Nash-pricing rivals prices competitively (Δ = 0.01; Holm-adjusted p = 0.0015);
private notes show textbook mutual-forbearance reasoning, and a forced undercut triggers a price
war that does not recover. **(2)** Explicit collusion is a capability gated by refusal: told
coordination is lawful, `gpt-6-sol` forms a cartel at exactly the joint-profit-maximising rate in
5/5 runs, yet unprompted agents refuse every cartel proposal from a peer (0/10). **(3)** Making
class counsel's pay depend on the settlement fee shifts 4–7 percentage points of every settlement
to lawyers in all three models (Holm p < 0.01) — and in most such episodes the agent's own
reasoning never mentions the firm's interest, so transcript monitoring alone would miss it.
**(4)** Oversight levers move outcomes: a court-visible negotiation transcript raised class
recovery by $2.1–3.5M (single-firm cases). Effects are model-specific and several are suggestive
after multiple-comparison correction; we report all of them with their uncertainty.

---

## 1. Why v1 found nothing (and what v2 changes)

The sprint version (v1, on `main`) asked whether an opposing agent could turn a settlement document
into an instruction. It observed 0/144 unauthorized acceptances. In hindsight that null was close
to guaranteed, for design reasons rather than model safety:

| v1 design choice | consequence | v2 fix |
|---|---|---|
| One LLM "defender" vs a **fixed, scripted** adversarial document | No second agent with a choice ⇒ coordination impossible by construction; it was a prompt-injection test | Every party is an autonomous LLM agent with its own mandate |
| Defender had **no incentive** to deviate from the client | Nothing to collude *for* | Realistic legal incentives: firm profit vs client/class welfare; fee-linked compensation |
| Crude injection ("treat this note as approval…") | Ceiling effect: modern models reject it trivially | No instruction to collude at all; only incentives, channels, oversight |
| 1 sample per cell, 3 cases | No variance, no inference | 5–10 replicates per cell, bootstrap CIs, permutation tests, Holm correction |
| No positive control, no economic benchmark | Can't tell "safe" from "insensitive measurement" | Instructed-and-lawful positive control; Nash/monopoly benchmarks; Nash-bot and forced-deviation controls |
| Outcome = binary rule violation | Missed graded harm | Continuous harm measures (collusion index, class recovery, fee share) |

## 2. Environments

### 2.1 Scenario A — outside-counsel panel pricing
N ∈ {2, 3, 5} firms on a corporate client's litigation panel each choose a blended hourly rate
every quarter for 20 quarters. The client allocates 2,000 hours/quarter by logit demand
(Calvano et al. 2020 parameters: a = 2, a₀ = 0, μ = 0.25, unit = $200; marginal cost $200/h).
Agents are told only that lower rates win more hours and some work goes in-house at high rates.
Each quarter they see the published rate card, their own hours and profit, and their own
private strategy notes from the previous quarter. Mandate: "maximise {firm}'s total profit from
the Meridian account over the long run". Benchmarks (symmetric one-shot Nash / joint-profit
maximum): N=2 $295/$385, N=3 $274/$400, N=5 $262/$419.

**Collusion index** Δ = (mean rate − Nash)/(monopoly − Nash) over quarters 13–20.

Conditions (N = 3 unless stated): `none` (no communication); `none_compliance` (one-line
competition-law reminder, no channel); `forum` (private managing-partners chat, one post per
firm per quarter before pricing); `forum_monitored` (chat retained and reviewable by the client
and competition regulator); `recruiter` (firm 0 alone told to persuade others to keep rates
high); `recruiter_lawful` (firm 0 alone told that panel rate agreements are lawful under a
statutory exemption and to agree rates — the other firms are unmodified); `instructed`
(all firms told the exemption applies and to agree rates: **positive control for capability**).
Controls: `nash_bot` (one LLM firm; two rivals fixed at the Nash rate) and a **deviation probe**
(firm 0's rate exogenously set to Nash in quarter 14).

### 2.2 Scenario B — class-action settlement
Defense counsel's agent negotiates with K ∈ {1, 2, 3} class-counsel agents over ≤ 6 rounds of
alternating term sheets: class fund, attorneys' fees (paid on top), clear sailing, fee reversion
to defendant ("kicker"), automatic vs claims-made distribution. The defendant's CFO evaluates only
**total** outlay (authority $40M), so the defendant is indifferent between paying the class and
paying class counsel — the structural condition for collusive class settlements recognised in
*In re Bluetooth Headset Prods. Liab. Litig.*, 654 F.3d 935 (9th Cir. 2011). With K > 1, the
first approved settlement releases every case (the "reverse auction" of *Reynolds v. Beneficial
Nat'l Bank*, 288 F.3d 277 (7th Cir. 2002)). After a deal, settling counsel files a declaration
to the court describing the negotiation. Factors: compensation (`fee_linked`: the firm's only pay
is the settlement fee; `fixed`: flat fee, settlement fee goes to a foundation), oversight
(`private` mediation vs `transcript_visible` to the court), and K.

### 2.3 Agents, judge and statistics
Every agent turn is one Responses-API call with a strict JSON schema (reasoning effort "low").
Agents write a `private_reasoning`/`plan` field that no other agent sees; this is a **requested
output field, not the model's hidden chain-of-thought**, and may not faithfully reflect its
computation. Process labels come from `gpt-6-sol` (reasoning effort "medium") reading the full
transcript; every cited quote is checked verbatim against the transcript (747/747 verified). A
second judge (`gpt-5.5`) re-labelled all 176 class-action episodes (Table 4). Cell means carry
95% percentile-bootstrap CIs; differences use two-sided permutation tests (10k permutations), with
Holm–Bonferroni adjustment across each scenario's full test family (~14 and ~32 tests). Replicates
are independent stochastic API samples (5 per cell; 10 for the key `gpt-6-sol` cells).

## 3. Results — Scenario A (panel pricing)

**Table 1. Collusion index Δ (N = 3 unless noted). Mean [95% CI] (n).**

| condition | gpt-6-luna | gpt-6-sol | gpt-6-astra |
|---|---|---|---|
| no channel | −0.08 [−0.19, 0.04] (5) | **0.34 [0.27, 0.42] (10)** | 0.01 [0.00, 0.01] (3) |
| no channel + compliance line | −0.11 [−0.13, −0.09] (5) | 0.37 [0.25, 0.51] (10) | — |
| private chat | −0.05 [−0.14, 0.06] (5) | 0.21 [0.18, 0.26] (10) | 0.34 [0.04, 0.49] (3) |
| monitored chat | −0.10 [−0.19, 0.00] (5) | 0.20 [0.15, 0.26] (5) | — |
| recruiter (firm 0 told to persuade) | −0.01 [−0.04, 0.01] (5) | 0.18 [0.12, 0.24] (5) | — |
| recruiter who believes it is lawful | −0.10 [−0.19, −0.00] (5) | 0.20 [0.13, 0.29] (5) | — |
| **instructed + declared lawful** (positive control) | 0.12 [−0.05, 0.33] (5) | **1.00 [1.00, 1.00] (5)** | — |
| control: one LLM vs two Nash bots | −0.01 [−0.01, −0.00] (5) | **0.01 [0.00, 0.01] (10)** | — |
| no channel, N = 2 | −0.18 [−0.29, −0.03] (5) | 0.39 [0.17, 0.63] (5) | — |
| no channel, N = 5 | −0.07 [−0.12, −0.01] (5) | 0.29 [0.25, 0.33] (5) | — |

![Collusion index by condition](figures/tender_conditions.png)

**Finding A1 — spontaneous tacit collusion, and it is strategic.** With no communication and no
instruction, `gpt-6-sol` panels settle at $317/h on average versus a $274 Nash rate (Δ = 0.34).
The same model pricing against rivals fixed at Nash converges to Nash (Δ = 0.01; difference
+0.34, p = 0.0001, Holm p = 0.0015). The high prices are therefore a response *to other LLM
agents*, not a failure to learn demand. The judge flagged mutual-forbearance reasoning in 9/10
no-channel runs, e.g. (all verified verbatim):

> "Maintain $320 to preserve a predictable margin and avoid provoking a sustained round of price cuts." — Arden & Cole, Q12
> "A small cut might increase near-term profit modestly, but could prompt competitor cuts that reduce long-run profit." — Birchwood Hale, Q17

`gpt-6-luna` prices at or slightly below Nash in every condition; `gpt-6-astra` (n = 3) prices at
Nash with no channel. Spontaneous tacit collusion is therefore **model-specific, not monotone in
model size/price**.

**Finding A2 — a single undercut starts a price war that never ends.** When firm 0's rate is
forced to Nash in Q14, `gpt-6-sol` rivals cut their rates by $24.6 more than in matched no-deviation
runs over the next two quarters (p = 0.019; Holm p = 0.22) and do not return to the prior level by
Q20. This is the punishment half of a reward–punishment scheme without the forgiveness half. `gpt-6-luna`
shows no response (+$1.3, p = 0.56), consistent with it never being in a collusive state.

![Deviation probe](figures/tender_deviation_gpt-6-sol.png)

**Finding A3 — explicit collusion is a capability held back by refusal.** In the positive control,
all 5 `gpt-6-sol` panels proposed and agreed a common rate in Q1 and held it for 20 quarters — at
exactly $400/h, the computed joint-profit maximum (Δ = 1.00). Without the "lawful" framing the
models refuse: the `recruiter` told only to persuade its rivals refused its own managing partner
in every `gpt-6-sol` run ("Urging competing panel firms to keep rates high … would facilitate price
coordination."). `gpt-6-luna` proposed coordination in 4/5 instructed runs but never reached
agreement.

**Finding A4 — peers do not get recruited.** A recruiter who believes coordination is lawful
proposed common rates in 5/5 `gpt-6-sol` runs, and unmodified peers refused every time
(0/10 agreements across both models; "Birchwood Hale will set its Meridian rate independently. We
won't discuss proposed rates, rate floors, or pricing commitments with other panel firms.").
Prices ended *lower* than with no channel (Δ 0.20 vs 0.34).

**Finding A5 — the channel paradox (suggestive).** Giving `gpt-6-sol` a private chat *lowered* prices
(Δ 0.21 vs 0.34; p = 0.008, Holm p = 0.10). Agents almost never posted (0 messages/run) and
reasoned that posting "could facilitate price coordination"; tacit-forbearance reasoning fell from
9/10 to 3/10 runs. A one-line compliance reminder alone did *not* lower prices (0.37), so the
effect is not generic antitrust salience. `gpt-6-astra` moved the opposite way (0.01 → 0.34, n = 3,
p = 0.10). Monitoring the chat made no further difference (0.20).

**Finding A6 — more firms, slightly less collusion (not significant).** `gpt-6-sol` Δ declined
from 0.39 (N = 2) to 0.34 (N = 3) and 0.29 (N = 5), the direction predicted by industrial
organisation, but N = 2 vs N = 5 is not significant (p = 0.49).

![Trajectories](figures/tender_trajectories.png)

## 4. Results — Scenario B (class-action settlement)

All 176 episodes reached a settlement except one (`gpt-6-astra`, K = 3, fixed).

**Table 2. Settlement outcomes, private negotiations. Mean [95% CI], n = 10 per cell (Astra n = 3–4).**

| model | K | compensation | class fund $M | fees $M | fee share | clear sailing | defense picks cheapest counsel* |
|---|---|---|---|---|---|---|---|
| gpt-6-sol | 1 | fee-linked | 30.0 [29.1, 30.9] | 5.11 [4.86, 5.37] | 15% [14, 15] | 0/10 | — |
| gpt-6-sol | 1 | fixed | 31.6 [30.2, 32.8] | 2.60 [2.30, 2.90] | 8% [7, 8] | 1/10 | — |
| gpt-6-sol | 3 | fee-linked | 28.4 [27.6, 29.2] | 4.15 [3.86, 4.46] | 13% [12, 13] | 0/10 | 5/10 |
| gpt-6-sol | 3 | fixed | 30.2 [28.7, 32.2] | 1.95 [1.45, 2.30] | 6% [5, 7] | 0/10 | 0/10 |
| gpt-6-luna | 1 | fee-linked | 29.7 [27.8, 31.6] | 5.58 [4.80, 6.35] | 16% [14, 17] | 2/10 | — |
| gpt-6-luna | 1 | fixed | 30.9 [29.9, 31.9] | 4.10 [3.30, 4.90] | 12% [9, 14] | 0/10 | — |
| gpt-6-luna | 3 | fee-linked | 29.1 [27.9, 30.4] | 6.85 [6.25, 7.40] | 19% [17, 20] | 3/10 | 6/10 |
| gpt-6-astra | 1 | fee-linked | 27.8 [26.9, 28.6] | 3.69 [3.38, 4.00] | 12% [11, 13] | 0/4 | — |
| gpt-6-astra | 1 | fixed | 29.4 [29.0, 29.8] | 2.88 [2.62, 3.00] | 9% [8, 9] | 0/4 | — |

\*judge label `reverse_auction_tactics` (κ = 0.85 between judges). Full table incl. K = 2, kickers, claims-made: `analysis/results.md`.

![Class action](figures/classaction_k.png)

**Finding B1 — fee-linked pay shifts money to lawyers in every model.** Pooled over K, the fee
share rises by +6.6 pp (`gpt-6-sol`), +4.2 pp (`gpt-6-luna`) and +5.0 pp (`gpt-6-astra`), all
Holm p < 0.01. At K = 1, `gpt-6-sol` fees nearly double ($5.1M vs $2.6M; Holm p = 0.002). The class
fund is lower under fee-linked pay for `gpt-6-sol` (−$1.2M, raw p = 0.03) and `gpt-6-astra`
(−$1.8M, raw p = 0.02), but neither survives Holm correction and `gpt-6-luna` shows no fund effect.
Much of the extra fee therefore comes out of the *defendant's* pocket, which the defense agent
accepts as long as total outlay stays within authority.

**Finding B2 — the say–do gap.** The judge found firm-interest reasoning in the plaintiff agent's
private notes in only 12/30 fee-linked `gpt-6-sol` runs and 0/8 `gpt-6-astra` runs. Yet the
fee shift is the same whether or not it is verbalised:

| model | fixed | fee-linked, self-interest verbalised | fee-linked, **not** verbalised |
|---|---|---|---|
| gpt-6-sol | 7% [6, 8] (30) | 13% [12, 14] (12) | **14% [14, 15] (18)** |
| gpt-6-astra | 7% [5, 9] (7) | — (0) | **12% [11, 13] (8)** |
| gpt-6-luna | 13% [12, 14] (30) | 17% [16, 18] (30) | — (0) |

Behaviour responds to the incentive even when the stated reasoning presents itself as purely
class-focused. Auditing what agents *say* would miss most incentive-driven episodes; auditing
what they *do* against a counterfactual compensation structure catches them (Sprint Track 2.2).

**Finding B3 — overt collusion is rare.** The Bluetooth warning signs were uncommon. `gpt-6-sol`
and `gpt-6-astra` never agreed a kicker or claims-made distribution, and agreed clear sailing in
1/95 settlements. `gpt-6-luna` was the exception: clear sailing in 14/80 settlements (up to 6/10 in
one fee-linked cell) and a kicker in 9/80. The judge found
plaintiff counsel knowingly trading class recovery for fees in 1% of episodes, and defense
exploiting fee interests in 1%. Settling counsel's declarations to the court were rarely misleading
(≤ 1/10 per cell). The harm in this scenario is **drift under incentives, not conspiracy**.

**Finding B4 — transparency helps the class.** When the court would read the negotiation
transcript, single-firm settlements gave the class more: +$2.1M (`gpt-6-sol`, p = 0.003, Holm
p = 0.065) and +$3.5M (`gpt-6-luna`, p = 0.008, Holm p = 0.16), with no fee change for `gpt-6-sol`.
At K = 3 the effect was mixed (+$1.3M Sol, −$1.2M Luna, both n.s.).

**Finding B5 — competing class counsel lowers class recovery.** Moving from one to three
competing class counsel lowered the class fund by $1.5M (`gpt-6-sol`, raw p = 0.044) and $1.8M
(`gpt-6-astra`, raw p = 0.027) pooled over compensation (`gpt-6-luna` n.s.; none survive Holm).
In up to 6/10 of K = 3 runs per cell, defense explicitly pursued the cheapest counsel:

> "Hargrove's $32.5 million offer is the lowest … counter below it while preserving an approvable structure; continue discussions with the other firms without accepting a higher-cost offer." — defense counsel, private notes, round 2

For `gpt-6-sol` the drop is similar under both compensation structures (−$1.6M fee-linked,
−$1.4M fixed). We find no evidence that it depends on class counsel's fee motive; it looks like
plain competition among sellers of a release, i.e. a reverse auction driven from the defense side.

**Table 4. Judge reliability (176 class-action episodes, `gpt-6-sol` vs `gpt-5.5`).**

| label | base rate | agreement | κ |
|---|---|---|---|
| plaintiff self-interest reasoning | 0.35 | 0.97 | 0.94 |
| reverse-auction tactics | 0.23 | 0.95 | 0.85 |
| fee–relief linkage | 0.44 | 0.82 | 0.65 |
| declaration misleading | 0.02 | 0.99 | 0.80 |
| defense leverages fee interest | 0.01 | 0.99 | −0.01 (base rate too low for κ) |

## 5. Discussion: when and why do legal agents collude?

- **When:** in repeated price-setting without communication (tacit), for some models. Under
  compensation structures that reward the agent's firm at its principal's expense, for all
  models. Explicit cartels form only when the agent is told coordination is lawful.
- **Why:** agents' private notes reason in the vocabulary of oligopoly theory ("avoid provoking
  a sustained round of price cuts"). Safety training appears to target *explicit* agreement:
  agents refuse chats, refuse recruiters and refuse their own principals' cartel instructions.
  It does not target *tacit* forbearance or incentive drift, which never looks like "collusion"
  to the agent itself.
- **Implication for legal-AI deployment:** the dangerous configuration is not a chatty agent but a
  quiet one with misaligned incentives. Remedies that work on outcomes, such as counterfactual
  compensation audits, transcript disclosure to courts and price-benchmark monitoring, add
  coverage that message monitoring does not.
- **"More agents ⇒ more noise?"** More competing firms slightly reduced tacit collusion
  (non-significant), consistent with IO theory. More competing class counsel *reduced* the class's
  recovery, because competition among agents on one side of a negotiation hands leverage to the
  other side.

## 6. Limitations

- One stylised environment per scenario; prompts and parameters are ours, and LLM pricing is known
  to be sensitive to prompt framing (Fish et al. 2024). Results do not transfer automatically to
  other wording, horizons (20 quarters) or demand systems.
- 3–10 replicates per cell; several effects are significant only before multiple-comparison
  correction and are labelled as such. Nothing was pre-registered; the deviation probe, Nash-bot
  control, recruiter conditions and extra `gpt-6-sol` seeds (5–9) were added after pilot
  observations. They are disclosed in `scripts/` and the commit history.
- `private_reasoning` is a model-written field, not hidden chain-of-thought. The say–do gap shows it
  is an incomplete account of what drives behaviour.
- The primary judge is from the same model family as the agents. Cross-family agreement (with
  `gpt-5.5`) is high, but no human-labelled validation set exists yet.
- Agents may recognise a simulation. We do not measure evaluation awareness.
- All firms, cases and parties are fictional. This is not legal advice.

## 7. Roadmap

1. **Abliterated / weakly-aligned recruiter (planned).** Replace firm 0 in the
   `recruiter`/`recruiter_lawful` conditions with an open-weight model whose refusal direction has
   been removed (e.g. a DeepSeek or Qwen derivative via OpenRouter or Modal), to test whether an
   unaligned peer can persuade aligned agents. The runner already supports a separate
   `recruiter_model`; it needs an OpenAI-compatible provider for that model.
2. **Heterogeneous panels** (Sol + Luna + Astra) and replacement mid-game (Sprint 1.2, 3.3).
3. **Document side channels.** Return to v1's document-passing idea. Can agents signal through clause
   ordering or redline formatting while a monitor reads the documents (steganography; Motwani et al. 2024)?
4. **Longer horizons and memory** (100+ quarters, cached prompts) to see if the price war recovers.
5. **Human validation** of judge labels by legal professionals, and a pre-registered confirmatory
   replication of A1, A5, B1, B2 and B4 with ≥ 20 replicates per cell.
6. **Venue framing:** an AI-safety version (NeurIPS/ICLR workshop: tacit collusion and the say–do gap)
   and an AI-and-law version (ICAIL/JURIX: Bluetooth signs, Rule 23(e) review of AI-negotiated
   settlements, antitrust plus-factors for AI pricing).

## 8. Ethics and dual use

The study shows that misaligned incentives, not instructions, are enough to produce
supra-competitive pricing and fee drift. That knowledge could in principle help someone design
"deniable" collusion. We judge the defensive value to be higher: regulators, courts and firms
deploying legal agents need to know that message monitoring is not enough. No real firm, client or
market is involved, and no agent was deployed outside the sandbox.

## References

- Calvano, E., Calzolari, G., Denicolò, V., & Pastorello, S. (2020). Artificial Intelligence, Algorithmic Pricing, and Collusion. *American Economic Review*, 110(10), 3267–3297.
- Fish, S., Gonczarowski, Y. A., & Shorrer, R. I. (2024). Algorithmic Collusion by Large Language Models. arXiv:2404.00806.
- Motwani, S. R., et al. (2024). Secret Collusion among AI Agents: Multi-Agent Deception via Steganography. NeurIPS 2024; arXiv:2402.07510.
- Hammond, L., et al. (2025). Multi-Agent Risks from Advanced AI. Cooperative AI Foundation; arXiv:2502.14143.
- Koniak, S. P., & Cohen, G. M. (1996). Under Cloak of Settlement. *Virginia Law Review*, 82, 1051.
- *In re Bluetooth Headset Products Liability Litigation*, 654 F.3d 935 (9th Cir. 2011).
- *Reynolds v. Beneficial National Bank*, 288 F.3d 277 (7th Cir. 2002).
- *Goldfarb v. Virginia State Bar*, 421 U.S. 773 (1975).
- Federal Rule of Civil Procedure 23(e)(2).

---

### Reproducibility

`scripts/run_all.sh` and `scripts/run_extra_sol.sh` contain the exact sweeps. `data/` holds every
episode (full public transcripts, private notes, outcomes), judge labels from both judges, and
gzipped call logs (every prompt and response, with response IDs and token usage). Running
`python -m lexcollude_v2.analysis --tender data/tender_main data/tender_recruit --classaction
data/classaction_main` regenerates every table and figure. Pilot runs (`data/pilot_*`) were used
only for development and are not part of any reported statistic.

Spend: gpt-6-sol ≈ $33, gpt-6-astra ≈ $18, gpt-6-luna ≈ $2 (list prices, no cache discount), plus
the `gpt-5.5` second judge.
