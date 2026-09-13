"""Small, evidence-bound postage comparison for a configured distributor case.

The module deliberately has no ERP client and no execution capability.  It
validates a trusted local configuration, exposes the four raw records a model
may read, calculates displayed scenario arithmetic, and checks the one
permitted economic proposal before the operations adapter prepares it.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from time import monotonic
from typing import Any, Literal, cast

from pydantic import BaseModel, Field, model_validator

from the_missing_20.ports.agent_model import (
    AgentBudgetLedger,
    AgentModelFactory,
    AgentStage,
    actual_provider_metadata,
)

ECONOMIC_PROPOSAL_VERSION = "v1"
SPLIT20_CANDIDATE_ID = "split20"
CONSOLIDATION25_CANDIDATE_ID = "consolidation25"
DEFER_CANDIDATE_ID = "DEFER"
_CANDIDATE_IDS = frozenset({SPLIT20_CANDIDATE_ID, CONSOLIDATION25_CANDIDATE_ID})
_TOOL_NAMES = (
    "read_contract_evidence",
    "read_quality_evidence",
    "read_cost_evidence",
    "read_operational_snapshot",
)


class EconomicSelection(BaseModel):
    """The model can select a named candidate or defer; it cannot author a plan."""

    candidate_id: Literal["split20", "consolidation25", "DEFER"]
    rationale: str = Field(min_length=1, max_length=480)
    citations: list[str] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def _unique_citations(self) -> EconomicSelection:
        if len(self.citations) != len(set(self.citations)):
            raise ValueError("economic citations must be unique")
        return self


def _copy(value: object) -> Any:
    """Detach JSON-like configuration and reject values that cannot cross the boundary."""

    return json.loads(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False))


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > 256:
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _number(value: object, label: str, *, positive: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{label} must be a number")
    try:
        parsed = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError(f"{label} must be a number") from error
    if not parsed.is_finite() or parsed < 0 or (positive and parsed <= 0):
        raise ValueError(f"{label} must be {'positive' if positive else 'non-negative'}")
    return parsed


def _whole(value: object, label: str, *, positive: bool = False) -> int:
    parsed = _number(value, label, positive=positive)
    if parsed != parsed.to_integral_value():
        raise ValueError(f"{label} must be a whole number")
    return int(parsed)


def _wire(value: Decimal) -> int | float:
    return int(value) if value == value.to_integral_value() else float(value)


def _time(value: object, label: str) -> datetime:
    text = _text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{label} must be an ISO-8601 time with timezone") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must be an ISO-8601 time with timezone")
    return parsed.astimezone(UTC)


def _date(value: object, label: str) -> str:
    text = _text(value, label)
    try:
        return datetime.fromisoformat(text).date().isoformat()
    except ValueError as error:
        raise ValueError(f"{label} must be an ISO date") from error


def _economic_config(config: Mapping[str, object]) -> Mapping[str, object] | None:
    raw = config.get("economic_proposal")
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise ValueError("economic_proposal must be an object")
    return raw


def validate_economic_config(config: Mapping[str, object]) -> None:
    """Validate the opt-in local evidence packet without changing legacy configs."""

    raw = _economic_config(config)
    if raw is None:
        return
    required = {
        "version",
        "contract",
        "quality",
        "cost",
        "physical_fit",
        "split20_event",
    }
    allowed = required | {
        "model_enabled",
        "case_alias",
        "evaluation_snapshot",
        "destination_mapping",
    }
    if set(raw) - allowed or not required.issubset(raw):
        raise ValueError("economic_proposal has missing or unexpected fields")
    if raw.get("version") != ECONOMIC_PROPOSAL_VERSION:
        raise ValueError("economic_proposal version is unsupported")
    if "model_enabled" in raw and type(raw["model_enabled"]) is not bool:
        raise ValueError("economic_proposal model_enabled must be a boolean")
    if "case_alias" in raw:
        _text(raw.get("case_alias"), "economic case_alias")
    if "evaluation_snapshot" in raw:
        _time(raw.get("evaluation_snapshot"), "economic evaluation_snapshot")
    contract = raw.get("contract")
    if not isinstance(contract, Mapping):
        raise ValueError("economic contract must be an object")
    contract_required = {
        "evidence_id",
        "customer_order",
        "destination_id",
        "total_quantity",
        "partial_minimum_quantity",
        "split_first_dispatch_deadline",
        "split_final_dispatch_deadline",
        "consolidated_dispatch_deadline",
        "arrival_guarantee",
        "late_penalty",
    }
    contract_allowed = contract_required | {"destination_alias"}
    if set(contract) - contract_allowed or not contract_required.issubset(contract):
        raise ValueError("economic contract has missing or unexpected fields")
    for field in ("evidence_id", "customer_order", "destination_id"):
        _text(contract.get(field), f"economic contract {field}")
    if (
        "destination_alias" in contract
        and _text(contract.get("destination_alias"), "economic contract destination_alias")
        != contract["destination_id"]
    ):
        raise ValueError("economic contract destination alias does not match destination_id")
    total = _whole(contract.get("total_quantity"), "economic total_quantity", positive=True)
    partial = _whole(
        contract.get("partial_minimum_quantity"), "economic partial_minimum_quantity", positive=True
    )
    if partial > total:
        raise ValueError("economic partial minimum exceeds the order quantity")
    first = _time(contract.get("split_first_dispatch_deadline"), "economic first deadline")
    final = _time(contract.get("split_final_dispatch_deadline"), "economic final deadline")
    consolidated = _time(
        contract.get("consolidated_dispatch_deadline"), "economic consolidated deadline"
    )
    if final < first or consolidated != first:
        raise ValueError("economic dispatch deadlines do not describe the fixed POC terms")
    if contract.get("arrival_guarantee") is not False or contract.get("late_penalty") is not False:
        raise ValueError("economic POC must not claim an arrival guarantee or late penalty")
    mapping = raw.get("destination_mapping")
    if mapping is not None:
        if not isinstance(mapping, Mapping) or set(mapping) != {"alias", "erp_address_id"}:
            raise ValueError("economic destination_mapping is malformed")
        if _text(mapping.get("alias"), "economic destination alias") != contract["destination_id"]:
            raise ValueError("economic destination mapping alias does not match contract")
        _text(mapping.get("erp_address_id"), "economic destination ERP address")

    quality = raw.get("quality")
    if not isinstance(quality, Mapping) or set(quality) != {"evidence_id", "lots"}:
        raise ValueError("economic quality must contain evidence_id and lots")
    _text(quality.get("evidence_id"), "economic quality evidence_id")
    lots = quality.get("lots")
    if not isinstance(lots, list) or len(lots) != 2:
        raise ValueError("economic quality requires exactly the A20 and B5 lots")
    expected_quality = {"LOT-A20": (20, "QUALIFIED"), "LOT-B5": (5, "NOT_RELEASED")}
    found_quality: set[str] = set()
    for row in lots:
        if not isinstance(row, Mapping) or set(row) != {"lot", "quantity", "status"}:
            raise ValueError("economic quality lot is malformed")
        lot = _text(row.get("lot"), "economic quality lot")
        expected = expected_quality.get(lot)
        if expected is None or lot in found_quality:
            raise ValueError("economic quality must name LOT-A20 and LOT-B5 exactly")
        if _whole(row.get("quantity"), "economic quality quantity", positive=True) != expected[0]:
            raise ValueError("economic quality quantity does not match the fixed POC")
        if row.get("status") != expected[1]:
            raise ValueError("economic quality status does not match the fixed POC")
        found_quality.add(lot)
    if found_quality != set(expected_quality):
        raise ValueError("economic quality lots are incomplete")

    cost = raw.get("cost")
    if not isinstance(cost, Mapping):
        raise ValueError("economic cost must be an object")
    cost_required = {
        "evidence_id",
        "source",
        "trusted_config",
        "service",
        "currency",
        "rate_per_physical_box",
        "checked_on",
        "effective_on",
    }
    cost_allowed = cost_required | {"public_rate_url", "source_url"}
    if set(cost) - cost_allowed or not cost_required.issubset(cost):
        raise ValueError("economic cost has missing or unexpected fields")
    for field in ("evidence_id", "source", "service", "currency"):
        _text(cost.get(field), f"economic cost {field}")
    for field in ("public_rate_url", "source_url"):
        if field in cost:
            url = _text(cost.get(field), f"economic cost {field}")
            if not url.startswith("https://pe.usps.com/"):
                raise ValueError("economic public rate URL must be the configured USPS reference")
    if (
        cost.get("source") != "USPS_NOTICE_123"
        or cost.get("trusted_config") is not True
        or cost.get("service") != "USPS_PRIORITY_MAIL_RETAIL_MEDIUM_FLAT_RATE_BOX"
        or cost.get("currency") != "USD"
        or _number(cost.get("rate_per_physical_box"), "economic rate", positive=True)
        != Decimal("24.80")
        or _date(cost.get("checked_on"), "economic rate checked_on") != "2026-09-13"
        or _date(cost.get("effective_on"), "economic rate effective_on") != "2026-07-12"
    ):
        raise ValueError("economic cost does not match the trusted USPS POC evidence")

    fits = raw.get("physical_fit")
    if not isinstance(fits, list) or len(fits) != 3:
        raise ValueError("economic physical_fit requires 20, 5, and 25-unit records")
    found_fit: set[int] = set()
    for row in fits:
        if not isinstance(row, Mapping) or set(row) != {
            "evidence_id",
            "quantity",
            "boxes",
            "genuine_usps_medium_flat_rate_box",
            "max_weight_lb",
            "nonhazardous",
        }:
            raise ValueError("economic physical fit record is malformed")
        quantity = _whole(row.get("quantity"), "economic fit quantity", positive=True)
        if quantity not in {5, 20, 25} or quantity in found_fit:
            raise ValueError("economic physical fit must cover 20, 5, and 25 exactly")
        if (
            _whole(row.get("boxes"), "economic fit boxes", positive=True) != 1
            or row.get("genuine_usps_medium_flat_rate_box") is not True
            or _number(row.get("max_weight_lb"), "economic max_weight_lb", positive=True)
            > Decimal("70")
            or row.get("nonhazardous") is not True
        ):
            raise ValueError("economic physical fit does not support a genuine eligible box")
        _text(row.get("evidence_id"), "economic physical fit evidence_id")
        found_fit.add(quantity)
    if found_fit != {5, 20, 25}:
        raise ValueError("economic physical fit records are incomplete")
    event = raw.get("split20_event")
    if not isinstance(event, Mapping):
        raise ValueError("economic split20_event must be an object")


def economic_config_digest(config: Mapping[str, object]) -> str | None:
    """Digest every trusted economic input so a prepared approval cannot outlive it."""

    raw = _economic_config(config)
    if raw is None:
        return None
    return sha256(
        json.dumps(_copy(raw), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _fit_by_quantity(config: Mapping[str, object]) -> dict[int, dict[str, object]]:
    raw = cast(Mapping[str, object], config["economic_proposal"])
    return {
        _whole(row["quantity"], "economic fit quantity", positive=True): dict(row)
        for row in cast(list[Mapping[str, object]], raw["physical_fit"])
    }


def _snapshot_evidence_id(snapshot: Mapping[str, object]) -> str:
    material = {
        key: snapshot.get(key)
        for key in (
            "source_status",
            "as_of",
            "source_revision",
            "quantities",
            "lots",
            "allocations",
            "contract_terms",
            "prepared_picks",
            "photo_observations",
        )
    }
    return (
        "operational:"
        + sha256(
            json.dumps(material, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest()[:24]
    )


def raw_economic_evidence(
    config: Mapping[str, object], operational_snapshot: Mapping[str, object]
) -> dict[str, object]:
    """Return source records only; no candidate or feasibility reaches a model."""

    raw = _economic_config(config)
    if raw is None:
        raise ValueError("economic proposal is not configured")
    snapshot = _copy(operational_snapshot)
    if not isinstance(snapshot, Mapping):  # pragma: no cover - JSON boundary only
        raise ValueError("economic operational snapshot is malformed")
    snapshot = dict(snapshot)
    # A caller may be reusing an earlier raw evidence record.  Its prior digest
    # is not source evidence and must never overwrite the fresh snapshot digest.
    snapshot.pop("evidence_id", None)
    contract = _copy(raw["contract"])
    configured_quality = cast(Mapping[str, object], raw["quality"])
    runtime_lots = snapshot.get("lots")
    quality = {
        "evidence_id": configured_quality["evidence_id"],
        "runtime_source_status": snapshot.get("source_status"),
        "lots": _copy(runtime_lots if isinstance(runtime_lots, list) else []),
        "authority": (
            "Runtime lot status and usable quantity are the quality-release authority; "
            "configured POC expectations cannot release stock."
        ),
    }
    cost = _copy(raw["cost"])
    if not isinstance(contract, dict) or not isinstance(cost, dict):  # pragma: no cover
        raise ValueError("economic evidence is malformed")
    # Definitions explain the two fixed POC choices without giving the model a
    # feasibility result, arithmetic total, or recommendation.
    contract["candidate_definitions"] = {
        SPLIT20_CANDIDATE_ID: {
            "first_quantity": 20,
            "first_lot": "LOT-A20",
            "final_quantity": 5,
            "final_lot": "LOT-B5",
            "first_dispatch_deadline": contract["split_first_dispatch_deadline"],
            "final_dispatch_deadline": contract["split_final_dispatch_deadline"],
        },
        CONSOLIDATION25_CANDIDATE_ID: {
            "quantity": 25,
            "dispatch_deadline": contract["consolidated_dispatch_deadline"],
            "condition": "all 25 quality-qualified by the dispatch deadline",
        },
    }
    for field in ("case_alias", "evaluation_snapshot", "destination_mapping"):
        if field in raw:
            contract[field] = _copy(raw[field])
    cost["physical_fit"] = _copy(raw["physical_fit"])
    return {
        "contract": contract,
        "quality": quality,
        "cost": cost,
        "operational_snapshot": {
            "evidence_id": _snapshot_evidence_id(snapshot),
            **snapshot,
        },
    }


def _evidence_ids(evidence: Mapping[str, object]) -> set[str]:
    result: set[str] = set()
    for name in ("contract", "quality", "cost", "operational_snapshot"):
        source = evidence.get(name)
        if isinstance(source, Mapping) and isinstance(source.get("evidence_id"), str):
            result.add(cast(str, source["evidence_id"]))
    cost = evidence.get("cost")
    if isinstance(cost, Mapping) and isinstance(cost.get("physical_fit"), list):
        result.update(
            row["evidence_id"]
            for row in cost["physical_fit"]
            if isinstance(row, Mapping) and isinstance(row.get("evidence_id"), str)
        )
    operational = evidence.get("operational_snapshot")
    if isinstance(operational, Mapping) and isinstance(operational.get("photo_observations"), list):
        result.update(
            row["evidence_id"]
            for row in operational["photo_observations"]
            if isinstance(row, Mapping) and isinstance(row.get("evidence_id"), str)
        )
    return result


def _quality_lot(config: Mapping[str, object], lot_name: str) -> Mapping[str, object]:
    raw = cast(Mapping[str, object], config["economic_proposal"])
    quality = cast(Mapping[str, object], raw["quality"])
    matches = [
        row
        for row in cast(list[Mapping[str, object]], quality["lots"])
        if row.get("lot") == lot_name
    ]
    if len(matches) != 1:  # config validator owns this invariant
        raise ValueError("economic quality lot is unavailable")
    return matches[0]


def _raw_lot(snapshot: Mapping[str, object], lot_name: str) -> Mapping[str, object] | None:
    lots = snapshot.get("lots")
    if not isinstance(lots, list):
        return None
    matches = [row for row in lots if isinstance(row, Mapping) and row.get("lot") == lot_name]
    return matches[0] if len(matches) == 1 else None


def _raw_allocation(snapshot: Mapping[str, object], order: str) -> Mapping[str, object] | None:
    rows = snapshot.get("allocations")
    if not isinstance(rows, list):
        return None
    matches = [
        row for row in rows if isinstance(row, Mapping) and row.get("customer_order") == order
    ]
    return matches[0] if len(matches) == 1 else None


def _contract_terms(snapshot: Mapping[str, object], order: str) -> Mapping[str, object] | None:
    rows = snapshot.get("contract_terms")
    if not isinstance(rows, list):
        return None
    matches = [
        row for row in rows if isinstance(row, Mapping) and row.get("customer_order") == order
    ]
    return matches[0] if len(matches) == 1 else None


def _prepared_quantity(snapshot: Mapping[str, object], order: str, lot: str) -> Decimal:
    rows = snapshot.get("prepared_picks")
    if not isinstance(rows, list):
        return Decimal()
    return sum(
        (
            _number(row.get("remaining"), "prepared pick remaining")
            for row in rows
            if isinstance(row, Mapping)
            and row.get("customer_order") == order
            and row.get("lot") == lot
        ),
        Decimal(),
    )


def _current_source(snapshot: Mapping[str, object]) -> bool:
    return snapshot.get("source_status") == "CURRENT"


def _split_event(raw: Mapping[str, object]) -> dict[str, object]:
    event = raw.get("split20_event")
    return _copy(event) if isinstance(event, Mapping) else {}


def economic_gate(
    config: Mapping[str, object],
    operational_snapshot: Mapping[str, object],
    *,
    now: datetime,
    candidate_id: str,
    event: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Independently recheck the exact event against fresh source and fixed evidence."""

    raw = _economic_config(config)
    if raw is None:
        return {"allowed": False, "candidate_id": candidate_id, "reasons": ["NOT_CONFIGURED"]}
    reasons: list[str] = []
    contract = cast(Mapping[str, object], raw["contract"])
    order = _text(contract["customer_order"], "economic customer order")
    source_event = _split_event(raw)
    proposed = event if event is not None else source_event
    if candidate_id != SPLIT20_CANDIDATE_ID:
        return {
            "allowed": False,
            "candidate_id": candidate_id,
            "reasons": ["CONSOLIDATION_REQUIRES_NATIVE_PREPARED_25"],
        }
    if not _current_source(operational_snapshot):
        reasons.append("CURRENT_OPERATIONAL_SNAPSHOT_REQUIRED")
    if now.astimezone(UTC) > _time(contract["split_first_dispatch_deadline"], "first deadline"):
        reasons.append("FIRST_DISPATCH_DEADLINE_EXPIRED")
    lot = _raw_lot(operational_snapshot, "LOT-A20")
    allocation = _raw_allocation(operational_snapshot, order)
    if (
        lot is None
        or lot.get("status") not in {"USABLE", "QUALIFIED", "RELEASED"}
        or _number(lot.get("usable", 0), "raw A20 usable") < Decimal("20")
    ):
        reasons.append("RAW_A20_USABLE_STOCK_INSUFFICIENT")
    if (
        allocation is None
        or _number(allocation.get("requested_quantity", 0), "raw SO25 requested quantity")
        != Decimal("25")
        or _number(allocation.get("allocated", 0), "raw SO25 allocation") < Decimal("20")
    ):
        reasons.append("RAW_SO25_ALLOCATION_INSUFFICIENT")
    terms = _contract_terms(operational_snapshot, order)
    if (
        terms is None
        or terms.get("partial_dispatch") is not True
        or _number(terms.get("minimum_dispatch_quantity", 0), "raw dispatch minimum")
        > Decimal("20")
    ):
        reasons.append("RAW_SO25_PARTIAL_DISPATCH_TERMS_INSUFFICIENT")
    expected = {
        "type": "picked",
        "customer_order": order,
        "lot": "LOT-A20",
        "quantity": 20,
    }
    for key, value in expected.items():
        if proposed.get(key) != value:
            reasons.append("SPLIT20_EVENT_IS_NOT_THE_CONFIGURED_EXACT_PICK")
            break
    fits = _fit_by_quantity(config)
    fit = fits.get(20)
    if (
        fit is None
        or fit.get("genuine_usps_medium_flat_rate_box") is not True
        or fit.get("nonhazardous") is not True
        or _number(fit.get("max_weight_lb"), "fit weight") > Decimal("70")
    ):
        reasons.append("A20_PHYSICAL_FIT_EVIDENCE_UNAVAILABLE")
    return {
        "allowed": not reasons,
        "candidate_id": candidate_id,
        "event": _copy(proposed),
        "reasons": reasons,
        "checked_at": now.astimezone(UTC).isoformat(),
        "source_evidence_id": _snapshot_evidence_id(operational_snapshot),
    }


