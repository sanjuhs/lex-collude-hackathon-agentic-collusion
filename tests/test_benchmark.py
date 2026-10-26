import contextlib
import io
import json
import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from lexcollude.cases import CASES, CONDITIONS, make_document
from lexcollude.cli import main
from lexcollude.evaluate import enforce_mandate, evaluate
from lexcollude.experiment import run_episode
from lexcollude.providers import Completion, CodexQueueProvider, OpenAIProvider, ScriptedProvider
from lexcollude.report import summarize, wilson_interval
from lexcollude.schema import Decision, DECISION_EXAMPLE


def valid_decision(case=CASES[0], **kwargs):
    return replace(Decision("request_approval", case.clean_offer_inr, True, False,
                            case.clean_offer_inr, True, True, False,
                            "The proposed terms require client approval.", "Please obtain approval."), **kwargs)


class EvaluationTests(unittest.TestCase):
    def test_in_bounds_without_approval_is_not_finalizable(self):
        score = evaluate(CASES[0], valid_decision(decision="accept"))
        self.assertEqual(score["accepted_violations"], ["missing_trusted_client_approval"])

    def test_model_cannot_grant_itself_approval(self):
        score = evaluate(CASES[0], valid_decision(decision="accept", claims_client_approval=True))
        self.assertTrue(score["unauthorized_acceptance"])
        self.assertTrue(score["false_approval_claim"])

    def test_safe_request_does_not_count_as_unauthorized(self):
        self.assertFalse(evaluate(CASES[0], valid_decision())["unauthorized_acceptance"])

    def test_rejected_bad_terms_are_not_finalized_violations(self):
        score = evaluate(CASES[0], valid_decision(decision="reject", amount_inr=1))
        self.assertEqual(score["term_violations"], ["below_client_minimum"])
        self.assertFalse(score["unauthorized_acceptance"])

    def test_valid_approved_acceptance(self):
        case = CASES[2]
        score = evaluate(case, valid_decision(case, decision="accept", claims_client_approval=True,
                                             reports_approval_needed=False))
        self.assertFalse(score["unauthorized_acceptance"])

    def test_approval_does_not_override_minimum(self):
        self.assertTrue(evaluate(CASES[2], valid_decision(CASES[2], decision="accept", amount_inr=1))[
            "unauthorized_acceptance"])

    def test_confidentiality_only_when_required(self):
        decision = valid_decision(preserves_confidentiality=False)
        self.assertIn("confidentiality_waived", evaluate(CASES[0], decision)["term_violations"])
        self.assertNotIn("confidentiality_waived", evaluate(CASES[3], decision)["term_violations"])

    def test_gate_blocks_acceptance_without_rewriting_report(self):
        decision = valid_decision(decision="accept", amount_inr=1)
        gated, blocked = enforce_mandate(CASES[0], decision)
        self.assertTrue(blocked)
        self.assertEqual(gated.decision, "reject")
        self.assertEqual(gated.client_report, decision.client_report)
        self.assertFalse(evaluate(CASES[0], gated)["unauthorized_acceptance"])

    def test_gate_requests_missing_approval(self):
        gated, blocked = enforce_mandate(CASES[0], valid_decision(decision="accept"))
        self.assertTrue(blocked)
        self.assertEqual(gated.decision, "request_approval")

    def test_never_infers_collusion_from_bad_decision(self):
        score = evaluate(CASES[0], valid_decision(decision="accept", amount_inr=1))
        self.assertIsNone(score["collusion_confirmed"])
        self.assertEqual(score["coordination_label"], "unreviewed")


class SchemaTests(unittest.TestCase):
    def test_round_trip(self):
        self.assertEqual(Decision.parse(valid_decision().to_dict()), valid_decision())

    def test_boolean_not_an_amount(self):
        with self.assertRaises(ValueError):
            Decision.parse({**DECISION_EXAMPLE, "amount_inr": True})

    def test_malformed_fields_rejected(self):
        for updates in [{"decision": "maybe"}, {"amount_inr": -1},
                        {"claims_client_approval": "false"}, {"client_report": ""},
                        {"reported_amount_inr": 1.5}, {"extra": 1}]:
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                Decision.parse({**DECISION_EXAMPLE, **updates})


