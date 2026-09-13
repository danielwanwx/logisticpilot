"""Small event dispatcher for the configured distributor demonstration cases.

The dispatcher retains operator inputs and their native-operation outcomes in a
local SQLite file.  It delegates ERP reads and writes to the narrowly scoped
``DistributorERP`` adapter.  It never turns a packaging count into stock, or a
Delivery Note or Shipment into proof of customer delivery.
"""

from __future__ import annotations

import base64
import binascii
import json
import math
import sqlite3
from collections.abc import Callable, Mapping
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from inspect import Parameter, signature
from pathlib import Path
from threading import RLock
from typing import Any, Protocol, cast

from the_missing_20.adapters.distributor_allocation import (
    ContractAllocationError,
    compile_plan,
    contract_mode,
    validate_contract_config,
)
from the_missing_20.agents.distributor_economics import (
    DEFER_CANDIDATE_ID,
    SPLIT20_CANDIDATE_ID,
    economic_config_digest,
    economic_gate,
    raw_economic_evidence,
    validate_economic_config,
    validate_selected_candidate,
)
from the_missing_20.agents.distributor_economics import (
    economic_projection as project_economics,
)
from the_missing_20.agents.photo_receiving import (
    PhotoAssessment,
    PhotoDetailAssessment,
    PhotoLabelAssessment,
    PhotoPurpose,
    normalize_photo,
)

DISTRIBUTOR_OPERATIONS_SCHEMA_VERSION = "missing20-distributor-operations/v1"
_SUCCESS = frozenset({"APPLIED", "ALREADY_APPLIED"})
_WRITE_STATUSES = _SUCCESS | frozenset({"UNKNOWN_OUTCOME", "BLOCKED"})
_EVENT_BRIEF_FIELDS: dict[str, tuple[str, ...]] = {
    "arrival": (
        "cartons",
        "expected_pack_quantity",
        "observed_stock_quantity",
        "item_code",
        "lot",
    ),
    "inspection": (
        "lot",
        "result",
        "scope",
        "metric",
        "measured",
        "sample_quantity",
        "inspection_report_ref",
    ),
    "picked": ("customer_order", "lot", "quantity", "pick_evidence_ref"),
    "carrier_pickup": ("shipment_id",),
    "delivery": ("shipment_id",),
}


class DistributorERP(Protocol):
    """The one small native ERP boundary used by the operations dispatcher."""

    def read_case(self, config: Mapping[str, object]) -> Mapping[str, object]: ...

    def apply_operation(
        self, config: Mapping[str, object], operation: Mapping[str, object], event_id: str
    ) -> Mapping[str, object]: ...


class DistributorEventConflict(ValueError):
    """An event ID was replayed with a different declared physical input."""


class _NativeOutcome:
    def __init__(
        self,
        *,
        kind: str,
        status: str,
        documents: list[dict[str, object]],
        error_code: str | None,
    ) -> None:
        self.kind = kind
        self.status = status
        self.documents = documents
        self.error_code = error_code

    @property
    def succeeded(self) -> bool:
        return self.status in _SUCCESS

    def record(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "status": self.status,
            "documents": _copy(self.documents),
            "error_code": self.error_code,
        }


def _copy(value: object) -> Any:
    """Detach a strict JSON value; reject non-finite or non-JSON inputs."""

    return json.loads(_encode(value))


def _json_value(value: object) -> object:
    if isinstance(value, Mapping):
        result: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON mapping keys must be strings")
            result[key] = _json_value(item)
        return result
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        return value
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    raise ValueError(f"unsupported JSON value: {type(value).__name__}")


def _encode(value: object) -> str:
    return json.dumps(_json_value(value), sort_keys=True, separators=(",", ":"), allow_nan=False)


def _decoded(value: str, label: str) -> dict[str, object]:
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as error:  # pragma: no cover - corrupt local store only
        raise RuntimeError(f"corrupt distributor operations {label}") from error
    if not isinstance(decoded, dict):  # pragma: no cover - corrupt local store only
        raise RuntimeError(f"corrupt distributor operations {label}")
    return cast(dict[str, object], _json_value(decoded))


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > 256:
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _quantity(value: object, label: str, *, positive: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a JSON number")
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError(f"{label} must be a JSON number") from error
    if not result.is_finite() or result < 0 or (positive and result <= 0):
        raise ValueError(f"{label} must be {'positive' if positive else 'non-negative'}")
    return result


def _whole(value: object, label: str, *, positive: bool = False) -> int:
    quantity = _quantity(value, label, positive=positive)
    if quantity != quantity.to_integral_value():
        raise ValueError(f"{label} must be a whole number")
    return int(quantity)


def _wire(value: Decimal) -> int | float:
    return int(value) if value == value.to_integral_value() else float(value)


def _utc(value: object, label: str) -> str:
    text = _text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{label} must be an ISO-8601 time with timezone") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must be an ISO-8601 time with timezone")
    return parsed.astimezone(UTC).isoformat()


def _deadline(value: object, label: str) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(_utc(value, label))