def economic_projection(
    config: Mapping[str, object],
    operational_snapshot: Mapping[str, object],
    *,
    now: datetime,
    last_result: Mapping[str, object] | None = None,
) -> dict[str, object] | None:
    """Project trusted evidence and two postage estimates without claiming fulfillment value."""

    raw = _economic_config(config)
    if raw is None:
        return None
    contract = cast(Mapping[str, object], raw["contract"])
    cost = cast(Mapping[str, object], raw["cost"])
    rate = _number(cost["rate_per_physical_box"], "economic rate", positive=True)
    gate = economic_gate(config, operational_snapshot, now=now, candidate_id=SPLIT20_CANDIDATE_ID)
    fits = _fit_by_quantity(config)
    evidence = raw_economic_evidence(config, operational_snapshot)
    model = (
        _copy(last_result.get("model"))
        if isinstance(last_result, Mapping) and isinstance(last_result.get("model"), Mapping)
        else {
            "status": "not_run",
            "candidate_id": None,
            "citations": [],
            "tool_trace": [],
            "model_response": None,
        }
    )
    if isinstance(model, dict):
        model["trace"] = _copy(model.get("tool_trace", []))
        model["decision"] = (
            model.get("rationale")
            or model.get("reason")
            or (
                "No economic model decision has run."
                if model.get("status") == "not_run"
                else "The model deferred pending supported evidence."
            )
        )
    checked_at = raw.get("evaluation_snapshot") or operational_snapshot.get("as_of")
    deterministic_gate = {
        **gate,
        "status": "READY" if gate["allowed"] is True else "NEEDS_EVIDENCE",
        "stock_snapshot": {
            "lots": _copy(operational_snapshot.get("lots", [])),
            "allocations": _copy(operational_snapshot.get("allocations", [])),
        },
        "contract_snapshot": _copy(contract),
        "time_snapshot": {"checked_at": gate["checked_at"], "source_as_of": checked_at},
    }
    source_evidence = [
        {
            "label": "Customer order and dispatch terms",
            "kind": "CONTRACT",
            "checked_at": checked_at,
            "ref": contract["evidence_id"],
        },
        {
            "label": "Runtime lot quality and stock",
            "kind": "OPERATIONAL_QUALITY",
            "checked_at": operational_snapshot.get("as_of"),
            "ref": cast(Mapping[str, object], raw["quality"])["evidence_id"],
        },
        {
            "label": "USPS flat-rate cost evidence",
            "kind": "COST",
            "checked_at": cost["checked_on"],
            "source_id": cost["evidence_id"],
            "ref": cost.get("public_rate_url", cost["evidence_id"]),
            **({"url": cost["public_rate_url"]} if "public_rate_url" in cost else {}),
        },
        {
            "label": "Physical package fit evidence",
            "kind": "PHYSICAL_FIT",
            "checked_at": checked_at,
            "ref": fits[20]["evidence_id"],
        },
    ]
    photo_observations = operational_snapshot.get("photo_observations")
    if isinstance(photo_observations, list):
        for observation in photo_observations:
            if not isinstance(observation, Mapping):
                continue
            evidence_id = observation.get("evidence_id")
            attachment_digest = observation.get("attachment_sha256")
            observed_at = observation.get("observed_at")
            if not (
                isinstance(evidence_id, str)
                and isinstance(attachment_digest, str)
                and isinstance(observed_at, str)
            ):
                continue
            source_evidence.append(
                {
                    "label": "Operator-linked photo observation (advisory only)",
                    "kind": "PHOTO_OBSERVATION",
                    "checked_at": observed_at,
                    "ref": evidence_id,
                    "attachment_sha256": attachment_digest,
                    "source_revision": observation.get("source_revision"),
                    "linked_lot": observation.get("linked_lot"),
                    "linkage_source": observation.get("linkage_source"),
                    "linked_quantity": observation.get("linked_quantity"),
                    "recommendation_code": observation.get("recommendation_code"),
                    "advisory_only": True,
                }
            )
    proposal_effect: dict[str, object] | None = None
    if isinstance(last_result, Mapping) and isinstance(
        last_result.get("requested_candidate_id"), str
    ):
        proposal_effect = {
            "candidate_id": last_result["requested_candidate_id"],
            "status": (
                "PREPARED_FOR_MANAGER_APPROVAL"
                if isinstance(last_result.get("prepared_proposal_id"), str)
                else "NOT_PREPARED"
            ),
        }
        if isinstance(last_result.get("prepared_proposal_id"), str):
            proposal_effect["proposal_id"] = last_result["prepared_proposal_id"]
            proposal_effect["quantity"] = 20
    return {
        "status": "CURRENT" if _current_source(operational_snapshot) else "NEEDS_EVIDENCE",
        "evidence": evidence,
        "source_evidence": source_evidence,
        "candidates": [
            {
                "candidate_id": SPLIT20_CANDIDATE_ID,
                "customer_order": contract["customer_order"],
                "dispatches": [
                    {
                        "quantity": 20,
                        "lot": "LOT-A20",
                        "deadline": contract["split_first_dispatch_deadline"],
                        "boxes": fits[20]["boxes"],
                    },
                    {
                        "quantity": 5,
                        "lot": "LOT-B5",
                        "deadline": contract["split_final_dispatch_deadline"],
                        "boxes": fits[5]["boxes"],
                    },
                ],
                "estimated_postage_only": _wire(rate * Decimal("2")),
                "estimated_postage": {
                    "amount": _wire(rate * Decimal("2")),
                    "currency": cost["currency"],
                    "label": "Postage-only estimate; not paid or booked",
                    "source_id": cost["evidence_id"],
                    "source_ref": cost.get("public_rate_url", cost["evidence_id"]),
                },
                "currency": cost["currency"],
                "estimate_status": "NOT_PAID_NOT_BOOKED",
                "execution_status": "PREPARABLE" if gate["allowed"] else "NEEDS_EVIDENCE",
                "executable": gate["allowed"] is True,
                "shipment_quantities": [20, 5],
                "dispatch_deadline": contract["split_first_dispatch_deadline"],
                "conditions": [
                    (
                        "The first 20 require current runtime LOT-A20 usable stock and SO25 "
                        "allocation."
                    ),
                    "The final 5 remain subject to future quality release and its own deadline.",
                ],
                "gate": deterministic_gate,
                **(
                    {"proposal_effect": _copy(proposal_effect)}
                    if proposal_effect is not None
                    and proposal_effect["candidate_id"] == SPLIT20_CANDIDATE_ID
                    else {}
                ),
            },
            {
                "candidate_id": CONSOLIDATION25_CANDIDATE_ID,
                "customer_order": contract["customer_order"],
                "dispatches": [
                    {
                        "quantity": 25,
                        "deadline": contract["consolidated_dispatch_deadline"],
                        "boxes": fits[25]["boxes"],
                    }
                ],
                "estimated_postage_only": _wire(rate),
                "estimated_postage": {
                    "amount": _wire(rate),
                    "currency": cost["currency"],
                    "label": "Postage-only estimate; not paid or booked",
                    "source_id": cost["evidence_id"],
                    "source_ref": cost.get("public_rate_url", cost["evidence_id"]),
                },
                "currency": cost["currency"],
                "estimate_status": "NOT_PAID_NOT_BOOKED",
                "execution_status": "NEEDS_EVIDENCE",
                "executable": False,
                "shipment_quantities": [25],
                "dispatch_deadline": contract["consolidated_dispatch_deadline"],
                "conditions": [
                    "All 25 must be quality-qualified by the consolidated dispatch deadline.",
                    "Native prepared25 evidence is required before any executable action.",
                ],
                "condition": (
                    "All 25 must be quality-qualified by the consolidated dispatch deadline."
                ),
                "native_preparation": (
                    "No economic proposal can prepare this candidate; native prepared25 evidence "
                    "is required."
                ),
                "arrival_guarantee": False,
                "late_penalty": False,
                **(
                    {"proposal_effect": _copy(proposal_effect)}
                    if proposal_effect is not None
                    and proposal_effect["candidate_id"] == CONSOLIDATION25_CANDIDATE_ID
                    else {}
                ),
            },
        ],
        "postage_only_estimated_difference": _wire(rate),
        "estimated_postage_difference": {
            "amount": _wire(rate),
            "currency": cost["currency"],
            "label": "Postage-only estimate difference; not confirmed or realized",
        },
        "difference_status": "NOT_CONFIRMED_NOT_REALIZED",
        "deterministic_gate": deterministic_gate,
        "selected_candidate_id": (
            last_result.get("requested_candidate_id") if isinstance(last_result, Mapping) else None
        ),
        **({"proposal_effect": proposal_effect} if proposal_effect is not None else {}),
        "last_result": _copy(last_result) if isinstance(last_result, Mapping) else None,
        "model": model,
    }


