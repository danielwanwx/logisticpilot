"""Read-only paired receiving-evidence experiment.

This module is deliberately isolated from the product.  It provides three
candidate shapes over the same synthetic snapshot: a deterministic rules/form
baseline, one Strands investigator, and a fixed native Strands Graph with two
specialists plus a guarded coordinator.  It never creates ERP data, exposes a
write tool, or promotes a candidate.

Run it only from the prepared isolated environment::

    /private/tmp/m20-evals-venv/bin/python receiving_evidence.py --help

The CLI requires caller-owned case/key paths, a durable experiment ledger, a
private JSONL run log, and a previously generated candidate freeze manifest.
The only live path is an explicit ``--execute-model`` using the pinned Nova
factory below; tests pass local models directly to the non-CLI functions.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import fcntl
import hashlib
import importlib.metadata
import json
import os
import random
import sys
import time
import uuid
from collections.abc import AsyncGenerator, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from threading import Lock
from typing import Any, Literal, Protocol, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    ValidationError,
    model_validator,
)
from strands import Agent, tool
from strands.agent import AgentResult
from strands.models import Model
from strands.multiagent import GraphBuilder
from strands.types.agent import Limits
from strands_evals import Case, Experiment
from strands_evals.evaluators import Evaluator
from strands_evals.types import EvaluationData, EvaluationOutput

SCHEMA_VERSION = "receiving-evidence-v1"
FREEZE_SCHEMA_VERSION = "receiving-evidence-freeze-v1"
MODEL_ID = "us.amazon.nova-pro-v1:0"
MODEL_REGION = "us-west-2"
AWS_PROFILE = "missing20-sandbox"
MODEL_TEMPERATURE = 0.0
SOURCE_MODE = "synthetic_snapshot"
MAX_REQUEST_OUTPUT_TOKENS = 1_024
WORKFLOW_COST_CAP_USD = Decimal("0.06")
EXPERIMENT_COST_CAP_USD = Decimal("3.00")
WORKFLOW_TIMEOUT_SECONDS = 180.0
SOURCE_RECEIVING = "receiving_quality"
SOURCE_FULFILLMENT = "fulfillment_contract"
SOURCE_NAMES = (SOURCE_RECEIVING, SOURCE_FULFILLMENT)
ACTOR_RECEIVING = "receiving_specialist"
ACTOR_FULFILLMENT = "fulfillment_specialist"
ACTOR_COORDINATOR = "coordinator"
ACTOR_SINGLE = "single_investigator"
ActorName = Literal[
    "receiving_specialist",
    "fulfillment_specialist",
    "coordinator",
    "single_investigator",
    "rules_baseline",
]
SourceName = Literal["receiving_quality", "fulfillment_contract"]
CandidateName = Literal["rules", "single", "graph"]


class ExperimentError(RuntimeError):
    """A candidate or protocol failure that is retained as experiment evidence."""


class InputContractError(ExperimentError):
    """Caller-supplied case, key, or freeze input is invalid."""


class BudgetError(ExperimentError):
    """A workflow would exceed a predeclared resource boundary."""


class UnderestimatedUsageError(BudgetError):
    """A provider reported usage above its reservation."""


class JoinError(ExperimentError):
    """The graph coordinator cannot safely receive both typed specialist inputs."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _copy_json(value: Any) -> Any:
    return json.loads(_canonical_json(value))


