"""Check saved artifacts for completeness and internal consistency, not model identity proof."""

import hashlib
import json
import sys
from pathlib import Path

from lexcollude.evaluate import enforce_mandate, evaluate
from lexcollude.report import summarize
from lexcollude.schema import Case, Decision


def verify(directory: Path) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest["status"] != "completed" or manifest["errors"] or manifest["pending"]:
        raise ValueError("Run is incomplete or contains errors")
    records = [json.loads(p.read_text()) for p in sorted((directory / "episodes").glob("*.json"))]
    expected = {(case, condition, repetition)
                for case in manifest["cases"] for condition in manifest["conditions"]
                for repetition in range(1, manifest["repetitions"] + 1)}
    observed = {(r["case"]["case_id"], r["condition"], r["repetition"]) for r in records}
    if observed != expected or len(records) != len(expected):
        raise ValueError("Missing, extra, or duplicate episodes")
    total_calls = 0
    agent_ids = []
    for record in records:
        if record["status"] != "ok" or record["model"] != manifest["model"]:
            raise ValueError("Episode status/model mismatch")
        case = Case(**record["case"])
        raw = Decision.parse(record["raw_decision"])
        effective, blocked = (enforce_mandate(case, raw) if record["condition"] == "verified_injection"
                              else (raw, False))
        if (record["raw_score"] != evaluate(case, raw)
                or record["effective_score"] != evaluate(case, effective)
                or record["effective_decision"] != effective.to_dict()
                or record["gate_blocked"] != blocked):
            raise ValueError("Saved evaluation does not match authoritative rules")
        for call in record["calls"]:
            total_calls += 1
            if manifest["backend"] != "codex":
                continue
            job_id = record["episode_id"] + "__" + call["stage"]
            request = json.loads((directory / "requests" / f"{job_id}.json").read_text())
            response = json.loads((directory / "responses" / f"{job_id}.json").read_text())
            digest = hashlib.sha256(json.dumps({"model": manifest["model"],
                                                "messages": call["messages"]}, sort_keys=True).encode()).hexdigest()
            if (request["prompt_sha256"] != digest or response["prompt_sha256"] != digest
                    or request["messages"] != call["messages"]
                    or response["model"] != manifest["model"]
                    or response["content"] != call["raw_output"]
                    or response["agent_id"] != call["request_id"]
                    or response["tool_use"] is not False):
                raise ValueError("Native prompt/response attribution mismatch")
            agent_ids.append(response["agent_id"])
    if total_calls != manifest["planned_calls"]:
        raise ValueError("Completed call count differs from planned calls")
    if agent_ids and len(agent_ids) != len(set(agent_ids)):
        raise ValueError("Experimental child reused across model calls")
    if summarize(records) != json.loads((directory / "summary.json").read_text()):
        raise ValueError("Saved summary differs from episode records")
    return {"run": str(directory), "episodes": len(records), "calls": total_calls,
            "model": manifest["model"], "status": "verified"}


if __name__ == "__main__":
    try:
        for argument in sys.argv[1:]:
            print(json.dumps(verify(Path(argument))))
        if len(sys.argv) < 2:
            raise ValueError("Usage: python scripts/verify_run.py RUN_DIRECTORY [RUN_DIRECTORY ...]")
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(f"Artifact verification failed: {exc}")
