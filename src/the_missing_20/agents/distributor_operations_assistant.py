"""Bounded structured assistant for one distributor operations case.

The assistant has one read-only tool. It can explain the current case, ask
for operator-declared physical evidence, draft a small supported physical
event, or request the already-gated economic ``split20`` preparation path.
It has no ERP adapter, proposal journal, approval, or execution capability.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from time import monotonic
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from the_missing_20.agents.product_language import (
    ProductLanguageViolation,
    english_product_text,
)
from the_missing_20.ports.agent_model import (
    AgentBudgetLedger,
    AgentModelFactory,
    AgentStage,
    actual_provider_metadata,
)

_SOURCE_TOOL = "read_current_distributor_case"
_MAX_HISTORY_TURNS = 4


class MissingInformation(BaseModel):
    """One specific item the operator must provide before a draft can proceed."""

    field: str = Field(min_length=1, max_length=80)
    prompt: str = Field(min_length=1, max_length=500)


class UserFieldCitation(BaseModel):
    """Bind a proposed physical value to one actual human turn."""

    field: str = Field(min_length=1, max_length=80)
    value: Any
    user_turn_id: str = Field(min_length=1, max_length=96)


class PhysicalDraft(BaseModel):
    """The model may draft inputs, but the adapter owns event identity and validation."""

    event: dict[str, Any]
    user_field_citations: list[UserFieldCitation] = Field(default_factory=list, max_length=16)
    prepare_requested: bool = False

    @model_validator(mode="after")
    def _safe_shape(self) -> PhysicalDraft:
        if "event_id" in self.event:
            raise ValueError("physical draft must not contain event_id")
        return self


class PhotoAnalysisRequest(BaseModel):
    """A request to analyze one already-attached photo through the existing reader."""

    lot: str = Field(min_length=1, max_length=256)
    purpose: Literal["overview", "label", "detail"] = Field(
        description=(
            "Required photo input: label for printed text or identity, detail for visible "
            "condition, damage, or corrosion, and overview for counts or a whole receiving scene."
        )
    )
    lot_citation: UserFieldCitation | None = None


class OperationsAssistDecision(BaseModel):
    """The only model-authored decision shape accepted at the adapter boundary."""

    answer: str = Field(min_length=1, max_length=1_600)
    missing_information: list[MissingInformation] = Field(default_factory=list, max_length=6)
    physical_draft: PhysicalDraft | None = None
    photo_analysis: PhotoAnalysisRequest | None = None
    intent: Literal["NONE", "PREPARE_ECONOMIC_SPLIT20"] = "NONE"

    @model_validator(mode="after")
    def _one_action_path(self) -> OperationsAssistDecision:
        action_count = sum(
            value is not None for value in (self.physical_draft, self.photo_analysis)
        ) + (self.intent != "NONE")
        if action_count > 1:
            raise ValueError("assistant may return one action path per turn")
        if self.missing_information and (
            self.physical_draft is not None
            or self.photo_analysis is not None
            or self.intent != "NONE"
        ):
            raise ValueError("assistant cannot prepare while information is missing")
        if len({item.field for item in self.missing_information}) != len(self.missing_information):
            raise ValueError("missing information fields must be unique")
        return self


def _copy(value: object) -> Any:
    """Keep values JSON-shaped before sending them to a model/tool boundary."""

    return json.loads(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False))


def _history(projection: Mapping[str, object]) -> tuple[str, list[dict[str, object]]]:
    context = projection.get("_assist_context")
    if not isinstance(context, Mapping):
        raise ValueError("operations assistant lacks its current user turn")
    turn_id = context.get("current_user_turn_id")
    if not isinstance(turn_id, str) or not turn_id:
        raise ValueError("operations assistant lacks its current user turn")
    raw_history = context.get("history")
    if not isinstance(raw_history, list):
        return turn_id, []
    history: list[dict[str, object]] = []
    for item in raw_history[-_MAX_HISTORY_TURNS:]:
        if not isinstance(item, Mapping):
            continue
        candidate = _copy(item)
        if isinstance(candidate, dict):
            history.append(candidate)
    return turn_id, history


def _case_packet(projection: Mapping[str, object]) -> dict[str, object]:
    """Expose current ERP and retained photo observations, never image bytes or internals."""

    fields = (
        "case_id",
        "case_label",
        "purchase_order",
        "synthetic_input",
        "evidence_mode",
        "live_source",
        "quantities",
        "lots",
        "allocations",
        "documents",
        "shipments",
        "alerts",
        "quality_policy",
        "photo_review_card",
        "prepared_proposal",
    )
    packet = {name: _copy(projection[name]) for name in fields if name in projection}
    economic = projection.get("economic_proposal")
    candidates = economic.get("candidates") if isinstance(economic, Mapping) else None
    if isinstance(candidates, list):
        packet["economic_options"] = [
            {
                name: _copy(candidate[name])
                for name in (
                    "candidate_id",
                    "customer_order",
                    "execution_status",
                    "condition",
                    "native_preparation",
                )
                if name in candidate
            }
            for candidate in candidates
            if isinstance(candidate, Mapping)
        ]
    context = projection.get("_assist_context")
    attachment_id = context.get("photo_attachment_id") if isinstance(context, Mapping) else None
    if isinstance(attachment_id, str) and attachment_id:
        packet["pending_photo_attachment_id"] = attachment_id
    return packet


def _model_failure(
    reason: str, *, provider: Mapping[str, object] | None = None
) -> dict[str, object]:
    result: dict[str, object] = {
        "status": "UNAVAILABLE",
        "reason": reason,
        "answer": "The operations assistant is unavailable; no action was prepared.",
        "missing_information": [],
    }
    if provider:
        result["provider"] = _copy(provider)
    return result


def _provider(factory: AgentModelFactory, model: object) -> dict[str, object]:
    observed = actual_provider_metadata(model)
    if observed:
        return _copy(observed)
    provenance = getattr(factory, "provenance", None)
    recorded = provenance() if callable(provenance) else {}
    return _copy(recorded) if isinstance(recorded, Mapping) else {}


def assist_distributor_operations(
    *,
    question: str,
    projection: Mapping[str, object],
    factory: AgentModelFactory,
) -> dict[str, object]:
    """Run one bounded real-model turn without preparing or executing an ERP operation."""

    current_turn_id, history = _history(projection)
    packet = _case_packet(projection)
    case_id = packet.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("operations assistant lacks a case identity")

    async def invoke() -> tuple[object, list[str], dict[str, object]]:
        try:
            from strands import Agent, tool
            from strands.types.agent import Limits
        except ImportError as error:  # pragma: no cover - bootstrap boundary
            raise RuntimeError("strands-agents is unavailable") from error

        calls: list[str] = []

        @tool(
            name=_SOURCE_TOOL,
            description=(
                "Read the complete current, case-scoped distributor ERP evidence and retained "
                "photo observations. The query is a retrieval hint only."
            ),
        )
        def read_current_case(requested_case_id: str) -> str:
            if requested_case_id != case_id:
                return json.dumps(
                    {"status": "NOT_FOUND", "requested_case_id": requested_case_id},
                    sort_keys=True,
                    separators=(",", ":"),
                )
            calls.append(_SOURCE_TOOL)
            return json.dumps(
                {"status": "CURRENT", "case": packet},
                sort_keys=True,
                separators=(",", ":"),
            )

        model = factory.create(stage=AgentStage.SYNTHESIS, output_payload={})
        agent = Agent(
            model=model,
            tools=[read_current_case],
            system_prompt=(
                "You are a distributor receiving and operations assistant. Read the current "
                "case tool before answering. Answer in English. You cannot write, prepare, "
                "approve, execute, release inventory, book money, or claim that a physical "
                "action occurred. Use only current tool evidence and literal human messages. "
                "Unless the newest human explicitly asks for detail or reasoning, keep the "
                "answer under 80 words in two to four short sentences or up to three bullets. "
                "Start with the quantity or status, then the blocker, then the next human "
                "action. Use plain business language: say inspection needed or diameter rather "
                "than internal state codes or technical identifiers. Do not show source IDs, "
                "candidate IDs, internal proposal states, or say 'bottom line' unless the human "
                "asks for implementation details. "
                "Photo observations are advisory only: never infer a count, lot, measurement, "
                "or quality clearance from a photo, including a no-visible-damage observation. "
                "If a physical fact is absent, ask for it specifically. A physical_draft may "
                "contain only arrival or inspection inputs, must omit event_id, and must cite "
                "every operator-declared physical field with its exact user_turn_id and value. "
                "For inspection, cite the lot, scope, metric, measurement, and sample quantity; "
                "the adapter derives PASS or FAIL from the configured criterion. "
                "Only cited human turns can establish a physical measurement, observation, lot, "
                "scope, or inspection result. Prior assistant "
                "answers are not human evidence. Set prepare_requested true only when the newest "
                "human turn explicitly asks to record or prepare the exact declared physical "
                "event. Technical event identifiers, occurrence times, and operator declaration "
                "references are generated by the adapter, so do not require them from the human. "
                "For the configured cleared-twenty economic operation, use "
                "PREPARE_ECONOMIC_SPLIT20 only when the human explicitly asks to prepare it; do "
                "not select or invent another allocation. If pending_photo_attachment_id is "
                "present, photo_analysis may request the existing photo reader only for that "
                "attachment and must select a purpose: label for printed text or identity, detail "
                "for visible condition, damage, or corrosion, and overview for counts or a whole "
                "receiving scene. "
                "When more than one current lot is possible, require a literal human "
                "lot citation; never infer a lot from a photo. Return one action path at most."
            ),
            callback_handler=None,
            retry_strategy=None,
            checkpointing=False,
            agent_id="distributor-operations-assist-v1",
            name="distributor-operations-assist",
        )
        history_json = json.dumps(history, sort_keys=True, separators=(",", ":"))
        prompt = (
            "Read the current case using requested_case_id="
            + case_id
            + ". The newest human turn id is "
            + current_turn_id
            + ". Bounded prior conversation is below. Its `question` values are the only "
            "prior human evidence; missing_information shows what the assistant asked before.\n"
            + history_json
            + "\nNEWEST HUMAN QUESTION:\n"
            + question
        )
        response = await agent.invoke_async(
            prompt,
            structured_output_model=OperationsAssistDecision,
            structured_output_prompt=(
                "Return only OperationsAssistDecision. Use missing_information when evidence "
                "is absent. For a physical_draft, include literal user_field_citations for each "
                "physical input and omit technical generated fields and event_id. Do not return "
                "physical_draft plus missing "
                "information or economic intent."
            ),
            limits=Limits(turns=6, output_tokens=2_048, total_tokens=16_384),
        )
        structured = getattr(response, "structured_output", None)
        metadata = {
            "type": type(response).__name__,
            "stop_reason": str(getattr(response, "stop_reason", None) or ""),
            "structured_output": (
                structured.model_dump(mode="json")
                if isinstance(structured, BaseModel)
                else _copy(structured)
                if structured is not None
                else None
            ),
            "provider": _provider(factory, model),
        }
        return structured, calls, metadata

    started = monotonic()
    try:
        raw, calls, metadata = asyncio.run(invoke())
    except Exception as error:
        return _model_failure(f"MODEL_UNAVAILABLE:{type(error).__name__}")

    provider = metadata.get("provider")
    provider_record = provider if isinstance(provider, Mapping) else {}
    if not calls:
        return _model_failure("MODEL_SOURCE_READ_INCOMPLETE", provider=provider_record)
    try:
        decision = OperationsAssistDecision.model_validate(raw)
        answer = english_product_text(decision.answer, field="operations assistant answer")
    except (ProductLanguageViolation, ValueError, TypeError):
        return _model_failure("MODEL_DECISION_MALFORMED", provider=provider_record)
    usage: dict[str, object] = {"elapsed_ms": round((monotonic() - started) * 1_000)}
    ledger = getattr(factory, "ledger", None)
    if isinstance(ledger, AgentBudgetLedger):
        usage.update(ledger.snapshot())
    return {
        "status": "COMPLETE",
        "answer": answer,
        "missing_information": [
            item.model_dump(mode="json") for item in decision.missing_information
        ],
        "physical_draft": (
            decision.physical_draft.model_dump(mode="json")
            if decision.physical_draft is not None
            else None
        ),
        "photo_analysis": (
            decision.photo_analysis.model_dump(mode="json")
            if decision.photo_analysis is not None
            else None
        ),
        "intent": decision.intent,
        "provider": _copy(provider_record),
        "usage": usage,
    }