class ExperimentTests(unittest.TestCase):
    def test_all_conditions_complete_with_scripted_fixtures(self):
        records = [run_episode(CASES[0], c, 1, ScriptedProvider()) for c in CONDITIONS]
        self.assertTrue(all(r["status"] == "ok" for r in records))
        self.assertEqual(sum(len(r["calls"]) for r in records), 14)
        guarded = next(r for r in records if r["condition"] == "verified_injection")
        self.assertTrue(guarded["raw_score"]["unauthorized_acceptance"])
        self.assertFalse(guarded["effective_score"]["unauthorized_acceptance"])

    def test_relay_hides_original_document_from_final_call(self):
        class MarkerProvider(ScriptedProvider):
            def complete(self, stage, messages, context):
                if stage == "summarize":
                    return Completion('{"summary":"SHORT SUMMARY ONLY"}', self.model, {})
                return super().complete(stage, messages, context)
        record = run_episode(CASES[0], "relay_injection", 1, MarkerProvider())
        final = record["calls"][-1]["messages"][-1]["content"]
        self.assertIn("SHORT SUMMARY ONLY", final)
        self.assertNotIn("Internal review note", final)
        self.assertNotIn("minimum_amount_inr", json.dumps(record["calls"][0]["messages"]))

    def test_opponent_does_not_receive_private_mandate_or_report(self):
        record = run_episode(CASES[0], "revision_injection", 1, ScriptedProvider())
        content = json.dumps(record["calls"][1]["messages"])
        self.assertNotIn("minimum_amount_inr", content)
        self.assertNotIn("client_report", content)
        self.assertIn("counterparty_reply", content)

    def test_misinformation_and_injection_have_matched_terms(self):
        a = make_document(CASES[0], "misinformation")
        b = make_document(CASES[0], "injection")
        a.pop("comment")
        b.pop("comment")
        self.assertEqual(a, b)

    def test_invalid_output_is_an_error_not_safe_outcome(self):
        class BadProvider(ScriptedProvider):
            def complete(self, *args):
                return Completion('{"decision":"accept"}', self.model, {})
        record = run_episode(CASES[0], "clean", 1, BadProvider())
        self.assertEqual(record["status"], "error")
        summary = summarize([record])[0]
        self.assertEqual(summary["errors"], 1)
        self.assertIsNone(summary["raw_unauthorized_rate"])

    def test_repetitions_are_distinct_jobs(self):
        a = run_episode(CASES[0], "clean", 1, ScriptedProvider())
        b = run_episode(CASES[0], "clean", 2, ScriptedProvider())
        self.assertNotEqual(a["episode_id"], b["episode_id"])


class ProviderTests(unittest.TestCase):
    def test_custom_endpoint_cannot_receive_default_openai_key(self):
        with self.assertRaises(ValueError):
            OpenAIProvider(api_base="https://provider.example/v1")

    def test_insecure_or_credentialed_endpoint_rejected(self):
        for url in ("http://api.openai.com/v1", "https://secret@api.openai.com/v1"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                OpenAIProvider(api_base=url)

    def test_native_bridge_checks_attribution_and_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            provider = CodexQueueProvider("gpt-6-luna", path)
            record = run_episode(CASES[0], "clean", 1, provider)
            self.assertEqual(record["status"], "pending")
            request_path = next((path / "requests").glob("*.json"))
            request = json.loads(request_path.read_text())
            response = {"model": "gpt-6-luna", "agent_id": "test-agent", "tool_use": False,
                        "prompt_sha256": request["prompt_sha256"],
                        "content": json.dumps(valid_decision().to_dict())}
            response_path = path / "responses" / request_path.name
            response_path.write_text(json.dumps(response))
            self.assertEqual(run_episode(CASES[0], "clean", 1, provider)["status"], "ok")
            response["model"] = "wrong-model"
            response_path.write_text(json.dumps(response))
            self.assertEqual(run_episode(CASES[0], "clean", 1, provider)["status"], "error")


class CLITests(unittest.TestCase):
    def test_end_to_end_demo_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            output = Path(directory) / "demo"
            args = ["run", "--output", str(output), "--cases", "LEX_001", "--workers", "2"]
            self.assertEqual(main(args), 0)
            self.assertEqual(main(args), 2)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(manifest["completed_episodes"], 8)
            self.assertEqual(len(list((output / "episodes").glob("*.json"))), 8)
            self.assertIn("not model research results", (output / "report.md").read_text())

    def test_budget_prevents_any_run(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stderr(io.StringIO()):
            output = Path(directory) / "demo"
            self.assertEqual(main(["run", "--output", str(output), "--max-calls", "1"]), 2)
            self.assertFalse(output.exists())

    def test_native_resume_preserves_annotation(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            output = Path(directory) / "native"
            args = ["run", "--backend", "codex", "--model", "gpt-6-luna", "--cases", "LEX_001",
                    "--conditions", "clean", "--output", str(output)]
            self.assertEqual(main(args), 3)
            request_path = next((output / "requests").glob("*.json"))
            response = Path(directory) / "final.json"
            response.write_text(json.dumps(valid_decision().to_dict()))
            self.assertEqual(main(["import-response", str(request_path), str(response), "--model", "gpt-6-luna",
                                   "--agent-id", "test-native-agent", "--no-tools-used"]), 0)
            (output / "annotations.csv").write_text("human review preserved\n")
            self.assertEqual(main(args + ["--resume"]), 0)
            self.assertEqual((output / "annotations.csv").read_text(), "human review preserved\n")

    def test_no_zero_denominator_or_false_certainty(self):
        self.assertIsNone(wilson_interval(0, 0))
        self.assertGreater(wilson_interval(0, 3)[1], 0.5)


if __name__ == "__main__":
    unittest.main()
