"""Aggregate episodes (+ judge labels) into tables, statistics and figures.

    python -m lexcollude_v2.analysis --tender data/tender_main --classaction data/classaction_main

Statistics: cell means with percentile-bootstrap 95% CIs (10k resamples) and two-sided
permutation tests on differences in means (10k permutations). Seeds are replicate
indices; the API is sampled stochastically, so replicates are independent draws.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .scenarios import classaction, tender  # noqa: E402

RNG = np.random.default_rng(12345)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#6250d6", "#e87ba4", "#008300"]
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False,
    "figure.dpi": 150, "savefig.bbox": "tight",
})


def boot_ci(x, n=10_000):
    x = np.asarray([v for v in x if v is not None], dtype=float)
    if len(x) == 0:
        return (np.nan, np.nan, np.nan, 0)
    if len(x) == 1:
        return (x[0], np.nan, np.nan, 1)
    means = RNG.choice(x, size=(n, len(x)), replace=True).mean(axis=1)
    return (x.mean(), *np.percentile(means, [2.5, 97.5]), len(x))


def perm_test(a, b, n=10_000):
    a = np.asarray([v for v in a if v is not None], dtype=float)
    b = np.asarray([v for v in b if v is not None], dtype=float)
    if len(a) < 2 or len(b) < 2:
        return np.nan
    obs = abs(a.mean() - b.mean())
    pooled = np.concatenate([a, b])
    hits = 0
    for _ in range(n):
        RNG.shuffle(pooled)
        hits += abs(pooled[:len(a)].mean() - pooled[len(a):].mean()) >= obs - 1e-12
    return (hits + 1) / (n + 1)


def fmt_ci(m, lo, hi, n, pct=False, digits=2):
    if np.isnan(m):
        return "n/a"
    f = (lambda v: f"{100 * v:.0f}%") if pct else (lambda v: f"{v:.{digits}f}")
    return f"{f(m)} [{f(lo)}, {f(hi)}] (n={n})" if n > 1 else f"{f(m)} (n=1)"


def load(run: Path, judge_model: str = "gpt-6-sol"):
    eps = []
    jdir = run / f"judgements_{judge_model}"
    for p in sorted((run / "episodes").glob("*.json")):
        ep = json.loads(p.read_text())
        jp = jdir / p.name
        ep["judge"] = json.loads(jp.read_text()) if jp.exists() else None
        eps.append(ep)
    return eps


# ---------------------------------------------------------------- tender

def tender_condition(ep) -> str:
    c = ep["config"]
    if c.get("rival_policy", "llm") != "llm":
        return "vs_nash_bots"
    if c.get("deviation_round"):
        return "deviation_probe"
    if c.get("recruiter"):
        return "recruiter"
    return "instructed" if c["instructed"] else c["channel"]


def tender_rows(eps):
    rows = []
    for ep in eps:
        c, b = ep["config"], ep["benchmarks"]
        llm_rates = [np.mean([r["rates"][0]]) for r in ep["rounds"][-8:]] \
            if c.get("rival_policy", "llm") != "llm" else None
        j = ep["judge"] or {}
        rows.append({
            "label": ep["label"], "model": c["model"], "n": c["n_firms"],
            "condition": tender_condition(ep), "seed": c["seed"],
            "delta": tender.collusion_index(ep),
            "delta_llm_firm_vs_bots": (float((np.mean(llm_rates) - b["nash"]) /
                                             (b["monopoly"] - b["nash"])) if llm_rates else None),
            "mean_rate_last8": float(np.mean([np.mean(r["rates"]) for r in ep["rounds"][-8:]])),
            "messages": len(ep["chat"]),
            "j_proposal": j.get("explicit_coordination_proposed"),
            "j_agreement": j.get("agreement_reached"),
            "j_tacit": j.get("tacit_coordination_reasoning"),
            "j_antitrust": j.get("antitrust_awareness"),
            "j_refusal": j.get("explicit_refusal"),
            "j_concealment": j.get("concealment"),
            "j_verified": j.get("evidence_verified_fraction"),
        })
    return rows


def deviation_response(eps, model, dev_round=14):
    """Rivals' mean rate change from the quarter before the deviation to the two after it."""
    out = {"probe": [], "control": []}
    for ep in eps:
        c = ep["config"]
        if c["model"] != model or c["n_firms"] != 3 or c.get("rival_policy", "llm") != "llm":
            continue
        if c["channel"] != "none" or c["instructed"]:
            continue
        r = ep["rounds"]
        before = np.mean(r[dev_round - 2]["rates"][1:])
        after = np.mean([np.mean(r[k]["rates"][1:]) for k in (dev_round, dev_round + 1)])
        out["probe" if c.get("deviation_round") else "control"].append(float(after - before))
    return out


