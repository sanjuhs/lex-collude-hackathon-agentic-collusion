"""Run a grid of episodes against the real API.

    python -m lexcollude_v2.runner tender --models gpt-6-luna --n-firms 2 3 5 \
        --channels none forum --seeds 0 1 2 --out data/tender_pilot

Episodes already present in the output directory are skipped (resume). A failed
episode is logged to failures.jsonl with its error and is never replaced by a
placeholder result.
"""

from __future__ import annotations

import argparse
import asyncio
import itertools
import json
import time
import traceback
from pathlib import Path

from .llm import LLM
from .scenarios import classaction, redline, tender


def build_configs(args) -> list:
    configs = []
    if args.scenario == "redline":
        for model, tier, seed in itertools.product(args.models, args.tiers, args.seeds):
            configs.append(redline.RedlineConfig(
                model=model, tier=tier, rounds=args.rounds,
                drafter_model=args.drafter_model, seed=seed))
        return configs
    if args.scenario == "tender":
        for model, n, channel, seed in itertools.product(args.models, args.n_firms, args.channels,
                                                         args.seeds):
            instructed = channel == "instructed"
            recruiter = channel.startswith("recruiter")
            configs.append(tender.TenderConfig(
                model=model, n_firms=n, rounds=args.rounds,
                channel="forum" if (instructed or recruiter) else channel, instructed=instructed,
                recruiter=recruiter, recruiter_model=args.recruiter_model,
                recruiter_lawful=channel == "recruiter_lawful",
                rival_policy=args.rival_policy, deviation_round=args.deviation_round,
                maverick=args.maverick, seed=seed))
    else:
        for model, k, comp, mon, seed in itertools.product(args.models, args.k_firms,
                                                           args.compensation, args.monitoring,
                                                           args.seeds):
            configs.append(classaction.ClassActionConfig(
                model=model, k_plaintiff_firms=k, compensation=comp, monitoring=mon,
                defense_comp=args.defense_comp, backchannel=args.backchannel,
                max_rounds=args.rounds, seed=seed))
    return configs


async def main_async(args) -> None:
    out = Path(args.out)
    (out / "episodes").mkdir(parents=True, exist_ok=True)
    llm = LLM(out / f"calls_{'_'.join(args.models)}.jsonl", concurrency=args.concurrency,
              reasoning_effort=args.reasoning_effort)
    module = {"tender": tender, "classaction": classaction, "redline": redline}[args.scenario]
    configs = [c for c in build_configs(args)
               if not (out / "episodes" / f"{c.label()}.json").exists()]
    print(f"{len(configs)} episodes to run -> {out}", flush=True)
    ep_sem = asyncio.Semaphore(args.parallel_episodes)
    done = 0
    started = time.time()

    async def one(cfg):
        nonlocal done
        async with ep_sem:
            try:
                if args.scenario == "redline":
                    ep = await module.run_episode(llm, cfg, out / "docx")
                else:
                    ep = await module.run_episode(llm, cfg)
            except Exception as exc:  # recorded, never papered over
                with (out / f"failures_{'_'.join(args.models)}.jsonl").open("a") as fh:
                    fh.write(json.dumps({"label": cfg.label(), "error": repr(exc),
                                         "traceback": traceback.format_exc()}) + "\n")
                print(f"FAILED {cfg.label()}: {exc!r}", flush=True)
                return
            ep["reasoning_effort"] = args.reasoning_effort
            (out / "episodes" / f"{cfg.label()}.json").write_text(json.dumps(ep, indent=1))
            done += 1
            print(f"[{done}/{len(configs)}] {cfg.label()}  calls={llm.usage.calls} "
                  f"cost=${llm.usage.cost_usd():.2f}  t={time.time() - started:.0f}s", flush=True)

    await asyncio.gather(*(one(c) for c in configs))
    usage_path = out / f"usage_{'_'.join(args.models)}.jsonl"
    with usage_path.open("a") as fh:
        fh.write(json.dumps({"finished": time.time(), "calls": llm.usage.calls,
                             "input_tokens": llm.usage.input_tokens,
                             "cached_tokens": llm.usage.cached_tokens,
                             "output_tokens": llm.usage.output_tokens,
                             "reasoning_tokens": llm.usage.reasoning_tokens,
                             "by_model": llm.usage.by_model,
                             "estimated_cost_usd": round(llm.usage.cost_usd(), 4)}) + "\n")
    print(f"done: {done} episodes, {llm.usage.calls} calls, est ${llm.usage.cost_usd():.2f}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("scenario", choices=["tender", "classaction", "redline"])
    p.add_argument("--models", nargs="+", required=True)
    p.add_argument("--seeds", nargs="+", type=int, default=[0])
    p.add_argument("--rounds", type=int, default=None)
    p.add_argument("--n-firms", nargs="+", type=int, default=[3])
    p.add_argument("--channels", nargs="+", default=["none"],
                   choices=["none", "none_compliance", "forum", "forum_monitored", "instructed",
                            "recruiter", "recruiter_lawful"])
    p.add_argument("--recruiter-model", default="")
    p.add_argument("--rival-policy", default="llm", choices=["llm", "nash_bot"])
    p.add_argument("--deviation-round", type=int, default=0)
    p.add_argument("--maverick", action="store_true")
    p.add_argument("--k-firms", nargs="+", type=int, default=[1])
    p.add_argument("--compensation", nargs="+", default=["fee_linked"],
                   choices=["fee_linked", "fixed"])
    p.add_argument("--monitoring", nargs="+", default=["private"],
                   choices=["private", "transcript_visible"])
    p.add_argument("--defense-comp", default="flat", choices=["flat", "hourly"])
    p.add_argument("--backchannel", action="store_true")
    p.add_argument("--tiers", nargs="+", default=["tier1_inadvertent", "tier2_incentive", "tier3_instructed"],
                   choices=["tier1_inadvertent", "tier2_incentive", "tier3_instructed"])
    p.add_argument("--drafter-model", default="")
    p.add_argument("--reasoning-effort", default="low", choices=["low", "medium", "high"])
    p.add_argument("--concurrency", type=int, default=24)
    p.add_argument("--parallel-episodes", type=int, default=8)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    if args.rounds is None:
        args.rounds = {"tender": 20, "classaction": 6, "redline": 2}[args.scenario]
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
