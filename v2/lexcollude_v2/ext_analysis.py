"""Analysis for the v4 expansions: pricing N-scaling + maverick, and the settlement back-channel/
defense-incentive study. Deterministic; emits a markdown summary and two figures.

    python -m lexcollude_v2.ext_analysis --tender data/tender_main --settle data/classaction_ext \
        --out analysis_ext --figdir figures
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .scenarios import tender, classaction

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.6, "legend.frameon": False, "figure.dpi": 150, "savefig.bbox": "tight"})


def pricing(tender_dir):
    rows = {}
    for f in glob.glob(f"{tender_dir}/episodes/tender_*_none*.json"):
        e = json.load(open(f)); c = e["config"]
        if (c["channel"] != "none" or c["instructed"] or c.get("recruiter")
                or c.get("rival_policy") != "llm" or c.get("deviation_round")):
            continue
        key = (c["model"], c["n_firms"], "maverick" if c.get("maverick") else "plain")
        rows.setdefault(key, []).append(tender.collusion_index(e))
    return rows


def settlement(settle_dir):
    cells = {}
    for f in glob.glob(f"{settle_dir}/episodes/*.json"):
        e = json.load(open(f)); c = e["config"]; m = classaction.outcome_metrics(e)
        if not m.get("deal"):
            continue
        cells.setdefault((c["model"], c.get("defense_comp", "flat"), bool(c.get("backchannel"))), []).append(m)
    return cells


def summarise(tender_dir, settle_dir, out: Path, figdir: Path):
    out.mkdir(parents=True, exist_ok=True); figdir.mkdir(parents=True, exist_ok=True)
    lines = ["# v4 expansions\n", "## Pricing: does tacit collusion change with more firms?\n",
             "Collusion index Δ (0 = competitive, 1 = cartel), no communication, last 8 of 20 quarters.\n",
             "| model | N=2 | N=3 | N=5 | N=8 | N=12 | N=5 + maverick |", "|---|---|---|---|---|---|---|"]
    pr = pricing(tender_dir)
    models = [m for m in ["gpt-6-sol", "gpt-6-luna"] if any(k[0] == m for k in pr)]
    for m in models:
        def cell(n, kind="plain"):
            v = pr.get((m, n, kind))
            return f"{np.mean(v):+.2f} (n={len(v)})" if v else "-"
        lines.append(f"| {m} | {cell(2)} | {cell(3)} | {cell(5)} | {cell(8)} | {cell(12)} | {cell(5,'maverick')} |")
    lines.append("")

    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    for mi, m in enumerate(models):
        ns = [n for n in (2, 3, 5, 8, 12) if (m, n, "plain") in pr]
        ax.plot(ns, [np.mean(pr[(m, n, "plain")]) for n in ns], "-o", color=SERIES[mi], lw=2, label=m)
        if (m, 5, "maverick") in pr:
            ax.plot([5], [np.mean(pr[(m, 5, "maverick")])], "D", color=SERIES[mi], ms=9, mfc="white",
                    label=f"{m} + maverick")
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xlabel("number of firms on the panel"); ax.set_ylabel("collusion index Δ")
    ax.set_title("Tacit collusion falls as the market crowds", loc="left", fontsize=10)
    ax.legend(fontsize=7)
    fig.savefig(figdir / "pricing_scaling.png"); fig.savefig(figdir / "pricing_scaling.pdf"); plt.close(fig)

    lines.append("## Settlement: defense incentive and an off-record back-channel (K=1, fee-linked)\n")
    lines.append("| model | defense pay | back-channel | n | class fund $M | fee share | rounds | off-record msgs |")
    lines.append("|---|---|---|---|---|---|---|---|")
    cells = settlement(settle_dir)
    for m in ["gpt-6-sol", "gpt-6-luna"]:
        for dc in ["flat", "hourly"]:
            for bc in (False, True):
                v = cells.get((m, dc, bc))
                if not v:
                    continue
                lines.append(f"| {m} | {dc} | {'yes' if bc else 'no'} | {len(v)} | "
                             f"{np.mean([x['class_fund'] for x in v])/1e6:.1f} | "
                             f"{np.mean([x['fee_share'] for x in v])*100:.1f}% | "
                             f"{np.mean([x['rounds_used'] for x in v]):.1f} | "
                             f"{np.mean([x['backchannel_messages'] for x in v]):.1f} |")
    lines.append("")
    (out / "ext.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tender", default="data/tender_main")
    p.add_argument("--settle", default="data/classaction_ext")
    p.add_argument("--out", default="analysis_ext")
    p.add_argument("--figdir", default="figures")
    a = p.parse_args()
    summarise(a.tender, a.settle, Path(a.out), Path(a.figdir))


if __name__ == "__main__":
    main()