def _model_failure(
    reason: str, *, provider: Mapping[str, object] | None = None
) -> dict[str, object]:
    result: dict[str, object] = {
        "status": "DEFER",
        "candidate_id": DEFER_CANDIDATE_ID,
        "reason": reason,
        "tool_trace": [],
        "model_response": None,
        "citations": [],
    }
    if provider:
        result["provider"] = _copy(provider)
    return result


def _validated_model_selection(
    raw: object, *, evidence: Mapping[str, object], calls: list[str]
) -> tuple[dict[str, object] | None, str | None]:
    try:
        selected = EconomicSelection.model_validate(raw)
    except Exception:
        return None, "MODEL_DECISION_MALFORMED"
    valid_ids = _evidence_ids(evidence)
    if not set(selected.citations).issubset(valid_ids):
        return None, "MODEL_CITATIONS_UNSUPPORTED"
    if selected.candidate_id == DEFER_CANDIDATE_ID:
        if set(calls) != set(_TOOL_NAMES):
            return None, "MODEL_SOURCE_READS_INCOMPLETE"
        return {
            "candidate_id": DEFER_CANDIDATE_ID,
            "rationale": selected.rationale.strip(),
            "citations": list(selected.citations),
        }, None
    required = {
        cast(str, cast(Mapping[str, object], evidence["contract"])["evidence_id"]),
        cast(str, cast(Mapping[str, object], evidence["quality"])["evidence_id"]),
        cast(str, cast(Mapping[str, object], evidence["cost"])["evidence_id"]),
        cast(str, cast(Mapping[str, object], evidence["operational_snapshot"])["evidence_id"]),
    }
    if not required.issubset(selected.citations):
        return None, "MODEL_CITATIONS_INCOMPLETE"
    if set(calls) != set(_TOOL_NAMES):
        return None, "MODEL_SOURCE_READS_INCOMPLETE"
    return {
        "candidate_id": selected.candidate_id,
        "rationale": selected.rationale.strip(),
        "citations": list(selected.citations),
    }, None