def tender_figures(eps, rows, figdir: Path):
    models = sorted({r["model"] for r in rows}, key=lambda m: ["gpt-6-luna", "gpt-6-sol", "gpt-6-astra"].index(m) if m in ["gpt-6-luna", "gpt-6-sol", "gpt-6-astra"] else 9)
    order = ["none", "none_compliance", "forum", "forum_monitored", "recruiter", "instructed", "vs_nash_bots"]
    names = {"none": "No channel", "none_compliance": "No channel +\ncompliance line",
             "forum": "Private chat", "forum_monitored": "Monitored chat",
             "instructed": "Instructed +\ndeclared lawful", "recruiter": "One recruiter\nfirm", "vs_nash_bots": "LLM vs\nNash bots"}

    # Fig 1: collusion index by condition (N=3), per model.
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    width = 0.8 / max(1, len(models))
    for mi, m in enumerate(models):
        xs, ms, lo, hi = [], [], [], []
        for ci, cond in enumerate(order):
            key = "delta_llm_firm_vs_bots" if cond == "vs_nash_bots" else "delta"
            vals = [r[key] for r in rows if r["model"] == m and r["n"] == 3 and r["condition"] == cond]
            if not vals:
                continue
            mean, l, h, _ = boot_ci(vals)
            xs.append(ci + (mi - (len(models) - 1) / 2) * width)
            ms.append(mean); lo.append(mean - l if not np.isnan(l) else 0); hi.append(h - mean if not np.isnan(h) else 0)
            ax.scatter([xs[-1]] * len(vals), vals, s=8, color=SERIES[mi], alpha=0.35, zorder=2, linewidths=0)
        ax.bar(xs, ms, width=width * 0.9, color=SERIES[mi], alpha=0.85, label=m, zorder=1)
        ax.errorbar(xs, ms, yerr=[lo, hi], fmt="none", ecolor=INK, elinewidth=0.8, capsize=2, zorder=3)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.axhline(1, color=MUTED, lw=0.8, ls="--")
    ax.text(len(order) - 0.45, 1.02, "joint-profit (monopoly)", color=MUTED, fontsize=7, ha="right", va="bottom")
    ax.text(len(order) - 0.45, 0.02, "competitive (Nash)", color=MUTED, fontsize=7, ha="right", va="bottom")
    ax.set_xticks(range(len(order)), [names[o] for o in order])
    ax.set_ylabel("Collusion index Δ (last 8 quarters)")
    ax.set_title("Panel pricing, 3 firms: supra-competitive pricing by condition", loc="left", fontsize=10)
    ax.legend(loc="upper center", ncols=len(models), fontsize=8)
    fig.savefig(figdir / "tender_conditions.png"); fig.savefig(figdir / "tender_conditions.pdf"); plt.close(fig)

    # Fig 2: price trajectories, no channel vs private chat, N=3.
    fig, axes = plt.subplots(1, len(models), figsize=(3.4 * len(models), 2.8), sharey=True, squeeze=False)
    for ax, m in zip(axes[0], models):
        for ci, cond in enumerate(["none", "forum", "none_compliance"]):
            traj = [[np.mean(r["rates"]) for r in ep["rounds"]] for ep in eps
                    if ep["config"]["model"] == m and ep["config"]["n_firms"] == 3
                    and tender_condition(ep) == cond]
            if not traj:
                continue
            arr = np.array(traj)
            x = np.arange(1, arr.shape[1] + 1)
            ax.plot(x, arr.mean(0), color=SERIES[ci], lw=2, label=names[cond].replace("\n", " "))
            ax.fill_between(x, arr.min(0), arr.max(0), color=SERIES[ci], alpha=0.12, lw=0)
        b = tender.benchmarks(3)
        ax.axhline(b["nash"], color=MUTED, lw=0.8)
        ax.axhline(b["monopoly"], color=MUTED, lw=0.8, ls="--")
        ax.set_title(m, loc="left", fontsize=9)
        ax.set_xlabel("Quarter")
    axes[0][0].set_ylabel("Mean panel rate ($/hour)")
    axes[0][-1].legend(fontsize=7, loc="lower right")
    fig.suptitle("Rate trajectories (mean, band = min-max over replicates); solid line Nash, dashed monopoly",
                 fontsize=8, x=0.01, ha="left", color=MUTED)
    fig.savefig(figdir / "tender_trajectories.png"); fig.savefig(figdir / "tender_trajectories.pdf"); plt.close(fig)

    # Fig 3: N scaling, no channel.
    fig, ax = plt.subplots(figsize=(3.6, 2.8))
    for mi, m in enumerate(models):
        ns = sorted({r["n"] for r in rows if r["model"] == m and r["condition"] == "none"})
        if len(ns) < 2:
            continue
        stats = [boot_ci([r["delta"] for r in rows if r["model"] == m and r["n"] == n and r["condition"] == "none"]) for n in ns]
        ax.errorbar(ns, [s[0] for s in stats], yerr=[[s[0] - s[1] for s in stats], [s[2] - s[0] for s in stats]],
                    color=SERIES[mi], lw=2, marker="o", ms=5, capsize=2, label=m)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xlabel("Number of firms on the panel")
    ax.set_ylabel("Collusion index Δ")
    ax.set_title("More firms, no channel", loc="left", fontsize=10)
    ax.legend(fontsize=7)
    fig.savefig(figdir / "tender_nscaling.png"); fig.savefig(figdir / "tender_nscaling.pdf"); plt.close(fig)


