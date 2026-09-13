"""Focused offline checks for the isolated receiving-evidence experiment.

Run with the prepared environment, not the product environment:

    /private/tmp/m20-evals-venv/bin/python -m unittest \
      experiments/receiving_evidence_v1/test_receiving_evidence.py
"""

from __future__ import annotations

import asyncio
import json
import stat
import sys
import tempfile
import unittest
from collections.abc import AsyncGenerator
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from strands.models import Model

EXPERIMENT = Path(__file__).resolve().parent
if str(EXPERIMENT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT))

import receiving_evidence as experiment  # noqa: E402


def _tool_events(name: str, payload: dict[str, Any], *, serial: int) -> list[dict[str, Any]]:
    return [
        {"messageStart": {"role": "assistant"}},
        {
            "contentBlockStart": {
                "start": {"toolUse": {"name": name, "toolUseId": f"fake-{serial}"}}
            }
        },
        {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(payload)}}}},
        {"contentBlockStop": {}},
        {"messageStop": {"stopReason": "tool_use"}},
        {"metadata": {"usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2}}},
    ]


class ScriptedLocalModel(Model):
    """Local protocol model used only by tests; it does no provider I/O."""

    def __init__(self, actions: list[tuple[str, Any]]) -> None:
        self.actions = list(actions)
        self.config: dict[str, Any] = {
            "model_id": "scripted-local-test-only",
            "max_tokens": 4096,
            "temperature": 0,
        }
        self.calls: list[dict[str, Any]] = []
        self._serial = 0

    def get_config(self) -> dict[str, Any]:
        return dict(self.config)

    def update_config(self, **kwargs: Any) -> None:
        self.config.update(kwargs)

    async def count_tokens(self, *_: Any, **__: Any) -> int:
        return 1

    async def structured_output(self, *_: Any, **__: Any) -> AsyncGenerator[dict[str, Any], None]:
        if False:  # pragma: no cover - satisfies async generator type.
            yield {}
        raise AssertionError("test model expects native Agent.stream structured output")

    async def stream(
        self,
        messages: Any,
        tool_specs: Any = None,
        system_prompt: str | None = None,
        **_: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:
        self.calls.append(
            {
                "messages": json.loads(json.dumps(messages, default=str)),
                "tool_specs": json.loads(json.dumps(tool_specs or [], default=str)),
                "config": dict(self.config),
                "system_prompt": system_prompt,
            }
        )
        if not self.actions:
            raise AssertionError("unexpected additional local model call")
        kind, value = self.actions.pop(0)
        if kind == "raise":
            raise RuntimeError(str(value))
        if kind == "tool":
            name, payload = value
        elif kind == "structured":
            source_tools = {
                spec.get("name")
                for spec in (tool_specs or [])
                if isinstance(spec, dict) and str(spec.get("name", "")).startswith("read_")
            }
            structured = [
                spec.get("name")
                for spec in (tool_specs or [])
                if isinstance(spec, dict) and spec.get("name") not in source_tools
            ]
            if len(structured) != 1:
                raise AssertionError(
                    f"could not find one native structured-output tool: {tool_specs!r}"
                )
            name, payload = structured[0], value
        else:  # pragma: no cover - fixtures enumerate all actions.
            raise AssertionError(f"unknown scripted action {kind}")
        self._serial += 1
        for event in _tool_events(str(name), dict(payload), serial=self._serial):
            yield event


def _case(name: str = "DEV4-completed-simple") -> experiment.CaseInput:
    return experiment.load_case(EXPERIMENT / "dev_cases" / f"{name}.case.json")


def _key(name: str = "DEV4-completed-simple") -> experiment.KeyFile:
    return experiment.load_key(EXPERIMENT / "dev_keys" / f"{name}.key.json")


def _receiving_observation(case: experiment.CaseInput) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "snapshot_id": case.snapshot_id,
        "actor": "receiving_specialist",
        "source_mode": "synthetic_snapshot",
        "as_of": case.as_of,
        "literals": [
            {
                "record_id": "RCV-D1",
                "field_path": "/received_quantity",
                "literal_value": {"value": 10, "unit": "EA"},
            },
            {"record_id": "RCV-D1", "field_path": "/quality_state", "literal_value": "released"},
        ],
        "interpretations": ["Quality evidence is released in the returned receiving record."],
        "source_read_status": "evidence_returned",
        "missing_evidence": [],
    }


def _fulfillment_observation(case: experiment.CaseInput) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "snapshot_id": case.snapshot_id,
        "actor": "fulfillment_specialist",
        "source_mode": "synthetic_snapshot",
        "as_of": case.as_of,
        "literals": [
            {"record_id": "ORD-D1", "field_path": "/order_id", "literal_value": "SO-D1"},
            {
                "record_id": "ORD-D1",
                "field_path": "/requested_quantity",
                "literal_value": {"value": 10, "unit": "EA"},
            },
            {
                "record_id": "ORD-D1",
                "field_path": "/acknowledgement_state",
                "literal_value": "confirmed",
            },
        ],
        "interpretations": [
            "The returned contract record does not declare a literal eligible quantity."
        ],
        "source_read_status": "evidence_returned",
        "missing_evidence": [],
    }


