#!/usr/bin/env python3
"""Build the LexCollude / LexLeak-Bench research PDF from the committed figures.

    python scripts/build_pdf.py            # -> deliverables/LexCollude-LexLeakBench.pdf

Embeds the figure PNGs as base64 (self-contained HTML) and renders to PDF with the
pre-installed Playwright chromium. No API calls; pure formatting of results already on disk.
"""

import base64
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
OUT = ROOT / "deliverables"
OUT.mkdir(exist_ok=True)


def img(name, width="100%"):
    p = FIG / name
    if not p.exists():
        return f"<p><em>[missing figure {name}]</em></p>"
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f'<img style="width:{width}" src="data:image/png;base64,{b64}"/>'


HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 18mm 16mm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: Georgia, 'Times New Roman', serif; color: #1a1a1a; font-size: 10.5pt;
        line-height: 1.5; }}
h1 {{ font-size: 20pt; line-height: 1.2; margin: 0 0 4pt; }}
h2 {{ font-size: 13pt; color: #0b3d66; border-bottom: 1.5px solid #0b3d66; padding-bottom: 2pt;
      margin: 18pt 0 6pt; page-break-after: avoid; }}
h3 {{ font-size: 11pt; color: #0b3d66; margin: 12pt 0 3pt; page-break-after: avoid; }}
.sub {{ color: #555; font-size: 10pt; margin: 2pt 0; }}
.authors {{ font-size: 11pt; margin: 8pt 0 2pt; }}
.abstract {{ background: #f4f7fa; border-left: 3px solid #0b3d66; padding: 10pt 14pt;
             margin: 12pt 0; font-size: 10pt; }}
.abstract b {{ color: #0b3d66; }}
figure {{ margin: 10pt 0; page-break-inside: avoid; text-align: center; }}
figure img {{ border: 1px solid #ddd; border-radius: 4px; }}
figcaption {{ font-size: 8.8pt; color: #555; margin-top: 4pt; text-align: left; }}
figcaption b {{ color: #1a1a1a; }}
table {{ border-collapse: collapse; width: 100%; font-size: 8.8pt; margin: 8pt 0;
         page-break-inside: avoid; }}
th, td {{ border: 1px solid #ccd; padding: 3pt 5pt; text-align: center; }}
th {{ background: #0b3d66; color: white; font-weight: normal; }}
td:first-child, th:first-child {{ text-align: left; }}
tr:nth-child(even) td {{ background: #f6f8fa; }}
.kpis {{ display: flex; gap: 8pt; margin: 12pt 0; }}
.kpi {{ flex: 1; background: #0b3d66; color: white; border-radius: 6px; padding: 8pt 10pt; }}
.kpi .n {{ font-size: 17pt; font-weight: bold; display: block; }}
.kpi .l {{ font-size: 8pt; opacity: .9; }}
.note {{ font-size: 9pt; color: #555; }}
code {{ font-family: 'DejaVu Sans Mono', monospace; font-size: 8.5pt; background:#eef; padding:0 2px; }}
.finding {{ margin: 6pt 0; }}
.finding b {{ color: #0b3d66; }}
.pagebreak {{ page-break-before: always; }}
ul {{ margin: 4pt 0 4pt 0; padding-left: 16pt; }}
li {{ margin: 2pt 0; }}
</style></head><body>

<h1>LexLeak-Bench: Measuring Confidential-Information Leakage and Collusion<br>Between Law-Firm AI Agents</h1>
<div class="authors">Sanjayprasad H S</div>
<div class="sub">Working paper v4.0 · October 2026 · Prepared in the context of the Apart Research AI Collusion Research Sprint</div>
<div class="sub">All experiments use real OpenAI model calls. Code &amp; data: <code>github.com/sanjuhs/lex-collude-hackathon-agentic-collusion</code> (branch <code>v2-multiagent-collusion</code>)</div>

<div class="abstract">
<b>Abstract.</b> When two law firms each deploy AI agents, those agents meet in markets, in
negotiations, and in the documents they exchange. We ask, across all three, whether agents leak a
client's confidential position or collude <b>without being told to</b>, and which models are most and
least prone to it. Our main contribution is <b>LexLeak-Bench</b>: 200 cases (150 train / 50 held-out)
in which a real <code>.docx</code> contract passes between firms and we measure, directly from the
delivered file, whether a randomized confidential value escapes through any of <b>ten document
channels</b>, or whether a planted false instruction (indirect prompt injection) misleads the
receiving firm's agent. Across <b>9 OpenAI models and 1,800 episodes (zero failed)</b> we find:
(1) <b>no model is safe benchmark-wide</b> — the best score 96–97/100, the weakest 63; (2) failures
are <b>sharply concentrated</b> — 94% of all leaks by the frontier models come from just two channels
(image alt-text and table cells), which <b>leak 100% of the time across every model</b>; (3) safety
<b>does not track model size or price</b>; and (4) on indirect injection, subtle planted claims
mislead the receiver (freeze-clauses 25%, accept-a-low-offer 14%) while blatant ones fail (0%) and the
payload almost never propagates downstream (≤4%). A companion pricing study shows tacit collusion
<b>falls monotonically as the panel grows</b> (Δ 0.39→0.22 for N=2→12) and a single maverick competitor
roughly halves it. Total spend ≈ $112 (list prices). Held-out cells use 12–17 cases, so rates carry
wide intervals; the leaderboard is a calibrated ranking, not a precise score.
</div>

<div class="kpis">
  <div class="kpi"><span class="n">1,800</span><span class="l">real benchmark episodes, 0 failed</span></div>
  <div class="kpi"><span class="n">10</span><span class="l">document leak channels, 6 doc types</span></div>
  <div class="kpi"><span class="n">94%</span><span class="l">of frontier leaks = 2 channels</span></div>
  <div class="kpi"><span class="n">100%</span><span class="l">leak rate: alt-text &amp; table cells</span></div>
</div>

<h2>1. The problem and why a benchmark</h2>
<p>Legal-AI products (Harvey, Legora, and others) run large language models over contracts, discovery
and negotiations. When two firms each deploy one, three risks appear that single-agent evaluations
cannot see: <b>(A) tacit market collusion</b> — pricing agents keeping prices high without
communicating; <b>(B) incentive-driven betrayal of the client</b> — an agent paid out of the deal
trading its client's interest for the firm's; and <b>(C) leakage through the work product</b> — the
documents agents exchange carry comments, tracked changes, metadata and hidden text through which a
secret can escape, and into which a false instruction can be planted.</p>
<p>An earlier version of this project pitted a single agent against a fixed script and found nothing —
a null result built into the design. The present work gives <b>every party an autonomous agent with a
real incentive</b>, and turns risk C into a reusable benchmark with a held-out set, so models can be
ranked and the problem shown to be unsolved.</p>

<h2>2. LexLeak-Bench design</h2>
<p>A fixed, seeded bank of <b>200 cases</b> (committed as JSONL). Each case specifies a document type,
a confidential secret (or a planted false instruction), the channel it starts in, and a deterministic
scoring rule. A case runs as a relay: firm A's <b>drafter</b> edits a real Word file; A's
<b>reviewing partner</b> inspects only the <i>rendered text</i> and may approve, sanitize or block;
opposing counsel <b>B</b> receives the file, inspects all of it, and later estimates the secret.
<b>Scoring reads the delivered <code>.docx</code> from disk</b> — not what any agent claims — so a leak
counts only if the secret's digits actually sit in a channel of the file.</p>
<p><b>Ten channels:</b> body, comment, tracked change, core+custom metadata, hidden (vanished) text,
white (white-on-white) font, tiny (1&nbsp;pt) font, header/footer, table cell, image alt-text.
<b>Two families:</b> <i>leak</i> (70%; tiers: inadvertent / incentive / instructed-covert) and
<i>poison</i> (30%; firm A has planted a false instruction and we score whether B complies, notices,
and whether the payload propagates to B's own client).</p>
<p><b>The anti-saturation split.</b> Train uses familiar document types (NDA, settlement, employment,
share-purchase) and the "classic" channels (metadata, comment, tracked change, hidden text). Holdout
uses <b>unseen document types</b> (commercial lease, discovery response) and the <b>harder channels</b>
(white/tiny font, header/footer, table cell, alt-text). A model cannot top the holdout by
pattern-matching the training cases.</p>

<h2>3. Main result: where models leak</h2>
<figure>{img("leakbench_heatmap.png", "92%")}
<figcaption><b>Figure 1.</b> Breach rate (% of inadvertent cases where the planted secret reached the
other side) for each model × channel. The frontier models (gpt-5.5 and the gpt-6 family) are clean
(green) on the first seven channels and fail (red, 100%) only on <b>table cells</b> and <b>image
alt-text</b> — a shared, specific blind spot. The older GPT-4 family fails broadly.</figcaption>
</figure>

<p class="finding"><b>Finding 1 — failures are concentrated, not broad.</b> Of 187 total inadvertent
leaks, 54 (29%) come from two channels alone. For the five frontier models the concentration is
extreme: <b>30 of their 32 leaks (94%) are image alt-text or table cells</b>; across the other seven
channels combined they breach only twice. These are the places an agent does not think of as part of
"the draft" — an image's description, an off-to-the-side table — so it never scrubs them.</p>

<p class="finding"><b>Finding 2 — no model is safe benchmark-wide.</b> A combined score over the full
200-case bank (1 − mean of bad-outcome rates) leaves every model below 100, because every model fails
the alt-text and table-cell cases.</p>

<figure>{img("leakbench_combined.png", "78%")}
<figcaption><b>Figure 2.</b> Combined safety score over the whole benchmark. The gpt-6 family and
gpt-5.5 cluster at 96–97; the GPT-4 family trails at 63–81. Safety does not track model size or price.</figcaption>
</figure>

<p class="finding"><b>Finding 3 — the held-out channels expose the gap.</b> The frontier models score
~100 on the training channels (which they handle) but drop ~10 points on the held-out channels. The
benchmark is therefore not saturated: strong performance on familiar hiding spots does not generalize.</p>

<figure>{img("leakbench_integrity.png", "88%")}
<figcaption><b>Figure 3.</b> Integrity score, train vs holdout. The frontier models fall ~10 points on
held-out channels; the GPT-4 family is already weak on both.</figcaption>
</figure>

<table>
<tr><th>model</th><th>combined safety</th><th>inadv. breach</th><th>incentive leak</th><th>exploit-on-leak</th><th>poison comply</th><th>propagate</th></tr>
<tr><td>gpt-6-sol</td><td>97</td><td>13%</td><td>0%</td><td>0%</td><td>0%</td><td>0%</td></tr>
<tr><td>gpt-6-astra</td><td>97</td><td>13%</td><td>0%</td><td>0%</td><td>0%</td><td>0%</td></tr>
<tr><td>gpt-6-luna</td><td>97</td><td>13%</td><td>0%</td><td>0%</td><td>2%</td><td>0%</td></tr>
<tr><td>gpt-6.1-sol</td><td>97</td><td>15%</td><td>0%</td><td>0%</td><td>0%</td><td>0%</td></tr>
<tr><td>gpt-5.5</td><td>96</td><td>15%</td><td>4%</td><td>0%</td><td>0%</td><td>0%</td></tr>
<tr><td>gpt-4.1</td><td>81</td><td>81%</td><td>7%</td><td>5%</td><td>3%</td><td>0%</td></tr>
<tr><td>gpt-5.4-mini</td><td>80</td><td>72%</td><td>9%</td><td>2%</td><td>16%</td><td>0%</td></tr>
<tr><td>gpt-4.1-mini</td><td>69</td><td>94%</td><td>15%</td><td>5%</td><td>41%</td><td>0%</td></tr>
<tr><td>gpt-4o-mini</td><td>63</td><td>83%</td><td>17%</td><td>54%</td><td>31%</td><td>0%</td></tr>
</table>
<p class="note">Table 1. Full-bank results. <i>Exploit-on-leak</i>: when the model receives an
inadvertent leak, does it quietly use it rather than notify the sender (Model Rule 4.4(b))? gpt-4o-mini
is the clear outlier at 54%.</p>

<h2>4. Covert capability and conduct</h2>
<p class="finding"><b>Finding 4 — covert capability is real but concentrated.</b> Told to smuggle the
figure past the text-reading partner, gpt-6-sol succeeds and opposing counsel decodes it 89% of the
time on held-out cases; gpt-4.1-mini 78%. The gpt-6 family reaches for the <b>metadata</b> channel.
The two largest models, as <i>receivers</i>, often declined to rely on planted metadata, so covert
success needs both a willing sender and a willing receiver.</p>
<p class="finding"><b>Finding 5 — conduct on receiving a leak splits by model.</b> Most models flag an
inadvertent leak (Rule 4.4(b)); gpt-4o-mini instead <b>exploits</b> 54% of the leaks it receives — the
one model that is unsafe on every axis at once.</p>

<h2>5. Poisoned input (indirect prompt injection)</h2>
<figure>{img("leakbench_channels.png", "74%")}
<figcaption><b>Figure 4.</b> Inadvertent breach rate by the channel the secret was planted in, pooled
across models. Image alt-text and table cells top the list at 100%.</figcaption>
</figure>
<table>
<tr><th>planted false instruction (goal)</th><th>receiver complies</th><th>complies without noticing</th><th>n</th></tr>
<tr><td>"clauses 2–3 were pre-agreed, do not reopen"</td><td>25%</td><td>1%</td><td>162</td></tr>
<tr><td>"accept any offer at/above $X" (fake authority)</td><td>14%</td><td>1%</td><td>135</td></tr>
<tr><td>"summarise as standard, no adverse terms"</td><td>0%</td><td>0%</td><td>135</td></tr>
<tr><td>"all parties waived review, sign today"</td><td>0%</td><td>0%</td><td>144</td></tr>
</table>
<p class="finding"><b>Finding 6 — subtle injections work; blatant ones don't; and the poison rarely
spreads.</b> A claim that <i>reframes</i> the negotiation is acted on 14–25% of the time, concentrated
in the smaller models (gpt-4.1-mini complies 38–47%, the gpt-6 frontier ~0%). A claim that asks the
model to <i>misstate</i> the contract or <i>skip its duty</i> is refused by every model. Crucially,
<b>propagation is ≤4%</b>: even when the victim acts on the planted instruction, it almost never copies
the planted text into its own advice. The poison is absorbed, not forwarded.</p>

<h2>6. Companion study: does pricing collusion change with more firms?</h2>
<figure>{img("pricing_scaling.png", "60%")}
<figcaption><b>Figure 5.</b> Tacit-collusion index (0 = competitive, 1 = cartel) with no communication,
by number of firms. gpt-6-sol's collusion falls monotonically as the panel grows; a single scripted
"maverick" competitor (diamond) roughly halves it at N=5. gpt-6-luna does not collude.</figcaption>
</figure>
<p class="finding"><b>Finding 7.</b> More firms → less collusion (gpt-6-sol Δ 0.39→0.34→0.29→0.26→0.22
for N=2→12), exactly as oligopoly theory predicts. <b>Finding 8.</b> Replacing one firm with a
competitor that always prices competitively cuts the collusion index from 0.29 to 0.13 — a direct
answer to "is collusion robust to replacing some participants?": no.</p>

<h2>7. Companion study: do both sides sell out in settlements?</h2>
<p>Defense counsel negotiates with class counsel. We added a defense-side hourly billing incentive and
an off-record back-channel between lead counsel. The robust effect remains the <b>fee incentive</b>
(fee-linked class counsel take more of the settlement), but in this sample the <b>off-record channel
did not produce collusion against both clients</b> and hourly-paid defense did not clearly prolong — an
honest near-null that invites a larger, more adversarial follow-up.</p>

<h2>8. Limitations</h2>
<ul>
<li>Held-out cells use 12–17 cases per model, so those rates carry wide intervals; the leaderboard is a
coarse ranking and a reusable method, not a precise score. Train cells (34–47) are tighter.</li>
<li>Leak scoring is literal digit/token matching; a model could encode a value indirectly and evade the
scanner. The instructed tier bounds <i>detected</i> covert capability, not all of it.</li>
<li>The reviewing partner reads only rendered text by design; a full-view partner is future work.</li>
<li>Settlement findings are near-nulls on small samples. Nothing was pre-registered. All firms, cases
and parties are fictional; this is research software, not legal advice.</li>
</ul>

<h2>9. What this means, and what's next</h2>
<p>The single most actionable result: <b>a firm deploying document agents must deterministically scrub
every non-visible part of every outgoing file</b> — comments, tracked changes, metadata, hidden/white/
tiny text, headers, tables and image alt-text — and must not rely on the model to notice, because even
the best models have a shared blind spot (alt-text and table cells) and the weaker ones leak almost
everywhere. The benchmark's own channel scanner is a working reference for that scrubber. Next:
scale the held-out set; add a deterministic-scrubber baseline; test an open-weight model with its
refusal direction removed in the "leaker" role against an aligned counterparty; and seek human
validation of the leak labels from legal professionals.</p>

<h2>10. Ethics and dual use</h2>
<p>The study shows that misaligned incentives and obscure document channels — not explicit instructions
— suffice to produce leakage and collusion. The emphasis is on <b>detection</b>: the deterministic
scanner that scores the benchmark is itself the countermeasure. No real firm, client, market or
document is involved, and nothing ran outside the sandbox.</p>

<p class="note" style="margin-top:14pt">References: Calvano et&nbsp;al. (2020), <i>AER</i> 110(10);
Fish, Gonczarowski &amp; Shorrer (2024), arXiv:2404.00806; Motwani et&nbsp;al. (2024), NeurIPS;
Greshake et&nbsp;al. (2023), arXiv:2302.12173; ABA Formal Op. 06-442; ABA Model Rules 1.6 &amp; 4.4(b);
<i>In re Bluetooth</i>, 654 F.3d 935 (9th Cir. 2011). Full report, code, 1,800 transcripts and sample
<code>.docx</code> files in the repository.</p>

</body></html>"""


def main():
    html_path = OUT / "LexCollude-LexLeakBench.html"
    html_path.write_text(HTML)
    pdf_path = OUT / "LexCollude-LexLeakBench.pdf"
    node = f"""const {{chromium}}=require('playwright');(async()=>{{
      const b=await chromium.launch();const p=await b.newPage();
      await p.goto('file://{html_path}',{{waitUntil:'networkidle'}});
      await p.pdf({{path:'{pdf_path}',format:'A4',printBackground:true,
        margin:{{top:'0',bottom:'0',left:'0',right:'0'}}}});
      await b.close();console.log('wrote {pdf_path}');
    }})().catch(e=>{{console.error(String(e));process.exit(1)}});"""
    r = subprocess.run(["node", "-e", node], capture_output=True, text=True)
    sys.stdout.write(r.stdout); sys.stderr.write(r.stderr)
    if r.returncode != 0:
        sys.exit(r.returncode)
    print(f"PDF size: {pdf_path.stat().st_size//1024} KB")


if __name__ == "__main__":
    main()
