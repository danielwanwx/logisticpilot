"""Focused economic POC source-of-truth checks."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from scripts.provision_distributor_operations import _economic_plan
from the_missing_20.adapters.distributor_operations import DistributorOperations
from the_missing_20.agents.distributor_economics import (
    SPLIT20_CANDIDATE_ID,
    _classify_model_failure,
    _validated_model_selection,
    economic_gate,
    economic_projection,
    raw_economic_evidence,
    validate_economic_config,
)


def test_runtime_quality_not_configured_fixture_controls_split_readiness() -> None:
    config = _economic_plan(
        supplier="SYNTHETIC-SUPPLIER",
        date="2026-09-13",
        purchase_order="PUR-ECONOMIC-TEST",
        purchase_order_item="PUR-ECONOMIC-TEST-ITEM",
        instance="TEST",
    )
    validate_economic_config(config)
    order = config["allocations"][0]["customer_order"]
    snapshot = {
        "source_status": "CURRENT",
        "quantities": {"usable": 0},
        "lots": [
            {"lot": "LOT-A20", "usable": 0, "held": 0, "status": "AWAITING_ARRIVAL"},
            {"lot": "LOT-B5", "usable": 0, "held": 0, "status": "AWAITING_ARRIVAL"},
        ],
        "allocations": [
            {
                "customer_order": order,
                "requested_quantity": 25,
                "allocated": 0,
            }
        ],
        "contract_terms": config["allocations"],
        "prepared_picks": [],
    }

    evidence = raw_economic_evidence(config, snapshot)
    assert "QUALIFIED" not in str(evidence["quality"])

    gate = economic_gate(
        config,
        snapshot,
        now=datetime.fromisoformat("2026-09-13T09:00:00-07:00"),
        candidate_id=SPLIT20_CANDIDATE_ID,
    )
    assert gate["allowed"] is False
    assert "RAW_A20_USABLE_STOCK_INSUFFICIENT" in gate["reasons"]

    projected = economic_projection(
        config,
        snapshot,
        now=datetime.fromisoformat("2026-09-13T09:00:00-07:00"),
    )
    assert projected is not None
    split = projected["candidates"][0]
    assert split["execution_status"] == "NEEDS_EVIDENCE"
    assert split["estimated_postage"] == {
        "amount": 49.6,
        "currency": "USD",
        "label": "Postage-only estimate; not paid or booked",
        "source_id": "public:usps-notice-123-2026-07-12",
        "source_ref": "https://pe.usps.com/text/dmm300/Notice123.htm",
    }
    assert projected["estimated_postage_difference"] == {
        "amount": 24.8,
        "currency": "USD",
        "label": "Postage-only estimate difference; not confirmed or realized",
    }
    assert projected["source_evidence"][2]["ref"] == "https://pe.usps.com/text/dmm300/Notice123.htm"
    assert projected["model"]["status"] == "not_run"


def test_model_defer_still_requires_all_raw_evidence_tool_reads() -> None:
    config = _economic_plan(
        supplier="SYNTHETIC-SUPPLIER",
        date="2026-09-13",
        purchase_order="PUR-ECONOMIC-TEST",
        purchase_order_item="PUR-ECONOMIC-TEST-ITEM",
        instance="TEST",
    )
    evidence = raw_economic_evidence(
        config,
        {
            "source_status": "CURRENT",
            "quantities": {"usable": 20, "held": 5},
            "lots": [
                {"lot": "LOT-A20", "usable": 20, "held": 0, "status": "QUALIFIED"},
                {"lot": "LOT-B5", "usable": 0, "held": 5, "status": "HELD"},
            ],
            "allocations": [],
            "contract_terms": config["allocations"],
            "prepared_picks": [],
        },
    )
    raw = {
        "candidate_id": "DEFER",
        "rationale": "The remaining lot is not released.",
        "citations": [evidence["quality"]["evidence_id"]],
    }

    selected, failure = _validated_model_selection(
        raw, evidence=evidence, calls=["read_quality_evidence"]
    )

    assert selected is None
    assert failure == "MODEL_SOURCE_READS_INCOMPLETE"


def test_limit_stop_with_no_structured_result_is_a_budget_exhaustion() -> None:
    assert (
        _classify_model_failure("MODEL_DECISION_MALFORMED", stop_reason="limit_output_tokens")
        == "MODEL_BUDGET_EXHAUSTED"
    )
    assert (
        _classify_model_failure("MODEL_DECISION_MALFORMED", stop_reason="completed")
        == "MODEL_DECISION_MALFORMED"
    )


def test_persisted_economic_effect_reads_applied_event_and_marks_prior_model_historical(
    tmp_path: Path,
) -> None:
    """A fresh projection must not present an applied split20 as merely prepared."""

    config = _economic_plan(
        supplier="SYNTHETIC-SUPPLIER",
        date="2026-09-13",
        purchase_order="PUR-ECONOMIC-TEST",
        purchase_order_item="PUR-ECONOMIC-TEST-ITEM",
        instance="TEST",
    )
    configured = config["economic_proposal"]
    assert isinstance(configured, dict)
    event = configured["split20_event"]
    assert isinstance(event, dict)
    proposal_id = "economic-persisted-split20"
    encoded_event = json.dumps(event, sort_keys=True, separators=(",", ":"))
    historical = {
        "requested_candidate_id": "split20",
        "prepared_proposal_id": proposal_id,
        "source_evidence_id": "operational:before-dispatch",
        "model": {
            "status": "SELECTED",
            "candidate_id": "split20",
            "rationale": "The first twenty units were executable at the prior snapshot.",
            "citations": [],
            "tool_trace": [],
            "model_response": None,
        },
    }
    service = DistributorOperations(
        tmp_path / "economic-effect.sqlite3",
        config,
        None,
        clock=lambda: datetime.fromisoformat("2026-09-13T09:00:00-07:00"),
    )
    service._db.execute(
        "INSERT INTO distributor_operation_events "
        "(event_id, payload_json, result_json, state_json, recorded_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            event["event_id"],
            encoded_event,
            json.dumps(
                {
                    "events": [
                        {
                            "event_id": event["event_id"],
                            "status": "APPLIED",
                            "operations": [
                                {
                                    "kind": "submit_pick",
                                    "status": "APPLIED",
                                    "documents": [
                                        {
                                            "kind": "Pick List",
                                            "name": "PICK-SPLIT20",
                                            "status": "Completed",
                                        }
                                    ],
                                },
                                {
                                    "kind": "submit_delivery_note",
                                    "status": "APPLIED",
                                    "documents": [
                                        {
                                            "kind": "Delivery Note",
                                            "name": "DN-SPLIT20",
                                            "status": "To Bill",
                                        }
                                    ],
                                },
                                {
                                    "kind": "create_shipment",
                                    "status": "APPLIED",
                                    "documents": [
                                        {
                                            "kind": "Shipment",
                                            "name": "SHIP-SPLIT20",
                                            "status": "Submitted",
                                        }
                                    ],
                                },
                            ],
                        }
                    ]
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            "{}",
            "2026-09-13T16:00:00+00:00",
        ),
    )
    service._db.execute(
        "INSERT INTO distributor_operation_proposals "
        "(proposal_id, case_id, event_json, source, attachment_id, state_revision, "
        "result_json, manager_id, approved_at, recorded_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            proposal_id,
            config["case_id"],
            encoded_event,
            "ECONOMIC_RECOMMENDATION",
            None,
            "pre-dispatch-revision",
            json.dumps(
                {"economic_proposal": {"last_result": historical}},
                sort_keys=True,
                separators=(",", ":"),
            ),
            "manager-1",
            "2026-09-13T16:01:00+00:00",
            "2026-09-13T16:01:00+00:00",
        ),
    )
    snapshot = {
        "source_status": "CURRENT",
        "as_of": "2026-09-13T16:02:00+00:00",
        "quantities": {"usable": 0, "held": 5, "allocated": 0, "dispatched": 20},
        "lots": [
            {"lot": "LOT-A20", "usable": 0, "held": 0, "status": "DISPATCHED"},
            {"lot": "LOT-B5", "usable": 0, "held": 5, "status": "HELD"},
        ],
        "allocations": [
            {
                "customer_order": config["allocations"][0]["customer_order"],
                "requested_quantity": 25,
                "allocated": 0,
                "backordered": 5,
                "dispatched": 20,
            }
        ],
        "contract_terms": config["allocations"],
        "prepared_picks": [],
    }

    projection = service._economic_view(snapshot, None)
    effect = projection["proposal_effect"]
    assert effect["status"] == "APPLIED"
    assert effect["approval"] == {
        "manager_id": "manager-1",
        "approved_at": "2026-09-13T16:01:00+00:00",
    }
    assert [document["name"] for document in effect["native_documents"]] == [
        "DN-SPLIT20",
        "PICK-SPLIT20",
        "SHIP-SPLIT20",
    ]
    assert projection["model"]["status"] == "HISTORICAL"
    assert projection["model"]["prior_status"] == "SELECTED"
    assert projection["model"]["source_evidence_id"] == "operational:before-dispatch"
    assert projection["model"]["current_source_evidence_id"] != "operational:before-dispatch"
    split = projection["candidates"][0]
    assert split["proposal_effect"]["status"] == "APPLIED"
    service.close()