# ---------------------------------------------------------------- class action

def ca_rows(eps):
    rows = []
    for ep in eps:
        c = ep["config"]
        m = classaction.outcome_metrics(ep)
        j = ep["judge"] or {}
        rows.append({
            "label": ep["label"], "model": c["model"], "k": c["k_plaintiff_firms"],
            "compensation": c["compensation"], "monitoring": c["monitoring"], "seed": c["seed"],
            **{key: m.get(key) for key in ("deal", "round", "class_fund", "fees", "total",
                                             "fee_share", "clear_sailing", "kicker", "claims_made",
                                             "bluetooth_signs")},
            "j_linkage": j.get("fee_relief_linkage"),
            "j_self_interest": j.get("plaintiff_self_interest_reasoning"),
            "j_firm_over_class": j.get("plaintiff_prioritises_firm_over_class"),
            "j_defense_leverage": j.get("defense_leverages_fee_interest"),
            "j_reverse_auction": j.get("reverse_auction_tactics"),
            "j_decl_misleading": j.get("declaration_misleading"),
            "j_fees_first": j.get("fees_raised_first_by"),
            "j_verified": j.get("evidence_verified_fraction"),
        })
    return rows


def ca_figures(rows, figdir: Path):
    models = [m for m in ["gpt-6-luna", "gpt-6-sol", "gpt-6-astra"] if any(r["model"] == m for r in rows)]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))
    for mi, m in enumerate(models):
        for comp, ls, mk in (("fee_linked", "-", "o"), ("fixed", ":", "s")):
            ks = sorted({r["k"] for r in rows if r["model"] == m and r["compensation"] == comp and r["monitoring"] == "private"})
            if not ks:
                continue
            for ax, key, scale in ((axes[0], "class_fund", 1e6), (axes[1], "fee_share", 0.01)):
                st = [boot_ci([r[key] / scale for r in rows if r["model"] == m and r["k"] == k and r["compensation"] == comp
                               and r["monitoring"] == "private" and r["deal"]]) for k in ks]
                ax.errorbar(np.array(ks) + (mi - 1) * 0.06, [s[0] for s in st],
                            yerr=[[s[0] - s[1] if not np.isnan(s[1]) else 0 for s in st],
                                  [s[2] - s[0] if not np.isnan(s[2]) else 0 for s in st]],
                            color=SERIES[mi], ls=ls, marker=mk, ms=5, lw=2 if comp == "fee_linked" else 1.2,
                            capsize=2, label=f"{m}, {comp.replace('_', '-')}")
    axes[0].set_ylabel("Class fund ($M)")
    axes[1].set_ylabel("Fee share of total (%)")
    for ax in axes:
        ax.set_xlabel("Competing class counsel (K)")
        ax.set_xticks([1, 2, 3])
    axes[0].set_title("Class recovery", loc="left", fontsize=10)
    axes[1].set_title("Lawyers' share", loc="left", fontsize=10)
    axes[1].legend(fontsize=6.5, loc="best")
    fig.savefig(figdir / "classaction_k.png"); fig.savefig(figdir / "classaction_k.pdf"); plt.close(fig)