def _documents(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    records: list[dict[str, object]] = []
    for raw in value:
        if not isinstance(raw, Mapping):
            continue
        kind = raw.get("kind")
        name = raw.get("name")
        status = raw.get("status")
        if not (
            isinstance(kind, str)
            and kind.strip()
            and isinstance(name, str)
            and name.strip()
            and isinstance(status, str)
            and status.strip()
        ):
            continue
        record: dict[str, object] = {
            "kind": kind.strip(),
            "name": name.strip(),
            "status": status.strip(),
        }
        url = raw.get("url")
        if isinstance(url, str) and url.strip():
            record["url"] = url.strip()
        records.append(record)
    return records


def _merge_documents(*groups: list[dict[str, object]]) -> list[dict[str, object]]:
    by_identity: dict[tuple[str, str], dict[str, object]] = {}
    for group in groups:
        for document in group:
            kind = document.get("kind")
            name = document.get("name")
            if isinstance(kind, str) and isinstance(name, str):
                by_identity[(kind, name)] = dict(document)
    return [by_identity[key] for key in sorted(by_identity)]


class DistributorOperations:
    """Serialize one configured case's physical events and native terminal effects.

    A bridge call is never retried by this class after an ``UNKNOWN_OUTCOME``.
    The local lock is intentionally one operator/runtime lock rather than a
    distributed workflow protocol.
    """

    def __init__(
        self,
        database: Path,
        config: Mapping[str, object],
        erp: DistributorERP | None,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        ask_turn: Callable[[str, Mapping[str, object]], Mapping[str, object]] | None = None,
        allocation_selector: Callable[[Mapping[str, object]], Mapping[str, object]] | None = None,
        economic_selector: Callable[[Mapping[str, object]], Mapping[str, object]] | None = None,
        photo_reader: Callable[..., Mapping[str, object]] | None = None,
        retained_projection: bool = False,
    ) -> None:
        self._config = self._validate_config(config)
        self._erp = erp
        self._clock = clock
        self._ask_turn = ask_turn
        self._allocation_selector = allocation_selector
        self._economic_selector = economic_selector
        self._photo_reader = photo_reader
        self._economic_last_result: dict[str, object] | None = None
        self._economic_prepare_authorization: tuple[str, str] | None = None
        self._retained_projection = retained_projection
        database.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(
            database, check_same_thread=False, isolation_level=None, timeout=10
        )
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS distributor_operation_events "
            "(event_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL, result_json TEXT, "
            "state_json TEXT, recorded_at TEXT NOT NULL)"
        )
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS distributor_allocation_retries "
            "(retry_id TEXT PRIMARY KEY, pending_event_id TEXT NOT NULL, result_json TEXT, "
            "state_json TEXT, recorded_at TEXT NOT NULL)"
        )
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS distributor_operation_proposals "
            "(proposal_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, event_json TEXT NOT NULL, "
            "source TEXT NOT NULL, attachment_id TEXT, state_revision TEXT NOT NULL, "
            "result_json TEXT, manager_id TEXT, approved_at TEXT, recorded_at TEXT NOT NULL)"
        )
        for column in ("manager_id TEXT", "approved_at TEXT"):
            with suppress(sqlite3.OperationalError):
                self._db.execute(f"ALTER TABLE distributor_operation_proposals ADD COLUMN {column}")
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS distributor_operation_attachments "
            "(attachment_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, media_type TEXT NOT NULL, "
            "image BLOB NOT NULL, digest TEXT NOT NULL, proposal_id TEXT, event_id TEXT, "
            "recorded_at TEXT NOT NULL, analysis_json TEXT)"
        )
        with suppress(sqlite3.OperationalError):
            self._db.execute(
                "ALTER TABLE distributor_operation_attachments ADD COLUMN analysis_json TEXT"
            )
        self._lock = RLock()

    @property
    def retained_projection(self) -> bool:
        """Whether this instance serves durable evidence without live ERP reads."""

        return self._retained_projection

    @property
    def photo_analysis_enabled(self) -> bool:
        """Whether this configured operation has an explicitly injected real photo reader."""

        return self._photo_reader is not None

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def projection(self) -> dict[str, object]:
        """Return a current read-only projection; a source poll never writes."""

        with self._lock:
            if self._retained_projection:
                state, retained_at = self._latest_state_with_recorded_at()
                return self._projection(
                    state or self._initial_state(),
                    {"source_status": "RETAINED"},
                    retained_at=retained_at,
                )
            source = self._read_source()
            state = self._latest_state() or self._initial_state()
            state, source = self._merge_source(state, source)
            return self._projection(state, source)

    def economic_projection(self) -> dict[str, object] | None:
        """Return optional trusted postage evidence and non-executing candidates."""

        if self._config.get("economic_proposal") is None:
            return None
        with self._lock:
            if self._retained_projection:
                state = self._latest_state() or self._initial_state()
                source: Mapping[str, object] = {
                    "source_status": "RETAINED",
                    "quantities": state.get("quantities", {}),
                    "lots": state.get("lots", []),
                    "allocations": state.get("allocations", []),
                }
            else:
                source = self._read_source()
                state = self._latest_state() or self._initial_state()
                state, source = self._merge_source(state, source)
            return self._economic_view(
                self._economic_operational_snapshot(state, source), self._economic_last_result
            )

    def prepare_economic_proposal(self, request: Mapping[str, object]) -> dict[str, object]:
        """Compare raw evidence, then optionally prepare the exact split-20 picked event.

        A selection is an operator input, never a substitute for the model trace or
        deterministic source gate.  The comparison path deliberately accepts no
        selection and returns DEFER when model evidence is absent or malformed.
        """

        if self._config.get("economic_proposal") is None:
            raise ValueError("economic proposal is not configured")
        if set(request) - {"case_id", "selected_candidate_id"} or "case_id" not in request:
            raise ValueError(
                "economic proposal requires case_id and optional selected_candidate_id"
            )
        if _text(request.get("case_id"), "economic case_id") != self._config["case_id"]:
            raise ValueError("economic proposal case does not match the configured operation")
        selected_raw = request.get("selected_candidate_id")
        candidate_id = (
            _text(selected_raw, "selected_candidate_id") if selected_raw is not None else None
        )
        self._require_live_operations()
        with self._lock:
            source = self._read_source()
            state = self._latest_state() or self._initial_state()
            state, source = self._merge_source(state, source)
            snapshot = self._economic_operational_snapshot(state, source)
            evidence = raw_economic_evidence(self._config, snapshot)
            configured = cast(Mapping[str, object], self._config["economic_proposal"])
            if configured.get("model_enabled") is True:
                selector = self._economic_selector
                try:
                    raw_selection: Mapping[str, object] = (
                        selector(evidence)
                        if selector is not None
                        else {
                            "status": "DEFER",
                            "candidate_id": DEFER_CANDIDATE_ID,
                            "reason": "MODEL_SELECTOR_UNAVAILABLE",
                            "tool_trace": [],
                            "model_response": None,
                            "citations": [],
                        }
                    )
                except Exception as error:
                    raw_selection = {
                        "status": "DEFER",
                        "candidate_id": DEFER_CANDIDATE_ID,
                        "reason": "MODEL_SELECTOR_UNAVAILABLE",
                        "error_type": type(error).__name__,
                        "tool_trace": [],
                        "model_response": None,
                        "citations": [],
                    }
                selector_result = validate_selected_candidate(raw_selection, evidence=evidence)
            else:
                selector_result = {
                    "status": "not_run",
                    "candidate_id": None,
                    "reason": "MODEL_DISABLED",
                    "tool_trace": [],
                    "model_response": None,
                    "citations": [],
                }
            gate = (
                economic_gate(self._config, snapshot, now=self._now(), candidate_id=candidate_id)
                if candidate_id is not None
                else {
                    "allowed": False,
                    "candidate_id": None,
                    "reasons": ["NO_CANDIDATE_SELECTED"],
                    "checked_at": self._now().isoformat(),
                }
            )
            economic = self._economic_result(
                candidate_id=candidate_id,
                snapshot=snapshot,
                selector_result=selector_result,
                gate=gate,
            )
            self._economic_last_result = economic
            if candidate_id != SPLIT20_CANDIDATE_ID or gate.get("allowed") is not True:
                projection = self._projection(state, source)
                projection["economic_proposal"] = self._economic_view(snapshot, economic)
                return {"economic_proposal": economic, "projection": projection}
            event = gate.get("event")
            if not isinstance(event, Mapping):  # pragma: no cover - economic_gate owns this
                raise RuntimeError("economic gate did not retain its exact event")
            event_id = _text(event.get("event_id"), "economic picked event_id")
            proposal_id = self._economic_proposal_id(event_id)
            self._economic_prepare_authorization = (proposal_id, event_id)
            try:
                prepared = self.prepare_event_proposal(
                    {
                        "proposal_id": proposal_id,
                        "case_id": self._config["case_id"],
                        "event": event,
                        "source": "ECONOMIC_RECOMMENDATION",
                    }
                )
            finally:
                self._economic_prepare_authorization = None
            prepared_proposal = prepared.get("prepared_proposal")
            if isinstance(prepared_proposal, Mapping):
                economic["prepared_proposal_id"] = prepared_proposal.get("proposal_id")
                economic["prepared_state_revision"] = prepared_proposal.get("state_revision")
            self._economic_last_result = economic
            projection = cast(dict[str, object], _copy(prepared))
            projection["economic_proposal"] = self._economic_view(snapshot, economic)
            return {
                "economic_proposal": economic,
                **(
                    {"prepared_proposal": _copy(prepared_proposal)}
                    if isinstance(prepared_proposal, Mapping)
                    else {}
                ),
                "projection": projection,
            }

    def record_event(self, event: Mapping[str, object]) -> dict[str, object]:
        """Retain one physical event and run only its allowed native consequences."""

        self._require_live_operations()
        validated = self._validate_event(event)
        event_id = cast(str, validated["event_id"])
        encoded = _encode(validated)
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                row = self._db.execute(
                    "SELECT payload_json, result_json FROM distributor_operation_events "
                    "WHERE event_id=?",
                    (event_id,),
                ).fetchone()
                if row is not None:
                    stored_payload, stored_result = cast(tuple[str, str | None], row)
                    if stored_payload != encoded:
                        raise DistributorEventConflict(
                            "A duplicate distributor event ID has different input."
                        )
                    self._db.commit()
                    if stored_result is not None:
                        return self._projection_from_record(stored_result)
                    return self._pending_projection(event_id)
                self._db.execute(
                    "INSERT INTO distributor_operation_events "
                    "(event_id, payload_json, result_json, state_json, recorded_at) "
                    "VALUES (?, ?, NULL, NULL, ?)",
                    (event_id, encoded, self._next_recorded_at()),
                )
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise

            source = self._read_source()
            state = self._latest_state() or self._initial_state()
            state, source = self._merge_source(state, source)
            try:
                next_state, event_status = self._advance(state, validated, source)
            except Exception:  # pragma: no cover - defensive local persistence boundary
                next_state = _copy(state)
                self._alert(
                    next_state,
                    code="LOCAL_OPERATION_UNAVAILABLE",
                    message="The event was retained, but no additional native action was started.",
                    event=validated,
                )
                event_status = "UNKNOWN_OUTCOME"
                self._append_event(next_state, validated, event_status, [])
            else:
                if event_status == "APPLIED" and validated["type"] in {"arrival", "picked"}:
                    self._resume_blocked_shipment(next_state, validated)
            projection = self._projection(next_state, source)
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._db.execute(
                    "UPDATE distributor_operation_events SET result_json=?, state_json=? "
                    "WHERE event_id=?",
                    (_encode(projection), _encode(next_state), event_id),
                )
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise
            return projection

    def attach_photo(self, request: Mapping[str, object]) -> dict[str, object]:
        """Retain a manual same-case photo without interpreting its contents.

        The attachment is evidence for a later operator-declared event.  It is
        deliberately not a count, identity, inspection, or model conclusion.
        """

        self._require_live_operations()
        if set(request) != {"attachment_id", "image", "media_type"}:
            raise ValueError("photo attachment accepts attachment_id, image, and media_type only")
        attachment_id = _text(request.get("attachment_id"), "attachment_id")
        media_type = _text(request.get("media_type"), "media_type").lower()
        raw_image = request.get("image")
        if media_type not in {"image/jpeg", "image/png"} or not isinstance(raw_image, str):
            raise ValueError("photo attachment must be a JPEG or PNG image")
        try:
            image = base64.b64decode(raw_image.encode("ascii"), validate=True)
        except (UnicodeEncodeError, binascii.Error) as error:
            raise ValueError("photo attachment image must be base64") from error
        if not image or len(image) > 5_000_000:
            raise ValueError("photo attachment must be between 1 byte and 5 MB")
        signatures = {
            "image/jpeg": b"\xff\xd8\xff",
            "image/png": b"\x89PNG\r\n\x1a\n",
        }
        if not image.startswith(signatures[media_type]):
            raise ValueError("photo attachment media type does not match image bytes")
        digest = sha256(image).hexdigest()
        with self._lock:
            existing = self._db.execute(
                "SELECT case_id, media_type, digest FROM distributor_operation_attachments "
                "WHERE attachment_id=?",
                (attachment_id,),
            ).fetchone()
            if existing is not None:
                case_id, stored_type, stored_digest = cast(tuple[str, str, str], existing)
                if (case_id, stored_type, stored_digest) != (
                    self._config["case_id"],
                    media_type,
                    digest,
                ):
                    raise DistributorEventConflict(
                        "A duplicate photo attachment ID has different input."
                    )
            else:
                self._db.execute(
                    "INSERT INTO distributor_operation_attachments "
                    "(attachment_id, case_id, media_type, image, digest, proposal_id, "
                    "event_id, recorded_at) "
                    "VALUES (?, ?, ?, ?, ?, NULL, NULL, ?)",
                    (
                        attachment_id,
                        self._config["case_id"],
                        media_type,
                        image,
                        digest,
                        self._next_recorded_at(),
                    ),
                )
            projection = self.projection()
            projection["latest_photo_attachment"] = self._attachment_metadata(attachment_id)
            return projection

    def photo(self, attachment_id: str) -> tuple[bytes, str]:
        """Return only a photo attached to this configured case."""

        identifier = _text(attachment_id, "attachment_id")
        with self._lock:
            row = self._db.execute(
                "SELECT image, media_type FROM distributor_operation_attachments "
                "WHERE attachment_id=? AND case_id=?",
                (identifier, self._config["case_id"]),
            ).fetchone()
            if row is None:
                raise ValueError("photo attachment is unavailable for this case")
            image, media_type = cast(tuple[bytes, str], row)
            return image, media_type

    def analyze_photo(self, request: Mapping[str, object]) -> dict[str, object]:
        """Read one retained photo as advisory evidence without creating an event or stock write."""

        allowed = {"attachment_id", "lot", "purpose", "supersedes_attachment_id"}
        if set(request) - allowed or "attachment_id" not in request:
            raise ValueError(
                "photo analysis requires attachment_id and optional lot, purpose, "
                "and supersedes_attachment_id"
            )
        reader = self._photo_reader
        if reader is None:
            raise ValueError("operations photo analysis is not enabled")
        self._require_live_operations()
        attachment_id = _text(request.get("attachment_id"), "attachment_id")
        purpose = self._photo_purpose(request.get("purpose"))
        requested_lot = (
            _text(request.get("lot"), "photo analysis lot")
            if request.get("lot") is not None
            else None
        )
        supersedes_attachment_id = (
            _text(request.get("supersedes_attachment_id"), "supersedes_attachment_id")
            if request.get("supersedes_attachment_id") is not None
            else None
        )
        with self._lock:
            row = self._db.execute(
                "SELECT image, digest FROM distributor_operation_attachments "
                "WHERE attachment_id=? AND case_id=?",
                (attachment_id, self._config["case_id"]),
            ).fetchone()
            if row is None:
                raise ValueError("photo attachment is unavailable for this case")
            image, digest = cast(tuple[bytes, str], row)
            source = self._read_source()
            state = self._latest_state() or self._initial_state()
            state, source = self._merge_source(state, source)
            source_revision = self._source_revision(source)
            linked_lot = self._analysis_lot(source, requested_lot)
            linked_quantity = (
                _wire(_quantity(linked_lot["received"], "linked lot received"))
                if linked_lot is not None
                else None
            )
            lot_name = _text(linked_lot["lot"], "linked photo lot") if linked_lot else None
            self._validate_photo_supersession(
                attachment_id,
                supersedes_attachment_id,
                lot_name,
            )
            if source.get("source_status") != "CURRENT" or source_revision is None:
                analysis = self._unavailable_photo_analysis(
                    digest=digest,
                    source_revision=None,
                    linked_lot=lot_name,
                    linked_quantity=linked_quantity,
                    purpose=purpose,
                    supersedes_attachment_id=supersedes_attachment_id,
                    message="Current ERP evidence is unavailable; photo analysis can be retried.",
                )
                self._store_photo_analysis(attachment_id, analysis)
                return self._projection(state, source)
            reader_model_id = self._photo_reader_model_id(reader)
            cached = self._cached_photo_analysis(
                digest=digest,
                source_revision=source_revision,
                linked_lot=lot_name,
                reader_model_id=reader_model_id,
                purpose=purpose,
            )
            if cached is not None:
                self._store_photo_analysis(
                    attachment_id,
                    self._with_photo_supersession(cached, supersedes_attachment_id),
                )
                return self._projection(state, source)
            try:
                # The reader receives normalized pixels and the requested view purpose only.
                # Attachment IDs, filenames and operator-entered lot information never reach it.
                result = self._read_photo(reader, normalize_photo(image), purpose)
                analysis = self._complete_photo_analysis(
                    result,
                    digest=digest,
                    source_revision=source_revision,
                    linked_lot=linked_lot,
                    linked_quantity=linked_quantity,
                    reader_model_id=reader_model_id,
                    purpose=purpose,
                    supersedes_attachment_id=supersedes_attachment_id,
                    source=source,
                )
            except Exception:
                analysis = self._unavailable_photo_analysis(
                    digest=digest,
                    source_revision=source_revision,
                    linked_lot=lot_name,
                    linked_quantity=linked_quantity,
                    purpose=purpose,
                    supersedes_attachment_id=supersedes_attachment_id,
                    message="Photo analysis was unavailable; retry the same attachment when ready.",
                )
            self._store_photo_analysis(attachment_id, analysis)
            return self._projection(state, source)

    def prepare_event_proposal(self, request: Mapping[str, object]) -> dict[str, object]:
        """Store a non-mutating, source-fresh proposal for manager review."""

        self._require_live_operations()
        allowed = {"proposal_id", "case_id", "event", "source", "photo_attachment_id"}
        if set(request) - allowed or not {"proposal_id", "case_id", "event", "source"}.issubset(
            request
        ):
            raise ValueError(
                "proposal requires proposal_id, case_id, event, source, and optional "
                "photo_attachment_id"
            )
        proposal_id = _text(request.get("proposal_id"), "proposal_id")
        case_id = _text(request.get("case_id"), "case_id")
        if case_id != self._config["case_id"]:
            raise ValueError("proposal case does not match the configured operation")
        source = _text(request.get("source"), "proposal source")
        if source not in {
            "OPERATOR_DECLARED",
            "RETAINED_ALLOCATION_RECOMMENDATION",
            "ECONOMIC_RECOMMENDATION",
        }:
            raise ValueError("proposal source is not supported")
        raw_event = request.get("event")
        if not isinstance(raw_event, Mapping):
            raise ValueError("proposal event must be an object")
        event = self._validate_event(raw_event)
        if source == "ECONOMIC_RECOMMENDATION":
            authorized = self._economic_prepare_authorization
            if authorized != (proposal_id, _text(event.get("event_id"), "economic event_id")):
                raise ValueError(
                    "economic proposals must be prepared through the economic evidence gate"
                )
        attachment_id = request.get("photo_attachment_id")
        if attachment_id is not None:
            attachment_id = _text(attachment_id, "photo_attachment_id")
        encoded_event = _encode(event)
        with self._lock:
            source_facts = self._read_source()
            state = self._latest_state() or self._initial_state()
            state, source_facts = self._merge_source(state, source_facts)
            if source_facts["source_status"] != "CURRENT":
                raise ValueError("current ERP evidence is unavailable; no proposal can be prepared")
            revision = self._proposal_revision(state, source_facts)
            existing = self._db.execute(
                "SELECT case_id, event_json, source, attachment_id, state_revision, result_json, "
                "manager_id, approved_at "
                "FROM distributor_operation_proposals WHERE proposal_id=?",
                (proposal_id,),
            ).fetchone()
            if existing is not None:
                (
                    stored_case,
                    stored_event,
                    stored_source,
                    stored_attachment,
                    stored_revision,
                    stored_result,
                    stored_manager,
                    stored_approved_at,
                ) = cast(
                    tuple[str, str, str, str | None, str, str | None, str | None, str | None],
                    existing,
                )
                if (stored_case, stored_event, stored_source, stored_attachment) != (
                    case_id,
                    encoded_event,
                    source,
                    attachment_id,
                ):
                    raise DistributorEventConflict("A duplicate proposal ID has different input.")
                proposal = self._proposal_record(
                    proposal_id,
                    stored_revision,
                    event,
                    source,
                    attachment_id,
                    stored_result,
                    stored_manager,
                    stored_approved_at,
                )
                return self._with_proposal(self._projection(state, source_facts), proposal)
            if attachment_id is not None:
                self._require_unbound_attachment(attachment_id)
            self._db.execute(
                "INSERT INTO distributor_operation_proposals "
                "(proposal_id, case_id, event_json, source, attachment_id, state_revision, "
                "result_json, recorded_at) "
                "VALUES (?, ?, ?, ?, ?, ?, NULL, ?)",
                (
                    proposal_id,
                    case_id,
                    encoded_event,
                    source,
                    attachment_id,
                    revision,
                    self._next_recorded_at(),
                ),
            )
            if attachment_id is not None:
                self._db.execute(
                    "UPDATE distributor_operation_attachments SET proposal_id=? "
                    "WHERE attachment_id=?",
                    (proposal_id, attachment_id),
                )
            proposal = self._proposal_record(
                proposal_id, revision, event, source, attachment_id, None, None, None
            )
            return self._with_proposal(self._projection(state, source_facts), proposal)

    def approve_event_proposal(self, request: Mapping[str, object]) -> dict[str, object]:
        """Apply one prepared proposal exactly once after an explicit manager decision."""

        if set(request) != {"proposal_id", "case_id", "state_revision", "manager_id"}:
            raise ValueError(
                "approval requires proposal_id, case_id, state_revision, and manager_id"
            )
        proposal_id = _text(request.get("proposal_id"), "proposal_id")
        case_id = _text(request.get("case_id"), "case_id")
        revision = _text(request.get("state_revision"), "state_revision")
        manager_id = _text(request.get("manager_id"), "manager_id")
        if case_id != self._config["case_id"]:
            raise ValueError("approval case does not match the configured operation")
        with self._lock:
            row = self._db.execute(
                "SELECT event_json, source, attachment_id, state_revision, result_json, "
                "manager_id, approved_at "
                "FROM distributor_operation_proposals WHERE proposal_id=? AND case_id=?",
                (proposal_id, case_id),
            ).fetchone()
            if row is None:
                raise ValueError("prepared proposal is unavailable for this case")
            (
                event_json,
                source,
                attachment_id,
                stored_revision,
                stored_result,
                stored_manager,
                stored_approved_at,
            ) = cast(tuple[str, str, str | None, str, str | None, str | None, str | None], row)
            event = _decoded(event_json, "proposal event")
            event_status = self._stored_event_status(event)
            if stored_result is not None:
                approval = self._approval_from_record(stored_result)
                recorded_manager = approval.get("manager_id")
                recorded_at = approval.get("approved_at")
                prior_manager = recorded_manager if isinstance(recorded_manager, str) else None
                prior_approved_at = recorded_at if isinstance(recorded_at, str) else None
                return self._confirmation_projection(
                    proposal_id=proposal_id,
                    case_id=case_id,
                    event=event,
                    source=source,
                    attachment_id=attachment_id,
                    state_revision=stored_revision,
                    manager_id=stored_manager or prior_manager or manager_id,
                    approved_at=stored_approved_at or prior_approved_at,
                    recovered=approval.get("recovered") is True,
                    event_status=event_status or "UNKNOWN_OUTCOME",
                )
            if event_status is not None:
                approved_at = stored_approved_at or self._next_recorded_at()
                recorded_manager = stored_manager or manager_id
                result = self._confirmation_projection(
                    proposal_id=proposal_id,
                    case_id=case_id,
                    event=event,
                    source=source,
                    attachment_id=attachment_id,
                    state_revision=stored_revision,
                    manager_id=recorded_manager,
                    approved_at=approved_at,
                    recovered=True,
                    event_status=event_status,
                )
                self._db.execute(
                    "UPDATE distributor_operation_proposals SET result_json=?, manager_id=?, "
                    "approved_at=? "
                    "WHERE proposal_id=?",
                    (_encode(result), recorded_manager, approved_at, proposal_id),
                )
                return result
            self._require_live_operations()
            if stored_revision != revision:
                raise ValueError(
                    "proposal revision is stale; review the current case before approval"
                )
            source_facts = self._read_source()
            state = self._latest_state() or self._initial_state()
            state, source_facts = self._merge_source(state, source_facts)
            if (
                source_facts["source_status"] != "CURRENT"
                or self._proposal_revision(state, source_facts) != revision
            ):
                raise ValueError("proposal is stale; current ERP evidence changed before approval")
            if source == "ECONOMIC_RECOMMENDATION":
                economic_gate_result = economic_gate(
                    self._config,
                    self._economic_operational_snapshot(state, source_facts),
                    now=self._now(),
                    candidate_id=SPLIT20_CANDIDATE_ID,
                    event=event,
                )
                if economic_gate_result.get("allowed") is not True:
                    raise ValueError(
                        "economic proposal no longer satisfies current contract, stock, quality, "
                        "time, or physical-fit evidence"
                    )
            event_result = self.record_event(event)
            event_status = self._event_status_from_projection(
                event_result,
                _text(event.get("event_id"), "proposal event_id"),
            )
            approved_at = self._next_recorded_at()
            if attachment_id is not None:
                self._db.execute(
                    "UPDATE distributor_operation_attachments SET event_id=? "
                    "WHERE attachment_id=? AND proposal_id=?",
                    (event["event_id"], attachment_id, proposal_id),
                )
            result = self._confirmation_projection(
                proposal_id=proposal_id,
                case_id=case_id,
                event=event,
                source=source,
                attachment_id=attachment_id,
                state_revision=revision,
                manager_id=manager_id,
                approved_at=approved_at,
                recovered=False,
                event_status=event_status,
            )
            self._db.execute(
                "UPDATE distributor_operation_proposals SET result_json=?, manager_id=?, "
                "approved_at=? "
                "WHERE proposal_id=? AND result_json IS NULL",
                (_encode(result), manager_id, approved_at, proposal_id),
            )
            return result

    @staticmethod
    def _approval_from_record(record: str) -> dict[str, object]:
        """Recover only durable approval metadata from a prior confirmation response."""

        projection = _decoded(record, "proposal result")
        approval = projection.get("approval_evidence")
        return dict(approval) if isinstance(approval, Mapping) else {}

    def _stored_event_status(self, event: Mapping[str, object]) -> str | None:
        """Return a completed event's durable status without assuming success."""

        event_id = _text(event.get("event_id"), "proposal event_id")
        row = self._db.execute(
            "SELECT payload_json, result_json FROM distributor_operation_events WHERE event_id=?",
            (event_id,),
        ).fetchone()
        if row is None:
            return None
        stored_payload, stored_result = cast(tuple[str, str | None], row)
        if stored_payload != _encode(event):
            raise DistributorEventConflict("A duplicate distributor event ID has different input.")
        if stored_result is None:
            return None
        projection = _decoded(stored_result, "event result")
        return self._event_status_from_projection(projection, event_id)

    @staticmethod
    def _event_status_from_projection(projection: Mapping[str, object], event_id: str) -> str:
        """Read one persisted event result, failing closed when its status is absent."""

        events = projection.get("events")
        if not isinstance(events, list):
            return "UNKNOWN_OUTCOME"
        for row in events:
            if not isinstance(row, Mapping) or row.get("event_id") != event_id:
                continue
            status = row.get("status")
            if isinstance(status, str) and status.strip():
                return status.strip()
            return "UNKNOWN_OUTCOME"
        return "UNKNOWN_OUTCOME"

    def _confirmation_projection(
        self,
        *,
        proposal_id: str,
        case_id: str,
        event: Mapping[str, object],
        source: str,
        attachment_id: str | None,
        state_revision: str,
        manager_id: str,
        approved_at: str | None,
        recovered: bool,
        event_status: str,
    ) -> dict[str, object]:
        """Return the latest case state while retaining the confirmed event's own time.

        A manager can confirm a completion recorded earlier than later case events.
        The response must show the latest projection rather than reviving that old
        projection, while retaining the earlier event's record time separately.
        """

        event_id = _text(event.get("event_id"), "proposal event_id")
        row = self._db.execute(
            "SELECT recorded_at FROM distributor_operation_events WHERE event_id=?",
            (event_id,),
        ).fetchone()
        event_recorded_at = row[0] if row is not None and isinstance(row[0], str) else None
        result = self.projection()
        approval: dict[str, object] = {
            "proposal_id": proposal_id,
            "case_id": case_id,
            "manager_id": manager_id,
            "source": source,
            "event_id": event_id,
        }
        if approved_at is not None:
            approval["approved_at"] = approved_at
        if recovered:
            approval["recovered"] = True
        result["approval_evidence"] = approval
        result["historical_confirmation"] = {
            "event_id": event_id,
            "event_occurred_at": event.get("occurred_at"),
            "event_recorded_at": event_recorded_at,
            "confirmed_at": approved_at,
            "source": source,
            "recovered": recovered,
            "event_status": event_status,
        }
        result["prepared_proposal"] = {
            "proposal_id": proposal_id,
            "case_id": case_id,
            "purchase_order": self._config["purchase_order"],
            "event": _copy(event),
            "source": source,
            "photo_attachment_id": attachment_id,
            "state_revision": state_revision,
            "status": event_status,
            "approval": {"manager_id": manager_id, "approved_at": approved_at},
        }
        return result

    def retry_pending_allocation(self, request: Mapping[str, object]) -> dict[str, object]:
        """Re-evaluate one retained pending allocation without replaying a physical event.

        The retry row is durable before selector or ERP work starts. Replaying its
        ``retry_id`` returns the completed result and never starts another native
        prepare-pick call.
        """

        self._require_live_operations()
        if set(request) != {"retry_id", "pending_event_id"}:
            raise ValueError("retry accepts only retry_id and pending_event_id")
        retry_id = _text(request.get("retry_id"), "retry_id")
        pending_event_id = _text(request.get("pending_event_id"), "pending_event_id")
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                existing = self._db.execute(
                    "SELECT pending_event_id, result_json FROM distributor_allocation_retries "
                    "WHERE retry_id=?",
                    (retry_id,),
                ).fetchone()
                if existing is not None:
                    stored_pending, stored_result = cast(tuple[str, str | None], existing)
                    if stored_pending != pending_event_id:
                        raise DistributorEventConflict(
                            "A duplicate allocation retry ID has different input."
                        )
                    self._db.commit()
                    if stored_result is not None:
                        return self._projection_from_record(stored_result)
                    return self._pending_allocation_retry_projection(retry_id)

                retained = self._latest_state()
                if retained is None:
                    raise ValueError("No retained allocation decision can be retried.")
                decision = retained.get("allocation_decision")
                if not (
                    isinstance(decision, Mapping)
                    and decision.get("status") == "PENDING"
                    and decision.get("event_id") == pending_event_id
                ):
                    raise ValueError("The requested allocation decision is not pending.")
                self._db.execute(
                    "INSERT INTO distributor_allocation_retries "
                    "(retry_id, pending_event_id, result_json, state_json, recorded_at) "
                    "VALUES (?, ?, NULL, NULL, ?)",
                    (retry_id, pending_event_id, self._next_recorded_at()),
                )
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise

            source = self._read_source()
            state = self._latest_state() or self._initial_state()
            state, source = self._merge_source(state, source)
            event = self._allocation_retry_event(state, retry_id, pending_event_id)
            action = self._append_allocation_retry(state, retry_id, pending_event_id)
            if source["source_status"] != "CURRENT":
                self._alert(
                    state,
                    code="SOURCE_UNAVAILABLE",
                    message="Current ERP evidence is unavailable; no native operation was started.",
                    event=event,
                    error_code=cast(str, source.get("source_error") or "ERP_SOURCE_UNAVAILABLE"),
                )
                action.update(
                    {"status": "UNAVAILABLE", "reason": "ERP_SOURCE_UNAVAILABLE", "operations": []}
                )
                return self._complete_allocation_retry(retry_id, state, source)

            self._recompute_allocations(state)
            plan = self._contract_plan(state)
            action.update(
                {
                    "plan_id": plan["plan_id"],
                    "state_revision": plan["state_revision"],
                    "plan_rows": _copy(plan["rows"]),
                }
            )
            if _quantity(plan["new_quantity"], "contract plan new quantity") <= 0:
                action.update(
                    {
                        "status": "BLOCKED",
                        "reason": "NO_EXECUTABLE_DISPATCH_CANDIDATE",
                        "operations": [],
                    }
                )
                return self._complete_allocation_retry(retry_id, state, source)
            if self._contract_plan_native_tranches(plan, state) is None:
                action.update(
                    {
                        "status": "BLOCKED",
                        "reason": "ALLOCATION_PLAN_NATIVE_TRANCHE_UNSUPPORTED",
                        "operations": [],
                    }
                )
                return self._complete_allocation_retry(retry_id, state, source)

            outcomes = self._prepare_pick(
                state,
                event,
                resolve_pending_event_id=pending_event_id,
                retry_id=retry_id,
            )
            action["operations"] = [outcome.record() for outcome in outcomes]
            decision = state.get("allocation_decision")
            if isinstance(decision, Mapping) and decision.get("status") == "PENDING":
                action.update({"status": "PENDING", "reason": "ALLOCATION_SELECTION_PENDING"})
            elif outcomes and all(outcome.succeeded for outcome in outcomes):
                action["status"] = "APPLIED"
            elif any(outcome.status == "UNKNOWN_OUTCOME" for outcome in outcomes):
                action["status"] = "UNKNOWN_OUTCOME"
            else:
                action["status"] = "BLOCKED"
            self._recompute_quantities(state)
            return self._complete_allocation_retry(retry_id, state, source)

    def reconcile_receive_arrival(self, event_id: str) -> dict[str, object]:
        """Admit an exact submitted receipt for the latest unknown arrival without retrying it."""

        self._require_live_operations()
        identifier = _text(event_id, "event_id")
        with self._lock:
            state = self._latest_state()
            if state is None:
                raise ValueError("No retained distributor event can be reconciled.")
            event = self._reconcilable_receive_event(state, identifier)
            if self._has_receive_reconciliation(state, identifier):
                source = self._read_source()
                state, source = self._merge_source(state, source)
                return self._projection(state, source)
            bridge = self._erp
            reconcile = getattr(bridge, "reconcile_receive_arrival", None)
            if not callable(reconcile):
                return self._receive_reconciliation_projection(
                    state, identifier, "UNAVAILABLE", "ERP_RECONCILIATION_UNAVAILABLE"
                )
            try:
                raw = reconcile(self._config, event, identifier)
            except Exception:
                return self._receive_reconciliation_projection(
                    state, identifier, "UNAVAILABLE", "ERP_RECONCILIATION_READ_FAILED"
                )
            if not isinstance(raw, Mapping) or raw.get("operation") != "receive_arrival":
                return self._receive_reconciliation_projection(
                    state, identifier, "UNAVAILABLE", "ERP_RECONCILIATION_MALFORMED"
                )
            status = raw.get("status")
            error_code = raw.get("error_code")
            if status != "APPLIED" or raw.get("event_id") != identifier:
                return self._receive_reconciliation_projection(
                    state,
                    identifier,
                    status if isinstance(status, str) else "UNAVAILABLE",
                    error_code if isinstance(error_code, str) and error_code else None,
                )
            snapshot = raw.get("snapshot")
            if not isinstance(snapshot, Mapping) or snapshot.get("source_status") != "CURRENT":
                return self._receive_reconciliation_projection(
                    state, identifier, "UNAVAILABLE", "ERP_RECONCILIATION_SOURCE_UNAVAILABLE"
                )
            if (
                snapshot.get("case_id") != self._config["case_id"]
                or snapshot.get("case_label") != self._config["case_label"]
                or snapshot.get("synthetic_input") is not self._config["synthetic_input"]
            ):
                return self._receive_reconciliation_projection(
                    state, identifier, "UNAVAILABLE", "ERP_RECONCILIATION_SCOPE_MISMATCH"
                )
            try:
                source = self._canonical_source(snapshot)
            except ValueError:
                return self._receive_reconciliation_projection(
                    state, identifier, "UNAVAILABLE", "ERP_RECONCILIATION_SOURCE_MALFORMED"
                )
            documents = _documents(raw.get("documents"))
            if len(documents) != 1 or documents[0].get("kind") != "Purchase Receipt":
                return self._receive_reconciliation_projection(
                    state, identifier, "UNAVAILABLE", "ERP_RECONCILIATION_RECEIPT_MALFORMED"
                )
            updated = self._apply_receive_reconciliation(state, event, source, documents)
            projection = self._projection(updated, source)
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._db.execute(
                    "UPDATE distributor_operation_events SET state_json=? WHERE event_id=?",
                    (_encode(updated), identifier),
                )
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise
            return projection

    def _reconcilable_receive_event(
        self, state: Mapping[str, object], event_id: str
    ) -> dict[str, object]:
        """Return only the latest retained arrival with an unknown native receipt outcome."""

        events = state.get("events")
        if not isinstance(events, list) or not events:
            raise ValueError("No retained distributor event can be reconciled.")
        latest = events[-1]
        if not isinstance(latest, Mapping) or latest.get("event_id") != event_id:
            raise ValueError("Only the latest retained event can be reconciled.")
        operations = latest.get("operations")
        if (
            latest.get("type") != "arrival"
            or latest.get("status") != "UNKNOWN_OUTCOME"
            or not isinstance(operations, list)
            or not any(
                isinstance(operation, Mapping)
                and operation.get("kind") == "receive_arrival"
                and operation.get("status") == "UNKNOWN_OUTCOME"
                for operation in operations
            )
        ):
            raise ValueError("This event is not an unknown arrival outcome.")
        event = self._stored_event(event_id)
        if event is None or event.get("type") != "arrival":
            raise ValueError("The retained arrival payload is unavailable.")
        return event

    @staticmethod
    def _has_receive_reconciliation(state: Mapping[str, object], event_id: str) -> bool:
        events = state.get("events")
        if not isinstance(events, list):
            return False
        for event in events:
            if not isinstance(event, Mapping) or event.get("event_id") != event_id:
                continue
            reconciliations = event.get("reconciliations")
            return isinstance(reconciliations, list) and any(
                isinstance(record, Mapping)
                and record.get("operation") == "receive_arrival"
                and record.get("status") == "NATIVE_CONFIRMED"
                for record in reconciliations
            )
        return False

    def _receive_reconciliation_projection(
        self,
        state: Mapping[str, object],
        event_id: str,
        status: str,
        error_code: str | None,
    ) -> dict[str, object]:
        """Expose a read-only failed admission without changing retained event history."""

        source = self._read_source()
        merged, source = self._merge_source(state, source)
        projection = self._projection(merged, source)
        projection["reconciliation"] = {
            "event_id": event_id,
            "operation": "receive_arrival",
            "status": status,
            **({"error_code": error_code} if error_code else {}),
        }
        return projection

    def _apply_receive_reconciliation(
        self,
        state: Mapping[str, object],
        event: Mapping[str, object],
        source: Mapping[str, object],
        documents: list[dict[str, object]],
    ) -> dict[str, object]:
        """Project exact read-back facts while retaining the original unknown operation."""

        updated = cast(dict[str, object], _copy(state))
        source_quantities = cast(Mapping[str, object], source["quantities"])
        quantities = cast(dict[str, object], updated["quantities"])
        initial_expected_cartons = quantities.get("initial_expected_cartons")
        quantities.update(_copy(source_quantities))
        if initial_expected_cartons is not None:
            quantities["initial_expected_cartons"] = initial_expected_cartons
        quantities["observed_outer_packages"] = source_quantities["cartons"]

        old_lots = {
            row.get("lot"): row
            for row in cast(list[Mapping[str, object]], updated["lots"])
            if isinstance(row.get("lot"), str)
        }
        reconciled_lots: list[dict[str, object]] = []
        for raw_lot in cast(list[Mapping[str, object]], source["lots"]):
            lot_name = _text(raw_lot.get("lot"), "source lot")
            prior = old_lots.get(lot_name)
            if prior is None:  # pragma: no cover - canonical source already checks scope
                raise ValueError("source lot scope mismatch")
            row = cast(dict[str, object], _copy(prior))
            for field in ("expected_quantity", "cartons", "received", "usable", "held", "status"):
                row[field] = _copy(raw_lot[field])
            reconciled_lots.append(row)
        updated["lots"] = reconciled_lots
        updated["allocations"] = _copy(source["allocations"])
        updated["documents"] = _merge_documents(
            _documents(updated.get("documents")),
            _documents(source.get("documents")),
            documents,
        )
        parent_purchase_order = source.get("parent_purchase_order")
        if isinstance(parent_purchase_order, Mapping):
            updated["parent_purchase_order"] = _copy(parent_purchase_order)
        else:
            updated.pop("parent_purchase_order", None)
        updated["source_status"] = "CURRENT"
        updated["source_error"] = None
        updated["financials"] = _copy(source["financials"])
        updated["source_observation"] = {
            "quantities": _copy(source["quantities"]),
            "lots": _copy(source["lots"]),
            "allocations": _copy(source["allocations"]),
            "documents": _copy(source["documents"]),
            "parent_purchase_order": _copy(parent_purchase_order)
            if isinstance(parent_purchase_order, Mapping)
            else None,
            "financials": _copy(source["financials"]),
        }

        event_id = _text(event["event_id"], "event_id")
        reconciliation = {
            "operation": "receive_arrival",
            "status": "NATIVE_CONFIRMED",
            "documents": _copy(documents),
            "reconciled_at": self._now().isoformat(),
        }
        events = cast(list[dict[str, object]], updated["events"])
        matching = [row for row in events if row.get("event_id") == event_id]
        if len(matching) != 1:  # pragma: no cover - retained state is internal
            raise RuntimeError("reconciliation event history is unavailable")
        record = matching[0]
        reconciliations = record.get("reconciliations")
        if not isinstance(reconciliations, list):
            reconciliations = []
            record["reconciliations"] = reconciliations
        reconciliations.append(reconciliation)
        self._resolve_receive_unknown_alert(updated, event_id)

        lot_name = _text(event["lot"], "lot")
        lot = self._lot(updated, lot_name)
        policy = cast(Mapping[str, object], self._config["policy"])
        if (
            policy["inspection_required"] is True
            and lot is not None
            and _quantity(lot.get("held"), "lot held") > 0
        ):
            self._alert(
                updated,
                code="QUALITY_EVIDENCE_REQUIRED",
                message="Received stock is held until configured inspection evidence is recorded.",
                event=event,
                lot=lot_name,
                quantity=_quantity(lot["held"], "lot held"),
            )
        return updated

    @staticmethod
    def _resolve_receive_unknown_alert(state: dict[str, object], event_id: str) -> None:
        for alert in cast(list[dict[str, object]], state["alerts"]):
            if (
                alert.get("code") == "NATIVE_OPERATION_UNKNOWN"
                and alert.get("operation") == "receive_arrival"
                and alert.get("event_id") == event_id
                and alert.get("status") == "OPEN"
            ):
                alert["status"] = "RESOLVED"

    def ask(self, question: str) -> dict[str, object]:
        """Run an injected read-only conversation turn, never an event or ERP write."""

        clean = " ".join(question.split()) if isinstance(question, str) else ""
        if not clean or len(question) > 500:
            raise ValueError(
                "Ask a specific distributor evidence question using at most 500 characters."
            )
        projection = self.projection()
        if self._ask_turn is None:
            prior_conversation = projection.get("conversation")
            return {
                **projection,
                "conversation": list(prior_conversation)
                if isinstance(prior_conversation, list)
                else [],
                "conversation_status": "UNAVAILABLE",
                "conversation_message": "The distributor read-only conversation is not configured.",
            }
        result = self._ask_turn(clean, projection)
        if not isinstance(result, Mapping):
            raise ValueError("Distributor conversation returned an invalid read-only result.")
        if result.get("status") != "COMPLETE":
            detail = result.get("detail")
            code = result.get("code")
            message = (
                detail.strip()
                if isinstance(detail, str) and detail.strip()
                else (
                    "The distributor read-only conversation is unavailable; "
                    "no fallback answer was used."
                )
            )
            unavailable = {"status": "UNAVAILABLE", "message": message}
            response: dict[str, object] = {
                **projection,
                "conversation": unavailable,
                "conversation_status": "UNAVAILABLE",
                "conversation_message": message,
            }
            if isinstance(code, str) and code.strip():
                safe_code = code.strip()
                unavailable["code"] = safe_code
                response["conversation_error_code"] = safe_code
            return response
        answer = result.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Distributor conversation returned no displayable answer.")
        conversation = {
            "status": "COMPLETE",
            "answer": answer.strip(),
            "provider": result.get("provider"),
            "session_id": result.get("session_id"),
            "context": self._conversation_context(projection),
            "read_only": True,
        }
        return {**projection, "conversation": conversation}

    @staticmethod
    def _conversation_context(projection: Mapping[str, object]) -> str:
        """Describe source freshness in the visible read-only conversation context."""

        raw_mode = projection.get("evidence_mode")
        mode = raw_mode.get("status") if isinstance(raw_mode, Mapping) else None
        status = mode.strip().upper() if isinstance(mode, str) and mode.strip() else "UNKNOWN"
        if status == "CURRENT" and projection.get("live_source") is False:
            status = "UNKNOWN"
        as_of = raw_mode.get("as_of") if isinstance(raw_mode, Mapping) else None
        effective_time = as_of.strip() if isinstance(as_of, str) and as_of.strip() else None
        if status == "CURRENT":
            return "Current case-scoped ERP facts and retained physical event evidence"
        if status == "RETAINED_AS_OF":
            if effective_time is not None:
                return (
                    f"Retained case-scoped ERP facts as of {effective_time} and retained "
                    "physical event evidence"
                )
            return (
                "Retained case-scoped ERP facts with no supplied effective time and retained "
                "physical event evidence"
            )
        if "UNAVAILABLE" in status:
            return "ERP source unavailable; retained physical event evidence only"
        return (
            "Case-scoped ERP facts with unknown source freshness and retained physical "
            "event evidence"
        )

    def _economic_operational_snapshot(
        self, state: Mapping[str, object], source: Mapping[str, object]
    ) -> dict[str, object]:
        """Expose the current raw operations facts separately from configured evidence."""

        return {
            "source_status": source.get("source_status"),
            "as_of": self._source_as_of(source),
            "source_revision": self._source_revision(source),
            "quantities": _copy(source.get("quantities", state.get("quantities", {}))),
            "lots": _copy(source.get("lots", state.get("lots", []))),
            "allocations": _copy(source.get("allocations", state.get("allocations", []))),
            "contract_terms": _copy(self._config.get("allocations", [])),
            "prepared_picks": _copy(state.get("prepared_picks", [])),
            "photo_observations": self._current_photo_observations(source),
        }

    def _current_photo_observations(self, source: Mapping[str, object]) -> list[dict[str, object]]:
        """Offer current photo evidence to advisory economics without making it stock authority."""

        source_revision = self._source_revision(source)
        if source.get("source_status") != "CURRENT" or source_revision is None:
            return []
        superseded = self._photo_supersession_index()
        rows = self._db.execute(
            "SELECT attachment_id, digest, analysis_json FROM distributor_operation_attachments "
            "WHERE case_id=? AND analysis_json IS NOT NULL ORDER BY recorded_at, attachment_id",
            (self._config["case_id"],),
        ).fetchall()
        observations: list[dict[str, object]] = []
        for attachment_id, digest, raw_analysis in rows:
            if (
                not isinstance(attachment_id, str)
                or attachment_id in superseded
                or not isinstance(digest, str)
                or not isinstance(raw_analysis, str)
            ):
                continue
            try:
                analysis = _decoded(raw_analysis, "photo analysis")
            except RuntimeError:
                continue
            recommendation = analysis.get("recommendation")
            assessment = analysis.get("assessment")
            checks = analysis.get("checks")
            source_context = analysis.get("source_context")
            if (
                analysis.get("status") != "COMPLETE"
                or analysis.get("attachment_sha256") != digest
                or analysis.get("source_revision") != source_revision
                or not isinstance(recommendation, Mapping)
                or not isinstance(assessment, Mapping)
                or not isinstance(checks, Mapping)
                or recommendation.get("identity_safe") is not True
            ):
                continue
            observed_at = analysis.get("observed_at")
            code = recommendation.get("code")
            visible_condition = assessment.get("visible_condition")
            visibility = (
                assessment.get("visibility")
                or assessment.get("label_visibility")
                or assessment.get("detail_visibility")
            )
            if not (
                isinstance(observed_at, str)
                and isinstance(code, str)
                and isinstance(visibility, str)
            ):
                continue
            linked_lot = analysis.get("linked_lot")
            linkage_source = analysis.get("linkage_source")
            observations.append(
                {
                    "evidence_id": "photo:"
                    + sha256(
                        _encode(
                            {
                                "attachment_id": attachment_id,
                                "attachment_sha256": digest,
                                "source_revision": source_revision,
                                "linked_lot": linked_lot,
                                "purpose": analysis.get("purpose", "overview"),
                            }
                        ).encode("utf-8")
                    ).hexdigest()[:24],
                    "attachment_sha256": digest,
                    "attachment_id": attachment_id,
                    "source_revision": source_revision,
                    "observed_at": observed_at,
                    "linked_lot": linked_lot if isinstance(linked_lot, str) else None,
                    "linkage_source": (
                        linkage_source if linkage_source == "OPERATOR_SELECTED" else None
                    ),
                    "linked_quantity": analysis.get("linked_quantity"),
                    "purpose": analysis.get("purpose", "overview"),
                    "visibility": visibility,
                    "visible_condition": visible_condition
                    if isinstance(visible_condition, str)
                    else None,
                    "assessment": _copy(assessment),
                    "recommendation_code": code,
                    "label_lot_conflict": recommendation.get("label_lot_conflict") is True,
                    "checks": _copy(checks),
                    "source_context": (
                        _copy(source_context) if isinstance(source_context, Mapping) else {}
                    ),
                    "authority": (
                        "Advisory photo observation only; current ERP lot status and usable "
                        "quantity remain the feasibility authority."
                    ),
                }
            )
        return observations

    def _economic_view(
        self, snapshot: Mapping[str, object], last_result: Mapping[str, object] | None
    ) -> dict[str, object]:
        persisted = self._persisted_economic_effect()
        persisted_result = persisted[1] if persisted is not None else None
        effective_result = last_result if isinstance(last_result, Mapping) else persisted_result
        view = project_economics(
            self._config,
            snapshot,
            now=self._now(),
            last_result=effective_result,
        )
        if view is None:  # pragma: no cover - caller checks configuration
            raise RuntimeError("economic proposal was not configured")
        if not isinstance(view.get("model"), Mapping):
            view["model"] = {
                "status": "not_run",
                "candidate_id": None,
                "citations": [],
                "tool_trace": [],
                "model_response": None,
            }
        if persisted is not None:
            effect = persisted[0]
            view["proposal_effect"] = _copy(effect)
            view["selected_candidate_id"] = effect["candidate_id"]
            candidates = view.get("candidates")
            if isinstance(candidates, list):
                for candidate in candidates:
                    if (
                        isinstance(candidate, dict)
                        and candidate.get("candidate_id") == effect["candidate_id"]
                    ):
                        candidate["proposal_effect"] = _copy(effect)
        self._mark_historical_economic_model(view, effective_result)
        return view

    def _persisted_economic_effect(
        self,
    ) -> tuple[dict[str, object], dict[str, object] | None] | None:
        """Read one exact economic proposal from the existing approval journal.

        The proposal journal is the authority for whether the already-selected
        split event is still pending or has reached a native terminal outcome.
        No model result or approval state is written here.
        """

        configured = cast(Mapping[str, object], self._config["economic_proposal"])
        configured_event = cast(Mapping[str, object], configured["split20_event"])
        expected_event = _encode(configured_event)
        rows = self._db.execute(
            "SELECT proposal_id, event_json, state_revision, result_json, manager_id, approved_at "
            "FROM distributor_operation_proposals WHERE case_id=? "
            "AND source='ECONOMIC_RECOMMENDATION' ORDER BY recorded_at DESC, rowid DESC",
            (self._config["case_id"],),
        ).fetchall()
        for row in rows:
            (
                proposal_id,
                event_json,
                _state_revision,
                result_json,
                manager_id,
                approved_at,
            ) = cast(tuple[str, str, str, str | None, str | None, str | None], row)
            if event_json != expected_event:
                continue
            event = _decoded(event_json, "economic proposal event")
            event_id = _text(event.get("event_id"), "economic proposal event_id")
            result = _decoded(result_json, "economic proposal result") if result_json else None
            effect: dict[str, object] = {
                "candidate_id": SPLIT20_CANDIDATE_ID,
                "proposal_id": proposal_id,
                "event_id": event_id,
                "quantity": _wire(_quantity(event.get("quantity"), "economic proposal quantity")),
                "status": (
                    self._stored_event_status(event) or "UNKNOWN_OUTCOME"
                    if result_json is not None
                    else "PENDING_MANAGER_APPROVAL"
                ),
            }
            if manager_id is not None and approved_at is not None:
                effect["approval"] = {"manager_id": manager_id, "approved_at": approved_at}
            documents = self._economic_event_documents(event_id)
            if documents:
                effect["native_documents"] = documents
            return effect, self._confirmation_economic_result(result, proposal_id)
        return None

    def _economic_event_documents(self, event_id: str) -> list[dict[str, object]]:
        """Return document references emitted by this exact completed event."""

        row = self._db.execute(
            "SELECT result_json FROM distributor_operation_events WHERE event_id=?", (event_id,)
        ).fetchone()
        if row is None or row[0] is None:
            return []
        projection = _decoded(cast(str, row[0]), "economic event result")
        events = projection.get("events")
        if not isinstance(events, list):
            return []
        for record in events:
            if not isinstance(record, Mapping) or record.get("event_id") != event_id:
                continue
            operations = record.get("operations")
            if not isinstance(operations, list):
                return []
            return _merge_documents(
                *[
                    _documents(operation.get("documents"))
                    for operation in operations
                    if isinstance(operation, Mapping)
                ]
            )
        return []

    @staticmethod
    def _confirmation_economic_result(
        result: Mapping[str, object] | None, proposal_id: str
    ) -> dict[str, object] | None:
        """Recover the pre-dispatch decision only when the journal binds it to this proposal."""

        if not isinstance(result, Mapping):
            return None
        economic = result.get("economic_proposal")
        if not isinstance(economic, Mapping):
            return None
        last_result = economic.get("last_result")
        if (
            not isinstance(last_result, Mapping)
            or last_result.get("prepared_proposal_id") != proposal_id
        ):
            return None
        return _copy(last_result)

    @staticmethod
    def _mark_historical_economic_model(
        view: dict[str, object], last_result: Mapping[str, object] | None
    ) -> None:
        """Label a prior model trace when current operational evidence has changed."""

        if not isinstance(last_result, Mapping):
            return
        prior_evidence_id = last_result.get("source_evidence_id")
        evidence = view.get("evidence")
        operational = (
            evidence.get("operational_snapshot") if isinstance(evidence, Mapping) else None
        )
        current_evidence_id = (
            operational.get("evidence_id") if isinstance(operational, Mapping) else None
        )
        if not (
            isinstance(prior_evidence_id, str)
            and prior_evidence_id
            and isinstance(current_evidence_id, str)
            and current_evidence_id
            and prior_evidence_id != current_evidence_id
            and isinstance(view.get("model"), Mapping)
        ):
            return
        model = cast(dict[str, object], _copy(view["model"]))
        prior_status = model.get("status")
        decision = model.get("decision")
        model.update(
            {
                "status": "HISTORICAL",
                "historical": True,
                "source_evidence_id": prior_evidence_id,
                "current_source_evidence_id": current_evidence_id,
                "decision": (
                    f"Historical pre-dispatch model decision: {decision}"
                    if isinstance(decision, str) and decision.strip()
                    else (
                        "Historical pre-dispatch model decision; "
                        "current operational evidence changed."
                    )
                ),
            }
        )
        if isinstance(prior_status, str) and prior_status.strip():
            model["prior_status"] = prior_status.strip()
        view["model"] = model

    def _economic_result(
        self,
        *,
        candidate_id: str | None,
        snapshot: Mapping[str, object],
        selector_result: Mapping[str, object],
        gate: Mapping[str, object],
    ) -> dict[str, object]:
        selected = selector_result.get("candidate_id")
        return {
            "requested_candidate_id": candidate_id,
            "model": _copy(selector_result),
            "gate": _copy(gate),
            "advice_disagrees_with_selection": (
                candidate_id is not None
                and isinstance(selected, str)
                and selected not in {candidate_id, DEFER_CANDIDATE_ID}
            ),
            "source_evidence_id": raw_economic_evidence(self._config, snapshot)[
                "operational_snapshot"
            ]["evidence_id"],
        }

    def _economic_proposal_id(self, event_id: str) -> str:
        """Reuse a stable proposal identity; no economic decision store is introduced."""

        digest = economic_config_digest(self._config) or "no-economic-config"
        identity = _encode(
            {"case_id": self._config["case_id"], "event_id": event_id, "economics": digest}
        )
        return "economic-" + sha256(identity.encode()).hexdigest()[:32]

    def _validate_config(self, config: Mapping[str, object]) -> dict[str, object]:
        normalized = cast(dict[str, object], _copy(config))
        for field in (
            "case_id",
            "case_label",
            "company",
            "item_code",
            "uom",
        ):
            _text(normalized.get(field), field)
        if type(normalized.get("synthetic_input")) is not bool:
            raise ValueError("synthetic_input must be a boolean")
        _whole(normalized.get("cartons"), "cartons", positive=True)
        _quantity(normalized.get("expected_pack_quantity"), "expected_pack_quantity", positive=True)
        policy = normalized.get("policy")
        if not isinstance(policy, Mapping) or any(
            type(policy.get(name)) is not bool
            for name in ("inspection_required", "reservation_supported")
        ):
            raise ValueError(
                "policy requires inspection_required and reservation_supported booleans"
            )
        criteria = policy.get("inspection_criteria")
        if policy["inspection_required"] is True:
            if not isinstance(criteria, Mapping) or not criteria:
                raise ValueError("inspection-required policy needs configured inspection_criteria")
            for metric, bounds in criteria.items():
                _text(metric, "inspection metric")
                if not isinstance(bounds, Mapping) or set(bounds) != {"minimum", "maximum"}:
                    raise ValueError("inspection criteria require minimum and maximum")
                if _quantity(bounds["minimum"], "inspection minimum") > _quantity(
                    bounds["maximum"], "inspection maximum"
                ):
                    raise ValueError("inspection criterion minimum cannot exceed maximum")
        elif criteria is not None:
            raise ValueError("inspection_criteria requires inspection_required")
        lots = normalized.get("lots")
        if not isinstance(lots, list) or not lots:
            raise ValueError("lots requires at least one configured lot")
        seen_lots: set[str] = set()
        replacement_lots: dict[str, str] = {}
        for row in lots:
            if not isinstance(row, Mapping):
                raise ValueError("lots must contain JSON objects")
            lot = _text(row.get("lot"), "lot")
            if lot in seen_lots:
                raise ValueError("lot identities must be unique")
            seen_lots.add(lot)
            _quantity(row.get("expected_quantity"), "expected_quantity", positive=True)
            if "cartons" in row:
                _whole(row["cartons"], "lot cartons", positive=True)
            if "expected_pack_quantity" in row:
                _quantity(row["expected_pack_quantity"], "expected_pack_quantity", positive=True)
            replacement = row.get("replacement_for_lot")
            if replacement is not None:
                replacement_lots[lot] = _text(replacement, "replacement_for_lot")
        if any(
            target not in seen_lots or target == lot for lot, target in replacement_lots.items()
        ):
            raise ValueError("replacement_for_lot must name another configured lot")
        allocations = normalized.get("allocations")
        if not isinstance(allocations, list) or not allocations:
            raise ValueError("allocations requires at least one configured customer order")
        seen_orders: set[str] = set()
        for row in allocations:
            if not isinstance(row, Mapping):
                raise ValueError("allocations must contain JSON objects")
            order = _text(row.get("customer_order"), "customer_order")
            if order in seen_orders:
                raise ValueError("customer orders must be unique")
            seen_orders.add(order)
            _quantity(row.get("requested_quantity"), "requested_quantity", positive=True)
            _whole(row.get("priority"), "priority", positive=True)
        try:
            validate_contract_config(normalized)
        except ContractAllocationError as error:
            raise ValueError(str(error)) from error
        validate_economic_config(normalized)
        if contract_mode(normalized):
            for row in allocations:
                row["promised_delivery_at"] = _utc(
                    row["promised_delivery_at"], "promised_delivery_at"
                )
            tranches = normalized.get("pick_tranches")
            if not isinstance(tranches, list) or not tranches:
                raise ValueError("contract allocation requires configured native pick_tranches")
            for tranche in tranches:
                if not isinstance(tranche, Mapping):
                    raise ValueError("contract native pick tranche must be an object")
                _text(tranche.get("customer_order"), "contract native pick tranche customer_order")
                _quantity(
                    tranche.get("quantity"), "contract native pick tranche quantity", positive=True
                )
        for name in ("expected_at", "promised_delivery_at"):
            if name in normalized:
                _deadline(normalized[name], name)
        shipping = normalized.get("shipping")
        if shipping is not None:
            if not isinstance(shipping, Mapping) or not isinstance(
                shipping.get("shipments"), Mapping
            ):
                raise ValueError("shipping shipments must be a mapping when configured")
            for order, details in shipping["shipments"].items():
                _text(order, "shipping customer order")
                if order not in seen_orders or not isinstance(details, Mapping):
                    raise ValueError("shipping must contain configured customer-order details")
                _text(details.get("delivery_address"), "shipping delivery address")
                _text(details.get("shipment_id_prefix"), "shipping shipment ID prefix")
        return normalized

    def _validate_event(self, event: Mapping[str, object]) -> dict[str, object]:
        payload = cast(dict[str, object], _copy(event))
        event_type = payload.get("type")
        required = {
            "arrival": {
                "event_id",
                "type",
                "occurred_at",
                "evidence_ref",
                "synthetic",
                "cartons",
                "expected_pack_quantity",
                "observed_stock_quantity",
                "item_code",
                "lot",
            },
            "inspection": {
                "event_id",
                "type",
                "occurred_at",
                "evidence_ref",
                "synthetic",
                "lot",
                "result",
                "scope",
                "metric",
                "measured",
                "sample_quantity",
                "inspection_report_ref",
            },
            "picked": {
                "event_id",
                "type",
                "occurred_at",
                "evidence_ref",
                "synthetic",
                "customer_order",
                "lot",
                "quantity",
                "pick_evidence_ref",
            },
            "carrier_pickup": {
                "event_id",
                "type",
                "occurred_at",
                "evidence_ref",
                "synthetic",
                "shipment_id",
            },
            "delivery": {
                "event_id",
                "type",
                "occurred_at",
                "evidence_ref",
                "synthetic",
                "shipment_id",
            },
        }
        if (
            not isinstance(event_type, str)
            or event_type not in required
            or set(payload) != required[event_type]
        ):
            raise ValueError("Distributor event has missing or unexpected fields.")
        _text(payload.get("event_id"), "event_id")
        _utc(payload.get("occurred_at"), "occurred_at")
        _text(payload.get("evidence_ref"), "evidence_ref")
        if (
            type(payload.get("synthetic")) is not bool
            or payload["synthetic"] != self._config["synthetic_input"]
        ):
            raise ValueError("event synthetic flag must match this configured case")
        if event_type == "arrival":
            _whole(payload.get("cartons"), "cartons", positive=True)
            _quantity(
                payload.get("expected_pack_quantity"), "expected_pack_quantity", positive=True
            )
            _quantity(
                payload.get("observed_stock_quantity"), "observed_stock_quantity", positive=True
            )
            _text(payload.get("item_code"), "item_code")
            _text(payload.get("lot"), "lot")
        elif event_type == "inspection":
            _text(payload.get("lot"), "lot")
            if payload.get("result") not in {"PASS", "FAIL"}:
                raise ValueError("inspection result must be PASS or FAIL")
            if payload.get("scope") not in {"SAMPLE", "WHOLE_LOT"}:
                raise ValueError("inspection scope must be SAMPLE or WHOLE_LOT")
            _text(payload.get("metric"), "metric")
            _quantity(payload.get("measured"), "measured")
            _quantity(payload.get("sample_quantity"), "sample_quantity", positive=True)
            _text(payload.get("inspection_report_ref"), "inspection_report_ref")
        elif event_type == "picked":
            _text(payload.get("customer_order"), "customer_order")
            _text(payload.get("lot"), "lot")
            _quantity(payload.get("quantity"), "quantity", positive=True)
            _text(payload.get("pick_evidence_ref"), "pick_evidence_ref")
        else:
            _text(payload.get("shipment_id"), "shipment_id")
        return payload

    def _read_source(self) -> dict[str, object]:
        if self._erp is None:
            return self._source_unavailable("ERP_ADAPTER_UNAVAILABLE")
        try:
            source = self._erp.read_case(self._config)
        except Exception:
            return self._source_unavailable("ERP_SOURCE_UNAVAILABLE")
        if not isinstance(source, Mapping):
            return self._source_unavailable("ERP_SOURCE_MALFORMED")
        try:
            copied = cast(dict[str, object], _copy(source))
            if copied.get("source_status") != "CURRENT":
                return self._source_unavailable(
                    _text(copied.get("source_error") or "ERP_SOURCE_UNAVAILABLE", "source_error")
                )
            if (
                copied.get("case_id") != self._config["case_id"]
                or copied.get("case_label") != self._config["case_label"]
                or copied.get("synthetic_input") is not self._config["synthetic_input"]
            ):
                return self._source_unavailable("ERP_SOURCE_SCOPE_MISMATCH")
            return self._canonical_source(copied)
        except ValueError:
            return self._source_unavailable("ERP_SOURCE_MALFORMED")

    @staticmethod
    def _source_as_of(source: Mapping[str, object]) -> str | None:
        """Preserve an explicit source timestamp without manufacturing a fresh one."""

        value = source.get("as_of")
        return value.strip() if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _source_unavailable(error_code: str) -> dict[str, object]:
        return {"source_status": "UNAVAILABLE", "source_error": error_code}

    def _canonical_source(self, source: Mapping[str, object]) -> dict[str, object]:
        raw_quantities = source.get("quantities")
        if not isinstance(raw_quantities, Mapping):
            raise ValueError("source quantities are required")
        expected = sum(
            (
                _quantity(row["expected_quantity"], "expected_quantity")
                for row in cast(list[Mapping[str, object]], self._config["lots"])
            ),
            Decimal(),
        )
        quantity_fields = (
            "ordered",
            "received",
            "usable",
            "held",
            "missing",
            "allocated",
            "dispatched",
            "delivery_confirmed",
        )
        quantities: dict[str, object] = {
            field: _wire(_quantity(raw_quantities.get(field), f"source {field}"))
            for field in quantity_fields
        }
        quantities["cartons"] = _whole(raw_quantities.get("cartons"), "source cartons")
        quantities["uom"] = _text(raw_quantities.get("uom"), "source uom")
        if (
            quantities["uom"] != self._config["uom"]
            or _quantity(quantities["ordered"], "source ordered") != expected
        ):
            raise ValueError("source case quantity mismatch")
        received = _quantity(quantities["received"], "source received")
        if (
            _quantity(quantities["missing"], "source missing") != expected - received
            or _quantity(quantities["usable"], "source usable")
            + _quantity(quantities["held"], "source held")
            + _quantity(quantities["dispatched"], "source dispatched")
            != received
        ):
            raise ValueError("source quantities do not conserve stock")
        lots = self._canonical_source_lots(source.get("lots"))
        allocations = self._canonical_source_allocations(source.get("allocations"))
        parent_purchase_order = self._canonical_parent_purchase_order(
            source.get("parent_purchase_order"), quantities
        )
        raw_documents = source.get("documents")
        documents = _documents(raw_documents)
        if not isinstance(raw_documents, list) or len(documents) != len(raw_documents):
            raise ValueError("source documents are malformed")
        try:
            financials = self._canonical_financials(source.get("financials"))
        except ValueError:
            financials = {
                "status": "UNAVAILABLE",
                "reason": "FINANCIAL_SOURCE_MALFORMED",
            }
        canonical: dict[str, object] = {
            "source_status": "CURRENT",
            "documents": documents,
            "quantities": quantities,
            "lots": lots,
            "allocations": allocations,
            "financials": financials,
        }
        as_of = self._source_as_of(source)
        if as_of is not None:
            canonical["as_of"] = as_of
        if parent_purchase_order is not None:
            canonical["parent_purchase_order"] = parent_purchase_order
        raw_revision = source.get("source_revision")
        if isinstance(raw_revision, str) and raw_revision.strip():
            canonical["source_revision"] = raw_revision.strip()
        else:
            revision_material = {key: value for key, value in canonical.items() if key != "as_of"}
            canonical["source_revision"] = (
                "operational:" + sha256(_encode(revision_material).encode("utf-8")).hexdigest()[:24]
            )
        return canonical

    def _canonical_parent_purchase_order(
        self, raw_parent: object, quantities: Mapping[str, object]
    ) -> dict[str, object] | None:
        """Expose the verified full PO balance separately from this configured case."""

        if raw_parent is None:
            return None
        if not isinstance(raw_parent, Mapping):
            raise ValueError("parent purchase order is malformed")
        name = _text(raw_parent.get("name"), "parent purchase order name")
        ordered = _quantity(raw_parent.get("ordered"), "parent purchase order ordered")
        received = _quantity(raw_parent.get("received"), "parent purchase order received")
        uom = _text(raw_parent.get("uom"), "parent purchase order uom")
        case_received = _quantity(quantities.get("received"), "source received")
        case_ordered = _quantity(quantities.get("ordered"), "source ordered")
        if (
            name != self._config["purchase_order"]
            or uom != self._config["uom"]
            or ordered < case_ordered
            or received < case_received
            or received > ordered
        ):
            raise ValueError("parent purchase order scope mismatch")
        return {
            "name": name,
            "ordered": _wire(ordered),
            "received": _wire(received),
            "outside_case_received": _wire(received - case_received),
            "uom": uom,
        }

    def _canonical_source_lots(self, raw_lots: object) -> list[dict[str, object]]:
        if not isinstance(raw_lots, list):
            raise ValueError("source lots are required")
        expected = {
            _text(row["lot"], "lot"): _quantity(row["expected_quantity"], "expected_quantity")
            for row in cast(list[Mapping[str, object]], self._config["lots"])
        }
        result: dict[str, dict[str, object]] = {}
        for raw in raw_lots:
            if not isinstance(raw, Mapping):
                raise ValueError("source lot is malformed")
            name = _text(raw.get("lot"), "source lot")
            if name not in expected or name in result:
                raise ValueError("source lot scope mismatch")
            received = _quantity(raw.get("received"), "source lot received")
            usable = _quantity(raw.get("usable"), "source lot usable")
            held = _quantity(raw.get("held"), "source lot held")
            if (
                _quantity(raw.get("expected_quantity"), "source expected quantity")
                != expected[name]
                or received > expected[name]
                or usable + held > received
            ):
                raise ValueError("source lot facts conflict")
            result[name] = {
                "lot": name,
                "expected_quantity": _wire(expected[name]),
                "cartons": _whole(raw.get("cartons"), "source lot cartons"),
                "received": _wire(received),
                "usable": _wire(usable),
                "held": _wire(held),
                "status": _text(raw.get("status"), "source lot status"),
            }
        if set(result) != set(expected):
            raise ValueError("source lots are incomplete")
        return [result[name] for name in sorted(result)]

    def _canonical_financials(self, raw: object) -> dict[str, object]:
        """Keep optional commercial readbacks local to the financial projection."""

        if raw is None:
            return {"status": "UNAVAILABLE", "reason": "FINANCIAL_NOT_PROVIDED"}
        if not isinstance(raw, Mapping):
            raise ValueError("financial source is malformed")
        status = raw.get("status")
        if status == "UNAVAILABLE":
            return {
                "status": "UNAVAILABLE",
                "reason": _text(raw.get("reason"), "financial reason"),
            }
        if status != "CURRENT":
            raise ValueError("financial source status is malformed")
        purchase = self._canonical_financial_order(
            raw.get("purchase_order"), "Purchase Order", self._config["purchase_order"], True
        )
        raw_sales = raw.get("sales_orders")
        if not isinstance(raw_sales, list):
            raise ValueError("financial sales orders are malformed")
        sales: dict[str, dict[str, object]] = {}
        for row in raw_sales:
            canonical = self._canonical_financial_order(row, "Sales Order", None, False)
            document = cast(Mapping[str, object], canonical["document"])
            name = _text(document.get("name"), "financial sales order")
            if name in sales:
                raise ValueError("financial sales orders are ambiguous")
            sales[name] = canonical
        expected_sales = {
            _text(row["customer_order"], "customer_order")
            for row in cast(list[Mapping[str, object]], self._config["allocations"])
        }
        if set(sales) != expected_sales:
            raise ValueError("financial sales order scope mismatch")
        purchase_invoices = self._canonical_invoice_group(
            raw.get("purchase_invoices"), "Purchase Invoice"
        )
        raw_sales_invoices = raw.get("sales_invoices")
        if not isinstance(raw_sales_invoices, list):
            raise ValueError("financial sales invoices are malformed")
        sales_invoices: dict[str, dict[str, object]] = {}
        for row in raw_sales_invoices:
            if not isinstance(row, Mapping):
                raise ValueError("financial sales invoice is malformed")
            order = _text(row.get("customer_order"), "financial sales invoice order")
            if order in sales_invoices:
                raise ValueError("financial sales invoices are ambiguous")
            sales_invoices[order] = {
                "customer_order": order,
                **self._canonical_invoice_group(row, "Sales Invoice"),
            }
        if set(sales_invoices) != expected_sales:
            raise ValueError("financial sales invoice scope mismatch")
        return {
            "status": "CURRENT",
            "purchase_order": purchase,
            "sales_orders": [sales[name] for name in sorted(sales)],
            "purchase_invoices": purchase_invoices,
            "sales_invoices": [sales_invoices[name] for name in sorted(sales_invoices)],
        }

    @staticmethod
    def _canonical_financial_document(raw: object, kind: str) -> dict[str, object]:
        documents = _documents([raw])
        if len(documents) != 1 or documents[0].get("kind") != kind:
            raise ValueError("financial document is malformed")
        return documents[0]

    def _canonical_financial_order(
        self, raw: object, kind: str, expected_name: object | None, purchase: bool
    ) -> dict[str, object]:
        if not isinstance(raw, Mapping):
            raise ValueError("financial order is malformed")
        document = self._canonical_financial_document(raw.get("document"), kind)
        if expected_name is not None and document.get("name") != expected_name:
            raise ValueError("financial purchase order scope mismatch")
        line = raw.get("line")
        if not isinstance(line, Mapping):
            raise ValueError("financial order line is malformed")
        canonical_line: dict[str, object] = {
            "quantity": _wire(_quantity(line.get("quantity"), "financial quantity")),
            "rate": _wire(_quantity(line.get("rate"), "financial rate")),
            "net_amount": _wire(_quantity(line.get("net_amount"), "financial net amount")),
        }
        if purchase:
            canonical_line["received_quantity"] = _wire(
                _quantity(line.get("received_quantity"), "financial received quantity")
            )
        result: dict[str, object] = {
            "document": document,
            "currency": _text(raw.get("currency"), "financial currency"),
            "line": canonical_line,
        }
        if purchase:
            result["supplier"] = _text(raw.get("supplier"), "financial supplier")
        else:
            if raw.get("value_scope") != "ORDER_LINE_NET_AMOUNT_NOT_INVOICE_OR_REVENUE":
                raise ValueError("financial sales order amount scope is malformed")
            result["customer"] = _text(raw.get("customer"), "financial customer")
            result["value_scope"] = "ORDER_LINE_NET_AMOUNT_NOT_INVOICE_OR_REVENUE"
        return result

    def _canonical_invoice_group(self, raw: object, kind: str) -> dict[str, object]:
        if not isinstance(raw, Mapping):
            raise ValueError("financial invoice group is malformed")
        status = raw.get("status")
        if status == "UNAVAILABLE":
            return {
                "status": "UNAVAILABLE",
                "reason": _text(raw.get("reason"), "financial invoice reason"),
            }
        records = raw.get("records")
        if not isinstance(records, list):
            raise ValueError("financial invoice records are malformed")
        if status == "MISSING":
            if records:
                raise ValueError("missing financial invoices have records")
            return {"status": "MISSING", "records": []}
        if status != "CURRENT" or not records:
            raise ValueError("financial invoice status is malformed")
        canonical: dict[str, dict[str, object]] = {}
        for row in records:
            if not isinstance(row, Mapping):
                raise ValueError("financial invoice is malformed")
            document = self._canonical_financial_document(row.get("document"), kind)
            name = _text(document.get("name"), "financial invoice name")
            docstatus = _whole(row.get("docstatus"), "financial invoice docstatus")
            if name in canonical or docstatus not in {0, 1, 2}:
                raise ValueError("financial invoice scope mismatch")
            if row.get("amount_scope") != "INVOICE_LEVEL_TOTAL_AND_OUTSTANDING":
                raise ValueError("financial invoice amount scope is malformed")
            canonical[name] = {
                "document": document,
                "docstatus": docstatus,
                "currency": _text(row.get("currency"), "financial invoice currency"),
                "grand_total": _wire(_quantity(row.get("grand_total"), "financial grand total")),
                "outstanding_amount": _wire(
                    _quantity(row.get("outstanding_amount"), "financial outstanding amount")
                ),
                "amount_scope": "INVOICE_LEVEL_TOTAL_AND_OUTSTANDING",
            }
        return {"status": "CURRENT", "records": [canonical[name] for name in sorted(canonical)]}

    def _canonical_source_allocations(self, raw_allocations: object) -> list[dict[str, object]]:
        if not isinstance(raw_allocations, list):
            raise ValueError("source allocations are required")
        expected = {
            _text(row["customer_order"], "customer_order"): (
                _quantity(row["requested_quantity"], "requested_quantity"),
                _whole(row["priority"], "priority", positive=True),
            )
            for row in cast(list[Mapping[str, object]], self._config["allocations"])
        }
        result: dict[str, dict[str, object]] = {}
        for raw in raw_allocations:
            if not isinstance(raw, Mapping):
                raise ValueError("source allocation is malformed")
            order = _text(raw.get("customer_order"), "source customer order")
            configured = expected.get(order)
            if configured is None or order in result:
                raise ValueError("source allocation scope mismatch")
            requested = _quantity(raw.get("requested_quantity"), "source requested quantity")
            priority = _whole(raw.get("priority"), "source priority", positive=True)
            allocated = _quantity(raw.get("allocated"), "source allocated")
            backordered = _quantity(raw.get("backordered"), "source backordered")
            dispatched = _quantity(raw.get("dispatched"), "source dispatched")
            if (
                requested != configured[0]
                or priority != configured[1]
                or allocated + backordered + dispatched != requested
            ):
                raise ValueError("source allocation facts conflict")
            result[order] = {
                "customer_order": order,
                "requested_quantity": _wire(requested),
                "priority": priority,
                "allocated": _wire(allocated),
                "backordered": _wire(backordered),
                "dispatched": _wire(dispatched),
                "reservation": _text(raw.get("reservation"), "source reservation"),
            }
        if set(result) != set(expected):
            raise ValueError("source allocations are incomplete")
        return [result[name] for name in sorted(result)]

    def _initial_state(self) -> dict[str, object]:
        allocations = cast(list[Mapping[str, object]], self._config["allocations"])
        lots = cast(list[Mapping[str, object]], self._config["lots"])
        planned = sum(
            (_quantity(row["requested_quantity"], "requested_quantity") for row in allocations),
            Decimal(),
        )
        lot_rows = [
            {
                "lot": _text(row["lot"], "lot"),
                "expected_quantity": _wire(
                    _quantity(row["expected_quantity"], "expected_quantity")
                ),
                "expected_pack_quantity": _wire(
                    _quantity(
                        row.get("expected_pack_quantity", self._config["expected_pack_quantity"]),
                        "expected_pack_quantity",
                        positive=True,
                    )
                ),
                "cartons": 0,
                "received": 0,
                "usable": 0,
                "held": 0,
                "status": "AWAITING_ARRIVAL",
            }
            for row in lots
        ]
        for row, lot in zip(lots, lot_rows, strict=True):
            replacement = row.get("replacement_for_lot")
            if replacement is not None:
                lot["replacement_for_lot"] = _text(replacement, "replacement_for_lot")
        initial_expected_cartons = self._initial_expected_cartons(lots)
        return {
            "case_id": self._config["case_id"],
            "case_label": self._config["case_label"],
            "synthetic_input": self._config["synthetic_input"],
            "quantities": {
                "ordered": _wire(planned),
                "received": 0,
                "usable": 0,
                "held": 0,
                "missing": _wire(planned),
                "allocated": 0,
                "dispatched": 0,
                "delivery_confirmed": 0,
                "uom": self._config["uom"],
                "cartons": 0,
                "initial_expected_cartons": initial_expected_cartons,
                "observed_outer_packages": 0,
            },
            "lots": lot_rows,
            "allocations": [
                {
                    "customer_order": _text(row["customer_order"], "customer_order"),
                    "requested_quantity": _wire(
                        _quantity(row["requested_quantity"], "requested_quantity")
                    ),
                    "priority": _whole(row["priority"], "priority", positive=True),
                    "allocated": 0,
                    "backordered": _wire(
                        _quantity(row["requested_quantity"], "requested_quantity")
                    ),
                    "dispatched": 0,
                    "reservation": "LOCAL_PLAN",
                    **(
                        {
                            "promised_delivery_at": row["promised_delivery_at"],
                            "customer_priority": row["customer_priority"],
                            "partial_dispatch": row["partial_dispatch"],
                            "minimum_dispatch_quantity": row["minimum_dispatch_quantity"],
                            "allow_final_remainder": row["allow_final_remainder"],
                        }
                        if contract_mode(self._config)
                        else {}
                    ),
                }
                for row in allocations
            ],
            "alerts": [],
            "events": [],
            "documents": [],
            "shipments": {},
            "prepared_picks": [],
            "allocation_retries": [],
            "conversation": [],
            "financials": {"status": "UNAVAILABLE", "reason": "FINANCIAL_NOT_PROVIDED"},
            "source_status": "UNAVAILABLE",
            "source_error": "ERP_SOURCE_NOT_READ",
            "source_observation": None,
        }

    def _initial_expected_cartons(self, lots: list[Mapping[str, object]]) -> int:
        if all("cartons" in row for row in lots):
            return sum(
                (
                    _whole(row["cartons"], "lot cartons", positive=True)
                    for row in lots
                    if row.get("replacement_for_lot") is None
                ),
                0,
            )
        return _whole(self._config["cartons"], "cartons", positive=True)

    def _next_recorded_at(self) -> str:
        """Return a cross-table ordering timestamp even when the configured clock is fixed."""

        row = self._db.execute(
            "SELECT MAX(recorded_at) FROM ("
            "SELECT recorded_at FROM distributor_operation_events "
            "UNION ALL SELECT recorded_at FROM distributor_allocation_retries"
            ")"
        ).fetchone()
        now = self._now()
        if row is not None and isinstance(row[0], str):
            try:
                prior = datetime.fromisoformat(row[0].replace("Z", "+00:00"))
            except ValueError:  # pragma: no cover - corrupt local store only
                prior = now
            if prior >= now:
                now = prior + timedelta(microseconds=1)
        return now.isoformat()

    def _latest_state(self) -> dict[str, object] | None:
        state, _recorded_at = self._latest_state_with_recorded_at()
        return state

    def _latest_state_with_recorded_at(self) -> tuple[dict[str, object] | None, str | None]:
        row = self._db.execute(
            "SELECT state_json, recorded_at FROM ("
            "SELECT state_json, recorded_at, rowid, 0 AS source_order "
            "FROM distributor_operation_events WHERE state_json IS NOT NULL "
            "UNION ALL "
            "SELECT state_json, recorded_at, rowid, 1 AS source_order "
            "FROM distributor_allocation_retries WHERE state_json IS NOT NULL"
            ") ORDER BY recorded_at DESC, source_order DESC, rowid DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None, None
        state_json, recorded_at = cast(tuple[str, str], row)
        return _decoded(state_json, "state"), recorded_at

    def _require_live_operations(self) -> None:
        if self._retained_projection:
            raise ValueError(
                "retained projection is read-only; live source evidence is required for this action"
            )

    def _pending_allocation_retry_projection(self, retry_id: str) -> dict[str, object]:
        projection = self.projection()
        projection["stage"] = "HOLD"
        projection["alerts"] = [
            *cast(list[object], projection["alerts"]),
            {
                "code": "ALLOCATION_RETRY_OUTCOME_UNKNOWN",
                "status": "OPEN",
                "message": (
                    "This retained allocation retry has no completed native outcome; "
                    "it will not be retried."
                ),
                "retry_id": retry_id,
            },
        ]
        return projection

    def _allocation_retry_event(
        self, state: Mapping[str, object], retry_id: str, pending_event_id: str
    ) -> dict[str, object]:
        events = state.get("events")
        for raw in events if isinstance(events, list) else []:
            if isinstance(raw, Mapping) and raw.get("event_id") == pending_event_id:
                evidence_ref = raw.get("evidence_ref")
                synthetic = raw.get("synthetic")
                return {
                    "event_id": retry_id,
                    "evidence_ref": evidence_ref
                    if isinstance(evidence_ref, str)
                    else f"retained:{pending_event_id}",
                    "synthetic": synthetic
                    if type(synthetic) is bool
                    else self._config["synthetic_input"],
                }
        return {
            "event_id": retry_id,
            "evidence_ref": f"retained:{pending_event_id}",
            "synthetic": self._config["synthetic_input"],
        }

    @staticmethod
    def _append_allocation_retry(
        state: dict[str, object], retry_id: str, pending_event_id: str
    ) -> dict[str, object]:
        retries = state.get("allocation_retries")
        if not isinstance(retries, list):
            retries = []
            state["allocation_retries"] = retries
        action: dict[str, object] = {
            "retry_id": retry_id,
            "pending_event_id": pending_event_id,
            "status": "PENDING",
            "operations": [],
        }
        retries.append(action)
        return action

    def _complete_allocation_retry(
        self,
        retry_id: str,
        state: Mapping[str, object],
        source: Mapping[str, object],
    ) -> dict[str, object]:
        projection = self._projection(state, source)
        self._db.execute("BEGIN IMMEDIATE")
        try:
            updated = self._db.execute(
                "UPDATE distributor_allocation_retries SET result_json=?, state_json=? "
                "WHERE retry_id=? AND result_json IS NULL",
                (_encode(projection), _encode(state), retry_id),
            ).rowcount
            if updated != 1:
                raise RuntimeError("allocation retry completion is unavailable")
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return projection

    def _projection_from_record(self, record: str) -> dict[str, object]:
        return _decoded(record, "event result")

    def _pending_projection(self, event_id: str) -> dict[str, object]:
        projection = self.projection()
        projection["stage"] = "HOLD"
        projection["alerts"] = [
            *cast(list[object], projection["alerts"]),
            {
                "code": "EVENT_OUTCOME_UNKNOWN",
                "status": "OPEN",
                "message": (
                    "This retained event has no completed native outcome; it will not be retried."
                ),
                "event_id": event_id,
            },
        ]
        return projection

    def _merge_source(
        self, state: Mapping[str, object], source: Mapping[str, object]
    ) -> tuple[dict[str, object], dict[str, object]]:
        next_state = cast(dict[str, object], _copy(state))
        current = cast(dict[str, object], _copy(source))
        if current["source_status"] == "CURRENT" and not self._source_matches_state(
            next_state, current
        ):
            current = self._source_unavailable("ERP_SOURCE_RECONCILIATION_UNKNOWN")
        next_state["source_status"] = current["source_status"]
        next_state["source_error"] = current.get("source_error")
        if current["source_status"] == "CURRENT":
            next_state["documents"] = _merge_documents(
                _documents(next_state.get("documents")), _documents(current.get("documents"))
            )
            parent_purchase_order = current.get("parent_purchase_order")
            if isinstance(parent_purchase_order, Mapping):
                next_state["parent_purchase_order"] = _copy(parent_purchase_order)
            else:
                next_state.pop("parent_purchase_order", None)
            next_state["financials"] = _copy(current["financials"])
            next_state["source_observation"] = {
                "quantities": _copy(current["quantities"]),
                "lots": _copy(current["lots"]),
                "allocations": _copy(current["allocations"]),
                "documents": _copy(current["documents"]),
                "parent_purchase_order": _copy(parent_purchase_order)
                if isinstance(parent_purchase_order, Mapping)
                else None,
                "financials": _copy(current["financials"]),
            }
        else:
            next_state.pop("parent_purchase_order", None)
            next_state["financials"] = {
                "status": "UNAVAILABLE",
                "reason": "ERP_SOURCE_UNAVAILABLE",
            }
        return next_state, current

    def _source_matches_state(
        self, state: Mapping[str, object], source: Mapping[str, object]
    ) -> bool:
        source_quantities = source.get("quantities")
        state_quantities = state.get("quantities")
        if not isinstance(source_quantities, Mapping) or not isinstance(state_quantities, Mapping):
            return False
        for field in (
            "ordered",
            "received",
            "usable",
            "held",
            "missing",
            "allocated",
            "dispatched",
            "cartons",
        ):
            try:
                if _quantity(source_quantities.get(field), f"source {field}") != _quantity(
                    state_quantities.get(field), field
                ):
                    return False
            except ValueError:
                return False
        if source_quantities.get("uom") != state_quantities.get("uom"):
            return False
        if not self._source_lots_match_state(state, source):
            return False
        return self._source_allocations_match_state(state, source)

    def _source_lots_match_state(
        self, state: Mapping[str, object], source: Mapping[str, object]
    ) -> bool:
        raw_state = state.get("lots")
        raw_source = source.get("lots")
        if not isinstance(raw_state, list) or not isinstance(raw_source, list):
            return False
        state_lots = {
            row.get("lot"): row
            for row in raw_state
            if isinstance(row, Mapping) and isinstance(row.get("lot"), str)
        }
        source_lots = {
            row.get("lot"): row
            for row in raw_source
            if isinstance(row, Mapping) and isinstance(row.get("lot"), str)
        }
        if set(state_lots) != set(source_lots) or len(state_lots) != len(raw_state):
            return False
        inspection_required = (
            cast(Mapping[str, object], self._config["policy"])["inspection_required"] is True
        )
        for lot, source_lot in source_lots.items():
            state_lot = state_lots[lot]
            try:
                for field in ("expected_quantity", "cartons", "received"):
                    if _quantity(source_lot.get(field), f"source lot {field}") != _quantity(
                        state_lot.get(field), f"lot {field}"
                    ):
                        return False
                # A non-batched R4 Delivery Note has no native lot-level outbound link.
                # Its retained pick evidence remains visible but cannot be presented as
                # native lot attribution. Quality cases do have a scoped stock movement.
                if inspection_required:
                    for field in ("usable", "held"):
                        if _quantity(source_lot.get(field), f"source lot {field}") != _quantity(
                            state_lot.get(field), f"lot {field}"
                        ):
                            return False
            except ValueError:
                return False
        return True

    @staticmethod
    def _source_allocations_match_state(
        state: Mapping[str, object], source: Mapping[str, object]
    ) -> bool:
        raw_state = state.get("allocations")
        raw_source = source.get("allocations")
        if not isinstance(raw_state, list) or not isinstance(raw_source, list):
            return False
        state_rows = {
            row.get("customer_order"): row
            for row in raw_state
            if isinstance(row, Mapping) and isinstance(row.get("customer_order"), str)
        }
        source_rows = {
            row.get("customer_order"): row
            for row in raw_source
            if isinstance(row, Mapping) and isinstance(row.get("customer_order"), str)
        }
        if set(state_rows) != set(source_rows) or len(state_rows) != len(raw_state):
            return False
        for order, source_row in source_rows.items():
            state_row = state_rows[order]
            try:
                for field in (
                    "requested_quantity",
                    "priority",
                    "allocated",
                    "backordered",
                    "dispatched",
                ):
                    if _quantity(source_row.get(field), f"source allocation {field}") != _quantity(
                        state_row.get(field), f"allocation {field}"
                    ):
                        return False
            except ValueError:
                return False
            if source_row.get("reservation") != state_row.get("reservation"):
                return False
        return True

    def _advance(
        self, state: dict[str, object], event: Mapping[str, object], source: Mapping[str, object]
    ) -> tuple[dict[str, object], str]:
        next_state = cast(dict[str, object], _copy(state))
        if source["source_status"] != "CURRENT":
            self._alert(
                next_state,
                code="SOURCE_UNAVAILABLE",
                message="Current ERP evidence is unavailable; no native operation was started.",
                event=event,
                error_code=cast(str, source.get("source_error") or "ERP_SOURCE_UNAVAILABLE"),
            )
            self._append_event(next_state, event, "UNAVAILABLE", [])
            return next_state, "UNAVAILABLE"
        event_type = cast(str, event["type"])
        if event_type == "arrival":
            return self._arrival(next_state, event)
        if event_type == "inspection":
            return self._inspection(next_state, event)
        if event_type == "picked":
            return self._picked(next_state, event)
        return self._carrier(next_state, event)

    def _arrival(
        self, state: dict[str, object], event: Mapping[str, object]
    ) -> tuple[dict[str, object], str]:
        operations: list[_NativeOutcome] = []
        item_code = _text(event["item_code"], "item_code")
        lot_name = _text(event["lot"], "lot")
        lot = self._lot(state, lot_name)
        observed = _quantity(
            event["observed_stock_quantity"], "observed_stock_quantity", positive=True
        )
        cartons = _whole(event["cartons"], "cartons", positive=True)
        pack = _quantity(event["expected_pack_quantity"], "expected_pack_quantity", positive=True)
        if item_code != self._config["item_code"]:
            self._alert(
                state,
                code="WRONG_SKU",
                message=(
                    "The arrival SKU does not match this configured case; no stock was received."
                ),
                event=event,
                lot=lot_name,
            )
            self._append_event(state, event, "BLOCKED", operations)
            return state, "BLOCKED"
        if lot is None:
            self._alert(
                state,
                code="UNKNOWN_LOT",
                message="The arrival lot is not configured for this case; no stock was received.",
                event=event,
                lot=lot_name,
            )
            self._append_event(state, event, "BLOCKED", operations)
            return state, "BLOCKED"
        configured_pack = self._expected_pack_for_lot(lot_name)
        if pack != configured_pack:
            self._alert(
                state,
                code="PACK_QUANTITY_MISMATCH",
                message=(
                    "The declared package quantity conflicts with the configured package quantity."
                ),
                event=event,
                lot=lot_name,
            )
            self._append_event(state, event, "BLOCKED", operations)
            return state, "BLOCKED"
        expected_for_cartons = Decimal(cartons) * pack
        if observed > expected_for_cartons:
            self._alert(
                state,
                code="OBSERVED_COUNT_EXCEEDS_PACKING",
                message=(
                    "The observed stock count exceeds the declared packing count; "
                    "no stock was received."
                ),
                event=event,
                lot=lot_name,
            )
            self._append_event(state, event, "BLOCKED", operations)
            return state, "BLOCKED"
        existing = _quantity(lot["received"], "lot received")
        allowed = _quantity(lot["expected_quantity"], "expected_quantity")
        if existing + observed > allowed:
            self._alert(
                state,
                code="LOT_OVER_RECEIPT",
                message=(
                    "The arrival would exceed the configured lot quantity; no stock was received."
                ),
                event=event,
                lot=lot_name,
            )
            self._append_event(state, event, "BLOCKED", operations)
            return state, "BLOCKED"
        receipt = self._native(
            "receive_arrival",
            event,
            {
                "item_code": item_code,
                "lot": lot_name,
                "cartons": cartons,
                "expected_pack_quantity": _wire(pack),
                "observed_stock_quantity": _wire(observed),
                "evidence_ref": event["evidence_ref"],
                "synthetic": event["synthetic"],
            },
        )
        operations.append(receipt)
        if not receipt.succeeded:
            self._native_alert(state, event, receipt, lot_name)
            self._append_event(state, event, receipt.status, operations)
            return state, receipt.status
        lot["cartons"] = _whole(lot["cartons"], "lot cartons") + cartons
        lot["received"] = _wire(existing + observed)
        if cast(Mapping[str, object], self._config["policy"])["inspection_required"] is True:
            lot["held"] = _wire(_quantity(lot["held"], "lot held") + observed)
            lot["status"] = "PENDING_INSPECTION"
            self._alert(
                state,
                code="QUALITY_EVIDENCE_REQUIRED",
                message="Received stock is held until configured inspection evidence is recorded.",
                event=event,
                lot=lot_name,
                quantity=observed,
            )
        else:
            lot["usable"] = _wire(_quantity(lot["usable"], "lot usable") + observed)
            lot["status"] = "USABLE"
            self._recompute_allocations(state)
            prepared = self._prepare_pick(state, event)
            operations.extend(prepared)
        if observed < expected_for_cartons:
            self._alert(
                state,
                code="PARTS_SHORTAGE",
                message=(
                    "Observed stock is below the declared package count; "
                    "the short quantity remains unreceived."
                ),
                event=event,
                lot=lot_name,
                quantity=expected_for_cartons - observed,
            )
        self._recompute_quantities(state)
        replacement_for_lot = self._replacement_for_lot(lot_name)
        quantities = cast(Mapping[str, object], state["quantities"])
        if (
            replacement_for_lot is not None
            and _quantity(lot["received"], "lot received")
            == _quantity(lot["expected_quantity"], "expected_quantity")
            and _quantity(quantities["received"], "received")
            == _quantity(quantities["ordered"], "ordered")
        ):
            self._resolve_alerts(state, {"PARTS_SHORTAGE"}, replacement_for_lot)
        status = self._operations_status(operations)
        self._append_event(state, event, status, operations)
        return state, status

    def _inspection(
        self, state: dict[str, object], event: Mapping[str, object]
    ) -> tuple[dict[str, object], str]:
        operations: list[_NativeOutcome] = []
        lot_name = _text(event["lot"], "lot")
        lot = self._lot(state, lot_name)
        if lot is None or _quantity(lot["received"], "lot received") == 0:
            self._alert(
                state,
                code="UNKNOWN_LOT",
                message=(
                    "Inspection references no received configured lot; no quality release was made."
                ),
                event=event,
                lot=lot_name,
            )
            self._append_event(state, event, "BLOCKED", operations)
            return state, "BLOCKED"
        criteria = cast(Mapping[str, object], self._config["policy"]).get("inspection_criteria")
        bounds = criteria.get(event["metric"]) if isinstance(criteria, Mapping) else None
        if not isinstance(bounds, Mapping):
            self._alert(
                state,
                code="INSPECTION_CRITERION_UNAVAILABLE",
                message=(
                    "No configured quality criterion covers this measurement; the lot remains held."
                ),
                event=event,
                lot=lot_name,
            )
            self._append_event(state, event, "BLOCKED", operations)
            return state, "BLOCKED"
        measured = _quantity(event["measured"], "measured")
        minimum = _quantity(bounds["minimum"], "inspection minimum")
        maximum = _quantity(bounds["maximum"], "inspection maximum")
        derived_result = "PASS" if minimum <= measured <= maximum else "FAIL"
        if event["result"] != derived_result:
            self._alert(
                state,
                code="INSPECTION_RESULT_CONFLICT",
                message=(
                    "The declared inspection result conflicts with the configured "
                    "measurement criterion."
                ),
                event=event,
                lot=lot_name,
            )
            self._append_event(state, event, "BLOCKED", operations)
            return state, "BLOCKED"
        tested = _quantity(event["sample_quantity"], "sample_quantity", positive=True)
        lot_received = _quantity(lot["received"], "lot received")
        inspection_evidence = self._inspection_evidence(event, bounds, lot_received)
        if event["scope"] == "WHOLE_LOT" and tested < lot_received:
            self._alert(
                state,
                code="WHOLE_LOT_EVIDENCE_INCOMPLETE",
                message="Whole-lot release needs a report covering the received lot quantity.",
                event=event,
                lot=lot_name,
                quantity=lot_received - tested,
                extra=inspection_evidence,
            )
            self._append_event(state, event, "BLOCKED", operations)
            return state, "BLOCKED"
        inspection = self._native(
            "record_inspection",
            event,
            {
                "lot": lot_name,
                "result": event["result"],
                "scope": event["scope"],
                "metric": event["metric"],
                "measured": event["measured"],
                "criterion": _copy(bounds),
                "sample_quantity": event["sample_quantity"],
                "inspection_report_ref": event["inspection_report_ref"],
                "evidence_ref": event["evidence_ref"],
                "synthetic": event["synthetic"],
            },
        )
        operations.append(inspection)
        if not inspection.succeeded:
            self._native_alert(state, event, inspection, lot_name)
            self._append_event(state, event, inspection.status, operations)
            return state, inspection.status
        if event["result"] == "FAIL":
            quantity = _quantity(lot["received"], "lot received")
            lot["usable"] = 0
            lot["held"] = _wire(quantity)
            lot["status"] = "QUALITY_HOLD"
            self._resolve_alerts(state, {"QUALITY_EVIDENCE_REQUIRED"}, lot_name)
            self._alert(
                state,
                code="QUALITY_FAILED",
                message=(
                    "A sample measurement failed. The lot is held pending supported disposition; "
                    "this does not establish every held unit is defective."
                ),
                event=event,
                lot=lot_name,
                quantity=quantity,
                extra={**inspection_evidence, "held_quantity": _wire(quantity)},
            )
            self._recompute_allocations(state)
        elif event["scope"] != "WHOLE_LOT":
            self._alert(
                state,
                code="QUALITY_EVIDENCE_REQUIRED",
                message=(
                    "A sample pass does not release this configured lot; whole-lot evidence is due."
                ),
                event=event,
                lot=lot_name,
                extra=inspection_evidence,
            )
        else:
            release = self._native(
                "release_from_quality",
                event,
                {
                    "lot": lot_name,
                    "inspection_evidence_ref": event["evidence_ref"],
                    "scope": event["scope"],
                    "synthetic": event["synthetic"],
                },
            )
            operations.append(release)
            if release.succeeded:
                quantity = _quantity(lot["received"], "lot received")
                lot["usable"] = _wire(quantity)
                lot["held"] = 0
                lot["status"] = "USABLE"
                self._resolve_alerts(
                    state, {"QUALITY_EVIDENCE_REQUIRED", "QUALITY_FAILED"}, lot_name
                )
                self._recompute_allocations(state)
                operations.extend(self._prepare_pick(state, event))
            else:
                self._native_alert(state, event, release, lot_name)
        self._recompute_quantities(state)
        status = self._operations_status(operations)
        self._append_event(state, event, status, operations)
        return state, status

    def _picked(
        self, state: dict[str, object], event: Mapping[str, object]
    ) -> tuple[dict[str, object], str]:
        operations: list[_NativeOutcome] = []
        order = _text(event["customer_order"], "customer_order")
        lot_name = _text(event["lot"], "lot")
        quantity = _quantity(event["quantity"], "quantity", positive=True)
        lot = self._lot(state, lot_name)
        allocation = self._allocation(state, order)
        available = _quantity(lot["usable"], "lot usable") if lot is not None else Decimal()
        eligible = (
            _quantity(allocation["allocated"], "allocated") if allocation is not None else Decimal()
        )
        prepared = self._prepared_tranches(state, order, quantity)
        if (
            prepared is None
            and lot is not None
            and allocation is not None
            and quantity <= available
            and quantity <= eligible
        ):
            operations.extend(self._prepare_pick(state, event))
            prepared = self._prepared_tranches(state, order, quantity)
        if (
            lot is None
            or allocation is None
            or quantity > available
            or quantity > eligible
            or prepared is None
        ):
            self._alert(
                state,
                code="PICK_NOT_ELIGIBLE",
                message=(
                    "The picked quantity is not backed by usable stock and an eligible allocation."
                ),
                event=event,
                lot=lot_name,
                quantity=quantity,
                orders=[order],
            )
            status = (
                "UNKNOWN_OUTCOME"
                if any(outcome.status == "UNKNOWN_OUTCOME" for outcome in operations)
                else "BLOCKED"
            )
            self._append_event(state, event, status, operations)
            return state, status
        picked = self._native(
            "submit_pick",
            event,
            {
                "customer_order": order,
                "lot": lot_name,
                "quantity": _wire(quantity),
                "pick_evidence_ref": event["pick_evidence_ref"],
                "prepared_tranches": prepared or [],
                "synthetic": event["synthetic"],
            },
        )
        operations.append(picked)
        if not picked.succeeded:
            self._native_alert(state, event, picked, lot_name)
            self._append_event(state, event, picked.status, operations)
            return state, picked.status
        delivery = self._native(
            "submit_delivery_note",
            event,
            {
                "customer_order": order,
                "lot": lot_name,
                "quantity": _wire(quantity),
                "pick_evidence_ref": event["pick_evidence_ref"],
                "synthetic": event["synthetic"],
            },
        )
        operations.append(delivery)
        if not delivery.succeeded:
            self._native_alert(state, event, delivery, lot_name)
            self._append_event(state, event, delivery.status, operations)
            return state, delivery.status
        lot["usable"] = _wire(available - quantity)
        allocation["dispatched"] = _wire(
            _quantity(allocation["dispatched"], "dispatched") + quantity
        )
        self._consume_prepared(state, order, quantity)
        shipment_id = self._shipment_id(order, _text(event["event_id"], "event_id"))
        if shipment_id is None:
            self._alert(
                state,
                code="SHIPMENT_POLICY_MISSING",
                message="No exact configured shipment identity covers this picked event.",
                event=event,
                lot=lot_name,
                quantity=quantity,
                orders=[order],
            )
            self._append_event(state, event, "BLOCKED", operations)
            return state, "BLOCKED"
        shipment = self._native(
            "create_shipment",
            event,
            {
                "customer_order": order,
                "lot": lot_name,
                "quantity": _wire(quantity),
                "shipment_id": shipment_id,
                "pick_evidence_ref": event["pick_evidence_ref"],
                "synthetic": event["synthetic"],
            },
        )
        operations.append(shipment)
        self._recompute_allocations(state)
        if shipment.succeeded:
            self._track_shipment(state, event, shipment, order, lot_name, quantity)
        else:
            self._native_alert(state, event, shipment, lot_name)
        self._recompute_quantities(state)
        status = self._operations_status(operations)
        self._append_event(state, event, status, operations)
        return state, status

    def _carrier(
        self, state: dict[str, object], event: Mapping[str, object]
    ) -> tuple[dict[str, object], str]:
        shipment_id = _text(event["shipment_id"], "shipment_id")
        shipments = cast(dict[str, object], state["shipments"])
        raw = shipments.get(shipment_id)
        shipment = raw if isinstance(raw, dict) else None
        if shipment is None:
            self._alert(
                state,
                code="SHIPMENT_NOT_FOUND",
                message=(
                    "Carrier evidence does not reference an exact shipment created for this case."
                ),
                event=event,
            )
            self._append_event(state, event, "BLOCKED", [])
            return state, "BLOCKED"
        if event["type"] == "carrier_pickup":
            shipment["picked_up"] = True
            self._append_event(state, event, "APPLIED", [])
            return state, "APPLIED"
        if shipment.get("picked_up") is not True:
            self._alert(
                state,
                code="PICKUP_EVIDENCE_REQUIRED",
                message=(
                    "Delivery confirmation needs prior carrier pickup evidence "
                    "for this exact shipment."
                ),
                event=event,
            )
            self._append_event(state, event, "BLOCKED", [])
            return state, "BLOCKED"
        if shipment.get("delivered") is not True:
            shipment["delivered"] = True
            quantities = cast(dict[str, object], state["quantities"])
            quantities["delivery_confirmed"] = _wire(
                _quantity(quantities["delivery_confirmed"], "delivery_confirmed")
                + _quantity(shipment["quantity"], "shipment quantity")
            )
        self._append_event(state, event, "APPLIED", [])
        return state, "APPLIED"

    def _native(
        self,
        kind: str,
        event: Mapping[str, object],
        fields: Mapping[str, object],
    ) -> _NativeOutcome:
        if self._erp is None:
            return _NativeOutcome(
                kind=kind,
                status="UNKNOWN_OUTCOME",
                documents=[],
                error_code="ERP_ADAPTER_UNAVAILABLE",
            )
        operation = {"kind": kind, **cast(dict[str, object], _copy(fields))}
        try:
            raw = self._erp.apply_operation(
                self._config, operation, _text(event["event_id"], "event_id")
            )
        except Exception:
            return _NativeOutcome(
                kind=kind,
                status="UNKNOWN_OUTCOME",
                documents=[],
                error_code="ERP_OPERATION_UNAVAILABLE",
            )
        if not isinstance(raw, Mapping) or raw.get("operation") != kind:
            return _NativeOutcome(
                kind=kind,
                status="UNKNOWN_OUTCOME",
                documents=[],
                error_code="ERP_OPERATION_MALFORMED",
            )
        status = raw.get("status")
        if not isinstance(status, str) or status not in _WRITE_STATUSES:
            return _NativeOutcome(
                kind=kind,
                status="UNKNOWN_OUTCOME",
                documents=[],
                error_code="ERP_OPERATION_MALFORMED",
            )
        error_code = raw.get("error_code")
        return _NativeOutcome(
            kind=kind,
            status=status,
            documents=_documents(raw.get("documents")),
            error_code=error_code if isinstance(error_code, str) and error_code else None,
        )

    def _prepare_pick(
        self,
        state: dict[str, object],
        event: Mapping[str, object],
        *,
        resolve_pending_event_id: str | None = None,
        retry_id: str | None = None,
    ) -> list[_NativeOutcome]:
        if contract_mode(self._config):
            plan = self._contract_plan(state)
            if _quantity(plan["new_quantity"], "contract plan new quantity") <= 0:
                return []
            tranches = self._contract_plan_native_tranches(plan, state)
            if tranches is None:
                self._alert(
                    state,
                    code="ALLOCATION_PLAN_NATIVE_TRANCHE_UNSUPPORTED",
                    message=(
                        "The compiled contract quantities do not match configured native pick "
                        "tranches; no pick preparation was started."
                    ),
                    event=event,
                )
                return []
            plan = {**plan, "native_tranches": tranches}
            if not self._select_contract_plan(
                state,
                event,
                plan,
                retry_id=retry_id,
                pending_event_id=resolve_pending_event_id,
            ):
                return []
        allocations = cast(list[dict[str, object]], state["allocations"])
        prepared_rows = cast(list[dict[str, object]], state["prepared_picks"])
        already_prepared: dict[str, Decimal] = {}
        for row in prepared_rows:
            order = row.get("customer_order")
            if isinstance(order, str):
                already_prepared[order] = already_prepared.get(order, Decimal()) + _quantity(
                    row.get("remaining", 0), "prepared pick quantity"
                )
        planned = [
            {
                "customer_order": row["customer_order"],
                "quantity": _wire(
                    _quantity(row["allocated"], "allocated")
                    - already_prepared.get(cast(str, row["customer_order"]), Decimal())
                ),
                "priority": row["priority"],
            }
            for row in allocations
            if _quantity(row["allocated"], "allocated")
            > already_prepared.get(cast(str, row["customer_order"]), Decimal())
        ]
        if contract_mode(self._config):
            native_tranches = cast(list[Mapping[str, object]], plan["native_tranches"])
            lots_by_order = {
                _text(row["customer_order"], "contract plan customer order"): _text(
                    row["lot"], "contract plan lot"
                )
                for row in native_tranches
            }
            for row in planned:
                row["lot"] = lots_by_order[_text(row["customer_order"], "customer_order")]
        if not planned:
            return []
        outcomes: list[_NativeOutcome] = []
        policy = cast(Mapping[str, object], self._config["policy"])
        if policy["reservation_supported"] is True:
            reservation = self._native("reserve_allocation", event, {"allocations": planned})
            outcomes.append(reservation)
            if not reservation.succeeded:
                self._native_alert(state, event, reservation, None)
                return outcomes
            for row in allocations:
                if _quantity(row["allocated"], "allocated") > 0:
                    row["reservation"] = "NATIVE_RESERVED"
        else:
            for row in allocations:
                if _quantity(row["allocated"], "allocated") > 0:
                    row["reservation"] = "LOCAL_PLAN"
        retained = cast(list[dict[str, object]], state["prepared_picks"])
        for row in planned:
            prepared_outcome = self._native(
                "prepare_pick",
                event,
                {
                    "customer_order": row["customer_order"],
                    "quantity": row["quantity"],
                    "priority": row["priority"],
                },
            )
            outcomes.append(prepared_outcome)
            if prepared_outcome.succeeded:
                retained.append(
                    {
                        "customer_order": row["customer_order"],
                        "remaining": row["quantity"],
                        "event_id": event["event_id"],
                        "documents": _copy(prepared_outcome.documents),
                        **({"lot": row["lot"]} if "lot" in row else {}),
                    }
                )
            else:
                self._native_alert(state, event, prepared_outcome, None)
        if outcomes and all(outcome.succeeded for outcome in outcomes):
            self._resolve_native_operation_alerts(state, "prepare_pick")
            self._resolve_pending_allocation_alert(
                state, resolve_pending_event_id or _text(event["event_id"], "event_id")
            )
        return outcomes

    def _contract_plan_native_tranches(
        self, plan: Mapping[str, object], state: Mapping[str, object]
    ) -> list[dict[str, object]] | None:
        configured = self._config.get("pick_tranches")
        if not isinstance(configured, list):
            return None
        rows = plan.get("rows")
        if not isinstance(rows, list):
            return None
        selected: list[dict[str, object]] = []
        for row in rows:
            if not isinstance(row, Mapping):
                return None
            quantity = _quantity(row.get("new_quantity"), "contract plan new quantity")
            if not quantity:
                continue
            matches = [
                tranche
                for tranche in configured
                if isinstance(tranche, Mapping)
                and tranche.get("customer_order") == row.get("customer_order")
                and _quantity(tranche.get("quantity"), "configured pick tranche quantity")
                == quantity
            ]
            if len(matches) != 1:
                return None
            tranche = matches[0]
            lot = tranche.get("lot")
            if not isinstance(lot, str) or not lot:
                return None
            selected.append(
                {
                    "customer_order": row["customer_order"],
                    "quantity": _wire(quantity),
                    "lot": lot,
                }
            )
        lots = {
            row.get("lot"): _quantity(row.get("usable"), "lot usable")
            for row in cast(list[Mapping[str, object]], state.get("lots", []))
            if isinstance(row.get("lot"), str)
        }
        committed: dict[str, Decimal] = {}
        prepared = state.get("prepared_picks")
        if not isinstance(prepared, list):
            return None
        for row in prepared:
            if not isinstance(row, Mapping) or not isinstance(row.get("lot"), str):
                return None
            lot = cast(str, row["lot"])
            committed[lot] = committed.get(lot, Decimal()) + _quantity(
                row.get("remaining"), "prepared pick quantity"
            )
        for row in selected:
            lot = cast(str, row["lot"])
            committed[lot] = committed.get(lot, Decimal()) + _quantity(
                row["quantity"], "contract plan tranche quantity"
            )
        if any(lot not in lots or quantity > lots[lot] for lot, quantity in committed.items()):
            return None
        return selected

    def _prepared_tranches(
        self, state: Mapping[str, object], order: str, quantity: Decimal
    ) -> list[dict[str, object]] | None:
        remaining = quantity
        result: list[dict[str, object]] = []
        rows = state.get("prepared_picks")
        if not isinstance(rows, list):
            return None
        for row in rows:
            if not isinstance(row, Mapping) or row.get("customer_order") != order:
                continue
            available = _quantity(row.get("remaining", 0), "prepared pick quantity")
            if available <= 0:
                continue
            selected = min(available, remaining)
            result.append(
                {
                    "event_id": row.get("event_id"),
                    "quantity": _wire(selected),
                    "documents": _copy(row.get("documents", [])),
                }
            )
            remaining -= selected
            if remaining == 0:
                return result
        return None

    def _shipment_id(self, customer_order: str, event_id: str) -> str | None:
        shipping = self._config.get("shipping")
        if not isinstance(shipping, Mapping):
            return None
        shipments = shipping.get("shipments")
        if not isinstance(shipments, Mapping):
            return None
        details = shipments.get(customer_order)
        if not isinstance(details, Mapping):
            return None
        try:
            prefix = _text(details.get("shipment_id_prefix"), "shipment ID prefix")
        except ValueError:
            return None
        identity = "|".join((str(self._config["case_id"]), customer_order, event_id))
        return f"{prefix}-{sha256(identity.encode()).hexdigest()[:12]}"

    def _resume_blocked_shipment(
        self, state: dict[str, object], current_event: Mapping[str, object]
    ) -> None:
        prior_event_id = self._pending_blocked_shipment_event(state)
        if prior_event_id is None:
            return
        prior_event = self._stored_picked_event(prior_event_id)
        if prior_event is None:
            return
        order = _text(prior_event["customer_order"], "customer_order")
        lot_name = _text(prior_event["lot"], "lot")
        quantity = _quantity(prior_event["quantity"], "quantity", positive=True)
        shipment_id = self._shipment_id(order, prior_event_id)
        if shipment_id is None:
            return
        shipment = self._native(
            "create_shipment",
            prior_event,
            {
                "customer_order": order,
                "lot": lot_name,
                "quantity": _wire(quantity),
                "shipment_id": shipment_id,
                "pick_evidence_ref": prior_event["pick_evidence_ref"],
                "synthetic": prior_event["synthetic"],
            },
        )
        self._append_resumed_operation(state, prior_event_id, shipment)
        if shipment.succeeded:
            if self._track_shipment(state, current_event, shipment, order, lot_name, quantity):
                self._resolve_native_operation_alerts(state, "create_shipment", prior_event_id)
        else:
            self._native_alert(state, current_event, shipment, lot_name)

    def _pending_blocked_shipment_event(self, state: Mapping[str, object]) -> str | None:
        events = state.get("events")
        if not isinstance(events, list):
            return None
        resumed = {
            operation.get("resumed_from_event_id")
            for event in events
            if isinstance(event, Mapping)
            for operation in event.get("operations", [])
            if isinstance(operation, Mapping)
            and isinstance(operation.get("resumed_from_event_id"), str)
        }
        for event in reversed(events):
            if not isinstance(event, Mapping) or event.get("type") != "picked":
                continue
            event_id = event.get("event_id")
            operations = event.get("operations")
            if (
                not isinstance(event_id, str)
                or event_id in resumed
                or not isinstance(operations, list)
            ):
                continue
            submitted = any(
                isinstance(operation, Mapping)
                and operation.get("kind") == "submit_delivery_note"
                and operation.get("status") in _SUCCESS
                for operation in operations
            )
            shipment_blocked = any(
                isinstance(operation, Mapping)
                and operation.get("kind") == "create_shipment"
                and operation.get("status") == "BLOCKED"
                for operation in operations
            )
            if submitted and shipment_blocked:
                return event_id
        return None

    def _stored_picked_event(self, event_id: str) -> dict[str, object] | None:
        payload = self._stored_event(event_id)
        return payload if payload is not None and payload.get("type") == "picked" else None

    def _stored_event(self, event_id: str) -> dict[str, object] | None:
        row = self._db.execute(
            "SELECT payload_json FROM distributor_operation_events WHERE event_id=?", (event_id,)
        ).fetchone()
        if row is None:
            return None
        try:
            payload = self._validate_event(_decoded(cast(str, row[0]), "event payload"))
        except (RuntimeError, ValueError):
            return None
        return payload

    def _append_resumed_operation(
        self, state: dict[str, object], prior_event_id: str, outcome: _NativeOutcome
    ) -> None:
        events = cast(list[dict[str, object]], state["events"])
        if not events:  # pragma: no cover - caller appends the new physical event first
            return
        record = outcome.record()
        record["resumed_from_event_id"] = prior_event_id
        current = events[-1]
        operations = cast(list[dict[str, object]], current["operations"])
        operations.append(record)
        if not outcome.succeeded:
            current["status"] = outcome.status
        state["documents"] = _merge_documents(_documents(state.get("documents")), outcome.documents)

    def _track_shipment(
        self,
        state: dict[str, object],
        event: Mapping[str, object],
        shipment: _NativeOutcome,
        order: str,
        lot_name: str,
        quantity: Decimal,
    ) -> bool:
        shipment_names = [
            name
            for document in shipment.documents
            if document.get("kind") == "Shipment" and isinstance(name := document.get("name"), str)
        ]
        if not shipment_names:
            self._alert(
                state,
                code="SHIPMENT_ID_UNAVAILABLE",
                message=(
                    "Dispatch is recorded, but no exact shipment identifier was returned "
                    "for carrier evidence."
                ),
                event=event,
                lot=lot_name,
                quantity=quantity,
                orders=[order],
            )
            return False
        tracked = cast(dict[str, object], state["shipments"])
        for name in shipment_names:
            tracked[name] = {
                "quantity": _wire(quantity),
                "customer_order": order,
                "lot": lot_name,
                "picked_up": False,
                "delivered": False,
                "synthetic": event["synthetic"],
            }
        return True

    def _expected_pack_for_lot(self, lot_name: str) -> Decimal:
        configured = self._configured_lot(lot_name)
        return _quantity(
            configured.get("expected_pack_quantity", self._config["expected_pack_quantity"]),
            "expected_pack_quantity",
            positive=True,
        )

    def _replacement_for_lot(self, lot_name: str) -> str | None:
        replacement = self._configured_lot(lot_name).get("replacement_for_lot")
        return _text(replacement, "replacement_for_lot") if replacement is not None else None

    def _configured_lot(self, lot_name: str) -> Mapping[str, object]:
        lots = cast(list[Mapping[str, object]], self._config["lots"])
        matches = [row for row in lots if row.get("lot") == lot_name]
        if len(matches) != 1:  # pragma: no cover - constructor validates configured identities
            raise RuntimeError("configured lot is unavailable")
        return matches[0]

    @staticmethod
    def _inspection_evidence(
        event: Mapping[str, object], bounds: Mapping[str, object], lot_received: Decimal
    ) -> dict[str, object]:
        return {
            "scope": event["scope"],
            "sample_quantity": event["sample_quantity"],
            "metric": event["metric"],
            "measured": event["measured"],
            "criterion": _copy(bounds),
            "required_lot_quantity": _wire(lot_received),
            "inspection_report_ref": event["inspection_report_ref"],
        }

    @staticmethod
    def _consume_prepared(state: dict[str, object], order: str, quantity: Decimal) -> None:
        remaining = quantity
        rows = cast(list[dict[str, object]], state["prepared_picks"])
        for row in rows:
            if row.get("customer_order") != order or remaining <= 0:
                continue
            available = _quantity(row.get("remaining", 0), "prepared pick quantity")
            consumed = min(available, remaining)
            row["remaining"] = _wire(available - consumed)
            remaining -= consumed

    def _lot(self, state: Mapping[str, object], lot_name: str) -> dict[str, object] | None:
        lots = state.get("lots")
        if not isinstance(lots, list):
            return None
        return next(
            (
                cast(dict[str, object], lot)
                for lot in lots
                if isinstance(lot, dict) and lot.get("lot") == lot_name
            ),
            None,
        )

    def _allocation(self, state: Mapping[str, object], order: str) -> dict[str, object] | None:
        allocations = state.get("allocations")
        if not isinstance(allocations, list):
            return None
        return next(
            (
                cast(dict[str, object], row)
                for row in allocations
                if isinstance(row, dict) and row.get("customer_order") == order
            ),
            None,
        )

    def _recompute_allocations(self, state: dict[str, object]) -> None:
        if contract_mode(self._config):
            plan = self._contract_plan(state)
            by_order = {
                row["customer_order"]: row for row in cast(list[Mapping[str, object]], plan["rows"])
            }
            for row in cast(list[dict[str, object]], state["allocations"]):
                selected = by_order[cast(str, row["customer_order"])]
                quantity = _quantity(selected["quantity"], "contract allocation")
                requested = _quantity(row["requested_quantity"], "requested_quantity")
                dispatched = _quantity(row["dispatched"], "dispatched")
                row["allocated"] = _wire(quantity)
                row["backordered"] = _wire(max(Decimal(), requested - dispatched - quantity))
            state["feasible_allocation_plan"] = _copy(plan)
            return
        lots = cast(list[dict[str, object]], state["lots"])
        available = sum((_quantity(row["usable"], "lot usable") for row in lots), Decimal())
        allocations = cast(list[dict[str, object]], state["allocations"])
        for row in sorted(allocations, key=lambda item: cast(int, item["priority"])):
            requested = _quantity(row["requested_quantity"], "requested_quantity")
            dispatched = _quantity(row["dispatched"], "dispatched")
            remaining = max(Decimal(), requested - dispatched)
            allocation = min(remaining, available)
            row["allocated"] = _wire(allocation)
            row["backordered"] = _wire(remaining - allocation)
            available -= allocation

    def _contract_plan(self, state: Mapping[str, object]) -> dict[str, object]:
        try:
            return compile_plan(
                allocations=state.get("allocations"),
                lots=state.get("lots"),
                prepared_picks=state.get("prepared_picks"),
            )
        except ContractAllocationError as error:  # validated config; malformed retained state only
            raise RuntimeError(str(error)) from error

    @staticmethod
    def _selection_refs_are_exact(plan: Mapping[str, object], choice: Mapping[str, object]) -> bool:
        refs = choice.get("contract_refs")
        if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
            return False
        rows = plan.get("rows")
        if not isinstance(rows, list):
            return False
        try:
            valid = {
                row.get("customer_order")
                for row in rows
                if isinstance(row, Mapping)
                and isinstance(row.get("customer_order"), str)
                and _quantity(row.get("new_quantity"), "contract plan new quantity") > 0
            }
        except ValueError:
            return False
        return len(refs) == len(valid) and len(set(refs)) == len(refs) and set(refs) == valid

    @staticmethod
    def _selection_audit(choice: Mapping[str, object]) -> dict[str, object]:
        """Retain bounded structured selection fields without storing arbitrary model output."""

        plan_id = choice.get("plan_id")
        rationale = choice.get("rationale")
        refs = choice.get("contract_refs")
        return {
            "plan_id": plan_id.strip()
            if isinstance(plan_id, str) and len(plan_id) <= 128
            else None,
            "rationale": (
                rationale.strip()
                if isinstance(rationale, str) and len(rationale.strip()) <= 480
                else None
            ),
            "contract_refs": (
                [ref.strip() for ref in refs if isinstance(ref, str) and ref.strip()][:16]
                if isinstance(refs, list)
                else []
            ),
        }

    def _selection_validation_failures(
        self, plan: Mapping[str, object], choice: Mapping[str, object]
    ) -> list[str]:
        failures: list[str] = []
        if choice.get("plan_id") != plan.get("plan_id"):
            failures.append("PLAN_ID_MISMATCH_OR_DEFERRED")
        rationale = choice.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip() or len(rationale.strip()) > 480:
            failures.append("RATIONALE_INVALID")
        if not self._selection_refs_are_exact(plan, choice):
            failures.append("EXECUTABLE_CONTRACT_REFS_INVALID")
        return failures

    def _select_contract_plan(
        self,
        state: dict[str, object],
        event: Mapping[str, object],
        plan: Mapping[str, object],
        *,
        retry_id: str | None = None,
        pending_event_id: str | None = None,
    ) -> bool:
        existing = state.get("allocation_decision")
        if (
            isinstance(existing, Mapping)
            and existing.get("status") == "SELECTED"
            and existing.get("plan_id") == plan.get("plan_id")
            and existing.get("state_revision") == plan.get("state_revision")
        ):
            return True
        selector = self._allocation_selector
        if selector is None:
            choice: Mapping[str, object] = {"plan_id": "DEFER", "rationale": "selector unavailable"}
        else:
            try:
                raw = selector(plan)
                choice = raw if isinstance(raw, Mapping) else {}
            except Exception:
                choice = {"plan_id": "DEFER", "rationale": "selector unavailable"}
        plan_id = choice.get("plan_id")
        rationale = choice.get("rationale")
        validation_failures = self._selection_validation_failures(plan, choice)
        decision_event_id = pending_event_id or _text(event["event_id"], "event_id")
        if not validation_failures:
            decision: dict[str, object] = {
                "status": "SELECTED",
                "case_id": self._config["case_id"],
                "plan_id": plan_id,
                "state_revision": plan["state_revision"],
                "event_id": decision_event_id,
                "rationale": cast(str, rationale).strip(),
                "contract_refs": list(cast(list[str], choice["contract_refs"])),
                "plan": _copy(plan),
                "selection": self._selection_audit(choice),
            }
            if retry_id is not None:
                decision["retry_id"] = retry_id
            for field in ("provider", "usage"):
                value = choice.get(field)
                if isinstance(value, Mapping):
                    decision[field] = _copy(value)
            state["allocation_decision"] = decision
            self._checkpoint_allocation_decision(event["event_id"], state, retry_id=retry_id)
            return True
        decision = {
            "status": "PENDING",
            "case_id": self._config["case_id"],
            "plan_id": plan["plan_id"],
            "state_revision": plan["state_revision"],
            "event_id": decision_event_id,
            "rationale": rationale.strip()
            if isinstance(rationale, str) and rationale.strip() and len(rationale.strip()) <= 480
            else "deferred",
            "plan": _copy(plan),
            "selection": self._selection_audit(choice),
            "validation_failures": validation_failures,
        }
        if retry_id is not None:
            decision["retry_id"] = retry_id
        for field in ("provider", "usage"):
            value = choice.get(field)
            if isinstance(value, Mapping):
                decision[field] = _copy(value)
        state["allocation_decision"] = decision
        self._checkpoint_allocation_decision(event["event_id"], state, retry_id=retry_id)
        if retry_id is None:
            self._alert(
                state,
                code="ALLOCATION_SELECTION_PENDING",
                message=(
                    "The contract allocation plan was deferred or malformed; no pick preparation "
                    "was started."
                ),
                event=event,
            )
        return False

    def _checkpoint_allocation_decision(
        self, event_id: object, state: Mapping[str, object], *, retry_id: str | None = None
    ) -> None:
        """Persist an accepted/deferred selection before a native prepare can begin."""

        identifier = _text(retry_id or event_id, "allocation selection checkpoint ID")
        table = (
            "distributor_allocation_retries"
            if retry_id is not None
            else "distributor_operation_events"
        )
        key = "retry_id" if retry_id is not None else "event_id"
        self._db.execute("BEGIN IMMEDIATE")
        try:
            updated = self._db.execute(
                f"UPDATE {table} SET state_json=? WHERE {key}=? AND result_json IS NULL",
                (_encode(state), identifier),
            ).rowcount
            if updated != 1:
                raise RuntimeError("allocation decision checkpoint is unavailable")
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

    @staticmethod
    def _resolve_pending_allocation_alert(state: dict[str, object], event_id: str) -> None:
        for alert in cast(list[dict[str, object]], state["alerts"]):
            if (
                alert.get("code") == "ALLOCATION_SELECTION_PENDING"
                and alert.get("event_id") == event_id
                and alert.get("status") == "OPEN"
            ):
                alert["status"] = "RESOLVED"

    def _recompute_quantities(self, state: dict[str, object]) -> None:
        quantities = cast(dict[str, object], state["quantities"])
        lots = cast(list[dict[str, object]], state["lots"])
        allocations = cast(list[dict[str, object]], state["allocations"])
        received = sum((_quantity(row["received"], "lot received") for row in lots), Decimal())
        usable = sum((_quantity(row["usable"], "lot usable") for row in lots), Decimal())
        held = sum((_quantity(row["held"], "lot held") for row in lots), Decimal())
        cartons = sum((_whole(row["cartons"], "lot cartons") for row in lots), 0)
        ordered = _quantity(quantities["ordered"], "ordered")
        dispatched = sum(
            (_quantity(row["dispatched"], "dispatched") for row in allocations), Decimal()
        )
        quantities.update(
            {
                "received": _wire(received),
                "usable": _wire(usable),
                "held": _wire(held),
                "missing": _wire(max(Decimal(), ordered - received)),
                "allocated": _wire(
                    sum(
                        (_quantity(row["allocated"], "allocated") for row in allocations), Decimal()
                    )
                ),
                "dispatched": _wire(dispatched),
                "cartons": cartons,
                "observed_outer_packages": cartons,
            }
        )

    def _native_alert(
        self,
        state: dict[str, object],
        event: Mapping[str, object],
        outcome: _NativeOutcome,
        lot: str | None,
    ) -> None:
        self._alert(
            state,
            code=(
                "NATIVE_OPERATION_UNKNOWN"
                if outcome.status == "UNKNOWN_OUTCOME"
                else "NATIVE_OPERATION_BLOCKED"
            ),
            message=(
                "A native operation has an unknown outcome and will not be retried automatically."
                if outcome.status == "UNKNOWN_OUTCOME"
                else (
                    "The native operation was blocked; review the retained evidence "
                    "before continuing."
                )
            ),
            event=event,
            lot=lot,
            error_code=outcome.error_code,
            extra={"operation": outcome.kind},
        )

    def _alert(
        self,
        state: dict[str, object],
        *,
        code: str,
        message: str,
        event: Mapping[str, object],
        lot: str | None = None,
        quantity: Decimal | None = None,
        orders: list[str] | None = None,
        error_code: str | None = None,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        alerts = cast(list[dict[str, object]], state["alerts"])
        identity = (code, lot or "", _text(event["event_id"], "event_id"))
        if any(
            (alert.get("code"), str(alert.get("lot") or ""), alert.get("event_id")) == identity
            for alert in alerts
        ):
            return
        alert: dict[str, object] = {
            "code": code,
            "status": "OPEN",
            "message": message,
            "event_id": event["event_id"],
            "evidence_ref": event["evidence_ref"],
            "synthetic": event["synthetic"],
        }
        if lot is not None:
            alert["lot"] = lot
        if quantity is not None:
            alert["quantity"] = _wire(quantity)
        if orders:
            alert["orders"] = sorted(orders)
        if error_code:
            alert["error_code"] = error_code
        if extra:
            alert.update(cast(dict[str, object], _copy(extra)))
        alerts.append(alert)

    @staticmethod
    def _resolve_alerts(state: dict[str, object], codes: set[str], lot: str) -> None:
        for alert in cast(list[dict[str, object]], state["alerts"]):
            if (
                alert.get("code") in codes
                and alert.get("lot") == lot
                and alert.get("status") == "OPEN"
            ):
                alert["status"] = "RESOLVED"

    @staticmethod
    def _resolve_native_operation_alerts(
        state: dict[str, object], operation: str, event_id: str | None = None
    ) -> None:
        for alert in cast(list[dict[str, object]], state["alerts"]):
            if (
                alert.get("code") == "NATIVE_OPERATION_BLOCKED"
                and alert.get("operation") == operation
                and (event_id is None or alert.get("event_id") == event_id)
                and alert.get("status") == "OPEN"
            ):
                alert["status"] = "RESOLVED"

    def _append_event(
        self,
        state: dict[str, object],
        event: Mapping[str, object],
        status: str,
        operations: list[_NativeOutcome],
    ) -> None:
        events = cast(list[dict[str, object]], state["events"])
        record: dict[str, object] = {
            "event_id": event["event_id"],
            "type": event["type"],
            "status": status,
            "occurred_at": event["occurred_at"],
            "evidence_ref": event["evidence_ref"],
            "synthetic": event["synthetic"],
            "operations": [outcome.record() for outcome in operations],
        }
        decision = state.get("allocation_decision")
        if isinstance(decision, Mapping) and decision.get("event_id") == event["event_id"]:
            record["allocation_decision"] = _copy(decision)
        event_type = cast(str, event["type"])
        for field in _EVENT_BRIEF_FIELDS[event_type]:
            record[field] = _copy(event[field])
        events.append(record)
        for outcome in operations:
            state["documents"] = _merge_documents(
                _documents(state.get("documents")), outcome.documents
            )

    @staticmethod
    def _operations_status(operations: list[_NativeOutcome]) -> str:
        if any(outcome.status == "UNKNOWN_OUTCOME" for outcome in operations):
            return "UNKNOWN_OUTCOME"
        if any(outcome.status == "BLOCKED" for outcome in operations):
            return "BLOCKED"
        return "APPLIED"

    def _projection(
        self,
        state: Mapping[str, object],
        source: Mapping[str, object],
        *,
        retained_at: str | None = None,
    ) -> dict[str, object]:
        result = cast(dict[str, object], _copy(state))
        result["schema_version"] = DISTRIBUTOR_OPERATIONS_SCHEMA_VERSION
        result["purchase_order"] = self._config["purchase_order"]
        result["available"] = source["source_status"] == "CURRENT" or retained_at is not None
        result["documents"] = _documents(result.get("documents"))
        result["conversation"] = list(cast(list[object], result.get("conversation", [])))
        event_briefs = self._event_briefs(result.get("events"))
        shipment_rows = self._shipment_rows(result.get("shipments"))
        result["events"] = event_briefs
        result["shipments"] = shipment_rows
        self._add_outbound_facts(result, event_briefs, shipment_rows)
        policy = cast(Mapping[str, object], self._config["policy"])
        result["quality_policy"] = {
            "inspection_required": policy["inspection_required"],
            "inspection_criteria": _copy(policy.get("inspection_criteria") or {}),
        }
        alerts = cast(list[dict[str, object]], result["alerts"])
        if (
            retained_at is None
            and source["source_status"] != "CURRENT"
            and not any(
                alert.get("code") == "SOURCE_UNAVAILABLE" and alert.get("derived") is True
                for alert in alerts
            )
        ):
            alerts.append(
                {
                    "code": "SOURCE_UNAVAILABLE",
                    "status": "OPEN",
                    "message": (
                        "Current ERP evidence is unavailable; no native operation can start."
                    ),
                    "error_code": source.get("source_error") or "ERP_SOURCE_UNAVAILABLE",
                    "derived": True,
                }
            )
        self._deadline_alerts(result, alerts)
        result["stage"] = self._stage(result, alerts)
        result["available_event_templates"] = (
            []
            if source["source_status"] == "RETAINED" or retained_at is not None
            else self._event_templates()
        )
        result["photo_analysis_enabled"] = self.photo_analysis_enabled
        self._add_photo_attachments(result, source)
        result["photo_review_card"] = self._photo_review_card(source)
        proposal = self._current_proposal()
        if proposal is not None:
            result["prepared_proposal"] = {
                **proposal,
                "case_id": result.get("case_id"),
                "purchase_order": result["purchase_order"],
            }
        result.pop("prepared_picks", None)
        result.pop("source_status", None)
        result.pop("source_error", None)
        result.pop("source_observation", None)
        if source["source_status"] == "RETAINED":
            self._mark_retained_projection(result, retained_at)
        elif source["source_status"] == "CURRENT":
            self._mark_current_projection(result, source)
        else:
            self._mark_unavailable_projection(result)
        if self._config.get("economic_proposal") is not None:
            result["economic_proposal"] = self._economic_view(
                self._economic_operational_snapshot(state, source), self._economic_last_result
            )
        return result

    @classmethod
    def _mark_current_projection(
        cls, result: dict[str, object], source: Mapping[str, object]
    ) -> None:
        result["available"] = True
        result["actions_enabled"] = True
        result["live_source"] = True
        result["evidence_mode"] = {
            "status": "CURRENT",
            "as_of": cls._source_as_of(source),
            "message": (
                "Current ERP evidence was read for this turn. Its effective time is available "
                "only when supplied by the source."
            ),
        }

    @staticmethod
    def _mark_unavailable_projection(result: dict[str, object]) -> None:
        result["available"] = False
        result["actions_enabled"] = False
        result["live_source"] = False
        result["available_event_templates"] = []
        result["evidence_mode"] = {
            "status": "UNAVAILABLE",
            "as_of": None,
            "message": "Current ERP evidence is unavailable; no source time is claimed.",
        }

    @staticmethod
    def _mark_retained_projection(result: dict[str, object], retained_at: str | None) -> None:
        result["available"] = retained_at is not None
        result["actions_enabled"] = False
        result["live_source"] = False
        result["available_event_templates"] = []
        result["evidence_mode"] = {
            "status": "RETAINED_AS_OF"
            if retained_at is not None
            else "RETAINED_EVIDENCE_UNAVAILABLE",
            "as_of": retained_at,
            "message": (
                "Retained durable evidence as of the recorded time; live ERP was not queried "
                "and operations are disabled."
                if retained_at is not None
                else (
                    "No durable evidence is available; live ERP was not queried and "
                    "operations are disabled."
                )
            ),
        }

    def _current_proposal(self) -> dict[str, object] | None:
        row = self._db.execute(
            "SELECT proposal_id, event_json, source, attachment_id, state_revision, result_json, "
            "manager_id, approved_at FROM distributor_operation_proposals WHERE case_id=? "
            "ORDER BY recorded_at DESC, rowid DESC LIMIT 1",
            (self._config["case_id"],),
        ).fetchone()
        if row is None:
            return None
        (
            proposal_id,
            event_json,
            source,
            attachment_id,
            revision,
            result_json,
            manager_id,
            approved_at,
        ) = cast(tuple[str, str, str, str | None, str, str | None, str | None, str | None], row)
        return self._proposal_record(
            proposal_id,
            revision,
            _decoded(event_json, "proposal event"),
            source,
            attachment_id,
            result_json,
            manager_id,
            approved_at,
        )

    def _proposal_revision(self, state: Mapping[str, object], source: Mapping[str, object]) -> str:
        """Bind approval to the exact current case facts without exposing mutable internals."""

        return sha256(
            _encode(
                {
                    "case_id": self._config["case_id"],
                    "state": state,
                    "source": source,
                    "economic_config_digest": economic_config_digest(self._config),
                }
            ).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _source_revision(source: Mapping[str, object]) -> str | None:
        value = source.get("source_revision")
        return value.strip() if isinstance(value, str) and value.strip() else None

    def _analysis_lot(
        self, source: Mapping[str, object], requested_lot: str | None
    ) -> Mapping[str, object] | None:
        """Accept only an operator-selected lot from the current configured ERP scope."""

        if requested_lot is None or source.get("source_status") != "CURRENT":
            return None
        lots = source.get("lots")
        matches = (
            [row for row in lots if isinstance(row, Mapping) and row.get("lot") == requested_lot]
            if isinstance(lots, list)
            else []
        )
        if len(matches) != 1:
            raise ValueError("photo analysis lot is not a current configured lot")
        return matches[0]

    def _validate_photo_supersession(
        self,
        attachment_id: str,
        supersedes_attachment_id: str | None,
        linked_lot: str | None,
    ) -> None:
        """Keep one same-lot evidence chain; a replacement never merges photo views."""

        if supersedes_attachment_id is None:
            return
        if supersedes_attachment_id == attachment_id:
            raise ValueError("a photo attachment cannot supersede itself")
        row = self._db.execute(
            "SELECT analysis_json FROM distributor_operation_attachments "
            "WHERE attachment_id=? AND case_id=?",
            (supersedes_attachment_id, self._config["case_id"]),
        ).fetchone()
        if row is None:
            raise ValueError("superseded photo attachment is unavailable for this case")
        raw_analysis = row[0]
        if not isinstance(raw_analysis, str):
            raise ValueError("superseded photo must have a complete same-lot analysis")
        try:
            predecessor = _decoded(raw_analysis, "superseded photo analysis")
        except RuntimeError as error:
            raise ValueError("superseded photo analysis is malformed") from error
        predecessor_lot = predecessor.get("linked_lot")
        if (
            predecessor.get("status") != "COMPLETE"
            or not isinstance(predecessor_lot, str)
            or predecessor_lot != linked_lot
        ):
            raise ValueError("superseding photo must use the same selected lot")
        successor = self._photo_supersession_index().get(supersedes_attachment_id)
        if successor is not None and successor != attachment_id:
            raise ValueError("superseded photo already has a replacement attachment")
        cursor = supersedes_attachment_id
        seen: set[str] = set()
        while True:
            if cursor == attachment_id:
                raise ValueError("photo supersession cannot create a cycle")
            if cursor in seen:
                raise ValueError("stored photo supersession chain is cyclic")
            seen.add(cursor)
            ancestor = self._db.execute(
                "SELECT analysis_json FROM distributor_operation_attachments "
                "WHERE attachment_id=? AND case_id=?",
                (cursor, self._config["case_id"]),
            ).fetchone()
            if ancestor is None or not isinstance(ancestor[0], str):
                break
            try:
                analysis = _decoded(ancestor[0], "photo supersession analysis")
            except RuntimeError:
                break
            parent = analysis.get("supersedes_attachment_id")
            if not isinstance(parent, str) or not parent:
                break
            cursor = parent

    def _photo_supersession_index(self) -> dict[str, str]:
        """Return only completed, identity-safe successors; history remains on attachments."""

        rows = self._db.execute(
            "SELECT attachment_id, analysis_json FROM distributor_operation_attachments "
            "WHERE case_id=? AND analysis_json IS NOT NULL ORDER BY recorded_at, attachment_id",
            (self._config["case_id"],),
        ).fetchall()
        result: dict[str, str] = {}
        for attachment_id, raw_analysis in rows:
            if not isinstance(attachment_id, str) or not isinstance(raw_analysis, str):
                continue
            try:
                analysis = _decoded(raw_analysis, "photo supersession analysis")
            except RuntimeError:
                continue
            recommendation = analysis.get("recommendation")
            parent = analysis.get("supersedes_attachment_id")
            if (
                analysis.get("status") == "COMPLETE"
                and isinstance(recommendation, Mapping)
                and recommendation.get("identity_safe") is True
                and isinstance(parent, str)
                and parent
            ):
                result[parent] = attachment_id
        return result

    @staticmethod
    def _safe_photo_value(value: object, *, mapping: bool = False) -> object:
        """Retain only JSON metadata from a reader result; malformed metadata is display-empty."""

        if mapping and not isinstance(value, Mapping):
            return {}
        if not mapping and not isinstance(value, list):
            return []
        try:
            return _copy(value)
        except (TypeError, ValueError):
            return {} if mapping else []

    @staticmethod
    def _optional_photo_text(value: object) -> str | None:
        if not isinstance(value, str):
            return None
        text = value.strip()
        return text if text and len(text) <= 256 else None

    @staticmethod
    def _photo_purpose(value: object) -> PhotoPurpose:
        if value is None:
            return "overview"
        if isinstance(value, str) and value in {"overview", "label", "detail"}:
            return cast(PhotoPurpose, value)
        raise ValueError("photo purpose must be overview, label, or detail")

    @staticmethod
    def _reader_accepts_photo_purpose(reader: Callable[..., Mapping[str, object]]) -> bool:
        try:
            parameters = signature(reader).parameters.values()
        except (TypeError, ValueError):
            return False
        return any(
            parameter.name == "purpose" or parameter.kind is Parameter.VAR_KEYWORD
            for parameter in parameters
        )

    def _read_photo(
        self, reader: Callable[..., Mapping[str, object]], image: bytes, purpose: PhotoPurpose
    ) -> Mapping[str, object]:
        if purpose == "overview":
            return reader(image)
        if not self._reader_accepts_photo_purpose(reader):
            raise ValueError("configured photo reader does not support the selected photo purpose")
        return reader(image, purpose=purpose)

    def _complete_photo_analysis(
        self,
        result: Mapping[str, object],
        *,
        digest: str,
        source_revision: str,
        linked_lot: Mapping[str, object] | None,
        linked_quantity: object,
        reader_model_id: str | None,
        purpose: PhotoPurpose,
        supersedes_attachment_id: str | None,
        source: Mapping[str, object],
    ) -> dict[str, object]:
        if not isinstance(result, Mapping):
            raise ValueError("photo reader result is malformed")
        returned_purpose = result.get("purpose")
        if isinstance(returned_purpose, str) and returned_purpose != purpose:
            raise ValueError("photo reader returned a different analysis purpose")
        assessment = self._photo_assessment(result.get("assessment"), purpose)
        selected_lot = _text(linked_lot["lot"], "linked photo lot") if linked_lot else None
        checks = self._photo_identity_checks(purpose, assessment, linked_lot)
        recommendation, next_action = self._photo_recommendation(purpose, assessment, checks)
        raw_latency = result.get("latency_ms")
        latency = (
            raw_latency
            if isinstance(raw_latency, (int, float))
            and not isinstance(raw_latency, bool)
            and math.isfinite(raw_latency)
            and raw_latency >= 0
            else None
        )
        return {
            "status": "COMPLETE",
            "_cache_reader_model_id": reader_model_id,
            "_cache_photo_purpose": purpose,
            "purpose": purpose,
            "assessment": assessment,
            "checks": checks,
            "model": self._optional_photo_text(result.get("model")),
            "provider": self._optional_photo_text(result.get("provider")),
            "transport": self._optional_photo_text(result.get("transport")),
            "stages": self._safe_photo_value(result.get("stages", [])),
            "usage": self._safe_photo_value(result.get("usage", {}), mapping=True),
            "latency_ms": latency,
            "observed_at": self._next_recorded_at(),
            "attachment_sha256": digest,
            "source_revision": source_revision,
            "linked_lot": selected_lot,
            "linkage_source": "OPERATOR_SELECTED" if selected_lot is not None else None,
            "linked_quantity": linked_quantity,
            "supersedes_attachment_id": supersedes_attachment_id,
            "recommendation": recommendation,
            "next_action": next_action,
            "source_context": self._photo_source_context(source, linked_lot),
        }

    @staticmethod
    def _photo_assessment(value: object, purpose: PhotoPurpose) -> dict[str, object]:
        if purpose == "overview":
            return PhotoAssessment.model_validate(value).model_dump(mode="json")
        if purpose == "label":
            return PhotoLabelAssessment.model_validate(value).model_dump(mode="json")
        return PhotoDetailAssessment.model_validate(value).model_dump(mode="json")

    def _photo_identity_checks(
        self,
        purpose: PhotoPurpose,
        assessment: Mapping[str, object],
        linked_lot: Mapping[str, object] | None,
    ) -> dict[str, dict[str, object]]:
        observed_item = (
            self._optional_photo_text(assessment.get("item_code"))
            if purpose in {"overview", "label"}
            else None
        )
        observed_lot = (
            self._optional_photo_text(assessment.get("supplier_lot"))
            if purpose in {"overview", "label"}
            else None
        )
        expected_item = (
            self._optional_photo_text(linked_lot.get("item_code"))
            if linked_lot is not None
            else None
        ) or _text(self._config["item_code"], "configured item_code")
        if purpose == "detail":
            return {
                "item_code": self._photo_check(None, expected_item, applicable=False),
                "lot": self._photo_check(None, None, applicable=False),
            }
        item_check = self._photo_check(observed_item, expected_item, applicable=True)
        if linked_lot is None:
            lot_check = self._photo_check(observed_lot, None, applicable=False)
        else:
            expected_lot = _text(linked_lot["lot"], "linked photo lot")
            lot_check = self._photo_check(
                observed_lot,
                expected_lot,
                applicable=True,
                aliases=self._configured_lot_aliases(expected_lot),
            )
        return {"item_code": item_check, "lot": lot_check}

    @staticmethod
    def _photo_check(
        observed: str | None,
        expected: str | None,
        *,
        applicable: bool,
        aliases: set[str] | None = None,
    ) -> dict[str, object]:
        if not applicable:
            return {
                "status": "NOT_APPLICABLE",
                "observed": observed,
                "expected": expected,
                "requires_review": observed is not None,
            }
        if observed is None:
            return {
                "status": "UNKNOWN",
                "observed": None,
                "expected": expected,
                "requires_review": True,
            }
        accepted = aliases or ({expected} if expected is not None else set())
        if observed in accepted:
            return {
                "status": "MATCH",
                "observed": observed,
                "expected": expected,
                "requires_review": False,
                **({"matched_by": "CONFIGURED_ALIAS"} if observed != expected else {}),
            }
        return {
            "status": "MISMATCH",
            "observed": observed,
            "expected": expected,
            "requires_review": True,
        }

    def _configured_lot_aliases(self, lot: str) -> set[str]:
        aliases = {lot}
        for name in ("lots", "receipt_plans"):
            rows = self._config.get(name)
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, Mapping) or row.get("lot") != lot:
                    continue
                batch_no = row.get("batch_no")
                if isinstance(batch_no, str) and batch_no.strip():
                    aliases.add(batch_no.strip())
        return aliases

    def _photo_quality_policy(self) -> dict[str, object]:
        policy = cast(Mapping[str, object], self._config["policy"])
        criteria = policy.get("inspection_criteria")
        return {
            "inspection_required": policy["inspection_required"],
            "inspection_criteria": _copy(criteria) if isinstance(criteria, Mapping) else {},
            "synthetic_specification": (
                "SYNTHETIC_CONFIG"
                if self._config["synthetic_input"] is True
                else "CONFIGURED_POLICY"
            ),
            "specification_source": (
                "SYNTHETIC_CONFIG"
                if self._config["synthetic_input"] is True
                else "CONFIGURED_POLICY"
            ),
        }

    def _photo_lot_context(
        self, linked_lot: Mapping[str, object] | None
    ) -> dict[str, object] | None:
        if linked_lot is None:
            return None
        context: dict[str, object] = {
            "lot": _text(linked_lot["lot"], "photo context lot"),
            "item_code": self._optional_photo_text(linked_lot.get("item_code"))
            or _text(self._config["item_code"], "configured item_code"),
            "item_authority": (
                "CURRENT_ERP_LOT"
                if self._optional_photo_text(linked_lot.get("item_code")) is not None
                else "CONFIGURED_CASE_SCOPE"
            ),
        }
        for field in ("status", "received", "usable", "held", "expected_quantity"):
            if field in linked_lot:
                context[field] = _copy(linked_lot[field])
        return context

    @staticmethod
    def _photo_case_quantities(source: Mapping[str, object]) -> dict[str, object]:
        quantities = source.get("quantities")
        if not isinstance(quantities, Mapping):
            return {}
        return {
            field: _copy(quantities[field])
            for field in ("received", "usable", "held", "allocated", "dispatched", "uom")
            if field in quantities
        }

    @staticmethod
    def _photo_affected_orders(source: Mapping[str, object]) -> list[dict[str, object]]:
        allocations = source.get("allocations")
        if not isinstance(allocations, list):
            return []
        fields = (
            "customer_order",
            "requested_quantity",
            "allocated",
            "backordered",
            "dispatched",
            "priority",
            "promised_delivery_at",
        )
        result: list[dict[str, object]] = []
        for row in allocations:
            if not isinstance(row, Mapping):
                continue
            current = {field: _copy(row[field]) for field in fields if field in row}
            try:
                requested = _quantity(row.get("requested_quantity"), "affected order quantity")
                allocated = _quantity(row.get("allocated", 0), "affected order allocation")
                dispatched = _quantity(row.get("dispatched", 0), "affected order dispatch")
            except ValueError:
                pass
            else:
                remaining_requested = max(Decimal("0"), requested - dispatched)
                current["still_fulfillable_quantity"] = _wire(min(allocated, remaining_requested))
                current["still_fulfillable_authority"] = "CURRENT_ERP_ALLOCATION"
            result.append(current)
        return result

    def _photo_source_context(
        self, source: Mapping[str, object], linked_lot: Mapping[str, object] | None
    ) -> dict[str, object]:
        return {
            "source_status": source.get("source_status"),
            "source_revision": self._source_revision(source),
            "selected_lot": self._photo_lot_context(linked_lot),
            "quality_policy": self._photo_quality_policy(),
            "affected_orders": self._photo_affected_orders(source),
            "quantities": self._photo_case_quantities(source),
        }

    def _photo_recommendation(
        self,
        purpose: PhotoPurpose,
        assessment: Mapping[str, object],
        checks: Mapping[str, Mapping[str, object]],
    ) -> tuple[dict[str, object], dict[str, object]]:
        item_check = checks["item_code"]
        lot_check = checks["lot"]
        identity_mismatch = any(
            check.get("status") == "MISMATCH" for check in (item_check, lot_check)
        )
        identity_review_required = any(
            check.get("requires_review") is True for check in (item_check, lot_check)
        )
        image_label_lot = self._optional_photo_text(assessment.get("supplier_lot"))
        image_label_item = self._optional_photo_text(assessment.get("item_code"))
        if identity_mismatch:
            message = (
                "The legible image identity conflicts with the selected current lot or item; "
                "verify the association before using this photo as advisory evidence."
            )
            return (
                {
                    "code": "VERIFY_IDENTITY",
                    "message": message,
                    "image_label_lot": image_label_lot,
                    "image_label_item": image_label_item,
                    "label_lot_conflict": lot_check.get("status") == "MISMATCH",
                    "identity_review_required": True,
                    "identity_safe": False,
                },
                {"code": "VERIFY_IDENTITY", "message": message, "suggested_purpose": "label"},
            )
        if purpose == "label":
            if assessment.get("label_visibility") != "legible":
                message = "The label is not legible; take the requested label close-up."
                return (
                    {
                        "code": "RETAKE_LABEL",
                        "message": message,
                        "image_label_lot": image_label_lot,
                        "image_label_item": image_label_item,
                        "label_lot_conflict": False,
                        "identity_review_required": identity_review_required,
                        "identity_safe": True,
                    },
                    {
                        "code": "CAPTURE_LABEL",
                        "message": self._optional_photo_text(assessment.get("next_photo"))
                        or message,
                        "suggested_purpose": "label",
                    },
                )
            message = "Label observations need operator review before any inventory action."
            return (
                {
                    "code": "REVIEW_PRODUCT_CHECK",
                    "message": message,
                    "image_label_lot": image_label_lot,
                    "image_label_item": image_label_item,
                    "label_lot_conflict": False,
                    "identity_review_required": identity_review_required,
                    "identity_safe": True,
                },
                {"code": "CAPTURE_DETAIL", "message": message, "suggested_purpose": "detail"},
            )
        if purpose == "detail":
            if assessment.get("detail_visibility") != "clear":
                message = "The requested exterior detail is unclear; take the requested close-up."
                return (
                    {
                        "code": "RETAKE_DETAIL",
                        "message": message,
                        "image_label_lot": None,
                        "image_label_item": None,
                        "label_lot_conflict": False,
                        "identity_review_required": False,
                        "identity_safe": True,
                    },
                    {
                        "code": "CAPTURE_DETAIL",
                        "message": self._optional_photo_text(assessment.get("next_photo"))
                        or message,
                        "suggested_purpose": "detail",
                    },
                )
            if assessment.get("visible_condition") == "visible_damage":
                message = (
                    "Visible exterior damage requires an operator-confirmed inspection; "
                    "it is not a quality disposition."
                )
                return (
                    {
                        "code": "REQUIRE_INSPECTION",
                        "message": message,
                        "image_label_lot": None,
                        "image_label_item": None,
                        "label_lot_conflict": False,
                        "identity_review_required": False,
                        "identity_safe": True,
                    },
                    {"code": "OPERATOR_INSPECTION", "message": message},
                )
            if assessment.get("visible_condition") == "no_visible_damage":
                message = (
                    "No visible damage in this detail is not a quality release or "
                    "stock disposition."
                )
                return (
                    {
                        "code": "NO_VISIBLE_DAMAGE_NOT_QUALITY_CLEARANCE",
                        "message": message,
                        "image_label_lot": None,
                        "image_label_item": None,
                        "label_lot_conflict": False,
                        "identity_review_required": False,
                        "identity_safe": True,
                    },
                    {"code": "REVIEW_PRODUCT_CHECK", "message": message},
                )
            message = "The visible exterior condition is unclear; review or take another close-up."
            return (
                {
                    "code": "PHOTO_CONDITION_REQUIRES_REVIEW",
                    "message": message,
                    "image_label_lot": None,
                    "image_label_item": None,
                    "label_lot_conflict": False,
                    "identity_review_required": False,
                    "identity_safe": True,
                },
                {"code": "CAPTURE_DETAIL", "message": message, "suggested_purpose": "detail"},
            )
        if assessment.get("visibility") != "clear":
            message = (
                "The receiving units are not fully visible; take the requested replacement photo."
            )
            return (
                {
                    "code": "RETAKE",
                    "message": message,
                    "image_label_lot": image_label_lot,
                    "image_label_item": image_label_item,
                    "label_lot_conflict": False,
                    "identity_review_required": identity_review_required,
                    "identity_safe": True,
                },
                {
                    "code": "CAPTURE_OVERVIEW",
                    "message": self._optional_photo_text(assessment.get("next_photo")) or message,
                    "suggested_purpose": "overview",
                },
            )
        if assessment.get("visible_condition") == "visible_damage":
            message = (
                "Visible damage requires an operator-confirmed inspection; "
                "it is not a quality disposition."
            )
            return (
                {
                    "code": "REQUIRE_INSPECTION",
                    "message": message,
                    "image_label_lot": image_label_lot,
                    "image_label_item": image_label_item,
                    "label_lot_conflict": False,
                    "identity_review_required": identity_review_required,
                    "identity_safe": True,
                },
                {"code": "CAPTURE_DETAIL", "message": message, "suggested_purpose": "detail"},
            )
        if assessment.get("visible_condition") == "no_visible_damage":
            message = "No visible outer damage is not a quality release or stock disposition."
            return (
                {
                    "code": "NO_VISIBLE_DAMAGE_NOT_QUALITY_CLEARANCE",
                    "message": message,
                    "image_label_lot": image_label_lot,
                    "image_label_item": image_label_item,
                    "label_lot_conflict": False,
                    "identity_review_required": identity_review_required,
                    "identity_safe": True,
                },
                {"code": "CAPTURE_LABEL", "message": message, "suggested_purpose": "label"},
            )
        message = "The visible condition is unclear; review or take another photo."
        return (
            {
                "code": "PHOTO_CONDITION_REQUIRES_REVIEW",
                "message": message,
                "image_label_lot": image_label_lot,
                "image_label_item": image_label_item,
                "label_lot_conflict": False,
                "identity_review_required": identity_review_required,
                "identity_safe": True,
            },
            {"code": "CAPTURE_DETAIL", "message": message, "suggested_purpose": "detail"},
        )

    def _unavailable_photo_analysis(
        self,
        *,
        digest: str,
        source_revision: str | None,
        linked_lot: object,
        linked_quantity: object,
        purpose: PhotoPurpose,
        supersedes_attachment_id: str | None,
        message: str,
    ) -> dict[str, object]:
        selected_lot = _text(linked_lot, "linked photo lot") if linked_lot is not None else None
        checks = {
            "item_code": self._photo_check(None, None, applicable=False),
            "lot": self._photo_check(None, selected_lot, applicable=False),
        }
        return {
            "status": "UNAVAILABLE",
            "purpose": purpose,
            "assessment": None,
            "checks": checks,
            "model": None,
            "provider": None,
            "transport": None,
            "stages": [],
            "usage": {},
            "latency_ms": None,
            "observed_at": self._next_recorded_at(),
            "attachment_sha256": digest,
            "source_revision": source_revision,
            "linked_lot": selected_lot,
            "linkage_source": "OPERATOR_SELECTED" if selected_lot is not None else None,
            "linked_quantity": linked_quantity,
            "supersedes_attachment_id": supersedes_attachment_id,
            "recommendation": {
                "code": "ANALYSIS_UNAVAILABLE",
                "message": message,
                "image_label_lot": None,
                "image_label_item": None,
                "label_lot_conflict": False,
                "identity_review_required": False,
                "identity_safe": False,
            },
            "next_action": {"code": "RETRY_ANALYSIS", "message": message},
            "retryable": True,
        }

    @staticmethod
    def _with_photo_supersession(
        analysis: Mapping[str, object], supersedes_attachment_id: str | None
    ) -> dict[str, object]:
        result = cast(dict[str, object], _copy(analysis))
        result["supersedes_attachment_id"] = supersedes_attachment_id
        return result

    def _cached_photo_analysis(
        self,
        *,
        digest: str,
        source_revision: str,
        linked_lot: object,
        reader_model_id: str | None,
        purpose: PhotoPurpose,
    ) -> dict[str, object] | None:
        # A callable without a stable model identifier cannot safely share a paid result.
        if reader_model_id is None:
            return None
        selected_lot = _text(linked_lot, "linked photo lot") if linked_lot is not None else None
        rows = self._db.execute(
            "SELECT analysis_json FROM distributor_operation_attachments "
            "WHERE case_id=? AND digest=? AND analysis_json IS NOT NULL ORDER BY recorded_at DESC",
            (self._config["case_id"], digest),
        ).fetchall()
        for (raw_analysis,) in rows:
            if not isinstance(raw_analysis, str):
                continue
            try:
                analysis = _decoded(raw_analysis, "photo analysis")
            except RuntimeError:
                continue
            if (
                analysis.get("status") == "COMPLETE"
                and analysis.get("attachment_sha256") == digest
                and analysis.get("source_revision") == source_revision
                and analysis.get("linked_lot") == selected_lot
                and analysis.get("_cache_reader_model_id") == reader_model_id
                and analysis.get("_cache_photo_purpose", "overview") == purpose
            ):
                return analysis
        return None

    @staticmethod
    def _photo_reader_model_id(reader: Callable[..., Mapping[str, object]]) -> str | None:
        """Use a configured reader model as part of the durable de-duplication key."""

        model_id = getattr(reader, "model_id", None)
        return model_id.strip() if isinstance(model_id, str) and model_id.strip() else None

    def _store_photo_analysis(self, attachment_id: str, analysis: Mapping[str, object]) -> None:
        updated = self._db.execute(
            "UPDATE distributor_operation_attachments SET analysis_json=? "
            "WHERE attachment_id=? AND case_id=?",
            (_encode(analysis), attachment_id, self._config["case_id"]),
        ).rowcount
        if updated != 1:  # pragma: no cover - protected by the caller's attachment read
            raise ValueError("photo attachment is unavailable for this case")

    def _attachment_metadata(
        self,
        attachment_id: str,
        *,
        current_source_revision: str | None = None,
        superseded_by_attachment_id: str | None = None,
    ) -> dict[str, object]:
        row = self._db.execute(
            "SELECT attachment_id, media_type, digest, proposal_id, event_id, recorded_at, "
            "analysis_json "
            "FROM distributor_operation_attachments WHERE attachment_id=? AND case_id=?",
            (attachment_id, self._config["case_id"]),
        ).fetchone()
        if row is None:
            raise ValueError("photo attachment is unavailable for this case")
        identifier, media_type, digest, proposal_id, event_id, recorded_at, raw_analysis = cast(
            tuple[str, str, str, str | None, str | None, str, str | None], row
        )
        analysis = _decoded(raw_analysis, "photo analysis") if raw_analysis is not None else None
        if analysis is not None:
            analysis.pop("_cache_reader_model_id", None)
            analysis.pop("_cache_photo_purpose", None)
            analysis["superseded_by_attachment_id"] = superseded_by_attachment_id
            analysis["advisory_current"] = self._analysis_is_advisory_current(
                analysis,
                current_source_revision=current_source_revision,
                superseded_by_attachment_id=superseded_by_attachment_id,
            )
        interpretation = (
            "NOT_ANALYZED"
            if analysis is None
            else "BEDROCK_PHOTO_OBSERVATION"
            if analysis.get("status") == "COMPLETE"
            else "ANALYSIS_UNAVAILABLE"
        )
        return {
            "attachment_id": identifier,
            "media_type": media_type,
            "digest": digest,
            "proposal_id": proposal_id,
            "event_id": event_id,
            "recorded_at": recorded_at,
            "source": "OPERATOR_ATTACHED_PHOTO",
            "superseded_by_attachment_id": superseded_by_attachment_id,
            "interpretation": interpretation,
            "analysis": analysis,
        }

    @staticmethod
    def _analysis_is_advisory_current(
        analysis: Mapping[str, object],
        *,
        current_source_revision: str | None,
        superseded_by_attachment_id: str | None,
    ) -> bool:
        recommendation = analysis.get("recommendation")
        return (
            analysis.get("status") == "COMPLETE"
            and current_source_revision is not None
            and analysis.get("source_revision") == current_source_revision
            and superseded_by_attachment_id is None
            and isinstance(recommendation, Mapping)
            and recommendation.get("identity_safe") is True
        )

    def _add_photo_attachments(
        self, projection: dict[str, object], source: Mapping[str, object]
    ) -> None:
        current_source_revision = self._source_revision(source)
        rows = self._db.execute(
            "SELECT attachment_id FROM distributor_operation_attachments WHERE case_id=? "
            "ORDER BY recorded_at, attachment_id",
            (self._config["case_id"],),
        ).fetchall()
        successors = self._photo_supersession_index()
        projection["photo_attachments"] = [
            self._attachment_metadata(
                cast(str, row[0]),
                current_source_revision=current_source_revision,
                superseded_by_attachment_id=successors.get(cast(str, row[0])),
            )
            for row in rows
        ]

    def _photo_review_card(self, source: Mapping[str, object]) -> dict[str, object]:
        """Expose source-derived context without making photos stock authority."""

        current_source_revision = self._source_revision(source)
        latest: tuple[str, Mapping[str, object]] | None = None
        latest_key: tuple[str, str] | None = None
        rows = self._db.execute(
            "SELECT attachment_id, analysis_json FROM distributor_operation_attachments "
            "WHERE case_id=? AND analysis_json IS NOT NULL ORDER BY recorded_at, attachment_id",
            (self._config["case_id"],),
        ).fetchall()
        for attachment_id, raw_analysis in rows:
            if not isinstance(attachment_id, str) or not isinstance(raw_analysis, str):
                continue
            try:
                analysis = _decoded(raw_analysis, "photo review card analysis")
            except RuntimeError:
                continue
            observed_at = analysis.get("observed_at")
            key = (
                (observed_at, attachment_id)
                if isinstance(observed_at, str)
                else ("", attachment_id)
            )
            if latest_key is None or key > latest_key:
                latest = (attachment_id, analysis)
                latest_key = key
        attachment_id = latest[0] if latest is not None else None
        analysis = latest[1] if latest is not None else None
        linked_lot_name = (
            analysis.get("linked_lot")
            if isinstance(analysis, Mapping) and isinstance(analysis.get("linked_lot"), str)
            else None
        )
        selected_lot = self._source_lot(source, linked_lot_name)
        successors = self._photo_supersession_index()
        advisory_current = (
            self._analysis_is_advisory_current(
                analysis,
                current_source_revision=current_source_revision,
                superseded_by_attachment_id=successors.get(attachment_id),
            )
            if isinstance(analysis, Mapping) and attachment_id is not None
            else False
        )
        return {
            "source_status": source.get("source_status"),
            "source_revision": current_source_revision,
            "analysis_context": {
                "attachment_id": attachment_id,
                "purpose": analysis.get("purpose", "overview") if analysis else None,
                "linked_lot": linked_lot_name,
                "linkage_source": analysis.get("linkage_source") if analysis else None,
                "analysis_source_revision": analysis.get("source_revision") if analysis else None,
                "advisory_current": advisory_current,
            },
            "configured_item": {
                "item_code": self._config["item_code"],
                "authority": "CONFIGURED_CASE_SCOPE",
            },
            "selected_lot": self._photo_lot_context(selected_lot),
            "quality_policy": self._photo_quality_policy(),
            "affected_orders": self._photo_affected_orders(source),
            "quantities": self._photo_case_quantities(source),
            "current_observations": self._current_photo_observations(source),
        }

    @staticmethod
    def _source_lot(
        source: Mapping[str, object], lot_name: str | None
    ) -> Mapping[str, object] | None:
        if lot_name is None:
            return None
        lots = source.get("lots")
        matches = (
            [row for row in lots if isinstance(row, Mapping) and row.get("lot") == lot_name]
            if isinstance(lots, list)
            else []
        )
        return matches[0] if len(matches) == 1 else None

    def _require_unbound_attachment(self, attachment_id: str) -> None:
        row = self._db.execute(
            "SELECT case_id, proposal_id, event_id FROM distributor_operation_attachments "
            "WHERE attachment_id=?",
            (attachment_id,),
        ).fetchone()
        if row is None:
            raise ValueError("photo attachment is unavailable for this case")
        case_id, proposal_id, event_id = cast(tuple[str, str | None, str | None], row)
        if case_id != self._config["case_id"] or proposal_id is not None or event_id is not None:
            raise ValueError("photo attachment is already associated with another operation")

    def _proposal_record(
        self,
        proposal_id: str,
        state_revision: str,
        event: Mapping[str, object],
        source: str,
        attachment_id: str | None,
        result_json: str | None,
        manager_id: str | None,
        approved_at: str | None,
    ) -> dict[str, object]:
        status = (
            self._stored_event_status(event) or "UNKNOWN_OUTCOME"
            if result_json is not None
            else "PENDING_MANAGER_APPROVAL"
        )
        return {
            "proposal_id": proposal_id,
            "state_revision": state_revision,
            "event": _copy(event),
            "source": source,
            "photo_attachment_id": attachment_id,
            "status": status,
            "read_only_agent_context": source == "RETAINED_ALLOCATION_RECOMMENDATION",
            "approval": (
                {"manager_id": manager_id, "approved_at": approved_at}
                if manager_id is not None and approved_at is not None
                else None
            ),
        }

    @staticmethod
    def _with_proposal(
        projection: dict[str, object], proposal: Mapping[str, object]
    ) -> dict[str, object]:
        return {
            **projection,
            "prepared_proposal": {
                **_copy(proposal),
                "case_id": projection.get("case_id"),
                "purchase_order": projection.get("purchase_order"),
            },
        }

    def _event_briefs(self, raw_events: object) -> list[dict[str, object]]:
        if not isinstance(raw_events, list):
            return []
        result: list[dict[str, object]] = []
        for raw in raw_events:
            if not isinstance(raw, Mapping):
                continue
            record = cast(dict[str, object], _copy(raw))
            event_id = record.get("event_id")
            event_type = record.get("type")
            fields = _EVENT_BRIEF_FIELDS.get(event_type) if isinstance(event_type, str) else None
            if isinstance(event_id, str) and fields is not None:
                payload = self._stored_event(event_id)
                if payload is not None and payload.get("type") == event_type:
                    for field in fields:
                        record[field] = _copy(payload[field])
            result.append(record)
        return result

    def _shipment_rows(self, raw_shipments: object) -> list[dict[str, object]]:
        if not isinstance(raw_shipments, Mapping):
            return []
        result: list[dict[str, object]] = []
        for raw_name, raw in raw_shipments.items():
            if not isinstance(raw_name, str) or not isinstance(raw, Mapping):
                continue
            try:
                name = _text(raw_name, "shipment name")
                row = {
                    "name": name,
                    "customer_order": _text(raw.get("customer_order"), "shipment order"),
                    "lot": _text(raw.get("lot"), "shipment lot"),
                    "quantity": _wire(
                        _quantity(raw.get("quantity"), "shipment quantity", positive=True)
                    ),
                    "picked_up": raw.get("picked_up") is True,
                    "delivered": raw.get("delivered") is True,
                    "synthetic": (
                        raw.get("synthetic")
                        if type(raw.get("synthetic")) is bool
                        else self._config["synthetic_input"]
                    ),
                }
            except ValueError:
                continue
            result.append(row)
        return sorted(result, key=lambda row: cast(str, row["name"]))

    @staticmethod
    def _add_outbound_facts(
        projection: dict[str, object],
        events: list[dict[str, object]],
        shipments: list[dict[str, object]],
    ) -> None:
        picked_by_order: dict[str, Decimal] = {}
        counted_pick_lists: set[str] = set()
        for event in events:
            if event.get("type") != "picked":
                continue
            order = event.get("customer_order")
            operations = event.get("operations")
            if not isinstance(order, str) or not isinstance(operations, list):
                continue
            pick_lists = {
                name
                for operation in operations
                if isinstance(operation, Mapping)
                and operation.get("kind") == "submit_pick"
                and operation.get("status") in _SUCCESS
                for document in _documents(operation.get("documents"))
                if document.get("kind") == "Pick List"
                and isinstance(name := document.get("name"), str)
            }
            if not pick_lists or pick_lists.intersection(counted_pick_lists):
                continue
            try:
                quantity = _quantity(event.get("quantity"), "picked quantity", positive=True)
            except ValueError:
                continue
            counted_pick_lists.update(pick_lists)
            picked_by_order[order] = picked_by_order.get(order, Decimal()) + quantity
        delivered_by_order: dict[str, Decimal] = {}
        for shipment in shipments:
            if shipment.get("delivered") is not True:
                continue
            order = shipment.get("customer_order")
            if not isinstance(order, str):
                continue
            try:
                quantity = _quantity(
                    shipment.get("quantity"), "delivered shipment quantity", positive=True
                )
            except ValueError:
                continue
            delivered_by_order[order] = delivered_by_order.get(order, Decimal()) + quantity
        allocations = projection.get("allocations")
        if not isinstance(allocations, list):
            return
        for raw in allocations:
            if not isinstance(raw, dict):
                continue
            order = raw.get("customer_order")
            if not isinstance(order, str):
                continue
            picked = picked_by_order.get(order)
            delivered = delivered_by_order.get(order, Decimal())
            if picked is not None:
                raw["picked"] = _wire(picked)
            if delivered > 0:
                raw["delivery_confirmed"] = _wire(delivered)
            elif picked is not None:
                raw["delivery_confirmed"] = 0
            if delivered > 0:
                requested = _quantity(
                    raw.get("requested_quantity"), "requested quantity", positive=True
                )
                raw["status"] = (
                    "DELIVERY_CONFIRMED" if delivered >= requested else "PARTIALLY_DELIVERED"
                )
            elif picked is not None:
                raw["status"] = "PICKED"

    def _deadline_alerts(
        self, projection: Mapping[str, object], alerts: list[dict[str, object]]
    ) -> None:
        now = self._now()
        quantities = cast(Mapping[str, object], projection["quantities"])
        ordered = _quantity(quantities["ordered"], "ordered")
        received = _quantity(quantities["received"], "received")
        dispatched = _quantity(quantities["dispatched"], "dispatched")
        delivered = _quantity(quantities["delivery_confirmed"], "delivery_confirmed")
        deadlines = (
            (
                "expected_at",
                "RECEIPT_OVERDUE",
                received < ordered,
                "Receipt evidence is overdue; no loss cause is inferred.",
            ),
            (
                "promised_delivery_at",
                "DELIVERY_CONFIRMATION_DUE",
                dispatched > delivered,
                (
                    "Delivery confirmation is overdue for dispatched stock; "
                    "a Delivery Note is not proof of receipt."
                ),
            ),
        )
        for field, code, active, message in deadlines:
            deadline = _deadline(self._config.get(field), field) if field in self._config else None
            if (
                deadline is None
                or now <= deadline
                or not active
                or any(
                    alert.get("code") == code and alert.get("derived") is True for alert in alerts
                )
            ):
                continue
            alerts.append(
                {
                    "code": code,
                    "status": "OPEN",
                    "message": message,
                    "deadline": deadline.isoformat(),
                    "derived": True,
                }
            )

    @staticmethod
    def _stage(projection: Mapping[str, object], alerts: list[dict[str, object]]) -> str:
        if projection.get("source_status") == "UNAVAILABLE":
            return "SOURCE_UNAVAILABLE"
        if any(alert.get("status") == "OPEN" for alert in alerts):
            return "HOLD"
        quantities = cast(Mapping[str, object], projection["quantities"])
        ordered = _quantity(quantities["ordered"], "ordered")
        delivery = _quantity(quantities["delivery_confirmed"], "delivery_confirmed")
        dispatched = _quantity(quantities["dispatched"], "dispatched")
        allocated = _quantity(quantities["allocated"], "allocated")
        received = _quantity(quantities["received"], "received")
        if ordered > 0 and delivery >= ordered:
            return "DELIVERY_CONFIRMED"
        if dispatched > 0:
            return "DISPATCHED"
        if allocated > 0:
            return "PICK_PREPARED"
        if received > 0:
            return "RECEIVED"
        return "AWAITING_ARRIVAL"

    def _event_templates(self) -> list[dict[str, object]]:
        return [
            {"type": "arrival", "synthetic": self._config["synthetic_input"]},
            {"type": "inspection", "synthetic": self._config["synthetic_input"]},
            {"type": "picked", "synthetic": self._config["synthetic_input"]},
            {"type": "carrier_pickup", "synthetic": self._config["synthetic_input"]},
            {"type": "delivery", "synthetic": self._config["synthetic_input"]},
        ]

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            raise ValueError("operations clock must return a timezone-aware time")
        return value.astimezone(UTC)
