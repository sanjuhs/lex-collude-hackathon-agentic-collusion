"""Small command-line runner. No network calls happen unless explicitly selected."""

import argparse
import hashlib
import json
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

from . import __version__
from .cases import CASES, CONDITIONS
from .experiment import now, run_episode
from .providers import CodexQueueProvider, OpenAIProvider, ResponsesProvider, ScriptedProvider
from .report import write_report


def positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("Must be positive")
    return number


def provenance() -> dict:
    source = Path(__file__).parent
    digest = hashlib.sha256()
    for path in sorted(source.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    def git(*args):
        result = subprocess.run(["git", "-C", str(source), *args], capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    return {"source_sha256": digest.hexdigest(), "git_commit": git("rev-parse", "HEAD"),
            "git_dirty": bool(git("status", "--porcelain")), "package_version": __version__}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="LexCollude synthetic legal-document benchmark")
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("cases", help="List fictional cases and trusted mandates")
    jobs = sub.add_parser("harness-jobs", help="List unanswered native Codex requests")
    jobs.add_argument("run_dir", type=Path)
    imp = sub.add_parser("import-response", help="Import final JSON from a native Codex agent")
    imp.add_argument("request", type=Path)
    imp.add_argument("response", type=Path, help="File containing only the agent's final JSON")
    imp.add_argument("--model", required=True)
    imp.add_argument("--agent-id", required=True)
    imp.add_argument("--no-tools-used", action="store_true", required=True,
                     help="Attest that the agent did not call tools or inspect files")
    run = sub.add_parser("run", help="Run fixtures, API experiments, or export native Codex jobs")
    run.add_argument("--backend", choices=["scripted", "openai", "responses", "codex"], default="scripted")
    run.add_argument("--model", default="gpt-6-luna")
    run.add_argument("--prompt-policy", choices=["ordinary", "hardened"], default="hardened")
    run.add_argument("--protocol-version", type=int, choices=[2], default=2)
    run.add_argument("--api-base", default="https://api.openai.com/v1")
    run.add_argument("--api-key-env", default="OPENAI_API_KEY")
    run.add_argument("--temperature", type=float, default=0.7)
    run.add_argument("--cases", nargs="+", default=[c.case_id for c in CASES[:3]])
    run.add_argument("--conditions", nargs="+", choices=CONDITIONS, default=list(CONDITIONS))
    run.add_argument("--repetitions", type=positive, default=1)
    run.add_argument("--seed", type=int, default=20261026, help="Schedule shuffle seed, not model seed")
    run.add_argument("--workers", type=positive, default=1)
    run.add_argument("--max-calls", type=positive, default=150)
    run.add_argument("--output", type=Path, required=True, help="New output directory (not overwritten)")
    run.add_argument("--resume", action="store_true", help="Resume pending native Codex jobs only")
    return root


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    if args.command == "cases":
        print(json.dumps([asdict(c) for c in CASES], indent=2))
        return 0
    if args.command in ("harness-jobs", "import-response"):
        try:
            if args.command == "harness-jobs":
                pending = [str(p) for p in sorted((args.run_dir / "requests").glob("*.json"))
                           if not (args.run_dir / "responses" / p.name).exists()]
                print(json.dumps(pending, indent=2))
            else:
                request = json.loads(args.request.read_text())
                if args.model != request["model"]:
                    raise ValueError("Response model does not match the requested model")
                content = args.response.read_text()
                if not isinstance(json.loads(content), dict):
                    raise ValueError("Final response must be a JSON object")
                destination = args.request.parent.parent / "responses" / args.request.name
                with destination.open("x") as file:
                    json.dump({"model": args.model, "agent_id": args.agent_id, "tool_use": False,
                               "prompt_sha256": request["prompt_sha256"], "content": content}, file, indent=2)
                    file.write("\n")
                print(f"Imported {request['job_id']}")
            return 0
        except (ValueError, OSError, KeyError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
    try:
        if args.workers > 8:
            raise ValueError("Use at most 8 workers")
        if not 0 <= args.temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        if len(args.cases) != len(set(args.cases)) or len(args.conditions) != len(set(args.conditions)):
            raise ValueError("Duplicate cases or conditions are not allowed")
        by_id = {c.case_id: c for c in CASES}
        if set(args.cases) - set(by_id):
            raise ValueError("Unknown case ID; use the cases command")
        jobs = [(by_id[c], cond, rep) for c in args.cases for cond in args.conditions
                for rep in range(1, args.repetitions + 1)]
        calls = sum(3 if cond.startswith("revision_") else 2 if cond.startswith("relay_") else 1
                    for _, cond, _ in jobs)
        if calls > args.max_calls:
            raise ValueError(f"Plan requires {calls} calls, above --max-calls {args.max_calls}")
        random.Random(args.seed).shuffle(jobs)
        config = {"backend": args.backend, "model": args.model if args.backend != "scripted" else "scripted-fixture-v1",
                  "cases": args.cases, "conditions": args.conditions, "repetitions": args.repetitions,
                  "schedule_seed": args.seed, "planned_calls": calls, "workers": args.workers,
                  "prompt_policy": args.prompt_policy, "protocol_version": args.protocol_version,
                  "temperature": args.temperature if args.backend == "openai" else None,
                  "api_base": args.api_base if args.backend in ("openai", "responses") else None}
        if args.resume:
            if args.backend != "codex":
                raise ValueError("Only native Codex pending jobs can be resumed")
            manifest = json.loads((args.output / "manifest.json").read_text())
            if any(manifest.get(k) != v for k, v in config.items()):
                raise ValueError("Resume arguments do not match the original run")
            if manifest["provenance"]["source_sha256"] != provenance()["source_sha256"]:
                raise ValueError("Source changed since export; use a new run directory")
        else:
            # Validate the API configuration before creating a directory.
            if args.backend in ("openai", "responses"):
                provider_class = OpenAIProvider if args.backend == "openai" else ResponsesProvider
                provider = provider_class(args.model, args.api_base, args.api_key_env, args.temperature)
            args.output.mkdir(parents=True, exist_ok=False)
            manifest = {**config, "schema_version": 1, "run_id": args.output.name,
                        "created_at": now(), "provenance": provenance(), "status": "running",
                        "harness": "native Codex agent jobs, no inherited turns, final JSON only"
                        if args.backend == "codex" else args.backend}
            (args.output / "episodes").mkdir()
        if args.backend == "codex":
            provider = CodexQueueProvider(args.model, args.output)
        elif args.backend == "scripted":
            provider = ScriptedProvider()
        (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

        def execute(job):
            case, condition, repetition = job
            path = args.output / "episodes" / f"{case.case_id}__{condition}__r{repetition}.json"
            if args.resume and path.exists():
                previous = json.loads(path.read_text())
                if previous["status"] != "pending":
                    return previous
            record = run_episode(case, condition, repetition, provider,
                                 args.prompt_policy, args.protocol_version)
            path.write_text(json.dumps(record, indent=2) + "\n")
            return record

        records = []
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for record in pool.map(execute, jobs):
                records.append(record)
                print(f"{record['episode_id']}: {record['status']}", flush=True)
        errors = sum(r["status"] == "error" for r in records)
        pending = sum(r["status"] == "pending" for r in records)
        manifest.update({"updated_at": now(), "errors": errors, "pending": pending,
                         "completed_episodes": sum(r["status"] == "ok" for r in records),
                         "status": "pending" if pending else "completed_with_errors" if errors else "completed"})
        (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        write_report(args.output, records, manifest)
        print(f"{len(records)} episodes; {errors} errors; {pending} pending. Artifacts: {args.output}")
        return 1 if errors else 3 if pending else 0
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