def _answer(
    case: experiment.CaseInput, *, citation_actor: str = "receiving_specialist"
) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "snapshot_id": case.snapshot_id,
        "source_mode": "synthetic_snapshot",
        "as_of": case.as_of,
        "quantities": [
            {"name": "RCV-D1:received_quantity", "value": 10, "unit": "EA", "state": "known"}
        ],
        "order_dispositions": [
            {
                "order_id": "SO-D1",
                "disposition": "unknown",
                "eligible_quantity": {
                    "name": "SO-D1:eligible_quantity",
                    "value": None,
                    "unit": "EA",
                    "state": "unknown",
                },
                "missing_prerequisites": ["mechanical eligibility state is absent"],
            }
        ],
        "citations": [
            {
                "actor": citation_actor,
                "record_id": "RCV-D1",
                "field_path": "/received_quantity",
                "literal_value": {"value": 10, "unit": "EA"},
            },
            {
                "actor": "fulfillment_specialist"
                if citation_actor != "single_investigator"
                else citation_actor,
                "record_id": "ORD-D1",
                "field_path": "/requested_quantity",
                "literal_value": {"value": 10, "unit": "EA"},
            },
        ],
        "missing_evidence": [
            "eligibility determination is absent from the returned contract record"
        ],
        "answer_text": (
            "The returned receipt identifies 10 EA, but the contract evidence "
            "lacks a literal eligibility determination; no approval or execution occurred."
        ),
        "authority": {"approval": False, "executed": False},
    }