def _classify_model_failure(failure: str | None, *, stop_reason: object) -> str | None:
    """Keep a bounded Strands stop distinct from malformed model output."""

    if (
        failure == "MODEL_DECISION_MALFORMED"
        and isinstance(stop_reason, str)
        and stop_reason.startswith("limit_")
    ):
        return "MODEL_BUDGET_EXHAUSTED"
    return failure


def select_economic_candidate(
    *, evidence: Mapping[str, object], factory: AgentModelFactory
) -> dict[str, object]:
    """Run one bounded Strands turn over raw trusted records only.

    The application sends no candidate, arithmetic result, gate outcome, or
    recommendation to the model.  Any incomplete tool coverage or unsupported
    citation is an explicit DEFER rather than a deterministic answer in model
    clothing.
    """

    if set(evidence) != {"contract", "quality", "cost", "operational_snapshot"}:
        return _model_failure("MODEL_EVIDENCE_MALFORMED")

    async def invoke() -> tuple[object, list[dict[str, object]], list[str], dict[str, object]]:
        try:
            from strands import Agent, tool
            from strands.types.agent import Limits
        except ImportError as error:  # pragma: no cover - bootstrap boundary
            raise RuntimeError("strands-agents is unavailable") from error

        calls: list[str] = []
        trace: list[dict[str, object]] = []

        def reader(name: str) -> Any:
            @tool(name=name, description="Read this parameterized raw economic evidence record.")
            def read(source_id: str) -> str:
                if not isinstance(source_id, str) or len(source_id) > 256:
                    raise ValueError(
                        "economic evidence source_id must be a string up to 256 characters"
                    )
                source_name = name.removeprefix("read_").removesuffix("_evidence")
                source_name = (
                    "operational_snapshot" if name == "read_operational_snapshot" else source_name
                )
                source = evidence[source_name]
                expected_id = source.get("evidence_id") if isinstance(source, Mapping) else None
                if source_id != expected_id:
                    payload = {"status": "NOT_FOUND", "requested_source_id": source_id}
                    trace.append({"tool": name, "source_id": source_id, "result": _copy(payload)})
                    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
                payload = {"status": "CURRENT", "source_id": source_id, "record": source}
                calls.append(name)
                trace.append({"tool": name, "source_id": source_id, "result": _copy(payload)})
                return json.dumps(payload, sort_keys=True, separators=(",", ":"))

            return read

        model = factory.create(stage=AgentStage.SYNTHESIS, output_payload={})
        agent = Agent(
            model=model,
            tools=[reader(name) for name in _TOOL_NAMES],
            system_prompt=(
                "You are a read-only distributor economics reviewer. Read all four raw evidence "
                "tools before selecting exactly one candidate ID or DEFER. You may select only "
                "split20, consolidation25, or DEFER. Do not invent stock, quality release, costs, "
                "deadlines, customer terms, physical fit, bookings, savings, arrival guarantees, "
                "or late penalties. If the raw evidence does not support a unique defensible "
                "choice, return DEFER. Distinguish what is currently executable from what remains "
                "future-conditional; never call an unknown future cost unavoidable or realized. "
                "Photo observations, when present in the operational snapshot, are advisory only; "
                "they cannot replace ERP lot status or usable quantity. Cite a photo evidence_id "
                "only when it informs your rationale. "
                "Cite exact evidence_id values from every raw source. "
                "You cannot "
                "write, prepare, approve, book, pay, or execute anything."
            ),
            callback_handler=None,
            retry_strategy=None,
            checkpointing=False,
            agent_id="distributor-economic-selection-v1",
            name="distributor-economic-selection",
        )
        response = await agent.invoke_async(
            "Read every raw evidence tool using its exact source ID, then return "
            "EconomicSelection. "
            "The source IDs are contract="
            + str(cast(Mapping[str, object], evidence["contract"])["evidence_id"])
            + ", quality="
            + str(cast(Mapping[str, object], evidence["quality"])["evidence_id"])
            + ", cost="
            + str(cast(Mapping[str, object], evidence["cost"])["evidence_id"])
            + ", operational_snapshot="
            + str(cast(Mapping[str, object], evidence["operational_snapshot"])["evidence_id"])
            + ". Copy one allowed candidate_id or DEFER. Do not add a new candidate or "
            "recommend an execution.",
            structured_output_model=EconomicSelection,
            structured_output_prompt=(
                "Return only EconomicSelection. candidate_id is split20, consolidation25, "
                "or DEFER. "
                "Citations must be exact evidence_id values from all four raw sources."
            ),
            limits=Limits(turns=6, output_tokens=2048, total_tokens=16384),
        )
        structured = getattr(response, "structured_output", None)
        stop_reason = getattr(response, "stop_reason", None)
        response_record = {
            "type": type(response).__name__,
            "stop_reason": str(stop_reason) if stop_reason is not None else None,
            "structured_output": (
                structured.model_dump(mode="json")
                if isinstance(structured, BaseModel)
                else _copy(structured)
                if structured is not None
                else None
            ),
        }
        return structured, trace, calls, actual_provider_metadata(model) | response_record

    started = monotonic()
    try:
        raw_result, trace, calls, metadata = asyncio.run(invoke())
    except Exception as error:
        return _model_failure(f"MODEL_UNAVAILABLE:{type(error).__name__}")
    provider = {
        key: value
        for key, value in metadata.items()
        if key not in {"type", "structured_output", "stop_reason"}
    }
    if not provider:
        provenance = getattr(factory, "provenance", None)
        observed = provenance() if callable(provenance) else {}
        provider = dict(observed) if isinstance(observed, Mapping) else {}
    validated, failure = _validated_model_selection(raw_result, evidence=evidence, calls=calls)
    failure = _classify_model_failure(failure, stop_reason=metadata.get("stop_reason"))
    usage: dict[str, object] = {"elapsed_ms": round((monotonic() - started) * 1000)}
    ledger = getattr(factory, "ledger", None)
    if isinstance(ledger, AgentBudgetLedger):
        usage.update(ledger.snapshot())
    response = {
        "type": metadata.get("type"),
        "stop_reason": metadata.get("stop_reason"),
        "structured_output": metadata.get("structured_output"),
    }
    if validated is None:
        result = _model_failure(failure or "MODEL_DECISION_UNSUPPORTED", provider=provider)
        result.update({"tool_trace": trace, "model_response": response, "usage": usage})
        return result
    if validated.get("candidate_id") == DEFER_CANDIDATE_ID:
        return {
            "status": "DEFER",
            **validated,
            "tool_trace": trace,
            "model_response": response,
            "provider": provider,
            "usage": usage,
        }
    return {
        "status": "SELECTED",
        **validated,
        "tool_trace": trace,
        "model_response": response,
        "provider": provider,
        "usage": usage,
    }