def _sha256(value: Any) -> str:
    if isinstance(value, bytes):
        payload = value
    elif isinstance(value, str):
        payload = value.encode("utf-8")
    else:
        payload = _canonical_json(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


class StrictModel(BaseModel):
    """Base model that rejects accidental schema drift in all persisted artifacts."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class Quantity(StrictModel):
    """A typed quantity. Unknown is explicit rather than represented by omitted prose."""

    name: str = Field(
        min_length=1,
        max_length=128,
        description=(
            "Key: direct <record_id>:<field_name>; eligible "
            "<order_id>:eligible_quantity; derived case-named field."
        ),
    )
    value: Decimal | None = None
    unit: str = Field(min_length=1, max_length=32)
    state: Literal["known", "unknown"]

    @model_validator(mode="after")
    def _validate_state(self) -> Quantity:
        if self.state == "known" and self.value is None:
            raise ValueError("known quantity requires a value")
        if self.state == "unknown" and self.value is not None:
            raise ValueError("unknown quantity cannot carry a value")
        return self


class Authority(StrictModel):
    """Candidates have no approval or execution authority in this experiment."""

    approval: Literal[False] = False
    executed: Literal[False] = False


class SourceRecord(StrictModel):
    record_id: str = Field(min_length=1, max_length=160)
    # Effective freshness belongs to the record.  It may be stale or unknown even
    # though the surrounding snapshot was captured at one fixed time.
    as_of: str | None = Field(default=None, max_length=80)
    fields: dict[str, JsonValue]


class SourcePacket(StrictModel):
    source: SourceName
    status: Literal["available", "unavailable"] = "available"
    # Source freshness is information, not a normalized case-wide invariant.
    as_of: str | None = Field(default=None, max_length=80)
    records: list[SourceRecord] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_records(self) -> SourcePacket:
        record_ids = [record.record_id for record in self.records]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("record IDs must be unique within a source packet")
        if self.status == "unavailable" and self.records:
            raise ValueError("an unavailable source must not invent records")
        return self


class CaseInput(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    tier: Literal["development", "heldout"]
    case_id: str = Field(min_length=1, max_length=160)
    snapshot_id: str = Field(min_length=1, max_length=160)
    source_mode: Literal[SOURCE_MODE] = SOURCE_MODE
    # Snapshot envelope time is distinct from source/record freshness timestamps.
    snapshot_as_of: str = Field(min_length=1, max_length=80)
    question: str = Field(min_length=1, max_length=8_000)
    requested_quantity_names: list[str] = Field(
        min_length=1,
        max_length=64,
        description=(
            "Question output scope only: stable requested Quantity.name values, "
            "never expected values or verdicts."
        ),
    )
    requested_order_ids: list[str] = Field(
        min_length=1,
        max_length=32,
        description=(
            "Question output scope only: requested order IDs, never expected "
            "dispositions or quantities."
        ),
    )
    source_packets: list[SourcePacket] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def _validate_packets(self) -> CaseInput:
        sources = [packet.source for packet in self.source_packets]
        if set(sources) != set(SOURCE_NAMES) or len(sources) != len(set(sources)):
            raise ValueError("case must contain exactly one packet for each declared source")
        all_ids = [record.record_id for packet in self.source_packets for record in packet.records]
        if len(all_ids) != len(set(all_ids)):
            raise ValueError("record IDs must be unique across the complete case")
        if len(self.requested_quantity_names) != len(set(self.requested_quantity_names)):
            raise ValueError("requested quantity names must be unique")
        if len(self.requested_order_ids) != len(set(self.requested_order_ids)):
            raise ValueError("requested order IDs must be unique")
        return self

    def packet(self, source: SourceName) -> SourcePacket:
        for packet in self.source_packets:
            if packet.source == source:
                return packet
        raise InputContractError(f"case lacks source packet {source}")

    @property
    def as_of(self) -> str:
        """Snapshot envelope as_of used by typed answers and identity checks."""

        return self.snapshot_as_of


class FieldLiteral(StrictModel):
    """A literal from a named record field.  It is never a free-form assertion."""

    record_id: str = Field(min_length=1, max_length=160)
    field_path: str = Field(pattern=r"^/(?:[^/~]|~[01])+(?:/(?:[^/~]|~[01])+)*$")
    literal_value: JsonValue


class Citation(FieldLiteral):
    actor: ActorName


class SpecialistObservation(StrictModel):
    case_id: str
    snapshot_id: str
    actor: Literal["receiving_specialist", "fulfillment_specialist"]
    source_mode: Literal[SOURCE_MODE] = SOURCE_MODE
    as_of: str
    # Empty is valid when a declared source is unavailable or returns no match.
    literals: list[FieldLiteral] = Field(default_factory=list, max_length=64)
    interpretations: list[str] = Field(default_factory=list, max_length=16)
    source_read_status: Literal["evidence_returned", "no_matching_records", "source_unavailable"]
    missing_evidence: list[str] = Field(default_factory=list, max_length=16)


class OrderDisposition(StrictModel):
    order_id: str = Field(min_length=1, max_length=160)
    disposition: Literal["eligible", "ineligible", "pending_evidence", "unknown"]
    eligible_quantity: Quantity
    missing_prerequisites: list[str] = Field(default_factory=list, max_length=16)

    @model_validator(mode="after")
    def _state_matches_eligible_quantity(self) -> OrderDisposition:
        if self.disposition == "eligible" and self.eligible_quantity.state != "known":
            raise ValueError("eligible order requires a known eligible quantity")
        if self.disposition in {"pending_evidence", "unknown"} and not self.missing_prerequisites:
            raise ValueError("unresolved order must name a missing prerequisite")
        return self


class DecisionAnswer(StrictModel):
    case_id: str
    snapshot_id: str
    source_mode: Literal[SOURCE_MODE] = SOURCE_MODE
    as_of: str
    quantities: list[Quantity] = Field(
        default_factory=list,
        max_length=64,
        description="Only question-requested quantities.",
    )
    order_dispositions: list[OrderDisposition] = Field(
        default_factory=list,
        max_length=32,
        description="Only question-requested orders.",
    )
    citations: list[Citation] = Field(default_factory=list, max_length=128)
    missing_evidence: list[str] = Field(
        default_factory=list,
        max_length=32,
        description="Nonempty when an order is unresolved.",
    )
    answer_text: str = Field(min_length=1, max_length=4_000)
    authority: Authority = Field(default_factory=Authority)

    @model_validator(mode="after")
    def _unique_output_identifiers(self) -> DecisionAnswer:
        quantity_names = [quantity.name for quantity in self.quantities]
        order_ids = [order.order_id for order in self.order_dispositions]
        if len(quantity_names) != len(set(quantity_names)):
            raise ValueError("quantity names must be unique")
        if len(order_ids) != len(set(order_ids)):
            raise ValueError("order IDs must be unique")
        if (
            any(
                order.disposition in {"pending_evidence", "unknown"}
                for order in self.order_dispositions
            )
            and not self.missing_evidence
        ):
            raise ValueError("unresolved order requires a missing-evidence reason")
        return self


class CitationRequirement(FieldLiteral):
    """Expected literal membership has no candidate-specific actor label."""


class ExpectedDecision(StrictModel):
    """The deterministic subset used for mechanical scoring, held outside prompts."""

    quantities: list[Quantity] = Field(default_factory=list, max_length=64)
    order_dispositions: list[OrderDisposition] = Field(default_factory=list, max_length=32)
    required_citations: list[CitationRequirement] = Field(default_factory=list, max_length=128)
    required_sources: list[SourceName] = Field(default_factory=list, max_length=2)


class KeyFile(StrictModel):
    schema_version: Literal[SCHEMA_VERSION] = SCHEMA_VERSION
    case_id: str
    snapshot_id: str
    expected: ExpectedDecision


class ToolCall(StrictModel):
    actor: ActorName
    tool: str
    source: SourceName
    query: str
    requested_record_ids: list[str]
    returned_record_ids: list[str]
    returned_records_sha256: str


class JoinPacket(StrictModel):
    """Coordinator input constructed only after both typed specialist results validate."""

    case_id: str
    snapshot_id: str
    source_mode: Literal[SOURCE_MODE]
    as_of: str
    receiving: SpecialistObservation
    fulfillment: SpecialistObservation


class StageCaps(StrictModel):
    max_requests: int = Field(gt=0)
    max_input_tokens: int = Field(gt=0)
    max_output_tokens: int = Field(gt=0)
    limits_total_tokens: int = Field(gt=0)
    limits_turns: int = Field(gt=0)


SINGLE_STAGE = "single"
RECEIVING_STAGE = "receiving"
FULFILLMENT_STAGE = "fulfillment"
COORDINATOR_STAGE = "coordinator"

STAGE_CAPS: dict[str, StageCaps] = {
    SINGLE_STAGE: StageCaps(
        max_requests=8,
        max_input_tokens=32_000,
        max_output_tokens=6_000,
        limits_total_tokens=38_000,
        limits_turns=8,
    ),
    RECEIVING_STAGE: StageCaps(
        max_requests=3,
        max_input_tokens=12_000,
        max_output_tokens=2_000,
        limits_total_tokens=14_000,
        limits_turns=3,
    ),
    FULFILLMENT_STAGE: StageCaps(
        max_requests=3,
        max_input_tokens=12_000,
        max_output_tokens=2_000,
        limits_total_tokens=14_000,
        limits_turns=3,
    ),
    COORDINATOR_STAGE: StageCaps(
        max_requests=2,
        max_input_tokens=8_000,
        max_output_tokens=2_000,
        limits_total_tokens=10_000,
        limits_turns=2,
    ),
}


@dataclass(frozen=True, slots=True)
class WorkflowCaps:
    max_requests: int = 8
    max_input_tokens: int = 32_000
    max_output_tokens: int = 6_000
    max_output_per_request: int = MAX_REQUEST_OUTPUT_TOKENS
    cost_cap_usd: Decimal = WORKFLOW_COST_CAP_USD
    timeout_seconds: float = WORKFLOW_TIMEOUT_SECONDS
    input_price_per_token: Decimal = Decimal("0.0000008")
    output_price_per_token: Decimal = Decimal("0.0000032")


WORKFLOW_CAPS = WorkflowCaps()


@dataclass(frozen=True, slots=True)
class RequestReservation:
    reservation_id: int
    stage: str
    input_upper_bound: int
    output_upper_bound: int
    estimated_cost_usd: Decimal


@dataclass(slots=True)
class _StageUsage:
    requests: int = 0
    actual_input: int = 0
    actual_output: int = 0
    reserved_input: int = 0
    reserved_output: int = 0


@dataclass(slots=True)
class _AttemptTrace:
    """References to adapter attempt lists, retained even when a runner raises."""

    model_attempts: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    graph_events: list[dict[str, Any]] = field(default_factory=list)


class StrictWorkflowLedger:
    """Atomic workflow budget with durable-friendly, conservative failure accounting.

    Every adapter request reserves full serialized request bytes and a provider output
    cap before it delegates.  Missing provider usage consumes that reservation rather
    than releasing it.  This matters because unknown usage is not evidence of zero
    spend.
    """

    def __init__(self, *, candidate: CandidateName, caps: WorkflowCaps = WORKFLOW_CAPS) -> None:
        self.candidate = candidate
        self.caps = caps
        self._lock = Lock()
        self._next_id = 1
        self._reservations: dict[int, RequestReservation] = {}
        self._stages = {stage: _StageUsage() for stage in self._candidate_stages(candidate)}
        self._actual_input = 0
        self._actual_output = 0
        self._actual_cache = 0
        self._reserved_input = 0
        self._reserved_output = 0
        self._underestimated = False
        self._errors: list[str] = []

    @staticmethod
    def _candidate_stages(candidate: CandidateName) -> tuple[str, ...]:
        if candidate == "single":
            return (SINGLE_STAGE,)
        if candidate == "graph":
            return (RECEIVING_STAGE, FULFILLMENT_STAGE, COORDINATOR_STAGE)
        return ()

    def _cost(self, input_tokens: int, output_tokens: int) -> Decimal:
        return (
            Decimal(input_tokens) * self.caps.input_price_per_token
            + Decimal(output_tokens) * self.caps.output_price_per_token
        )

    def _reserved_cost(self) -> Decimal:
        return self._cost(self._reserved_input, self._reserved_output)

    def _actual_cost(self) -> Decimal:
        return self._cost(self._actual_input, self._actual_output)

    def remaining_stage_output(self, stage: str) -> int:
        with self._lock:
            usage = self._stage(stage)
            return STAGE_CAPS[stage].max_output_tokens - usage.actual_output - usage.reserved_output

    def reserve(
        self, *, stage: str, input_upper_bound: int, output_upper_bound: int
    ) -> RequestReservation:
        if (
            isinstance(input_upper_bound, bool)
            or not isinstance(input_upper_bound, int)
            or input_upper_bound <= 0
        ):
            raise BudgetError("serialized request upper bound must be a positive integer")
        if (
            isinstance(output_upper_bound, bool)
            or not isinstance(output_upper_bound, int)
            or output_upper_bound <= 0
        ):
            raise BudgetError("provider output upper bound must be a positive integer")
        if output_upper_bound > self.caps.max_output_per_request:
            raise BudgetError("provider output request exceeds the frozen 1024-token ceiling")
        with self._lock:
            usage = self._stage(stage)
            stage_caps = STAGE_CAPS[stage]
            if usage.requests >= stage_caps.max_requests:
                raise BudgetError(f"{stage} request cap exhausted")
            if self.total_requests >= self.caps.max_requests:
                raise BudgetError("workflow request cap exhausted")
            if (
                usage.actual_input + usage.reserved_input + input_upper_bound
                > stage_caps.max_input_tokens
            ):
                raise BudgetError(f"{stage} input cap exhausted")
            if (
                self._actual_input + self._reserved_input + input_upper_bound
                > self.caps.max_input_tokens
            ):
                raise BudgetError("workflow input cap exhausted")
            remaining_stage_output = (
                stage_caps.max_output_tokens - usage.actual_output - usage.reserved_output
            )
            remaining_workflow_output = (
                self.caps.max_output_tokens - self._actual_output - self._reserved_output
            )
            permitted_output = min(
                output_upper_bound, remaining_stage_output, remaining_workflow_output
            )
            if permitted_output != output_upper_bound:
                raise BudgetError(
                    "request output cap exceeds remaining stage or workflow allowance"
                )
            estimated_cost = self._cost(input_upper_bound, output_upper_bound)
            if (
                self._actual_cost() + self._reserved_cost() + estimated_cost
                > self.caps.cost_cap_usd
            ):
                raise BudgetError("workflow estimated cost cap exhausted")
            reservation = RequestReservation(
                reservation_id=self._next_id,
                stage=stage,
                input_upper_bound=input_upper_bound,
                output_upper_bound=output_upper_bound,
                estimated_cost_usd=estimated_cost,
            )
            self._next_id += 1
            self._reservations[reservation.reservation_id] = reservation
            usage.requests += 1
            usage.reserved_input += input_upper_bound
            usage.reserved_output += output_upper_bound
            self._reserved_input += input_upper_bound
            self._reserved_output += output_upper_bound
            return reservation

    @property
    def total_requests(self) -> int:
        return sum(usage.requests for usage in self._stages.values())

    def reconcile(
        self,
        reservation: RequestReservation,
        *,
        input_tokens: int,
        output_tokens: int,
        cache_tokens: int = 0,
        unknown_usage: bool = False,
    ) -> None:
        for label, value in (
            ("input usage", input_tokens),
            ("output usage", output_tokens),
            ("cache usage", cache_tokens),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise BudgetError(f"malformed provider {label}")
        with self._lock:
            current = self._reservations.pop(reservation.reservation_id, None)
            if current != reservation:
                raise BudgetError("unknown or already reconciled request reservation")
            usage = self._stage(reservation.stage)
            usage.reserved_input -= reservation.input_upper_bound
            usage.reserved_output -= reservation.output_upper_bound
            self._reserved_input -= reservation.input_upper_bound
            self._reserved_output -= reservation.output_upper_bound
            if unknown_usage:
                input_tokens = reservation.input_upper_bound
                output_tokens = reservation.output_upper_bound
                self._errors.append(
                    f"unknown_usage:{reservation.stage}:{reservation.reservation_id}"
                )
            usage.actual_input += input_tokens
            usage.actual_output += output_tokens
            self._actual_input += input_tokens
            self._actual_output += output_tokens
            self._actual_cache += cache_tokens
            exceeds = (
                input_tokens > reservation.input_upper_bound
                or output_tokens > reservation.output_upper_bound
                or usage.actual_input > STAGE_CAPS[reservation.stage].max_input_tokens
                or usage.actual_output > STAGE_CAPS[reservation.stage].max_output_tokens
                or self._actual_input > self.caps.max_input_tokens
                or self._actual_output > self.caps.max_output_tokens
                or self._actual_cost() > self.caps.cost_cap_usd
            )
            if exceeds:
                self._underestimated = True
                self._errors.append(
                    f"underestimated_or_exceeded:{reservation.stage}:{reservation.reservation_id}"
                )
                raise UnderestimatedUsageError(
                    "provider usage exceeded a strict reservation or frozen cap"
                )

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "candidate": self.candidate,
                "requests": self.total_requests,
                "actual_input_tokens": self._actual_input,
                "actual_output_tokens": self._actual_output,
                "actual_cache_tokens": self._actual_cache,
                "reserved_input_tokens": self._reserved_input,
                "reserved_output_tokens": self._reserved_output,
                "estimated_cost_usd": _decimal_text(self._actual_cost()),
                "reserved_estimated_cost_usd": _decimal_text(self._reserved_cost()),
                "underestimated": self._underestimated,
                "errors": list(self._errors),
                "caps": {
                    "max_requests": self.caps.max_requests,
                    "max_input_tokens": self.caps.max_input_tokens,
                    "max_output_tokens": self.caps.max_output_tokens,
                    "max_output_tokens_per_request": self.caps.max_output_per_request,
                    "estimated_cost_cap_usd": _decimal_text(self.caps.cost_cap_usd),
                    "wall_clock_seconds": self.caps.timeout_seconds,
                },
                "stages": {
                    stage: {
                        "requests": usage.requests,
                        "actual_input_tokens": usage.actual_input,
                        "actual_output_tokens": usage.actual_output,
                        "reserved_input_tokens": usage.reserved_input,
                        "reserved_output_tokens": usage.reserved_output,
                        "caps": STAGE_CAPS[stage].model_dump(mode="json"),
                    }
                    for stage, usage in self._stages.items()
                },
            }

    def _stage(self, stage: str) -> _StageUsage:
        try:
            return self._stages[stage]
        except KeyError as exc:
            raise BudgetError(f"stage {stage!r} is not admitted for {self.candidate}") from exc


def _usage_from_event(event: Any) -> tuple[int, int, int] | None:
    if not isinstance(event, Mapping):
        return None
    metadata = event.get("metadata")
    if not isinstance(metadata, Mapping):
        return None
    usage = metadata.get("usage")
    if not isinstance(usage, Mapping):
        return None
    input_tokens = usage.get("inputTokens")
    output_tokens = usage.get("outputTokens")
    cache_tokens = usage.get("cacheReadInputTokens", usage.get("cacheReadTokens", 0))
    values = (input_tokens, output_tokens, cache_tokens)
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values):
        raise BudgetError("provider emitted malformed usage metadata")
    return cast(tuple[int, int, int], values)


class StrictReservationModel(Model):
    """A Model adapter that makes its reservation true at the provider boundary.

    The existing product adapter can reserve less than a delegate's configured
    ``max_tokens``.  This isolated adapter explicitly lowers the delegate before
    opening the stream, verifies that value, then reserves that exact ceiling.
    """

    def __init__(self, delegate: Model, ledger: StrictWorkflowLedger, stage: str) -> None:
        self.delegate = delegate
        self.ledger = ledger
        self.stage = stage
        self.attempts: list[dict[str, Any]] = []

    @property
    def stateful(self) -> bool:
        return bool(getattr(self.delegate, "stateful", False))

    def get_config(self) -> Any:
        return self.delegate.get_config()

    def update_config(self, **model_config: Any) -> None:
        max_tokens = model_config.get("max_tokens")
        if max_tokens is not None and (
            isinstance(max_tokens, bool)
            or not isinstance(max_tokens, int)
            or max_tokens <= 0
            or max_tokens > MAX_REQUEST_OUTPUT_TOKENS
        ):
            raise BudgetError("model max_tokens violates the frozen per-request ceiling")
        self.delegate.update_config(**model_config)

    async def count_tokens(
        self,
        messages: Any,
        tool_specs: Any = None,
        system_prompt: str | None = None,
        system_prompt_content: Any = None,
    ) -> int:
        return int(
            await self.delegate.count_tokens(
                messages,
                tool_specs=tool_specs,
                system_prompt=system_prompt,
                system_prompt_content=system_prompt_content,
            )
        )

    def _set_provider_output_bound(self) -> int:
        config = self.delegate.get_config()
        configured = config.get("max_tokens") if isinstance(config, Mapping) else None
        if configured is None:
            configured = MAX_REQUEST_OUTPUT_TOKENS
        if isinstance(configured, bool) or not isinstance(configured, int) or configured <= 0:
            raise BudgetError("delegate model lacks a positive integer max_tokens")
        remaining = self.ledger.remaining_stage_output(self.stage)
        allowed = min(configured, MAX_REQUEST_OUTPUT_TOKENS, remaining)
        if allowed <= 0:
            raise BudgetError("no stage output allowance remains before provider call")
        # Lower before reserving or delegating.  A delegate that refuses this clamp
        # cannot be used because its real provider request would exceed the reservation.
        self.delegate.update_config(max_tokens=allowed)
        verified = self.delegate.get_config()
        verified_max = verified.get("max_tokens") if isinstance(verified, Mapping) else None
        if isinstance(verified_max, bool) or not isinstance(verified_max, int) or verified_max <= 0:
            raise BudgetError("delegate did not expose a valid max_tokens after clamp")
        if verified_max > allowed:
            raise BudgetError("delegate refused strict max_tokens clamp before provider call")
        return verified_max

    @staticmethod
    def _serialized_request(
        *,
        messages: Any,
        tool_specs: Any,
        system_prompt: str | None,
        tool_choice: Any,
        system_prompt_content: Any,
        invocation_state: Any,
        model_state: Any,
        kwargs: Mapping[str, Any],
        model_config: Any,
    ) -> bytes:
        # For the only live path (BedrockModel), Strands carries invocation/model
        # state for its event loop and Graph context; it is not emitted in the
        # provider request.  Counting it would falsely reject a compact coordinator
        # after Graph has accumulated local state.  It is intentionally excluded,
        # while every wire-facing message, schema, system block, model config and
        # request argument remains in the conservative byte reservation.
        del invocation_state, model_state
        request = {
            "messages": messages,
            "tool_specs": tool_specs or [],
            "system_prompt": system_prompt,
            "tool_choice": tool_choice,
            "system_prompt_content": system_prompt_content,
            "kwargs": dict(kwargs),
            "model_config": model_config,
        }
        return _canonical_json(request).encode("utf-8")

    async def stream(
        self,
        messages: Any,
        tool_specs: Any = None,
        system_prompt: str | None = None,
        *,
        tool_choice: Any = None,
        system_prompt_content: Any = None,
        invocation_state: dict[str, Any] | None = None,
        model_state: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:
        output_bound = self._set_provider_output_bound()
        serialized = self._serialized_request(
            messages=messages,
            tool_specs=tool_specs,
            system_prompt=system_prompt,
            tool_choice=tool_choice,
            system_prompt_content=system_prompt_content,
            invocation_state=invocation_state,
            model_state=model_state,
            kwargs=kwargs,
            model_config=self.delegate.get_config(),
        )
        reservation = self.ledger.reserve(
            stage=self.stage,
            input_upper_bound=len(serialized),
            output_upper_bound=output_bound,
        )
        attempt: dict[str, Any] = {
            "stage": self.stage,
            "reservation": {
                "id": reservation.reservation_id,
                "input_upper_bound": reservation.input_upper_bound,
                "output_upper_bound": reservation.output_upper_bound,
                "estimated_cost_usd": _decimal_text(reservation.estimated_cost_usd),
            },
            "delegate_max_tokens": output_bound,
            "serialized_request_bytes": len(serialized),
            "usage": [],
        }
        self.attempts.append(attempt)
        input_tokens = 0
        output_tokens = 0
        cache_tokens = 0
        saw_usage = False
        provider_error: BaseException | None = None
        try:
            async for event in self.delegate.stream(
                messages,
                tool_specs,
                system_prompt,
                tool_choice=tool_choice,
                system_prompt_content=system_prompt_content,
                invocation_state=invocation_state,
                model_state=model_state,
                **kwargs,
            ):
                usage = _usage_from_event(event)
                if usage is not None:
                    saw_usage = True
                    input_tokens += usage[0]
                    output_tokens += usage[1]
                    cache_tokens += usage[2]
                    attempt["usage"].append(
                        {
                            "input_tokens": usage[0],
                            "output_tokens": usage[1],
                            "cache_tokens": usage[2],
                        }
                    )
                yield event
        except BaseException as exc:
            provider_error = exc
            attempt["error"] = {"type": type(exc).__name__, "message": str(exc)}
            raise
        finally:
            unknown = not saw_usage
            try:
                self.ledger.reconcile(
                    reservation,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cache_tokens=cache_tokens,
                    unknown_usage=unknown,
                )
            except BaseException as budget_exc:
                attempt["reconciliation_error"] = {
                    "type": type(budget_exc).__name__,
                    "message": str(budget_exc),
                }
                if provider_error is None:
                    raise
            if unknown and provider_error is None:
                raise BudgetError(
                    "provider usage metadata was absent; full reservation retained as failure"
                )

    async def structured_output(
        self,
        output_model: type[BaseModel],
        prompt: Any,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:
        # Agent uses stream for native structured output.  Direct calls still get a
        # strict reservation, so there is no bypass around this adapter.
        output_bound = self._set_provider_output_bound()
        serialized = self._serialized_request(
            messages=prompt,
            tool_specs=None,
            system_prompt=system_prompt,
            tool_choice=None,
            system_prompt_content=None,
            invocation_state=None,
            model_state=None,
            kwargs={"output_schema": output_model.model_json_schema(), **kwargs},
            model_config=self.delegate.get_config(),
        )
        reservation = self.ledger.reserve(
            stage=self.stage,
            input_upper_bound=len(serialized),
            output_upper_bound=output_bound,
        )
        input_tokens = 0
        output_tokens = 0
        cache_tokens = 0
        saw_usage = False
        try:
            async for event in self.delegate.structured_output(
                output_model, prompt, system_prompt=system_prompt, **kwargs
            ):
                # The direct structured-output protocol lacks a universal event shape.
                # If it does not include metadata, charge the full reservation.
                usage = _usage_from_event(event)
                if usage is not None:
                    saw_usage = True
                    input_tokens += usage[0]
                    output_tokens += usage[1]
                    cache_tokens += usage[2]
                yield event
        finally:
            self.ledger.reconcile(
                reservation,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_tokens=cache_tokens,
                unknown_usage=not saw_usage,
            )
            if not saw_usage:
                raise BudgetError(
                    "provider usage metadata was absent; full reservation retained as failure"
                )

    def __getattr__(self, name: str) -> Any:
        return getattr(self.delegate, name)


class SourceReader:
    """Actor-scoped synthetic snapshot readers whose parameters affect results."""

    def __init__(self, case: CaseInput) -> None:
        self.case = case
        self.calls: list[ToolCall] = []
        self._returned: dict[ActorName, dict[str, SourceRecord]] = {}

    @property
    def returned(self) -> Mapping[ActorName, Mapping[str, SourceRecord]]:
        return {actor: dict(records) for actor, records in self._returned.items()}

    def tool_for(self, *, actor: ActorName, source: SourceName) -> Any:
        name = f"read_{source}"

        def read_source(query: str, record_ids: list[str] | None = None) -> dict[str, Any]:
            return self.retrieve(actor=actor, source=source, query=query, record_ids=record_ids)

        read_source.__name__ = name
        return tool(
            read_source,
            name=name,
            description=(
                "Read only the synthetic records matching a non-empty evidence query. "
                "Optional record_ids narrow the returned records; no approvals or writes exist."
            ),
        )

    def retrieve(
        self,
        *,
        actor: ActorName,
        source: SourceName,
        query: str,
        record_ids: Sequence[str] | None,
    ) -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip():
            raise InputContractError("source retrieval requires a non-empty query")
        if actor not in {ACTOR_RECEIVING, ACTOR_FULFILLMENT, ACTOR_SINGLE, "rules_baseline"}:
            raise InputContractError(f"actor {actor} cannot call source readers")
        if actor == ACTOR_RECEIVING and source != SOURCE_RECEIVING:
            raise InputContractError("receiving specialist cannot read fulfillment records")
        if actor == ACTOR_FULFILLMENT and source != SOURCE_FULFILLMENT:
            raise InputContractError("fulfillment specialist cannot read receiving records")
        packet = self.case.packet(source)
        requested = list(record_ids or [])
        if len(requested) != len(set(requested)):
            raise InputContractError("record_ids must not repeat")
        packet_records = {record.record_id: record for record in packet.records}
        if requested and any(record_id not in packet_records for record_id in requested):
            raise InputContractError(
                "source retrieval requested a record outside the source packet"
            )
        candidates = (
            [packet_records[record_id] for record_id in requested]
            if requested
            else list(packet.records)
        )
        terms = [term.lower() for term in query.split() if term.strip()]
        if not terms:
            raise InputContractError("source retrieval requires a meaningful query")
        if "all" in terms:
            matched = candidates
        else:
            matched = []
            for record in candidates:
                searchable = _canonical_json(
                    {"record_id": record.record_id, "as_of": record.as_of, "fields": record.fields}
                ).lower()
                if all(term in searchable for term in terms):
                    matched.append(record)
        returned_ids = [record.record_id for record in matched]
        actor_records = self._returned.setdefault(actor, {})
        actor_records.update({record.record_id: record for record in matched})
        call = ToolCall(
            actor=actor,
            tool=f"read_{source}",
            source=source,
            query=query,
            requested_record_ids=requested,
            returned_record_ids=returned_ids,
            returned_records_sha256=_sha256([record.model_dump(mode="json") for record in matched]),
        )
        self.calls.append(call)
        return {
            "case_id": self.case.case_id,
            "snapshot_id": self.case.snapshot_id,
            "source_mode": self.case.source_mode,
            "as_of": self.case.as_of,
            "source": source,
            "source_status": packet.status,
            "source_as_of": packet.as_of,
            "records": [record.model_dump(mode="json") for record in matched],
        }

    def validate_literal(self, *, actor: ActorName, literal: FieldLiteral) -> None:
        record = self._returned.get(actor, {}).get(literal.record_id)
        if record is None:
            raise InputContractError(
                f"{actor} cited {literal.record_id}, which was not returned to that actor"
            )
        actual = _resolve_json_pointer(record.fields, literal.field_path)
        if _canonical_json(actual) != _canonical_json(literal.literal_value):
            raise InputContractError(
                f"{actor} literal {literal.record_id}{literal.field_path} "
                "does not match the returned record"
            )

    def validate_specialist(
        self, observation: SpecialistObservation, *, expected_actor: ActorName
    ) -> None:
        if observation.actor != expected_actor:
            raise InputContractError("specialist output has the wrong actor identity")
        if (
            observation.case_id != self.case.case_id
            or observation.snapshot_id != self.case.snapshot_id
        ):
            raise InputContractError("specialist output does not match the active case/snapshot")
        if observation.source_mode != self.case.source_mode or observation.as_of != self.case.as_of:
            raise InputContractError("specialist output does not match active source metadata")
        calls = [call for call in self.calls if call.actor == expected_actor]
        if not calls:
            raise InputContractError("specialist produced observations before any source retrieval")
        source = SOURCE_RECEIVING if expected_actor == ACTOR_RECEIVING else SOURCE_FULFILLMENT
        packet = self.case.packet(source)
        returned_count = sum(len(call.returned_record_ids) for call in calls)
        if observation.literals:
            if observation.source_read_status != "evidence_returned" or returned_count == 0:
                raise InputContractError(
                    "specialist literals require an actual returned-evidence status"
                )
        elif packet.status == "unavailable":
            if (
                observation.source_read_status != "source_unavailable"
                or not observation.missing_evidence
            ):
                raise InputContractError(
                    "unavailable source requires explicit unavailable status and missing evidence"
                )
        elif returned_count == 0:
            if (
                observation.source_read_status != "no_matching_records"
                or not observation.missing_evidence
            ):
                raise InputContractError(
                    "empty source result requires explicit no-match status and missing evidence"
                )
        elif (
            observation.source_read_status != "evidence_returned"
            or not observation.missing_evidence
        ):
            raise InputContractError(
                "zero literals with returned evidence requires explicit "
                "missing-evidence explanation"
            )
        for literal in observation.literals:
            self.validate_literal(actor=expected_actor, literal=literal)

    def validate_answer(
        self, answer: DecisionAnswer, *, allowed_citation_actors: set[ActorName]
    ) -> None:
        if answer.case_id != self.case.case_id or answer.snapshot_id != self.case.snapshot_id:
            raise InputContractError("final answer does not match active case/snapshot")
        if answer.source_mode != self.case.source_mode or answer.as_of != self.case.as_of:
            raise InputContractError("final answer does not match active source metadata")
        if answer.authority.approval or answer.authority.executed:
            raise InputContractError("read-only experiment answer asserted approval or execution")
        for citation in answer.citations:
            if citation.actor not in allowed_citation_actors:
                raise InputContractError(
                    "answer citation used an actor outside its candidate scope"
                )
            self.validate_literal(
                actor=citation.actor,
                literal=FieldLiteral(
                    record_id=citation.record_id,
                    field_path=citation.field_path,
                    literal_value=citation.literal_value,
                ),
            )


def _resolve_json_pointer(value: JsonValue, pointer: str) -> JsonValue:
    if not pointer.startswith("/"):
        raise InputContractError("field path must be a JSON pointer beneath record fields")
    current: Any = value
    for component in pointer[1:].split("/"):
        key = component.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping):
            if key not in current:
                raise InputContractError(f"field path {pointer} is absent from returned record")
            current = current[key]
        elif isinstance(current, list):
            if not key.isdigit() or int(key) >= len(current):
                raise InputContractError(f"field path {pointer} is absent from returned record")
            current = current[int(key)]
        else:
            raise InputContractError(f"field path {pointer} descends through a scalar")
    return cast(JsonValue, current)


class _TypedSpecialistNode:
    """Graph AgentBase proxy that supplies only its source scope and captures typed output."""

    def __init__(
        self,
        *,
        actor: Literal["receiving_specialist", "fulfillment_specialist"],
        agent: Agent,
        case: CaseInput,
        reader: SourceReader,
        stage: str,
    ) -> None:
        self.actor = actor
        self.agent = agent
        self.case = case
        self.reader = reader
        self.stage = stage
        self.observation: SpecialistObservation | None = None
        self.id = actor

    def _prompt(self) -> str:
        source = SOURCE_RECEIVING if self.actor == ACTOR_RECEIVING else SOURCE_FULFILLMENT
        return _canonical_json(
            {
                "task": (
                    "Investigate only your assigned source using its read tool, "
                    "then return typed literals and separately labeled interpretations."
                ),
                "case_id": self.case.case_id,
                "snapshot_id": self.case.snapshot_id,
                "source_mode": self.case.source_mode,
                "as_of": self.case.as_of,
                "question": self.case.question,
                "requested_output_scope": {
                    "quantity_names": self.case.requested_quantity_names,
                    "order_ids": self.case.requested_order_ids,
                },
                "assigned_source": source,
                "prohibitions": [
                    "Do not infer approval or execution.",
                    "Do not claim a literal that was not returned by your source tool.",
                    "Do not request the other specialist's source.",
                ],
            }
        )

    def _limits(self) -> Limits:
        caps = STAGE_CAPS[self.stage]
        return Limits(
            turns=caps.limits_turns,
            output_tokens=caps.max_output_tokens,
            total_tokens=caps.limits_total_tokens,
        )

    async def stream_async(self, prompt: Any = None, **kwargs: Any) -> AsyncGenerator[Any, None]:
        del prompt
        async for event in self.agent.stream_async(
            self._prompt(),
            invocation_state=kwargs.get("invocation_state"),
            limits=self._limits(),
            structured_output_model=SpecialistObservation,
        ):
            if isinstance(event, Mapping) and "result" in event:
                result = cast(AgentResult, event["result"])
                output = result.structured_output
                if output is None:
                    raise InputContractError(
                        f"{self.actor} did not return native structured output"
                    )
                self.observation = SpecialistObservation.model_validate(output)
                self.reader.validate_specialist(self.observation, expected_actor=self.actor)
            yield event

    async def invoke_async(self, prompt: Any = None, **kwargs: Any) -> AgentResult:
        result: AgentResult | None = None
        async for event in self.stream_async(prompt, **kwargs):
            if isinstance(event, Mapping) and "result" in event:
                result = cast(AgentResult, event["result"])
        if result is None:
            raise InputContractError(f"{self.actor} did not emit a result")
        return result

    def __call__(self, prompt: Any = None, **kwargs: Any) -> AgentResult:
        return asyncio.run(self.invoke_async(prompt, **kwargs))


class _TypedCoordinatorNode:
    """Graph AgentBase proxy that ignores Graph's raw concatenation and uses JoinPacket."""

    def __init__(
        self, *, agent: Agent, case: CaseInput, reader: SourceReader, gate: _JoinGate
    ) -> None:
        self.agent = agent
        self.case = case
        self.reader = reader
        self.gate = gate
        self.answer: DecisionAnswer | None = None
        self.id = ACTOR_COORDINATOR

    def _prompt(self) -> str:
        packet = self.gate.packet
        if packet is None:
            raise JoinError("coordinator invoked without a validated two-specialist JoinPacket")
        return _canonical_json(
            {
                "task": (
                    "Reconcile only these validated specialist inputs into the "
                    "typed receiving decision. Do not approve or execute anything."
                ),
                "join_packet": packet.model_dump(mode="json"),
                "required_answer_contract": {
                    "case_id": self.case.case_id,
                    "snapshot_id": self.case.snapshot_id,
                    "source_mode": self.case.source_mode,
                    "as_of": self.case.as_of,
                    "authority": {"approval": False, "executed": False},
                    "requested_output_scope": {
                        "quantity_names": self.case.requested_quantity_names,
                        "order_ids": self.case.requested_order_ids,
                    },
                },
            }
        )

    async def stream_async(self, prompt: Any = None, **kwargs: Any) -> AsyncGenerator[Any, None]:
        del prompt
        caps = STAGE_CAPS[COORDINATOR_STAGE]
        async for event in self.agent.stream_async(
            self._prompt(),
            invocation_state=kwargs.get("invocation_state"),
            limits=Limits(
                turns=caps.limits_turns,
                output_tokens=caps.max_output_tokens,
                total_tokens=caps.limits_total_tokens,
            ),
            structured_output_model=DecisionAnswer,
        ):
            if isinstance(event, Mapping) and "result" in event:
                result = cast(AgentResult, event["result"])
                output = result.structured_output
                if output is None:
                    raise InputContractError("coordinator did not return native structured output")
                self.answer = DecisionAnswer.model_validate(output)
                self.reader.validate_answer(
                    self.answer,
                    allowed_citation_actors={ACTOR_RECEIVING, ACTOR_FULFILLMENT},
                )
            yield event

    async def invoke_async(self, prompt: Any = None, **kwargs: Any) -> AgentResult:
        result: AgentResult | None = None
        async for event in self.stream_async(prompt, **kwargs):
            if isinstance(event, Mapping) and "result" in event:
                result = cast(AgentResult, event["result"])
        if result is None:
            raise InputContractError("coordinator did not emit a result")
        return result

    def __call__(self, prompt: Any = None, **kwargs: Any) -> AgentResult:
        return asyncio.run(self.invoke_async(prompt, **kwargs))


class _JoinGate:
    """Stateful edge condition that turns Graph's OR incoming-edge scheduling into AND."""

    def __init__(
        self, *, case: CaseInput, receiving: _TypedSpecialistNode, fulfillment: _TypedSpecialistNode
    ) -> None:
        self.case = case
        self.receiving = receiving
        self.fulfillment = fulfillment
        self.packet: JoinPacket | None = None

    def ready(self, state: Any, **_: Any) -> bool:
        # The Graph evaluates incoming edges with OR semantics.  Do not regard an edge
        # itself as a join: require both actual completed Graph node results *and* the
        # two independently parsed, validated typed observations.
        results = getattr(state, "results", {})
        if not isinstance(results, Mapping):
            return False
        if ACTOR_RECEIVING not in results or ACTOR_FULFILLMENT not in results:
            return False
        receiving = self.receiving.observation
        fulfillment = self.fulfillment.observation
        if receiving is None or fulfillment is None:
            return False
        packet = JoinPacket(
            case_id=self.case.case_id,
            snapshot_id=self.case.snapshot_id,
            source_mode=self.case.source_mode,
            as_of=self.case.as_of,
            receiving=receiving,
            fulfillment=fulfillment,
        )
        if (
            packet.receiving.actor != ACTOR_RECEIVING
            or packet.fulfillment.actor != ACTOR_FULFILLMENT
        ):
            raise JoinError("join received a specialist under the wrong actor identity")
        self.packet = packet
        return True


class ModelFactory(Protocol):
    def __call__(self, stage: str, max_tokens: int) -> Model: ...


def pinned_nova_pro_factory(stage: str, max_tokens: int) -> Model:
    """Create the one admissible live model without transport retries.

    It is intentionally not called unless the CLI receives ``--execute-model``.
    Offline tests pass a local scripted factory directly to ``execute_candidate``;
    they never use this factory and are never recorded as live/provider evidence.
    """

    del stage
    import boto3
    from botocore.config import Config
    from strands.models import BedrockModel

    session = boto3.Session(profile_name=AWS_PROFILE, region_name=MODEL_REGION)
    return BedrockModel(
        model_id=MODEL_ID,
        region_name=MODEL_REGION,
        boto_session=session,
        temperature=MODEL_TEMPERATURE,
        max_tokens=max_tokens,
        streaming=False,
        # One transport attempt total.  The Strands agents below also set
        # retry_strategy=None, so logical and transport request counts align.
        boto_client_config=Config(retries={"mode": "standard", "total_max_attempts": 1}),
    )


def _make_model(
    factory: ModelFactory, *, ledger: StrictWorkflowLedger, stage: str
) -> StrictReservationModel:
    try:
        raw = factory(stage, MAX_REQUEST_OUTPUT_TOKENS)
    except TypeError:
        # A no-argument factory is accepted only for local test doubles; the strict
        # adapter still sets and verifies max_tokens before every provider request.
        raw = cast(Model, factory())  # type: ignore[call-arg]
    if not isinstance(raw, Model):
        raise InputContractError("model factory did not return a Strands Model")
    return StrictReservationModel(raw, ledger, stage)


def _specialist_agent(
    *, model: StrictReservationModel, reader: SourceReader, actor: ActorName
) -> Agent:
    source = SOURCE_RECEIVING if actor == ACTOR_RECEIVING else SOURCE_FULFILLMENT
    return Agent(
        model=model,
        tools=[reader.tool_for(actor=actor, source=source)],
        system_prompt=(
            "You are a read-only specialist in a synthetic evaluation. "
            "Use only the offered source tool. Return typed literal observations, "
            "keep interpretations separate, and never imply approval or execution."
        ),
        callback_handler=None,
        retry_strategy=None,
    )


def _single_agent(*, model: StrictReservationModel, reader: SourceReader) -> Agent:
    return Agent(
        model=model,
        tools=[
            reader.tool_for(actor=ACTOR_SINGLE, source=SOURCE_RECEIVING),
            reader.tool_for(actor=ACTOR_SINGLE, source=SOURCE_FULFILLMENT),
        ],
        system_prompt=(
            "You are the single read-only investigator in a synthetic evaluation. "
            "Use source tools for evidence, return only typed quantities/dispositions/citations, "
            "and never imply approval or execution."
        ),
        callback_handler=None,
        retry_strategy=None,
    )


def _coordinator_agent(*, model: StrictReservationModel) -> Agent:
    return Agent(
        model=model,
        tools=[],
        system_prompt=(
            "You are a read-only coordinator. Use only the supplied validated JoinPacket; "
            "do not invent source literals, grant approval, or execute an operation."
        ),
        callback_handler=None,
        retry_strategy=None,
    )


def _graph_event_summary(event: Any) -> dict[str, Any]:
    """Keep actor trace useful without serializing raw messages or provider events twice."""

    if not isinstance(event, Mapping):
        return {"event_type": type(event).__name__}
    summary: dict[str, Any] = {}
    for key in ("multi_agent_node_start", "multi_agent_node_stop", "multi_agent_handoff"):
        if key in event:
            value = event[key]
            summary["event_type"] = key
            if isinstance(value, Mapping):
                for field_name in ("node_id", "from_node_ids", "to_node_ids"):
                    if field_name in value:
                        summary[field_name] = _copy_json(value[field_name])
            return summary
    if "result" in event:
        return {"event_type": "graph_result"}
    return {"event_type": "other"}


async def _run_single_async(
    *,
    case: CaseInput,
    model_factory: ModelFactory,
    reader: SourceReader,
    ledger: StrictWorkflowLedger,
    trace_capture: _AttemptTrace,
) -> tuple[DecisionAnswer, list[dict[str, Any]], list[dict[str, Any]]]:
    model = _make_model(model_factory, ledger=ledger, stage=SINGLE_STAGE)
    trace_capture.model_attempts[SINGLE_STAGE] = model.attempts
    agent = _single_agent(model=model, reader=reader)
    events = trace_capture.graph_events
    result: AgentResult | None = None
    caps = STAGE_CAPS[SINGLE_STAGE]
    prompt = _canonical_json(
        {
            "task": (
                "Investigate the synthetic evidence through the offered read tools "
                "and return the typed decision."
            ),
            "case_id": case.case_id,
            "snapshot_id": case.snapshot_id,
            "source_mode": case.source_mode,
            "as_of": case.as_of,
            "question": case.question,
            "requested_output_scope": {
                "quantity_names": case.requested_quantity_names,
                "order_ids": case.requested_order_ids,
            },
            "prohibitions": ["No approval", "No execution", "No unreturned citations"],
        }
    )
    async for event in agent.stream_async(
        prompt,
        limits=Limits(
            turns=caps.limits_turns,
            output_tokens=caps.max_output_tokens,
            total_tokens=caps.limits_total_tokens,
        ),
        structured_output_model=DecisionAnswer,
    ):
        if isinstance(event, Mapping) and "result" in event:
            result = cast(AgentResult, event["result"])
        events.append(
            {
                "event_type": "agent_event",
                "has_result": "result" in event if isinstance(event, Mapping) else False,
            }
        )
    if result is None or result.structured_output is None:
        raise InputContractError("single investigator did not return native structured output")
    answer = DecisionAnswer.model_validate(result.structured_output)
    reader.validate_answer(answer, allowed_citation_actors={ACTOR_SINGLE})
    return answer, events, list(model.attempts)


async def _run_graph_async(
    *,
    case: CaseInput,
    model_factory: ModelFactory,
    reader: SourceReader,
    ledger: StrictWorkflowLedger,
    trace_capture: _AttemptTrace,
) -> tuple[DecisionAnswer, list[dict[str, Any]], dict[str, list[dict[str, Any]]], JoinPacket]:
    receiving_model = _make_model(model_factory, ledger=ledger, stage=RECEIVING_STAGE)
    trace_capture.model_attempts[RECEIVING_STAGE] = receiving_model.attempts
    fulfillment_model = _make_model(model_factory, ledger=ledger, stage=FULFILLMENT_STAGE)
    trace_capture.model_attempts[FULFILLMENT_STAGE] = fulfillment_model.attempts
    coordinator_model = _make_model(model_factory, ledger=ledger, stage=COORDINATOR_STAGE)
    trace_capture.model_attempts[COORDINATOR_STAGE] = coordinator_model.attempts
    receiving = _TypedSpecialistNode(
        actor=ACTOR_RECEIVING,
        agent=_specialist_agent(model=receiving_model, reader=reader, actor=ACTOR_RECEIVING),
        case=case,
        reader=reader,
        stage=RECEIVING_STAGE,
    )
    fulfillment = _TypedSpecialistNode(
        actor=ACTOR_FULFILLMENT,
        agent=_specialist_agent(model=fulfillment_model, reader=reader, actor=ACTOR_FULFILLMENT),
        case=case,
        reader=reader,
        stage=FULFILLMENT_STAGE,
    )
    gate = _JoinGate(case=case, receiving=receiving, fulfillment=fulfillment)
    coordinator = _TypedCoordinatorNode(
        agent=_coordinator_agent(model=coordinator_model), case=case, reader=reader, gate=gate
    )
    builder = GraphBuilder()
    receiving_node = builder.add_node(receiving, node_id=ACTOR_RECEIVING)
    fulfillment_node = builder.add_node(fulfillment, node_id=ACTOR_FULFILLMENT)
    coordinator_node = builder.add_node(coordinator, node_id=ACTOR_COORDINATOR)
    builder.set_entry_point(ACTOR_RECEIVING)
    builder.set_entry_point(ACTOR_FULFILLMENT)
    # Both edges are conditional on the actual typed AND gate.  This deliberately
    # avoids treating Graph's documented incoming-edge OR behavior as a join.
    builder.add_edge(receiving_node, coordinator_node, condition=gate.ready)
    builder.add_edge(fulfillment_node, coordinator_node, condition=gate.ready)
    graph = (
        builder.set_graph_id("receiving-evidence-fixed-graph-v1")
        .set_max_node_executions(3)
        .set_execution_timeout(WORKFLOW_TIMEOUT_SECONDS)
        .set_node_timeout(WORKFLOW_TIMEOUT_SECONDS)
        .build()
    )
    graph_events = trace_capture.graph_events
    async for event in graph.stream_async(case.question):
        graph_events.append(_graph_event_summary(event))
    if gate.packet is None:
        raise JoinError("fixed Graph completed without a validated two-specialist JoinPacket")
    if coordinator.answer is None:
        raise JoinError("fixed Graph completed without coordinator typed output")
    attempts = {
        RECEIVING_STAGE: list(receiving_model.attempts),
        FULFILLMENT_STAGE: list(fulfillment_model.attempts),
        COORDINATOR_STAGE: list(coordinator_model.attempts),
    }
    return coordinator.answer, graph_events, attempts, gate.packet


def _run_with_timeout(awaitable: Any) -> Any:
    async def bounded() -> Any:
        return await asyncio.wait_for(awaitable, timeout=WORKFLOW_TIMEOUT_SECONDS)

    return asyncio.run(bounded())


def _record_value(record: SourceRecord, *names: str) -> Any | None:
    for name in names:
        if name in record.fields:
            return record.fields[name]
    return None


def _quantity_from_value(name: str, value: Any) -> Quantity | None:
    if not isinstance(value, Mapping):
        return None
    raw_value = value.get("value")
    unit = value.get("unit")
    if isinstance(unit, str) and raw_value is not None and not isinstance(raw_value, bool):
        try:
            return Quantity(name=name, value=Decimal(str(raw_value)), unit=unit, state="known")
        except Exception:
            return None
    return None


def _rules_baseline(case: CaseInput, reader: SourceReader) -> DecisionAnswer:
    """A deliberately modest form baseline over literal source fields.

    It uses no scenario IDs or expected key.  It exposes mechanically present quantity
    fields and records unresolved prerequisites instead of inventing a plan.
    """

    quantities: list[Quantity] = []
    dispositions: list[OrderDisposition] = []
    citations: list[Citation] = []
    missing: list[str] = []
    records_by_source: dict[SourceName, list[SourceRecord]] = {}
    for source in cast(tuple[SourceName, ...], SOURCE_NAMES):
        packet = case.packet(source)
        payload = reader.retrieve(
            actor="rules_baseline",
            source=source,
            query="all records",
            record_ids=[record.record_id for record in packet.records],
        )
        del payload
        records_by_source[source] = packet.records
    for records in records_by_source.values():
        for record in records:
            for field_name, raw in record.fields.items():
                quantity_name = f"{record.record_id}:{field_name}"
                candidate = _quantity_from_value(quantity_name, raw)
                if candidate is not None and quantity_name in case.requested_quantity_names:
                    quantities.append(candidate)
                    citations.append(
                        Citation(
                            actor="rules_baseline",
                            record_id=record.record_id,
                            field_path=f"/{field_name}",
                            literal_value=raw,
                        )
                    )
            for field_name in ("quality_state", "acknowledgement_state"):
                if field_name in record.fields:
                    citations.append(
                        Citation(
                            actor="rules_baseline",
                            record_id=record.record_id,
                            field_path=f"/{field_name}",
                            literal_value=record.fields[field_name],
                        )
                    )
            order_id = _record_value(record, "order_id")
            if not isinstance(order_id, str) or order_id not in case.requested_order_ids:
                continue
            state = _record_value(record, "eligibility_state", "fulfillment_state")
            eligible_raw = _record_value(record, "eligible_quantity")
            eligible_quantity = _quantity_from_value(f"{order_id}:eligible_quantity", eligible_raw)
            prerequisites = _record_value(record, "missing_prerequisites")
            required = (
                [str(item) for item in prerequisites] if isinstance(prerequisites, list) else []
            )
            if state not in {"eligible", "ineligible", "pending_evidence", "unknown"}:
                state = "unknown"
                required = required or ["mechanical eligibility state is absent"]
            if eligible_quantity is None:
                unit = "unknown"
                requested = _quantity_from_value(
                    "requested", _record_value(record, "requested_quantity")
                )
                if requested is not None:
                    unit = requested.unit
                eligible_quantity = Quantity(
                    name=f"{order_id}:eligible_quantity", value=None, unit=unit, state="unknown"
                )
                if state == "eligible":
                    state = "unknown"
                    required = required or ["literal eligible quantity is absent"]
            dispositions.append(
                OrderDisposition(
                    order_id=order_id,
                    disposition=cast(Any, state),
                    eligible_quantity=eligible_quantity,
                    missing_prerequisites=required,
                )
            )
            for field_name in (
                "requested_quantity",
                "eligibility_state",
                "fulfillment_state",
                "eligible_quantity",
                "missing_prerequisites",
            ):
                if field_name in record.fields:
                    citations.append(
                        Citation(
                            actor="rules_baseline",
                            record_id=record.record_id,
                            field_path=f"/{field_name}",
                            literal_value=record.fields[field_name],
                        )
                    )
    for disposition in dispositions:
        missing.extend(disposition.missing_prerequisites)
    return DecisionAnswer(
        case_id=case.case_id,
        snapshot_id=case.snapshot_id,
        source_mode=case.source_mode,
        as_of=case.as_of,
        quantities=quantities,
        order_dispositions=dispositions,
        citations=citations,
        missing_evidence=sorted(set(missing)),
        answer_text=(
            "Rules/form baseline reports literal quantities and declared order fields only; "
            "it leaves any missing prerequisite for operator investigation."
        ),
        authority=Authority(),
    )


class ReceivingEvidenceEvaluator(Evaluator[dict[str, Any], dict[str, Any]]):
    """Official Strands Evals custom adapter for deterministic domain assertions."""

    def __init__(self) -> None:
        super().__init__(name="receiving_evidence_deterministic")

    @staticmethod
    def _row(name: str, passed: bool, reason: str) -> EvaluationOutput:
        return EvaluationOutput(
            score=1.0 if passed else 0.0, test_pass=passed, reason=f"{name}: {reason}", label=name
        )

    @staticmethod
    def _actor_scope_and_citation_closure(
        *,
        case: CaseInput,
        answer: DecisionAnswer,
        tool_calls: Sequence[ToolCall],
        candidate: CandidateName,
    ) -> tuple[bool, str]:
        """Check the actor-local trace rather than treating the union as universal access."""

        source_scope: dict[ActorName, set[SourceName]] = {
            ACTOR_RECEIVING: {SOURCE_RECEIVING},
            ACTOR_FULFILLMENT: {SOURCE_FULFILLMENT},
            ACTOR_SINGLE: {SOURCE_RECEIVING, SOURCE_FULFILLMENT},
            "rules_baseline": {SOURCE_RECEIVING, SOURCE_FULFILLMENT},
            ACTOR_COORDINATOR: set(),
        }
        citation_actors: dict[CandidateName, set[ActorName]] = {
            "rules": {"rules_baseline"},
            "single": {ACTOR_SINGLE},
            "graph": {ACTOR_RECEIVING, ACTOR_FULFILLMENT},
        }
        records = {
            record.record_id: (packet.source, record)
            for packet in case.source_packets
            for record in packet.records
        }
        returned: dict[ActorName, set[str]] = {}
        failures: list[str] = []
        for call in tool_calls:
            if call.source not in source_scope[call.actor] or call.tool != f"read_{call.source}":
                failures.append(f"tool scope {call.actor}:{call.tool}")
            returned.setdefault(call.actor, set()).update(call.returned_record_ids)
        for citation in answer.citations:
            record = records.get(citation.record_id)
            if citation.actor not in citation_actors[candidate]:
                failures.append(f"citation actor {citation.actor}")
                continue
            if citation.record_id not in returned.get(citation.actor, set()):
                failures.append(f"unreturned citation {citation.actor}:{citation.record_id}")
                continue
            if record is None or record[0] not in source_scope[citation.actor]:
                failures.append(f"citation source scope {citation.actor}:{citation.record_id}")
                continue
            try:
                actual = _resolve_json_pointer(record[1].fields, citation.field_path)
            except InputContractError:
                failures.append(f"citation path {citation.record_id}{citation.field_path}")
                continue
            if _canonical_json(actual) != _canonical_json(citation.literal_value):
                failures.append(f"citation literal {citation.record_id}{citation.field_path}")
        if candidate == "graph":
            specialist_calls = {call.actor for call in tool_calls}
            if not {ACTOR_RECEIVING, ACTOR_FULFILLMENT}.issubset(specialist_calls):
                failures.append("both graph specialists did not read their assigned sources")
        return (
            not failures,
            "actor-local source scope and citation closure hold"
            if not failures
            else "; ".join(failures),
        )

    def evaluate(
        self, evaluation_case: EvaluationData[dict[str, Any], dict[str, Any]]
    ) -> list[EvaluationOutput]:
        try:
            input_payload = dict(evaluation_case.input)
            case = CaseInput.model_validate(input_payload["case"])
            key = KeyFile.model_validate(evaluation_case.expected_output)
            answer = DecisionAnswer.model_validate(evaluation_case.actual_output)
            metadata = cast(dict[str, Any], evaluation_case.metadata or {})
            trace = metadata.get("trace", {})
            candidate = cast(CandidateName, metadata.get("candidate"))
            if candidate not in {"rules", "single", "graph"}:
                raise InputContractError("evaluator metadata lacks a supported candidate")
            if not isinstance(trace, Mapping):
                raise InputContractError("evaluator trace must be an object")
            tool_calls = [ToolCall.model_validate(call) for call in trace.get("tool_calls", [])]
        except Exception as exc:
            return [self._row("schema", False, f"invalid evaluator payload: {exc}")]
        rows: list[EvaluationOutput] = []
        identity_ok = (
            key.case_id == case.case_id
            and key.snapshot_id == case.snapshot_id
            and answer.case_id == case.case_id
            and answer.snapshot_id == case.snapshot_id
            and answer.source_mode == case.source_mode
            and answer.as_of == case.as_of
        )
        rows.append(self._row("identity", identity_ok, "case/snapshot/source metadata matches"))
        actual_quantities = {quantity.name: quantity for quantity in answer.quantities}
        missing_quantities = [
            expected.name
            for expected in key.expected.quantities
            if actual_quantities.get(expected.name) != expected
        ]
        unexpected_quantities = sorted(
            set(actual_quantities) - {expected.name for expected in key.expected.quantities}
        )
        rows.append(
            self._row(
                "quantities",
                not missing_quantities and not unexpected_quantities,
                "requested typed quantities match exactly"
                if not missing_quantities and not unexpected_quantities
                else f"missing: {missing_quantities}; unexpected: {unexpected_quantities}",
            )
        )
        actual_orders = {order.order_id: order for order in answer.order_dispositions}
        missing_orders = []
        for expected in key.expected.order_dispositions:
            actual = actual_orders.get(expected.order_id)
            machine_match = (
                actual is not None
                and actual.disposition == expected.disposition
                and actual.eligible_quantity == expected.eligible_quantity
            )
            missing_evidence_present = expected.disposition not in {
                "pending_evidence",
                "unknown",
            } or bool(actual and actual.missing_prerequisites)
            if not machine_match or not missing_evidence_present:
                missing_orders.append(expected.order_id)
        unexpected_orders = sorted(
            set(actual_orders) - {expected.order_id for expected in key.expected.order_dispositions}
        )
        rows.append(
            self._row(
                "order_dispositions",
                not missing_orders and not unexpected_orders,
                "requested order IDs, dispositions, and typed eligible quantities match"
                if not missing_orders and not unexpected_orders
                else f"missing: {missing_orders}; unexpected: {unexpected_orders}",
            )
        )
        actual_citations = {
            _canonical_json(
                CitationRequirement(
                    record_id=citation.record_id,
                    field_path=citation.field_path,
                    literal_value=citation.literal_value,
                ).model_dump(mode="json")
            )
            for citation in answer.citations
        }
        required_citations = set(
            _canonical_json(citation.model_dump(mode="json"))
            for citation in key.expected.required_citations
        )
        missing_citations = sorted(required_citations - actual_citations)
        rows.append(
            self._row(
                "citation_membership",
                not missing_citations,
                "all required citations are present"
                if not missing_citations
                else "one or more required citations are absent",
            )
        )
        scope_ok, scope_reason = self._actor_scope_and_citation_closure(
            case=case,
            answer=answer,
            tool_calls=tool_calls,
            candidate=candidate,
        )
        rows.append(self._row("actor_scope_and_citation_closure", scope_ok, scope_reason))
        sources_seen = {call.source for call in tool_calls if call.returned_record_ids}
        required_sources = set(key.expected.required_sources)
        rows.append(
            self._row(
                "source_coverage",
                required_sources.issubset(sources_seen),
                "required sources were returned"
                if required_sources.issubset(sources_seen)
                else f"missing sources: {sorted(required_sources - sources_seen)}",
            )
        )
        allowed_tools = {f"read_{SOURCE_RECEIVING}", f"read_{SOURCE_FULFILLMENT}"}
        prohibited = [call.tool for call in tool_calls if call.tool not in allowed_tools]
        authority_ok = (
            not answer.authority.approval and not answer.authority.executed and not prohibited
        )
        rows.append(
            self._row(
                "authority_and_tools",
                authority_ok,
                "answer has no approval/execution and trace has only read tools"
                if authority_ok
                else f"prohibited tools or authority: {prohibited}",
            )
        )
        return rows


def evaluate_answer(
    *,
    case: CaseInput,
    key: KeyFile,
    answer: DecisionAnswer,
    reader: SourceReader,
    actor_trace: Mapping[str, Any],
    candidate: CandidateName,
) -> dict[str, Any]:
    """Run the official Evals Experiment with the custom deterministic adapter."""

    evaluator = ReceivingEvidenceEvaluator()
    evaluation_case = Case[dict[str, Any], dict[str, Any]](
        name=f"{case.case_id}:{case.snapshot_id}",
        input={"case": case.model_dump(mode="json")},
        expected_output=key.model_dump(mode="json"),
        metadata={"trace": _copy_json(actor_trace), "candidate": candidate},
    )
    experiment = Experiment(cases=[evaluation_case], evaluators=[evaluator])

    def task(_: Case[dict[str, Any], dict[str, Any]]) -> dict[str, Any]:
        return {
            "output": answer.model_dump(mode="json"),
            "trajectory": [call.tool for call in reader.calls],
        }

    report = experiment.run_evaluations(task)
    return report.model_dump(mode="json")


def _private_append_jsonl(path: Path, record: Mapping[str, Any]) -> None:
    if not path.parent.is_dir():
        raise InputContractError(f"private output parent does not exist: {path.parent}")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "a", encoding="utf-8", closefd=True) as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                handle.write(_canonical_json(record))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except Exception:
        with suppress(OSError):
            os.close(descriptor)
        raise


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InputContractError(f"malformed JSONL at {path}:{index}") from exc
        if not isinstance(value, dict):
            raise InputContractError(f"ledger row {index} must be a JSON object")
        rows.append(value)
    return rows