class ReceivingEvidenceTests(unittest.TestCase):
    def _freeze(self) -> dict[str, Any]:
        return experiment.create_freeze_payload_for_verification()

    def test_pinned_opus_factory_uses_pinned_session_with_real_bedrock_constructor(self) -> None:
        import boto3
        from strands.models import BedrockModel

        class FakeCredentials:
            access_key = "offline-access-key"
            secret_key = "offline-secret-key"
            token = "offline-session-token"

        class FakeClient:
            def __init__(self) -> None:
                self.meta = SimpleNamespace(region_name=experiment.MODEL_REGION)

        class FakeSession:
            region_name = experiment.MODEL_REGION

            def __init__(self) -> None:
                self.credentials = FakeCredentials()
                self.client_calls: list[dict[str, Any]] = []

            def get_credentials(self) -> FakeCredentials:
                return self.credentials

            def client(self, **kwargs: Any) -> FakeClient:
                self.client_calls.append(kwargs)
                return FakeClient()

        session = FakeSession()
        with patch.object(boto3, "Session", return_value=session) as session_constructor:
            model = experiment.pinned_opus_4_6_factory("single", 1024)

        self.assertIsInstance(model, BedrockModel)
        self.assertEqual(experiment.MODEL_ID, "us.anthropic.claude-opus-4-6-v1")
        session_constructor.assert_called_once_with(
            profile_name="missing20-sandbox", region_name="us-west-2"
        )
        self.assertEqual(len(session.client_calls), 1)
        self.assertEqual(session.client_calls[0]["region_name"], "us-west-2")
        self.assertEqual(model.client.meta.region_name, "us-west-2")

    def test_opus_budget_and_freeze_pin_pricing_and_maximum_cost(self) -> None:
        maximum_cost = Decimal("32000") * Decimal("0.0000055") + Decimal("6000") * Decimal(
            "0.0000275"
        )
        freeze = self._freeze()

        self.assertEqual(maximum_cost, Decimal("0.3410000"))
        self.assertEqual(experiment.WORKFLOW_CAPS.input_price_per_token, Decimal("0.0000055"))
        self.assertEqual(experiment.WORKFLOW_CAPS.output_price_per_token, Decimal("0.0000275"))
        self.assertEqual(experiment.WORKFLOW_CAPS.cost_cap_usd, Decimal("0.35"))
        self.assertLessEqual(maximum_cost, experiment.WORKFLOW_CAPS.cost_cap_usd)
        self.assertEqual(freeze["workflow_budget"]["input_price_usd_per_token"], "0.0000055")
        self.assertEqual(freeze["workflow_budget"]["output_price_usd_per_token"], "0.0000275")
        self.assertEqual(freeze["workflow_budget"]["estimated_cost_cap_usd"], "0.35")

    def test_global_budget_carries_forward_settled_nova_cost_before_opus_reservations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "ledger.jsonl"
            experiment._private_append_jsonl(
                ledger_path,
                {
                    "schema_version": experiment.SCHEMA_VERSION,
                    "event": "reserve_workflow",
                    "run_id": "historical-nova-v7",
                    "candidate": "single",
                    "case_sha256": "historical-synthetic-case",
                    "reserved_cost_usd": "0.06",
                    "timestamp": "2026-09-12T00:00:00+00:00",
                },
            )
            experiment._private_append_jsonl(
                ledger_path,
                {
                    "schema_version": experiment.SCHEMA_VERSION,
                    "event": "settle_workflow",
                    "run_id": "historical-nova-v7",
                    "charged_cost_usd": "0.0461952",
                    "status": "FAILED",
                    "timestamp": "2026-09-12T00:01:00+00:00",
                },
            )
            ledger = experiment.DurableExperimentLedger(ledger_path)
            for index in range(8):
                ledger.reserve_workflow(
                    run_id=f"opus-{index}", candidate="single", case_hash=f"case-{index}"
                )
            with self.assertRaises(experiment.BudgetError):
                ledger.reserve_workflow(
                    run_id="opus-over-cap", candidate="single", case_hash="case-over-cap"
                )

    def _evaluate_single_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        case = _case()
        reader = experiment.SourceReader(case)
        reader.retrieve(
            actor="single_investigator",
            source="receiving_quality",
            query="all evidence",
            record_ids=["RCV-D1"],
        )
        reader.retrieve(
            actor="single_investigator",
            source="fulfillment_contract",
            query="all evidence",
            record_ids=["ORD-D1"],
        )
        answer = experiment.DecisionAnswer.model_validate(payload)
        reader.validate_answer(answer, allowed_citation_actors={"single_investigator"})
        return experiment.evaluate_answer(
            case=case,
            key=_key(),
            answer=answer,
            reader=reader,
            actor_trace=experiment._trace_payload(reader, model_attempts={}),
            candidate="single",
        )

    def test_rules_dev4_vertical_slice_uses_official_evals_and_private_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = experiment.execute_candidate(
                case=_case(),
                key=_key(),
                candidate="rules",
                model_factory=None,
                freeze_manifest=self._freeze(),
                durable_ledger=experiment.DurableExperimentLedger(root / "ledger.jsonl"),
                run_log=root / "runs.jsonl",
                case_reference="DEV4-completed-simple.case.json",
            )
            self.assertEqual(record["status"], "COMPLETED")
            self.assertEqual(record["evaluation"]["overall_score"], 1.0)
            self.assertEqual(record["usage"]["requests"], 0)
            self.assertEqual(record["promotion_status"], "NOT_AUTOMATICALLY_PROMOTED")
            self.assertEqual(
                record["evaluation"]["cases"][0]["evaluator_type"], "ReceivingEvidenceEvaluator"
            )
            self.assertEqual(self._freeze()["runtime"]["aws_profile"], "missing20-sandbox")
            quantity_description = experiment.Quantity.model_json_schema()["properties"]["name"][
                "description"
            ]
            self.assertIn("<record_id>:<field_name>", quantity_description)
            output_description = experiment.DecisionAnswer.model_json_schema()["properties"][
                "quantities"
            ]["description"]
            self.assertIn("question-requested", output_description)
            self.assertEqual(stat.S_IMODE((root / "runs.jsonl").stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE((root / "ledger.jsonl").stat().st_mode), 0o600)

    def test_native_graph_waits_for_two_typed_inputs_and_clamps_each_provider_call(self) -> None:
        case = _case()
        key = _key()
        key = key.model_copy(
            update={
                "expected": key.expected.model_copy(
                    update={
                        "required_citations": [
                            experiment.CitationRequirement(
                                record_id="RCV-D1",
                                field_path="/quality_state",
                                literal_value="DEV4-COMPLETELY-UNRELATED-KEY-SENTINEL",
                            )
                        ]
                    }
                )
            }
        )
        models: dict[str, ScriptedLocalModel] = {}

        def factory(stage: str, _: int) -> Model:
            actions: dict[str, list[tuple[str, Any]]] = {
                "receiving": [
                    (
                        "tool",
                        (
                            "read_receiving_quality",
                            {"query": "all evidence", "record_ids": ["RCV-D1"]},
                        ),
                    ),
                    ("structured", _receiving_observation(case)),
                ],
                "fulfillment": [
                    (
                        "tool",
                        (
                            "read_fulfillment_contract",
                            {"query": "all evidence", "record_ids": ["ORD-D1"]},
                        ),
                    ),
                    ("structured", _fulfillment_observation(case)),
                ],
                "coordinator": [("structured", _answer(case))],
            }
            model = ScriptedLocalModel(actions[stage])
            models[stage] = model
            return model

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = experiment.execute_candidate(
                case=case,
                key=key,
                candidate="graph",
                model_factory=factory,
                freeze_manifest=self._freeze(),
                durable_ledger=experiment.DurableExperimentLedger(root / "ledger.jsonl"),
                run_log=root / "runs.jsonl",
            )
        self.assertEqual(record["status"], "COMPLETED", record["errors"])
        join = record["actor_trace"]["validated_join_packet"]
        self.assertEqual(join["receiving"]["actor"], "receiving_specialist")
        self.assertEqual(join["fulfillment"]["actor"], "fulfillment_specialist")
        self.assertEqual(record["usage"]["requests"], 5)
        for model in models.values():
            self.assertTrue(model.calls)
            self.assertTrue(all(call["config"]["max_tokens"] <= 1024 for call in model.calls))
        coordinator_messages = json.dumps(models["coordinator"].calls, sort_keys=True)
        self.assertIn("join_packet", coordinator_messages)
        self.assertNotIn("DEV4-COMPLETELY-UNRELATED-KEY-SENTINEL", coordinator_messages)
        receiving_prompt = json.loads(
            models["receiving"].calls[0]["messages"][0]["content"][0]["text"]
        )
        fulfillment_prompt = json.loads(
            models["fulfillment"].calls[0]["messages"][0]["content"][0]["text"]
        )
        self.assertEqual(receiving_prompt["required_actor"], experiment.ACTOR_RECEIVING)
        self.assertEqual(fulfillment_prompt["required_actor"], experiment.ACTOR_FULFILLMENT)

    def test_single_investigator_uses_native_read_tool_loop(self) -> None:
        case = _case()
        models: list[ScriptedLocalModel] = []
        answer = _answer(case, citation_actor="single_investigator")
        answer["order_dispositions"][0]["missing_prerequisites"] = [
            "raw contract evidence does not establish an eligible quantity"
        ]

        def factory(stage: str, _: int) -> Model:
            self.assertEqual(stage, "single")
            model = ScriptedLocalModel(
                [
                    (
                        "tool",
                        (
                            "read_receiving_quality",
                            {"query": "all evidence", "record_ids": ["RCV-D1"]},
                        ),
                    ),
                    (
                        "tool",
                        (
                            "read_fulfillment_contract",
                            {"query": "all evidence", "record_ids": ["ORD-D1"]},
                        ),
                    ),
                    ("structured", answer),
                ]
            )
            models.append(model)
            return model

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = experiment.execute_candidate(
                case=case,
                key=_key(),
                candidate="single",
                model_factory=factory,
                freeze_manifest=self._freeze(),
                durable_ledger=experiment.DurableExperimentLedger(root / "ledger.jsonl"),
                run_log=root / "runs.jsonl",
            )
        self.assertEqual(record["status"], "COMPLETED", record["errors"])
        self.assertEqual(record["evaluation"]["overall_score"], 1.0)
        self.assertEqual(record["usage"]["requests"], 3)
        self.assertEqual(
            [call["tool"] for call in record["actor_trace"]["tool_calls"]],
            ["read_receiving_quality", "read_fulfillment_contract"],
        )
        self.assertTrue(all(call["config"]["max_tokens"] <= 1024 for call in models[0].calls))
        single_prompt = json.loads(models[0].calls[0]["messages"][0]["content"][0]["text"])
        self.assertEqual(single_prompt["required_citation_actor"], experiment.ACTOR_SINGLE)

    def test_source_tool_discloses_and_implements_query_contract(self) -> None:
        reader = experiment.SourceReader(_case("DEV4-split-pending-quality"))
        tool_spec = reader.tool_for(
            actor=experiment.ACTOR_SINGLE, source=experiment.SOURCE_FULFILLMENT
        ).tool_spec
        description = str(tool_spec["description"])
        self.assertIn("case-insensitive substrings", description)
        self.assertIn("literal term 'all'", description)
        self.assertIn("intersection", description)

        matched = reader.retrieve(
            actor=experiment.ACTOR_SINGLE,
            source=experiment.SOURCE_FULFILLMENT,
            query="SO-D2 pending_evidence",
            record_ids=["ORD-D2"],
        )
        self.assertEqual([record["record_id"] for record in matched["records"]], ["ORD-D2"])
        all_records = reader.retrieve(
            actor=experiment.ACTOR_SINGLE,
            source=experiment.SOURCE_FULFILLMENT,
            query="all",
            record_ids=["ORD-D2"],
        )
        self.assertEqual([record["record_id"] for record in all_records["records"]], ["ORD-D2"])

    def test_evaluator_rejects_swapped_quantity_name(self) -> None:
        payload = _answer(_case(), citation_actor="single_investigator")
        payload["quantities"][0]["name"] = "ORD-D1:requested_quantity"
        report = self._evaluate_single_payload(payload)
        self.assertLess(report["overall_score"], 1.0)
        rows = {row["label"]: row for row in report["detailed_results"][0]}
        self.assertFalse(rows["quantities"]["test_pass"])

    def test_evaluator_rejects_unrequested_quantity_and_order_claims(self) -> None:
        payload = _answer(_case(), citation_actor="single_investigator")
        payload["quantities"].append(
            {"name": "HALLUCINATED:quantity", "value": 999, "unit": "EA", "state": "known"}
        )
        payload["order_dispositions"].append(
            {
                "order_id": "SO-UNRELATED",
                "disposition": "unknown",
                "eligible_quantity": {
                    "name": "SO-UNRELATED:eligible_quantity",
                    "value": None,
                    "unit": "EA",
                    "state": "unknown",
                },
                "missing_prerequisites": ["no evidence was requested for this order"],
            }
        )
        report = self._evaluate_single_payload(payload)
        self.assertLess(report["overall_score"], 1.0)
        rows = {row["label"]: row for row in report["detailed_results"][0]}
        self.assertFalse(rows["quantities"]["test_pass"])
        self.assertFalse(rows["order_dispositions"]["test_pass"])

    def test_unresolved_answer_requires_a_missing_evidence_reason(self) -> None:
        payload = _answer(_case(), citation_actor="single_investigator")
        payload["missing_evidence"] = []
        with self.assertRaises(ValueError):
            experiment.DecisionAnswer.model_validate(payload)

    def test_join_gate_requires_two_completed_typed_specialists(self) -> None:
        case = _case()
        receiving = SimpleNamespace(
            observation=experiment.SpecialistObservation.model_validate(
                _receiving_observation(case)
            )
        )
        fulfillment = SimpleNamespace(
            observation=experiment.SpecialistObservation.model_validate(
                _fulfillment_observation(case)
            )
        )
        gate = experiment._JoinGate(case=case, receiving=receiving, fulfillment=fulfillment)
        self.assertFalse(gate.ready(SimpleNamespace(results={"receiving_specialist": object()})))
        self.assertIsNone(gate.packet)
        self.assertTrue(
            gate.ready(
                SimpleNamespace(
                    results={"receiving_specialist": object(), "fulfillment_specialist": object()}
                )
            )
        )
        self.assertIsNotNone(gate.packet)

    def test_unavailable_source_and_zero_literals_are_honest_valid_states(self) -> None:
        case = _case()
        unavailable = experiment.SourcePacket(
            source="receiving_quality", status="unavailable", as_of=None, records=[]
        )
        revised = case.model_copy(
            update={"source_packets": [unavailable, case.packet("fulfillment_contract")]}
        )
        reader = experiment.SourceReader(revised)
        returned = reader.retrieve(
            actor="receiving_specialist",
            source="receiving_quality",
            query="all evidence",
            record_ids=[],
        )
        self.assertEqual(returned["records"], [])
        observation = experiment.SpecialistObservation(
            case_id=revised.case_id,
            snapshot_id=revised.snapshot_id,
            actor="receiving_specialist",
            source_mode="synthetic_snapshot",
            as_of=revised.as_of,
            literals=[],
            interpretations=[],
            source_read_status="source_unavailable",
            missing_evidence=["receiving source unavailable"],
        )
        reader.validate_specialist(observation, expected_actor="receiving_specialist")

    def test_unknown_provider_usage_charges_the_full_clamped_reservation(self) -> None:
        local = ScriptedLocalModel([("raise", "simulated provider timeout")])
        ledger = experiment.StrictWorkflowLedger(candidate="single")
        bounded = experiment.StrictReservationModel(local, ledger, "single")

        async def call() -> None:
            async for _ in bounded.stream(messages=[{"role": "user", "content": [{"text": "x"}]}]):
                pass

        with self.assertRaises(RuntimeError):
            asyncio.run(call())
        self.assertEqual(local.calls[0]["config"]["max_tokens"], 1024)
        snapshot = ledger.snapshot()
        self.assertEqual(snapshot["actual_output_tokens"], 1024)
        self.assertIn("unknown_usage:single:1", snapshot["errors"])

    def test_failed_single_retains_model_attempt_usage_and_tool_trace(self) -> None:
        case = _case()

        def factory(stage: str, _: int) -> Model:
            self.assertEqual(stage, "single")
            return ScriptedLocalModel(
                [
                    (
                        "tool",
                        (
                            "read_receiving_quality",
                            {"query": "all evidence", "record_ids": ["RCV-D1"]},
                        ),
                    ),
                    ("raise", "simulated provider timeout after source read"),
                ]
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = experiment.execute_candidate(
                case=case,
                key=_key(),
                candidate="single",
                model_factory=factory,
                freeze_manifest=self._freeze(),
                durable_ledger=experiment.DurableExperimentLedger(root / "ledger.jsonl"),
                run_log=root / "runs.jsonl",
            )
        self.assertEqual(record["status"], "FAILED")
        self.assertEqual(
            [call["tool"] for call in record["actor_trace"]["tool_calls"]],
            ["read_receiving_quality"],
        )
        attempts = record["actor_trace"]["model_attempts"]["single"]
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[-1]["error"]["type"], "RuntimeError")
        self.assertEqual(record["usage"]["requests"], 2)
        self.assertEqual(record["usage"]["actual_output_tokens"], 1025)
        self.assertIn(
            "read_receiving_quality",
            json.dumps(record["actor_trace"]["agent_messages"]["single"], sort_keys=True),
        )

    def test_failed_single_retains_native_validation_feedback_in_private_trace(self) -> None:
        case = _case()

        def factory(stage: str, _: int) -> Model:
            self.assertEqual(stage, "single")
            return ScriptedLocalModel(
                [
                    ("structured", {}),
                    ("raise", "stop after native structured-output validation feedback"),
                ]
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = experiment.execute_candidate(
                case=case,
                key=_key(),
                candidate="single",
                model_factory=factory,
                freeze_manifest=self._freeze(),
                durable_ledger=experiment.DurableExperimentLedger(root / "ledger.jsonl"),
                run_log=root / "runs.jsonl",
            )

        self.assertEqual(record["status"], "FAILED")
        rendered = json.dumps(record["actor_trace"]["agent_messages"]["single"], sort_keys=True)
        self.assertIn("Validation failed for", rendered)
        self.assertIn("toolResult", rendered)

    def test_blinded_export_hides_candidate_provider_and_actor_names(self) -> None:
        case = _case()
        answer = experiment.DecisionAnswer.model_validate(_answer(case))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_log = root / "runs.jsonl"
            for candidate in ("single", "graph"):
                experiment._private_append_jsonl(
                    run_log,
                    {
                        "record_type": "workflow",
                        "status": "COMPLETED",
                        "candidate": candidate,
                        "question": case.question,
                        "case": {
                            "case_id": case.case_id,
                            "snapshot_id": case.snapshot_id,
                            "tier": case.tier,
                            "source_packet_reference": "DEV4-completed-simple.case.json",
                        },
                        "answer": answer.model_dump(mode="json"),
                        "model": {"model_id": "do-not-export"},
                        "actor_trace": {"actor": "do-not-export"},
                    },
                )
            payload = experiment.export_blinded(
                run_log=run_log, output=root / "blinded.json", seed="fixed"
            )
            rendered = json.dumps(payload, sort_keys=True)
            self.assertEqual(len(payload["records"]), 2)
            self.assertNotIn("single", rendered)
            self.assertNotIn("graph", rendered)
            self.assertNotIn("do-not-export", rendered)
            self.assertNotIn("receiving_specialist", rendered)
            self.assertIn(case.question, rendered)


if __name__ == "__main__":
    unittest.main()