def validate_selected_candidate(
    selection: Mapping[str, object], *, evidence: Mapping[str, object]
) -> dict[str, object]:
    """Fail closed for selectors injected by the adapter/server boundary."""

    copied = _copy(selection)
    if not isinstance(copied, dict):  # pragma: no cover - JSON boundary only
        return _model_failure("MODEL_DECISION_MALFORMED")
    status = copied.get("status")
    candidate = copied.get("candidate_id")
    citations = copied.get("citations")
    if status == "DEFER" or candidate == DEFER_CANDIDATE_ID:
        if not isinstance(citations, list) or any(
            not isinstance(value, str) for value in citations
        ):
            copied["citations"] = []
        elif not set(citations).issubset(_evidence_ids(evidence)):
            copied["citations"] = []
            copied["reason"] = "MODEL_CITATIONS_UNSUPPORTED"
        copied["status"] = "DEFER"
        copied["candidate_id"] = DEFER_CANDIDATE_ID
        return copied
    if status != "SELECTED" or not isinstance(candidate, str) or candidate not in _CANDIDATE_IDS:
        return _model_failure("MODEL_DECISION_UNSUPPORTED")
    if not isinstance(citations, list) or any(not isinstance(value, str) for value in citations):
        return _model_failure("MODEL_CITATIONS_MALFORMED")
    allowed = _evidence_ids(evidence)
    required = {
        cast(str, cast(Mapping[str, object], evidence["contract"])["evidence_id"]),
        cast(str, cast(Mapping[str, object], evidence["quality"])["evidence_id"]),
        cast(str, cast(Mapping[str, object], evidence["cost"])["evidence_id"]),
        cast(str, cast(Mapping[str, object], evidence["operational_snapshot"])["evidence_id"]),
    }
    if (
        len(citations) != len(set(citations))
        or not set(citations).issubset(allowed)
        or not required.issubset(citations)
    ):
        return _model_failure("MODEL_CITATIONS_UNSUPPORTED")
    return copied
