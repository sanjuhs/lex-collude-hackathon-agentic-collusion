"""Run LexLeak-Bench cases across models, with cost tracking, resume, and a budget stop.

    python -m lexcollude_v2.bench_runner --split train holdout --models gpt-6-luna gpt-4o-mini \
        --out data/leakbench --budget 100 --max-cases 0

Resumes: a case/model already on disk is skipped. Stops cleanly if the running cost
estimate would exceed --budget. Failures are logged, never replaced with placeholders.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
import traceback
from pathlib import Path

from .casebank import load_cases
from .llm import LLM
from . import leakbench


async def main_async(args) -> None:
    out = Path(args.out)
    (out / "episodes").mkdir(parents=True, exist_ok=True)
    llm = LLM(out / f"calls_{'_'.join(args.models)}.jsonl", concurrency=args.concurrency,
              reasoning_effort=args.reasoning_effort)
    cases = []
    for split in args.split:
        cases += load_cases(Path(args.bank) / f"cases_{split}.jsonl")
    if args.families:
        cases = [c for c in cases if c.family in args.families]
    if args.max_cases:
        cases = cases[:args.max_cases]
    jobs = [(c, m) for m in args.models for c in cases
            if not (out / "episodes" / f"{c.id}__{m}.json").exists()]
    print(f"{len(jobs)} case/model jobs to run -> {out} (budget ${args.budget})", flush=True)
    ep_sem = asyncio.Semaphore(args.parallel)
    done = 0
    started = time.time()
    stop = asyncio.Event()

    async def one(case, model):
        nonlocal done
        if stop.is_set():
            return
        async with ep_sem:
            if stop.is_set() or llm.usage.cost_usd() >= args.budget:
                stop.set()
                return
            try:
                ep = await leakbench.run_case(llm, case, model, out / "docx",
                                              drafter_model=args.drafter_model, rounds=args.rounds)
            except Exception as exc:
                with (out / f"failures_{'_'.join(args.models)}.jsonl").open("a") as fh:
                    fh.write(json.dumps({"label": f"{case.id}__{model}", "error": repr(exc),
                                         "traceback": traceback.format_exc()}) + "\n")
                print(f"FAILED {case.id}__{model}: {exc!r}", flush=True)
                return
            (out / "episodes" / f"{case.id}__{model}.json").write_text(json.dumps(ep, indent=1))
            done += 1
            if done % 10 == 0 or llm.usage.cost_usd() >= args.budget * 0.9:
                print(f"[{done}/{len(jobs)}] {case.id}__{model} cost=${llm.usage.cost_usd():.2f} "
                      f"t={time.time()-started:.0f}s", flush=True)
            if llm.usage.cost_usd() >= args.budget:
                print(f"BUDGET REACHED at ${llm.usage.cost_usd():.2f}; stopping new work.", flush=True)
                stop.set()

    await asyncio.gather(*(one(c, m) for c, m in jobs))
    with (out / f"usage_{'_'.join(args.models)}.jsonl").open("a") as fh:
        fh.write(json.dumps({"finished": time.time(), "calls": llm.usage.calls,
                             "by_model": llm.usage.by_model,
                             "estimated_cost_usd": round(llm.usage.cost_usd(), 4)}) + "\n")
    print(f"done: {done} episodes, {llm.usage.calls} calls, est ${llm.usage.cost_usd():.2f}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--bank", default="benchmark")
    p.add_argument("--split", nargs="+", default=["train", "holdout"])
    p.add_argument("--families", nargs="+", default=[], choices=["leak", "poison"])
    p.add_argument("--models", nargs="+", required=True)
    p.add_argument("--drafter-model", default="")
    p.add_argument("--rounds", type=int, default=2)
    p.add_argument("--max-cases", type=int, default=0)
    p.add_argument("--budget", type=float, default=100.0)
    p.add_argument("--reasoning-effort", default="low", choices=["low", "medium", "high"])
    p.add_argument("--concurrency", type=int, default=24)
    p.add_argument("--parallel", type=int, default=8)
    p.add_argument("--out", default="data/leakbench")
    asyncio.run(main_async(p.parse_args()))


if __name__ == "__main__":
    main()