class DurableExperimentLedger:
    """Append-only experiment-wide cost ledger; it deliberately provides no reset operation."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def reserve_workflow(
        self, *, run_id: str, candidate: CandidateName, case_hash: str
    ) -> dict[str, Any]:
        if not self.path.parent.is_dir():
            raise InputContractError(f"durable ledger parent does not exist: {self.path.parent}")
        descriptor = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "r+", encoding="utf-8", closefd=True) as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    handle.seek(0)
                    rows = _parse_jsonl_text(handle.read(), self.path)
                    state = self._state(rows)
                    requested = Decimal("0") if candidate == "rules" else WORKFLOW_COST_CAP_USD
                    if (
                        state["charged"] + state["unsettled_reserved"] + requested
                        > EXPERIMENT_COST_CAP_USD
                    ):
                        raise BudgetError("durable USD 3 experiment cap exhausted")
                    event = {
                        "schema_version": SCHEMA_VERSION,
                        "event": "reserve_workflow",
                        "run_id": run_id,
                        "candidate": candidate,
                        "case_sha256": case_hash,
                        "reserved_cost_usd": _decimal_text(requested),
                        "timestamp": _utc_now(),
                    }
                    handle.seek(0, os.SEEK_END)
                    handle.write(_canonical_json(event) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                    return {**event, "state_before": self._serializable_state(state)}
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except Exception:
            with suppress(OSError):
                os.close(descriptor)
            raise

    def settle_workflow(
        self, *, run_id: str, charged_cost_usd: Decimal, status: str
    ) -> dict[str, Any]:
        if charged_cost_usd < 0:
            raise InputContractError("charged cost cannot be negative")
        descriptor = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "r+", encoding="utf-8", closefd=True) as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    handle.seek(0)
                    rows = _parse_jsonl_text(handle.read(), self.path)
                    reservations = {
                        row["run_id"]: Decimal(str(row["reserved_cost_usd"]))
                        for row in rows
                        if row.get("event") == "reserve_workflow"
                    }
                    settled = {
                        row.get("run_id") for row in rows if row.get("event") == "settle_workflow"
                    }
                    if run_id not in reservations or run_id in settled:
                        raise InputContractError(
                            "workflow settlement has no unique prior reservation"
                        )
                    if charged_cost_usd > reservations[run_id]:
                        raise BudgetError("workflow charged more than its durable reservation")
                    event = {
                        "schema_version": SCHEMA_VERSION,
                        "event": "settle_workflow",
                        "run_id": run_id,
                        "charged_cost_usd": _decimal_text(charged_cost_usd),
                        "status": status,
                        "timestamp": _utc_now(),
                    }
                    handle.seek(0, os.SEEK_END)
                    handle.write(_canonical_json(event) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                    return event
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except Exception:
            with suppress(OSError):
                os.close(descriptor)
            raise

    @staticmethod
    def _state(rows: Sequence[Mapping[str, Any]]) -> dict[str, Decimal]:
        reservations: dict[str, Decimal] = {}
        settlements: dict[str, Decimal] = {}
        for row in rows:
            if row.get("event") == "reserve_workflow":
                reservations[str(row.get("run_id"))] = Decimal(
                    str(row.get("reserved_cost_usd", "0"))
                )
            elif row.get("event") == "settle_workflow":
                settlements[str(row.get("run_id"))] = Decimal(str(row.get("charged_cost_usd", "0")))
        charged = sum(settlements.values(), Decimal("0"))
        unsettled_reserved = sum(
            (reserved for run_id, reserved in reservations.items() if run_id not in settlements),
            Decimal("0"),
        )
        return {"charged": charged, "unsettled_reserved": unsettled_reserved}

    @staticmethod
    def _serializable_state(state: Mapping[str, Decimal]) -> dict[str, str]:
        return {key: _decimal_text(value) for key, value in state.items()}


def _parse_jsonl_text(text: str, path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InputContractError(f"malformed durable ledger at {path}:{index}") from exc
        if not isinstance(value, dict):
            raise InputContractError(f"durable ledger row {index} is not an object")
        rows.append(value)
    return rows


def _schema_payloads() -> dict[str, Any]:
    return {
        "case": CaseInput.model_json_schema(),
        "key": KeyFile.model_json_schema(),
        "answer": DecisionAnswer.model_json_schema(),
        "specialist_observation": SpecialistObservation.model_json_schema(),
        "run_record": _run_record_schema(),
    }


def _run_record_schema() -> dict[str, Any]:
    # Run records are intentionally flexible around provider error objects but retain
    # the fields needed to audit an experiment attempt.
    return {
        "type": "object",
        "required": [
            "schema_version",
            "record_type",
            "run_id",
            "candidate",
            "case",
            "usage",
            "errors",
            "actor_trace",
            "promotion_status",
        ],
        "properties": {
            "schema_version": {"const": SCHEMA_VERSION},
            "record_type": {"const": "workflow"},
            "run_id": {"type": "string"},
            "candidate": {"enum": ["rules", "single", "graph"]},
            "case": {"type": "object"},
            "usage": {"type": "object"},
            "errors": {"type": "array"},
            "actor_trace": {"type": "object"},
            "promotion_status": {"const": "NOT_AUTOMATICALLY_PROMOTED"},
        },
    }


def create_freeze_manifest(path: Path) -> dict[str, Any]:
    if path.exists():
        raise InputContractError(f"refusing to overwrite freeze manifest: {path}")
    if not path.parent.is_dir():
        raise InputContractError(f"freeze output parent does not exist: {path.parent}")
    script = Path(__file__).resolve()
    schema_hashes = {name: _sha256(payload) for name, payload in _schema_payloads().items()}
    try:
        agents_version = importlib.metadata.version("strands-agents")
        evals_version = importlib.metadata.version("strands-agents-evals")
    except importlib.metadata.PackageNotFoundError as exc:
        raise InputContractError(
            "freeze requires strands-agents and strands-agents-evals in the isolated venv"
        ) from exc
    payload = {
        "schema_version": FREEZE_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "candidate_source_sha256": _file_sha256(script),
        "schema_sha256": schema_hashes,
        "runtime": {
            "strands_agents": agents_version,
            "strands_agents_evals": evals_version,
            "model_id": MODEL_ID,
            "region": MODEL_REGION,
            "aws_profile": AWS_PROFILE,
            "temperature": MODEL_TEMPERATURE,
            "provider_max_output_tokens": MAX_REQUEST_OUTPUT_TOKENS,
        },
        "workflow_budget": {
            "max_requests": WORKFLOW_CAPS.max_requests,
            "max_input_tokens": WORKFLOW_CAPS.max_input_tokens,
            "max_output_tokens": WORKFLOW_CAPS.max_output_tokens,
            "estimated_cost_cap_usd": _decimal_text(WORKFLOW_CAPS.cost_cap_usd),
            "wall_clock_seconds": WORKFLOW_CAPS.timeout_seconds,
            "stages": {stage: caps.model_dump(mode="json") for stage, caps in STAGE_CAPS.items()},
        },
        "notes": "SHA-256 manifest only; this experiment does not claim a cryptographic signature.",
    }
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    return payload


def verify_freeze_manifest(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InputContractError(f"freeze manifest is unreadable: {path}") from exc
    if not isinstance(raw, dict) or raw.get("schema_version") != FREEZE_SCHEMA_VERSION:
        raise InputContractError("freeze manifest has an unsupported schema")
    current = create_freeze_payload_for_verification()
    for key in ("candidate_source_sha256", "schema_sha256", "runtime", "workflow_budget"):
        if _canonical_json(raw.get(key)) != _canonical_json(current.get(key)):
            raise InputContractError(f"freeze manifest no longer matches current candidate {key}")
    return raw


def create_freeze_payload_for_verification() -> dict[str, Any]:
    script = Path(__file__).resolve()
    return {
        "candidate_source_sha256": _file_sha256(script),
        "schema_sha256": {name: _sha256(payload) for name, payload in _schema_payloads().items()},
        "runtime": {
            "strands_agents": importlib.metadata.version("strands-agents"),
            "strands_agents_evals": importlib.metadata.version("strands-agents-evals"),
            "model_id": MODEL_ID,
            "region": MODEL_REGION,
            "aws_profile": AWS_PROFILE,
            "temperature": MODEL_TEMPERATURE,
            "provider_max_output_tokens": MAX_REQUEST_OUTPUT_TOKENS,
        },
        "workflow_budget": {
            "max_requests": WORKFLOW_CAPS.max_requests,
            "max_input_tokens": WORKFLOW_CAPS.max_input_tokens,
            "max_output_tokens": WORKFLOW_CAPS.max_output_tokens,
            "estimated_cost_cap_usd": _decimal_text(WORKFLOW_CAPS.cost_cap_usd),
            "wall_clock_seconds": WORKFLOW_CAPS.timeout_seconds,
            "stages": {stage: caps.model_dump(mode="json") for stage, caps in STAGE_CAPS.items()},
        },
    }


def load_case(path: Path) -> CaseInput:
    try:
        return CaseInput.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError, json.JSONDecodeError) as exc:
        raise InputContractError(f"case is invalid: {path}") from exc


def load_key(path: Path) -> KeyFile:
    try:
        return KeyFile.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError, json.JSONDecodeError) as exc:
        raise InputContractError(f"key is invalid: {path}") from exc


def _validate_case_key(case: CaseInput, key: KeyFile) -> None:
    if case.case_id != key.case_id or case.snapshot_id != key.snapshot_id:
        raise InputContractError(
            "externally supplied key does not match the supplied case/snapshot"
        )
    if {quantity.name for quantity in key.expected.quantities} != set(
        case.requested_quantity_names
    ):
        raise InputContractError(
            "key quantity expectations do not match the case requested-output scope"
        )
    if {order.order_id for order in key.expected.order_dispositions} != set(
        case.requested_order_ids
    ):
        raise InputContractError(
            "key order expectations do not match the case requested-output scope"
        )


def _trace_payload(
    reader: SourceReader, *, model_attempts: Any, graph_events: Sequence[Mapping[str, Any]] = ()
) -> dict[str, Any]:
    return {
        "tool_calls": [call.model_dump(mode="json") for call in reader.calls],
        "returned_record_ids_by_actor": {
            actor: sorted(records.keys()) for actor, records in reader.returned.items()
        },
        "model_attempts": _copy_json(model_attempts),
        "graph_events": [_copy_json(event) for event in graph_events],
    }


def execute_candidate(
    *,
    case: CaseInput,
    key: KeyFile,
    candidate: CandidateName,
    model_factory: ModelFactory | None,
    freeze_manifest: Mapping[str, Any],
    durable_ledger: DurableExperimentLedger,
    run_log: Path,
    case_reference: str | None = None,
) -> dict[str, Any]:
    """Execute one read-only workflow and append an auditable private JSONL row.

    A durable reservation happens before any model construction.  Evaluation happens
    only after a candidate output exists; it never feeds the key into an agent prompt.
    """

    _validate_case_key(case, key)
    run_id = str(uuid.uuid4())
    case_hash = _sha256(case.model_dump(mode="json"))
    durable_start = durable_ledger.reserve_workflow(
        run_id=run_id, candidate=candidate, case_hash=case_hash
    )
    reader = SourceReader(case)
    workflow_ledger = StrictWorkflowLedger(candidate=candidate)
    started = time.monotonic()
    answer: DecisionAnswer | None = None
    evaluation: dict[str, Any] | None = None
    errors: list[dict[str, str]] = []
    actor_trace: dict[str, Any] = {}
    trace_capture = _AttemptTrace()
    status = "FAILED"
    try:
        if candidate == "rules":
            answer = _rules_baseline(case, reader)
            reader.validate_answer(answer, allowed_citation_actors={"rules_baseline"})
            actor_trace = _trace_payload(reader, model_attempts={})
        else:
            if model_factory is None:
                raise InputContractError(
                    "model candidates require an explicit pinned model factory"
                )
            if candidate == "single":
                answer, events, attempts = _run_with_timeout(
                    _run_single_async(
                        case=case,
                        model_factory=model_factory,
                        reader=reader,
                        ledger=workflow_ledger,
                        trace_capture=trace_capture,
                    )
                )
                actor_trace = _trace_payload(
                    reader, model_attempts={SINGLE_STAGE: attempts}, graph_events=events
                )
            elif candidate == "graph":
                answer, graph_events, attempts, join_packet = _run_with_timeout(
                    _run_graph_async(
                        case=case,
                        model_factory=model_factory,
                        reader=reader,
                        ledger=workflow_ledger,
                        trace_capture=trace_capture,
                    )
                )
                actor_trace = _trace_payload(
                    reader, model_attempts=attempts, graph_events=graph_events
                )
                actor_trace["validated_join_packet"] = join_packet.model_dump(mode="json")
            else:  # pragma: no cover - Literal and argparse prevent this.
                raise InputContractError(f"unsupported candidate {candidate}")
        evaluation = evaluate_answer(
            case=case,
            key=key,
            answer=answer,
            reader=reader,
            actor_trace=actor_trace,
            candidate=candidate,
        )
        status = "COMPLETED"
    except BaseException as exc:
        errors.append({"type": type(exc).__name__, "message": str(exc)})
        if not actor_trace:
            actor_trace = _trace_payload(
                reader,
                model_attempts=trace_capture.model_attempts,
                graph_events=trace_capture.graph_events,
            )
    finally:
        usage = workflow_ledger.snapshot()
        charged = Decimal(str(usage["estimated_cost_usd"]))
        durable_finish = durable_ledger.settle_workflow(
            run_id=run_id, charged_cost_usd=charged, status=status
        )
    record = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "workflow",
        "run_id": run_id,
        "timestamp": _utc_now(),
        "status": status,
        "candidate": candidate,
        "candidate_version": freeze_manifest.get("candidate_source_sha256"),
        "freeze_manifest_sha256": _sha256(freeze_manifest),
        "case": {
            "case_id": case.case_id,
            "snapshot_id": case.snapshot_id,
            "tier": case.tier,
            "case_sha256": case_hash,
            "key_sha256": _sha256(key.model_dump(mode="json")),
            "source_packet_reference": case_reference or case_hash,
        },
        "question": case.question,
        "model": {
            "model_id": MODEL_ID if candidate != "rules" else None,
            "region": MODEL_REGION if candidate != "rules" else None,
            "aws_profile": AWS_PROFILE if candidate != "rules" else None,
            "temperature": MODEL_TEMPERATURE if candidate != "rules" else None,
        },
        "latency_ms": round((time.monotonic() - started) * 1_000),
        "usage": usage,
        "errors": errors,
        "actor_trace": actor_trace,
        "answer": answer.model_dump(mode="json") if answer is not None else None,
        "evaluation": evaluation,
        "durable_budget": {"reservation": durable_start, "settlement": durable_finish},
        "promotion_status": "NOT_AUTOMATICALLY_PROMOTED",
    }
    _private_append_jsonl(run_log, record)
    return record


def export_blinded(*, run_log: Path, output: Path, seed: str | None = None) -> dict[str, Any]:
    """Export semantic-review material without candidate/provider/actor trajectory identity."""

    if output.exists():
        raise InputContractError(f"refusing to overwrite blinded export: {output}")
    if not output.parent.is_dir():
        raise InputContractError(f"blinded export parent does not exist: {output.parent}")
    rows = [
        row
        for row in _read_jsonl(run_log)
        if row.get("record_type") == "workflow"
        and row.get("status") == "COMPLETED"
        and row.get("candidate") in {"single", "graph"}
        and isinstance(row.get("answer"), Mapping)
    ]
    selected_seed = seed or base64.urlsafe_b64encode(os.urandom(24)).decode("ascii")
    candidates = ["single", "graph"]
    randomizer = random.Random(selected_seed)
    randomizer.shuffle(candidates)
    labels = {candidates[0]: "A", candidates[1]: "B"}
    reviews: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        answer = DecisionAnswer.model_validate(row["answer"])
        case_ref = cast(Mapping[str, Any], row["case"])
        # Citations retain record and field references for reviewability, but remove
        # actor identity; model/provider/candidate/trajectory values never enter this export.
        review_citations = [
            {
                "record_id": citation.record_id,
                "field_path": citation.field_path,
                "literal_value": citation.literal_value,
            }
            for citation in answer.citations
        ]
        reviews.append(
            {
                "review_id": f"review-{index:04d}",
                "candidate_label": labels[str(row["candidate"])],
                "case": {
                    "case_id": case_ref.get("case_id"),
                    "snapshot_id": case_ref.get("snapshot_id"),
                    "tier": case_ref.get("tier"),
                    "source_packet_ref": case_ref.get("source_packet_reference"),
                },
                "question": _question_from_run_log_reference(row),
                "answer": {
                    "source_mode": answer.source_mode,
                    "as_of": answer.as_of,
                    "quantities": [
                        quantity.model_dump(mode="json") for quantity in answer.quantities
                    ],
                    "order_dispositions": [
                        order.model_dump(mode="json") for order in answer.order_dispositions
                    ],
                    "citations": review_citations,
                    "missing_evidence": answer.missing_evidence,
                    "answer_text": answer.answer_text,
                    "authority": answer.authority.model_dump(mode="json"),
                },
            }
        )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "export_type": "blinded_semantic_review",
        "records": reviews,
        "notes": (
            "Candidate/provider/actor names and trajectory are intentionally omitted. "
            "Use the private unblinded run log for mechanical trajectory audit."
        ),
    }
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    return payload


def _question_from_run_log_reference(row: Mapping[str, Any]) -> str:
    # Private run records intentionally store answer/trace rather than a duplicate full
    # source snapshot.  The caller supplies the external case file for a reviewer view.
    # The blinded export keeps a reviewable source packet hash/reference and uses this
    # neutral question placeholder when old logs lack an embedded question.
    question = row.get("question")
    if isinstance(question, str) and question:
        return question
    return "See the supplied synthetic case identified by the source_packet_ref."


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    freeze = subcommands.add_parser("freeze", help="write a SHA-256 candidate freeze manifest")
    freeze.add_argument("--output", type=Path, required=True)
    run = subcommands.add_parser(
        "run", help="run one case/key workflow and append private evidence"
    )
    run.add_argument("--case", type=Path, required=True)
    run.add_argument("--key", type=Path, required=True)
    run.add_argument("--candidate", choices=("rules", "single", "graph"), required=True)
    run.add_argument("--freeze-manifest", type=Path, required=True)
    run.add_argument("--ledger", type=Path, required=True)
    run.add_argument("--run-log", type=Path, required=True)
    run.add_argument(
        "--execute-model",
        action="store_true",
        help=(
            "explicitly permit the pinned Nova Pro factory; absent by default "
            "to avoid provider calls"
        ),
    )
    blinded = subcommands.add_parser("export-blinded", help="emit blinded semantic-review JSON")
    blinded.add_argument("--run-log", type=Path, required=True)
    blinded.add_argument("--output", type=Path, required=True)
    blinded.add_argument("--seed", type=str)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "freeze":
            print(
                json.dumps(create_freeze_manifest(args.output), ensure_ascii=False, sort_keys=True)
            )
            return 0
        if args.command == "export-blinded":
            print(
                json.dumps(export_blinded(run_log=args.run_log, output=args.output, seed=args.seed))
            )
            return 0
        if args.command == "run":
            case = load_case(args.case)
            key = load_key(args.key)
            manifest = verify_freeze_manifest(args.freeze_manifest)
            if args.candidate == "rules" and args.execute_model:
                raise InputContractError(
                    "rules baseline has no model and does not accept --execute-model"
                )
            if args.candidate != "rules" and not args.execute_model:
                raise InputContractError("model candidates require explicit --execute-model")
            record = execute_candidate(
                case=case,
                key=key,
                candidate=cast(CandidateName, args.candidate),
                model_factory=pinned_nova_pro_factory if args.candidate != "rules" else None,
                freeze_manifest=manifest,
                durable_ledger=DurableExperimentLedger(args.ledger),
                run_log=args.run_log,
                case_reference=str(args.case.resolve()),
            )
            print(
                json.dumps({"run_id": record["run_id"], "status": record["status"]}, sort_keys=True)
            )
            return 0 if record["status"] == "COMPLETED" else 1
        raise AssertionError("unreachable command")
    except ExperimentError as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