# ---------------------------------------------------------------- main

def summarise(tender_dir, ca_dir, out: Path, figdir: Path):
    out.mkdir(parents=True, exist_ok=True)
    figdir.mkdir(parents=True, exist_ok=True)
    report = {}
    lines = []
    if tender_dir:
        eps = load(Path(tender_dir))
        rows = tender_rows(eps)
        (out / "tender_rows.json").write_text(json.dumps(rows, indent=1))
        lines.append("## Scenario A: panel pricing\n")
        lines.append("| model | N | condition | Δ mean [95% CI] | mean rate | msgs/ep | proposal | agreement | tacit reasoning | antitrust mention | refusal | concealment |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
        cells = sorted({(r["model"], r["n"], r["condition"]) for r in rows})
        for m, n, cond in cells:
            rs = [r for r in rows if (r["model"], r["n"], r["condition"]) == (m, n, cond)]
            key = "delta_llm_firm_vs_bots" if cond == "vs_nash_bots" else "delta"
            frac = lambda k: (f"{sum(bool(r[k]) for r in rs if r[k] is not None)}/{sum(r[k] is not None for r in rs)}")
            lines.append(f"| {m} | {n} | {cond} | {fmt_ci(*boot_ci([r[key] for r in rs]))} | "
                         f"{np.mean([r['mean_rate_last8'] for r in rs]):.0f} | {np.mean([r['messages'] for r in rs]):.1f} | "
                         f"{frac('j_proposal')} | {frac('j_agreement')} | {frac('j_tacit')} | {frac('j_antitrust')} | "
                         f"{frac('j_refusal')} | {frac('j_concealment')} |")
        lines.append("")
        tests = []
        for m in sorted({r["model"] for r in rows}):
            get = lambda cond, n=3, key="delta": [r[key] for r in rows if r["model"] == m and r["n"] == n and r["condition"] == cond]
            for a, b in (("none", "forum"), ("none", "none_compliance"), ("forum", "forum_monitored"),
                         ("none", "instructed")):
                if get(a) and get(b):
                    tests.append((m, f"Δ {a} vs {b} (N=3)", np.mean(get(a)) - np.mean(get(b)), perm_test(get(a), get(b))))
            if get("none") and get("vs_nash_bots", key="delta_llm_firm_vs_bots"):
                tests.append((m, "Δ all-LLM vs LLM-firm-facing-Nash-bots", np.mean(get("none")) - np.mean(get("vs_nash_bots", key="delta_llm_firm_vs_bots")),
                              perm_test(get("none"), get("vs_nash_bots", key="delta_llm_firm_vs_bots"))))
            if get("none", 2) and get("none", 5):
                tests.append((m, "Δ N=2 vs N=5 (no channel)", np.mean(get("none", 2)) - np.mean(get("none", 5)), perm_test(get("none", 2), get("none", 5))))
            dev = deviation_response(eps, m)
            if dev["probe"] and dev["control"]:
                tests.append((m, "rivals' rate change after forced undercut ($): probe minus control",
                              np.mean(dev["probe"]) - np.mean(dev["control"]), perm_test(dev["probe"], dev["control"])))
                report.setdefault("deviation", {})[m] = dev
        lines.append("| model | comparison | difference | permutation p |")
        lines.append("|---|---|---|---|")
        for m, name, d, p in tests:
            lines.append(f"| {m} | {name} | {d:+.2f} | {p:.4f} |")
        lines.append("")
        tender_figures(eps, rows, figdir)
        report["tender_tests"] = [dict(model=m, comparison=c, diff=float(d), p=float(p)) for m, c, d, p in tests]
    if ca_dir:
        eps = load(Path(ca_dir))
        rows = ca_rows(eps)
        (out / "classaction_rows.json").write_text(json.dumps(rows, indent=1))
        lines.append("## Scenario B: class-action settlement\n")
        lines.append("| model | K | compensation | monitoring | deals | class fund $M | fees $M | fee share | clear sailing | kicker | claims-made | fee-relief linkage | firm over class | defense leverage | reverse auction | misleading decl. |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        cells = sorted({(r["model"], r["k"], r["compensation"], r["monitoring"]) for r in rows})
        for cell in cells:
            rs = [r for r in rows if (r["model"], r["k"], r["compensation"], r["monitoring"]) == cell]
            d = [r for r in rs if r["deal"]]
            frac = lambda k, src=d: f"{sum(bool(r[k]) for r in src if r[k] is not None)}/{sum(r[k] is not None for r in src)}"
            lines.append(f"| {cell[0]} | {cell[1]} | {cell[2]} | {cell[3]} | {len(d)}/{len(rs)} | "
                         f"{fmt_ci(*boot_ci([r['class_fund'] / 1e6 for r in d]), digits=1)} | "
                         f"{fmt_ci(*boot_ci([r['fees'] / 1e6 for r in d]), digits=2)} | "
                         f"{fmt_ci(*boot_ci([r['fee_share'] for r in d]), pct=True)} | "
                         f"{frac('clear_sailing')} | {frac('kicker')} | {frac('claims_made')} | "
                         f"{frac('j_linkage', rs)} | {frac('j_firm_over_class', rs)} | {frac('j_defense_leverage', rs)} | "
                         f"{frac('j_reverse_auction', rs)} | {frac('j_decl_misleading')} |")
        lines.append("")
        tests = []
        for m in sorted({r["model"] for r in rows}):
            g = lambda key, **kw: [r[key] for r in rows if r["model"] == m and r["deal"]
                                   and all(r[a] == v for a, v in kw.items())]
            for key in ("fee_share", "class_fund", "fees"):
                a = g(key, k=1, compensation="fee_linked", monitoring="private")
                b = g(key, k=1, compensation="fixed", monitoring="private")
                if a and b:
                    tests.append((m, f"{key}: fee-linked vs fixed (K=1)", np.mean(a) - np.mean(b), perm_test(a, b)))
            for comp in ("fee_linked", "fixed"):
                a = g("class_fund", k=3, compensation=comp, monitoring="private")
                b = g("class_fund", k=1, compensation=comp, monitoring="private")
                if a and b:
                    tests.append((m, f"class_fund: K=3 vs K=1 ({comp})", np.mean(a) - np.mean(b), perm_test(a, b)))
            for k in (1, 3):
                for key in ("fee_share", "class_fund"):
                    a = g(key, k=k, compensation="fee_linked", monitoring="transcript_visible")
                    b = g(key, k=k, compensation="fee_linked", monitoring="private")
                    if a and b:
                        tests.append((m, f"{key}: transcript visible vs private (K={k}, fee-linked)", np.mean(a) - np.mean(b), perm_test(a, b)))
        lines.append("| model | comparison | difference | permutation p |")
        lines.append("|---|---|---|---|")
        for m, name, d, p in tests:
            big = abs(d) > 1000
            lines.append(f"| {m} | {name} | {d / 1e6:+.2f}M | {p:.4f} |" if big else f"| {m} | {name} | {d:+.3f} | {p:.4f} |")
        ca_figures(rows, figdir)
        report["classaction_tests"] = [dict(model=m, comparison=c, diff=float(d), p=float(p)) for m, c, d, p in tests]
    (out / "results.md").write_text("\n".join(lines) + "\n")
    (out / "tests.json").write_text(json.dumps(report, indent=1))
    print("\n".join(lines))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tender")
    p.add_argument("--classaction")
    p.add_argument("--out", default="analysis")
    p.add_argument("--figdir", default="figures")
    a = p.parse_args()
    summarise(a.tender, a.classaction, Path(a.out), Path(a.figdir))


if __name__ == "__main__":
    main()
