/* Distributor operations is a small source-driven view. It never invents a
 * quantity, event, delivery, or conversation answer when the API is silent. */
(() => {
  "use strict";

  const API_PATH = "/api/v1/distributor-operations";
  const EVENT_TYPES = new Set(["arrival", "inspection", "picked", "carrier_pickup", "delivery"]);
  const NUMBER_FIELDS = new Set([
    "cartons", "expected_pack_quantity", "observed_stock_quantity", "sample_quantity", "quantity", "measured",
  ]);
  const FIELD_DEFS = {
    arrival: [
      { key: "cartons", label: "Cartons observed", type: "number", min: "0", step: "1" },
      { key: "expected_pack_quantity", label: "Expected parts per carton", type: "number", min: "0", step: "any" },
      { key: "observed_stock_quantity", label: "Parts counted", type: "number", min: "0", step: "any" },
      { key: "item_code", label: "Item code", type: "text" },
      { key: "lot", label: "Lot / batch", type: "text" },
    ],
    inspection: [
      { key: "lot", label: "Lot / batch", type: "text" },
      { key: "result", label: "Result", type: "select", options: ["PASS", "FAIL"] },
      { key: "scope", label: "Inspection scope", type: "select", options: ["SAMPLE", "WHOLE_LOT"] },
      { key: "metric", label: "Metric", type: "text", placeholder: "e.g. diameter" },
      { key: "measured", label: "Measured value", type: "number", min: "0", step: "any" },
      { key: "inspection_report_ref", label: "Inspection report ID", type: "text", placeholder: "e.g. QI-2026-004" },
      { key: "sample_quantity", label: "Sample quantity", type: "number", min: "0", step: "any" },
    ],
    picked: [
      { key: "customer_order", label: "Customer order", type: "text" },
      { key: "lot", label: "Lot / batch", type: "text" },
      { key: "quantity", label: "Picked quantity", type: "number", min: "0", step: "any" },
      { key: "pick_evidence_ref", label: "Pick evidence ID", type: "text" },
    ],
    carrier_pickup: [
      { key: "shipment_id", label: "Shipment", type: "text" },
    ],
    delivery: [
      { key: "shipment_id", label: "Shipment", type: "text" },
    ],
  };
  const STAGES = [
    { key: "arrival", label: "Receiving", icon: "ph-package", metric: "received", detail: "Source receipt" },
    { key: "inspection", label: "Quality", icon: "ph-seal-check", metric: "usable", detail: "Quality evidence" },
    { key: "allocation", label: "Allocation", icon: "ph-users-three", metric: "allocated", detail: "Customer demand" },
    { key: "dispatch", label: "Dispatch", icon: "ph-truck", metric: "dispatched", detail: "Native dispatch" },
  ];

  const isRecord = (value) => Boolean(value) && typeof value === "object" && !Array.isArray(value);
  const finite = (value) => typeof value === "number" && Number.isFinite(value);
  const text = (value) => typeof value === "string" ? value.trim() : "";
  function displayUnit(value, fallback = "units") {
    const unit = text(value);
    return /^nos$/i.test(unit) ? "units" : unit || fallback;
  }
  const opsTargetView = (target) => {
    const normalized = text(target).replace(/^#+/, "");
    if (normalized === "ops-chat-panel" || normalized === "ops-overview" || normalized === "ops-economic-panel") return "agent";
    return "operations";
  };
  function opsTargetRoute(target, currentHref = "http://localhost/operations") {
    const normalizedTarget = text(target).replace(/^#+/, "");
    if (!normalizedTarget) return null;
    let url;
    try {
      url = new URL(currentHref, "http://localhost");
    } catch {
      return null;
    }
    const view = opsTargetView(normalizedTarget);
    url.searchParams.set("view", view);
    url.hash = normalizedTarget;
    return {
      target: normalizedTarget,
      view,
      href: `${url.pathname}${url.search}${url.hash}`,
    };
  }
  async function runAskQuestion({ value, asking = false, available = false, request, onEmpty } = {}) {
    const question = text(value);
    if (!question) {
      if (typeof onEmpty === "function") onEmpty();
      return { sent: false, reason: "EMPTY", question: "" };
    }
    if (asking || !available) return { sent: false, reason: "BLOCKED", question };
    await request(question);
    return { sent: true, reason: "", question };
  }
  const firstText = (record, keys) => {
    if (!isRecord(record)) return "";
    for (const key of keys) {
      const value = text(record[key]);
      if (value) return value;
    }
    return "";
  };
  const numberFrom = (value) => {
    if (finite(value)) return value;
    if (!isRecord(value)) return null;
    for (const key of ["value", "quantity", "count", "observed", "actual", "total"]) {
      if (finite(value[key])) return value[key];
    }
    return null;
  };
  const numberFromKeys = (record, keys) => {
    if (!isRecord(record)) return null;
    for (const key of keys) {
      const value = numberFrom(record[key]);
      if (finite(value)) return value;
    }
    return null;
  };
  const formatNumber = (value) => finite(value)
    ? value.toLocaleString(undefined, { maximumFractionDigits: 2 })
    : "Unknown";
  const formatDate = (value) => {
    const parsed = Date.parse(value);
    if (!Number.isFinite(parsed)) return "Time unavailable";
    return new Date(parsed).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  };
  const isRetainedEvidence = (value) => text(value?.status).toUpperCase() === "RETAINED_AS_OF";
  const conversationInferenceCapability = (value) => {
    const records = [];
    if (isRecord(value)) {
      records.push(value);
      if (isRecord(value.conversation)) records.push(value.conversation);
    }
    for (const record of records) {
      const candidate = record.inference_capability
        ?? record.conversation_capability
        ?? record.live_inference
        ?? record.capability;
      const state = isRecord(candidate) ? (candidate.status ?? candidate.state ?? candidate.value) : candidate;
      if (state === true || /^(AVAILABLE|LIVE|READY|ENABLED|TRUE)$/i.test(text(state))) return "Agent inference capability available";
    }
    return "";
  };
  const retainedEvidenceLabel = (value, conversation = null) => {
    if (!isRecord(value)) return "";
    const asOf = text(value.as_of);
    if (!isRetainedEvidence(value) || !asOf || !Number.isFinite(Date.parse(asOf))) return "";
    return `Retained accepted evidence · as of ${formatDate(asOf)} · ${conversationInferenceCapability(conversation) || "read-only Agent available when configured"}`;
  };
  const erpEvidenceSourceLabel = (value) => {
    const status = text(value?.status).toUpperCase();
    if (status === "RETAINED_AS_OF") return "retained accepted ERP evidence";
    if (status === "CURRENT") return "current ERP source";
    if (status.includes("UNAVAILABLE")) return "ERP source unavailable";
    return "ERP source freshness unknown";
  };
  const freshActionsAllowed = (value) => value?.actions_enabled !== false;
  const sourceAwareErpText = (value, evidenceMode) => {
    const source = erpEvidenceSourceLabel(evidenceMode);
    return text(value)
      .replace(/current ERP source/gi, source)
      .replace(/current source/gi, source);
  };
  const pretty = (value) => text(value).replace(/[_-]+/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

  function canonicalType(value) {
    const key = text(value).toLowerCase().replace(/[-\s]+/g, "_");
    if (key === "carrierpickup" || key === "pickup" || key === "carrier_pick_up") return "carrier_pickup";
    if (key === "delivery_confirmation" || key === "carrier_delivery") return "delivery";
    return EVENT_TYPES.has(key) ? key : "";
  }

  function templateDefault(template, key) {
    if (!isRecord(template)) return "";
    const candidates = [template, template.defaults, template.values, template.payload];
    for (const candidate of candidates) {
      if (isRecord(candidate) && candidate[key] !== undefined && candidate[key] !== null) return candidate[key];
    }
    if (Array.isArray(template.fields)) {
      const field = template.fields.find((item) => isRecord(item) && text(item.name || item.key) === key);
      if (field && field.value !== undefined && field.value !== null) return field.value;
    }
    return "";
  }

  function normalizeTemplate(template, index = 0) {
    if (typeof template === "string") {
      const type = canonicalType(template);
      return type ? { type, label: pretty(type), description: "Declared synthetic evidence", source: "Simulated operator input", _index: index } : null;
    }
    if (!isRecord(template)) return null;
    const type = canonicalType(template.type || template.event_type || template.kind || template.name);
    if (!type) return null;
    return {
      ...template,
      type,
      label: firstText(template, ["label", "title", "name"]) || pretty(type),
      description: firstText(template, ["description", "summary", "help"]) || "Declared synthetic evidence",
      source: firstText(template, ["source", "source_label", "provider"]) || "Simulated operator input",
      _index: index,
    };
  }

  function normalizeTemplates(value) {
    if (!Array.isArray(value)) return [];
    return value.map((template, index) => normalizeTemplate(template, index)).filter(Boolean);
  }

  function shouldPreserveTemplateFields({ currentType, nextType, fieldsRendered = false, resetFields = false } = {}) {
    return Boolean(!resetFields && currentType && nextType && currentType === nextType && fieldsRendered);
  }

  function normalizeEconomicProposal(value) {
    if (!isRecord(value)) return null;
    return {
      ...value,
      status: text(value.status).toUpperCase(),
      selected_candidate_id: text(value.selected_candidate_id),
      candidates: Array.isArray(value.candidates) ? value.candidates.filter(isRecord) : [],
      source_evidence: Array.isArray(value.source_evidence) ? value.source_evidence.filter(isRecord) : [],
      model: isRecord(value.model) ? { ...value.model } : {},
      deterministic_gate: isRecord(value.deterministic_gate) ? { ...value.deterministic_gate } : {},
    };
  }

  function economicProposalFrom(value) {
    return normalizeEconomicProposal(value?.economic_proposal);
  }

  function economicNumber(...values) {
    for (const value of values) {
      const number = numberFrom(value);
      if (finite(number)) return number;
    }
    return null;
  }

  function economicSnapshotValues(next, proposal) {
    const quantities = isRecord(next?.quantities) ? next.quantities : {};
    const gate = isRecord(proposal?.deterministic_gate) ? proposal.deterministic_gate : {};
    const stock = isRecord(gate.stock_snapshot) ? gate.stock_snapshot : {};
    return {
      ordered: economicNumber(
        proposal?.ordered_quantity,
        proposal?.order_quantity,
        proposal?.total_quantity,
        quantities.ordered,
        stock.ordered_quantity,
        stock.ordered,
        stock.total_quantity,
        stock.total,
      ),
      ready: economicNumber(
        proposal?.ready_quantity,
        proposal?.ready_now_quantity,
        proposal?.ready_now,
        proposal?.available_now,
        quantities.usable,
        quantities.available,
        stock.ready_quantity,
        stock.ready,
        stock.ready_now,
        stock.available_now,
        stock.usable,
        stock.available,
      ),
      dispatched: economicNumber(
        proposal?.dispatched_quantity,
        quantities.dispatched,
        quantities.dispatched_quantity,
        stock.dispatched_quantity,
        stock.dispatched,
      ),
      awaiting_release: economicNumber(
        proposal?.awaiting_release_quantity,
        proposal?.awaiting_release,
        proposal?.awaiting_release_units,
        proposal?.unreleased_quantity,
        proposal?.not_released_quantity,
        proposal?.held_quantity,
        proposal?.missing_quantity,
        proposal?.release_pending_quantity,
        quantities.held,
        quantities.missing,
        stock.awaiting_release_quantity,
        stock.awaiting_release,
        stock.awaiting_release_units,
        stock.unreleased_quantity,
        stock.not_released_quantity,
        stock.release_pending_quantity,
        stock.held,
        stock.held_quantity,
        stock.missing,
      ),
    };
  }

  function economicValueText(value, fallback = "Unavailable") {
    if (finite(value)) return formatNumber(value);
    if (typeof value === "boolean") return value ? "true" : "false";
    if (typeof value === "string") return text(value) || fallback;
    if (Array.isArray(value)) {
      const values = value.map((item) => economicValueText(item, "")).filter(Boolean);
      return values.length ? values.join(" · ") : fallback;
    }
    if (isRecord(value)) {
      const label = firstText(value, ["label", "title", "summary", "message", "reason", "value"]);
      if (label) return label;
      try {
        const encoded = JSON.stringify(value);
        return encoded || fallback;
      } catch (_) { return fallback; }
    }
    return fallback;
  }

  function economicQuantityText(value) {
    if (finite(value)) return formatNumber(value);
    if (typeof value === "string") return text(value) || "Quantity unavailable";
    if (Array.isArray(value)) {
      const values = value.map((item) => economicQuantityText(item)).filter((item) => item !== "Quantity unavailable");
      return values.length ? values.join(" · ") : "Quantity unavailable";
    }
    if (!isRecord(value)) return "Quantity unavailable";
    const amount = numberFrom(value);
    if (finite(amount)) {
      const unit = displayUnit(firstText(value, ["uom", "unit", "unit_label", "units_label"]), "");
      return `${formatNumber(amount)}${unit ? ` ${unit}` : ""}`;
    }
    const entries = Object.entries(value)
      .map(([key, item]) => {
        const number = numberFrom(item);
        return finite(number) ? `${pretty(key)} ${formatNumber(number)}` : "";
      })
      .filter(Boolean);
    return entries.length ? entries.join(" · ") : economicValueText(value, "Quantity unavailable");
  }

  function economicPostageDetails(candidate) {
    const estimate = isRecord(candidate?.estimated_postage) ? candidate.estimated_postage : {};
    const amount = numberFrom(estimate.amount);
    const currency = text(estimate.currency);
    const label = firstText(estimate, ["label", "description", "service"]);
    const sourceRef = firstText(estimate, ["source_ref", "source_id", "ref", "url", "href"]);
    const amountText = finite(amount)
      ? [currency, economicAmountText(amount)].filter(Boolean).join(" ")
      : "Estimate unavailable";
    return { amount, currency, label, sourceRef, amountText };
  }

  function economicAmountText(value) {
    return finite(value)
      ? value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      : "Amount unavailable";
  }

  function economicPostageDifference(proposal) {
    const supplied = [proposal?.estimated_postage_difference, proposal?.postage_difference, proposal?.economic_difference]
      .find((value) => isRecord(value) && finite(numberFrom(value.amount)) && text(value.currency));
    if (supplied) return { amount: numberFrom(supplied.amount), currency: text(supplied.currency) };
    const candidates = Array.isArray(proposal?.candidates) ? proposal.candidates : [];
    const details = candidates.map(economicPostageDetails);
    if (details.length < 2 || details.some((item) => !finite(item.amount) || !item.currency)) return null;
    const currency = details[0].currency;
    if (details.some((item) => item.currency.toUpperCase() !== currency.toUpperCase())) return null;
    const amount = Math.abs(details[0].amount - details[1].amount);
    return { amount, currency };
  }

  function economicStatusTone(status) {
    const value = text(status).toUpperCase();
    if (value === "PREPARED") return "lime";
    if (value === "DEFERRED" || value === "NEEDS_EVIDENCE") return "amber";
    if (/ERROR|FAILED|UNAVAILABLE/.test(value)) return "coral";
    return value ? "cyan" : "neutral";
  }

  function economicCandidateState(candidate) {
    if (candidate?.executable === true) return { label: "Executable", tone: "lime" };
    if (candidate?.executable === false) return { label: "Conditional", tone: "amber" };
    return { label: "Status unavailable", tone: "neutral" };
  }

  function economicConditionsText(value) {
    if (Array.isArray(value)) {
      const conditions = value.map((item) => economicConditionsText(item)).filter(Boolean);
      return conditions.length ? conditions.join(" · ") : "Conditions unavailable from source.";
    }
    if (isRecord(value)) {
      return firstText(value, ["label", "title", "summary", "message", "reason", "requirement"])
        || economicValueText(value, "Conditions unavailable from source.");
    }
    return economicValueText(value, "Conditions unavailable from source.");
  }

  function economicStructuredText(value, fallback = "Unavailable from source.") {
    if (typeof value === "string") return text(value) || fallback;
    if (finite(value) || typeof value === "boolean") return economicValueText(value, fallback);
    if (Array.isArray(value) || isRecord(value)) {
      try {
        const encoded = JSON.stringify(value);
        return encoded || fallback;
      } catch (_) { return fallback; }
    }
    return fallback;
  }

  function economicDateText(value, fallback = "Unavailable from source.") {
    const raw = text(value);
    if (!raw || !Number.isFinite(Date.parse(raw))) return economicValueText(value, fallback);
    try {
      return new Intl.DateTimeFormat("en-US", {
        timeZone: "America/Los_Angeles",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
        timeZoneName: "short",
      }).format(new Date(raw));
    } catch (_) {
      return economicValueText(value, fallback);
    }
  }

  function economicSnapshotText(value, fallback = "Unavailable from source.") {
    if (!isRecord(value)) return economicValueText(value, fallback);
    const parts = [];
    if (Array.isArray(value.lots)) {
      const lotSummaries = value.lots.map((lot) => {
        if (!isRecord(lot)) return "";
        const name = firstText(lot, ["lot", "name", "id"]) || "Lot";
        const usable = numberFromKeys(lot, ["usable", "usable_quantity", "available"]);
        const held = numberFromKeys(lot, ["held", "held_quantity", "on_hold"]);
        const quantity = numberFromKeys(lot, ["quantity", "received", "expected_quantity"]);
        const details = [
          finite(usable) ? `usable ${formatNumber(usable)}` : "",
          finite(held) ? `held ${formatNumber(held)}` : "",
          !finite(usable) && !finite(held) && finite(quantity) ? `quantity ${formatNumber(quantity)}` : "",
          firstText(lot, ["status"]) ? pretty(firstText(lot, ["status"])) : "",
        ].filter(Boolean);
        return `${name}${details.length ? ` · ${details.join(" · ")}` : ""}`;
      }).filter(Boolean);
      if (lotSummaries.length) parts.push(`Lots: ${lotSummaries.join("; ")}`);
      else {
        const aggregateUsable = value.lots.reduce((total, lot) => total + (isRecord(lot) ? (numberFromKeys(lot, ["usable", "usable_quantity", "available"]) || 0) : 0), 0);
        const aggregateHeld = value.lots.reduce((total, lot) => total + (isRecord(lot) ? (numberFromKeys(lot, ["held", "held_quantity", "on_hold"]) || 0) : 0), 0);
        if (aggregateUsable || aggregateHeld) parts.push(`Lots: usable ${formatNumber(aggregateUsable)} · held ${formatNumber(aggregateHeld)}`);
      }
    }
    if (Array.isArray(value.allocations)) {
      const allocationSummaries = value.allocations.map((allocation) => {
        if (!isRecord(allocation)) return "";
        const order = firstText(allocation, ["customer_order", "order", "order_id"]) || "Order";
        const requested = numberFromKeys(allocation, ["requested_quantity", "requested", "quantity"]);
        const allocated = numberFromKeys(allocation, ["allocated", "allocated_quantity", "ready_quantity"]);
        const details = [
          finite(allocated) ? `allocated ${formatNumber(allocated)}` : "",
          finite(requested) ? `requested ${formatNumber(requested)}` : "",
        ].filter(Boolean);
        return `${order}${details.length ? ` · ${details.join(" · ")}` : ""}`;
      }).filter(Boolean);
      if (allocationSummaries.length) parts.push(`Allocations: ${allocationSummaries.join("; ")}`);
    }
    const fields = [
      ["status", "Status"],
      ["quantity", "Quantity"],
      ["ordered_quantity", "Ordered"],
      ["ready_quantity", "Ready"],
      ["ready_now", "Ready now"],
      ["available_now", "Available now"],
      ["awaiting_release_quantity", "Awaiting release"],
      ["awaiting_release", "Awaiting release"],
      ["unreleased_quantity", "Unreleased"],
      ["held_quantity", "Held"],
      ["missing_quantity", "Missing"],
      ["released_quantity", "Released"],
      ["partial_dispatch_allowed", "Partial dispatch"],
      ["minimum_dispatch_quantity", "Minimum dispatch"],
      ["final_remainder_allowed", "Final remainder"],
      ["consolidation_allowed", "Consolidation"],
      ["partial_dispatch", "Partial dispatch"],
      ["final_remainder", "Final remainder"],
      ["available", "Available"],
      ["release_status", "Release"],
      ["split_first_dispatch_deadline", "First dispatch deadline"],
      ["split_final_dispatch_deadline", "Tail dispatch deadline"],
      ["consolidated_dispatch_deadline", "Consolidation deadline"],
      ["partial_minimum_quantity", "Partial minimum"],
      ["customer_order", "Customer order"],
      ["destination_id", "Destination"],
      ["deadline_status", "Deadline status"],
      ["release_time", "Release time"],
      ["deadline", "Deadline"],
      ["checked_at", "Checked at"],
      ["source_as_of", "Source as of"],
      ["as_of", "As of"],
      ["at", "At"],
    ];
    for (const [key, label] of fields) {
      const valueText = [
        "split_first_dispatch_deadline",
        "split_final_dispatch_deadline",
        "consolidated_dispatch_deadline",
        "release_time",
        "deadline",
        "checked_at",
        "source_as_of",
        "as_of",
        "at",
      ].includes(key)
        ? economicDateText(value[key], "")
        : economicValueText(value[key], "");
      if (valueText) parts.push(`${label}: ${valueText}`);
    }
    if (parts.length) return parts.join(" · ");
    return firstText(value, ["label", "title", "summary", "message", "reason"]) || fallback;
  }

  function economicSourceEntries(proposal) {
    return Array.isArray(proposal?.source_evidence) ? proposal.source_evidence.filter(isRecord) : [];
  }

  function economicEffectReadback(proposal, next) {
    const effect = isRecord(proposal?.proposal_effect) ? proposal.proposal_effect : {};
    return [
      effect.native_readback,
      effect.native_result,
      effect.readback,
      effect.native_operation,
      effect.result,
      next?.native_readback,
      next?.native_result,
    ].find(isRecord) || null;
  }

  function economicPreparedProposalMatches(effect, next) {
    const prepared = isRecord(next?.prepared_proposal) ? next.prepared_proposal : null;
    if (!prepared) return false;
    const proposalId = firstText(effect, ["proposal_id"]);
    const eventId = firstText(effect, ["event_id"]);
    const candidateId = firstText(effect, ["candidate_id"]);
    const preparedProposalId = firstText(prepared, ["proposal_id"]);
    const preparedEventId = firstText(prepared.event, ["event_id"]);
    const preparedCandidateId = firstText(prepared, ["candidate_id"])
      || firstText(prepared.event, ["candidate_id"]);
    if (proposalId && preparedProposalId !== proposalId) return false;
    if (eventId && preparedEventId !== eventId) return false;
    if (candidateId && preparedCandidateId && preparedCandidateId !== candidateId) return false;
    return Boolean(
      (proposalId && preparedProposalId)
      || (eventId && preparedEventId)
      || (candidateId && preparedCandidateId),
    );
  }

  function economicEffectStatus(proposal, next) {
    const effect = isRecord(proposal?.proposal_effect) ? proposal.proposal_effect : {};
    const readback = economicEffectReadback(proposal, next);
    const readbackStatus = firstText(readback, ["status", "state", "outcome"]).toUpperCase();
    const effectStatus = firstText(effect, ["status", "state", "outcome"]).toUpperCase();
    const preparedStatus = firstText(next?.prepared_proposal, ["status", "state"]).toUpperCase();
    const preparedMatches = economicPreparedProposalMatches(effect, next);
    if (/^(APPLIED|ALREADY_APPLIED)$/.test(readbackStatus)) return readbackStatus;
    if (/^(APPLIED|ALREADY_APPLIED)$/.test(effectStatus)) return effectStatus;
    if (preparedMatches && /^(APPLIED|ALREADY_APPLIED)$/.test(preparedStatus)) return preparedStatus;
    return effectStatus || readbackStatus || (preparedMatches ? preparedStatus : "");
  }

  function economicEffectQuantity(proposal, next) {
    const effect = isRecord(proposal?.proposal_effect) ? proposal.proposal_effect : {};
    const readback = economicEffectReadback(proposal, next);
    return economicNumber(
      effect.quantity,
      effect.applied_quantity,
      effect.dispatched_quantity,
      readback?.quantity,
      readback?.applied_quantity,
      readback?.dispatched_quantity,
    );
  }

  function economicEffectSummary(proposal, next) {
    const effect = isRecord(proposal?.proposal_effect) ? proposal.proposal_effect : {};
    const readback = economicEffectReadback(proposal, next);
    const status = economicEffectStatus(proposal, next);
    const quantity = economicEffectQuantity(proposal, next);
    const eventId = firstText(effect, ["event_id"])
      || firstText(readback, ["event_id", "record_id", "operation_id"])
      || (economicPreparedProposalMatches(effect, next)
        ? firstText(next?.prepared_proposal?.event, ["event_id"])
        : "");
    const nativeRecord = firstText(readback, ["record_id", "document_id", "shipment_id"]);
    const approval = isRecord(effect.approval) ? effect.approval : {};
    const approvedBy = economicPreparedProposalMatches(effect, next)
      ? firstText(approval, ["manager_id"])
      : "";
    const approvedAt = economicPreparedProposalMatches(effect, next)
      ? firstText(approval, ["approved_at"])
      : "";
    const nativeDocuments = Array.isArray(effect.native_documents)
      ? effect.native_documents.filter(isRecord).map((document) => {
        const name = firstText(document, ["name", "record_id", "id"]);
        const kind = firstText(document, ["kind"]);
        return [name || kind || "Native record", name && kind ? kind : ""]
          .filter(Boolean)
          .join(" ");
      }).filter(Boolean)
      : [];
    const quantityLabel = finite(quantity)
      ? /^(APPLIED|ALREADY_APPLIED)$/.test(status)
        ? `${formatNumber(quantity)} dispatched`
        : `${formatNumber(quantity)} planned`
      : "";
    const parts = [
      /^(APPLIED|ALREADY_APPLIED)$/.test(status) ? `Native readback ${pretty(status)}` : status ? `Status ${pretty(status)}` : "",
      quantityLabel,
      eventId ? `Event ${eventId}` : "",
      nativeRecord && nativeRecord !== eventId ? `Record ${nativeRecord}` : "",
      approvedBy ? `Approved by ${approvedBy}` : "",
      approvedAt ? `Approved at ${economicDateText(approvedAt)}` : "",
      nativeDocuments.length ? `Execution-time native records ${nativeDocuments.join("; ")}` : "",
      firstText(readback, ["message", "detail", "summary"]),
    ].filter(Boolean);
    return parts.join(" · ");
  }

  function economicModelIsStale(model) {
    if (!isRecord(model)) return false;
    const freshness = [
      model.status,
      model.freshness_status,
      model.freshness,
      model.model_freshness,
      isRecord(model.freshness) ? model.freshness.status : "",
    ].map((value) => text(value).toUpperCase());
    return model.stale === true
      || model.is_stale === true
      || model.historical === true
      || freshness.some((value) => value === "STALE" || value === "HISTORICAL");
  }

  function normalizeProjection(value) {
    const source = isRecord(value) ? value : {};
    const provided = {
      quantities: isRecord(source.quantities),
      lots: Array.isArray(source.lots),
      allocations: Array.isArray(source.allocations),
      alerts: Array.isArray(source.alerts),
      events: Array.isArray(source.events),
      documents: Array.isArray(source.documents),
      handoffs: Array.isArray(source.handoffs),
      financials: isRecord(source.financials),
      available_event_templates: Array.isArray(source.available_event_templates),
    };
    const normalized = {
      ...source,
      available: source.available === true,
      case_id: text(source.case_id),
      case_label: text(source.case_label),
      stage: text(source.stage) || "UNKNOWN",
      quantities: isRecord(source.quantities) ? { ...source.quantities } : {},
      lots: Array.isArray(source.lots) ? source.lots : [],
      allocations: Array.isArray(source.allocations) ? source.allocations : [],
      alerts: Array.isArray(source.alerts) ? source.alerts : [],
      events: Array.isArray(source.events) ? source.events : [],
      documents: Array.isArray(source.documents) ? source.documents : [],
      handoffs: Array.isArray(source.handoffs) ? source.handoffs : [],
      financials: isRecord(source.financials) ? normalizeFinancials(source.financials) : {},
      available_event_templates: normalizeTemplates(source.available_event_templates),
      conversation: Array.isArray(source.conversation)
        ? source.conversation
        : isRecord(source.conversation) ? { ...source.conversation } : {},
      _provided: provided,
    };
    const economic = normalizeEconomicProposal(source.economic_proposal);
    if (economic) normalized.economic_proposal = economic;
    return normalized;
  }

  function handoffFailureText(value) {
    if (typeof value === "string") return text(value);
    if (!isRecord(value)) return "";
    const detail = firstText(value, ["message", "detail", "reason", "error", "code"]);
    if (detail) return detail;
    const kind = firstText(value, ["kind"]);
    const phase = firstText(value, ["phase"]);
    return [kind, phase ? `phase ${phase}` : ""].filter(Boolean).join(" · ");
  }

  function handoffProvider(record, evidence) {
    const raw = firstText(evidence, ["provider"]) || firstText(record, ["provider", "route"]);
    const value = raw.toLowerCase();
    if (value.includes("airtable")) return "Airtable";
    if (value.includes("jira")) return "Jira";
    if (value.includes("slack")) return "Slack via Celigo";
    if (value.includes("celigo")) return "Celigo";
    return raw ? pretty(raw) : "External record";
  }

  function normalizeHandoffs(value) {
    if (!Array.isArray(value)) return [];
    return value.filter(isRecord).map((record, index) => {
      const evidence = isRecord(record.evidence) ? record.evidence : {};
      const url = firstText(evidence, ["url", "href"]);
      return {
        provider: handoffProvider(record, evidence),
        status: firstText(record, ["status", "state"]) || "Status unavailable",
        updated_at: firstText(record, ["updated_at", "updatedAt", "readback_at"]),
        record_id: firstText(evidence, ["record_id", "id", "key", "name"]),
        url,
        safe_url: safeHref(url),
        last_failure: handoffFailureText(record.last_failure),
        _index: index,
      };
    });
  }

  function groupHandoffs(value) {
    const groups = new Map();
    for (const handoff of normalizeHandoffs(value)) {
      const key = handoff.provider.toLowerCase();
      if (!groups.has(key)) groups.set(key, { provider: handoff.provider, records: [] });
      groups.get(key).records.push(handoff);
    }
    return [...groups.values()].map((group) => {
      const records = [...group.records].sort((left, right) => {
        const leftTime = Date.parse(left.updated_at);
        const rightTime = Date.parse(right.updated_at);
        if (Number.isFinite(leftTime) && Number.isFinite(rightTime) && leftTime !== rightTime) return rightTime - leftTime;
        return right._index - left._index;
      });
      return {
        provider: group.provider,
        latest: records[0],
        last_verified: records.find((record) => record.status.toUpperCase() === "VERIFIED") || null,
        records,
      };
    });
  }

  function normalizeInvoiceGroup(value) {
    const source = isRecord(value) ? value : {};
    const rawStatus = text(source.status).toUpperCase();
    const status = ["CURRENT", "MISSING", "UNAVAILABLE"].includes(rawStatus) ? rawStatus : "UNAVAILABLE";
    return {
      ...source,
      status,
      records: Array.isArray(source.records) ? source.records.filter(isRecord) : [],
    };
  }

  function normalizeFinancials(value) {
    const source = isRecord(value) ? value : {};
    return {
      ...source,
      status: ["CURRENT", "UNAVAILABLE"].includes(text(source.status).toUpperCase())
        ? text(source.status).toUpperCase()
        : "UNAVAILABLE",
      purchase_order: isRecord(source.purchase_order) ? { ...source.purchase_order } : null,
      sales_orders: Array.isArray(source.sales_orders) ? source.sales_orders.filter(isRecord) : [],
      purchase_invoices: normalizeInvoiceGroup(source.purchase_invoices),
      sales_invoices: Array.isArray(source.sales_invoices)
        ? source.sales_invoices.filter(isRecord).map((row) => ({
          ...row,
          customer_order: firstText(row, ["customer_order", "sales_order"]),
          ...normalizeInvoiceGroup(row),
        }))
        : [],
    };
  }

  function financialStatusMessage(status, kind = "", evidenceMode = null) {
    const label = kind ? `${kind} invoice` : "Invoice";
    const source = erpEvidenceSourceLabel(evidenceMode);
    const normalized = text(status).toUpperCase();
    if (normalized === "CURRENT") return `${source[0].toUpperCase()}${source.slice(1)} returned invoice records.`;
    if (normalized === "MISSING") return `No ${label.toLowerCase()} linked in the ${source}.`;
    return `${label} data is unavailable from the ${source}.`;
  }

  function formatMoney(value, currency) {
    const amount = numberFrom(value);
    const unit = text(currency);
    if (!finite(amount)) return "Amount unavailable";
    return unit ? `${unit} ${formatNumber(amount)}` : `Amount known; currency unavailable (${formatNumber(amount)})`;
  }

  function financialOrderSummary(order, unit = "units") {
    const line = isRecord(order?.line) ? order.line : {};
    const currency = text(order?.currency);
    const amount = formatMoney(line.net_amount, currency);
    const rate = formatMoney(line.rate, currency);
    const quantity = numberFrom(line.quantity);
    const quantityText = finite(quantity) ? `${formatNumber(quantity)} ${unit}` : "Quantity unavailable";
    return `Line amount: ${amount} · Rate: ${rate} × ${quantityText}`;
  }

  function invoiceRecordSummary(record) {
    if (!isRecord(record)) return "Invoice record unavailable.";
    const documentRecord = isRecord(record.document) ? record.document : {};
    const docstatus = finite(numberFrom(record.docstatus)) ? `Docstatus ${formatNumber(numberFrom(record.docstatus))}` : "Docstatus unavailable";
    const status = firstText(documentRecord, ["status"]) || "Status unavailable";
    const currency = text(record.currency) || "Currency unavailable";
    return `${docstatus} · Status ${status} · Currency ${currency} · Invoice-level grand total ${formatMoney(record.grand_total, record.currency)} · Invoice-level outstanding amount ${formatMoney(record.outstanding_amount, record.currency)}`;
  }

  function normalizeContractPlan(value) {
    if (!isRecord(value) || text(value.version) !== "v1" || !text(value.plan_id) || !text(value.state_revision) || !Array.isArray(value.rows) || !value.rows.length) return null;
    if (value.rows.some((row) => !isRecord(row) || !firstText(row, ["customer_order"]))) return null;
    return {
      ...value,
      version: "v1",
      plan_id: text(value.plan_id),
      state_revision: text(value.state_revision),
      rows: value.rows,
    };
  }

  function contractPlanRows(plan) {
    const normalized = normalizeContractPlan(plan);
    if (!normalized) return [];
    return normalized.rows.map((row) => {
      const dispatchEligibility = firstText(row, ["dispatch_eligibility"]);
      return {
        customer_order: firstText(row, ["customer_order"]),
        promised_delivery_at: firstText(row, ["promised_delivery_at"]),
        customer_priority: numberFrom(row.customer_priority),
        partial_dispatch: typeof row.partial_dispatch === "boolean" ? row.partial_dispatch : null,
        minimum_dispatch_quantity: numberFrom(row.minimum_dispatch_quantity),
        allow_final_remainder: typeof row.allow_final_remainder === "boolean" ? row.allow_final_remainder : null,
        prepared_commitment: numberFrom(row.prepared_commitment),
        new_quantity: numberFrom(row.new_quantity),
        quantity: numberFrom(row.quantity),
        remaining_after_dispatch: numberFrom(row.remaining_after_dispatch),
        ...(dispatchEligibility ? { dispatch_eligibility: dispatchEligibility } : {}),
      };
    });
  }

  function contractDecisionState(plan, decision) {
    const normalized = normalizeContractPlan(plan);
    if (!normalized || !isRecord(decision)) return "UNAVAILABLE";
    const status = text(decision.status).toUpperCase();
    if (status === "PENDING") return "PENDING";
    if (status !== "SELECTED") return "UNAVAILABLE";
    return text(decision.plan_id) === normalized.plan_id && text(decision.state_revision) === normalized.state_revision
      ? "SELECTED"
      : "PENDING";
  }

  function contractPanelState(plan, decision) {
    const normalized = normalizeContractPlan(plan);
    if (!normalized) return "UNAVAILABLE";
    if (numberFrom(normalized.new_quantity) === 0) return "COMPLETE";
    return contractDecisionState(normalized, decision);
  }

  function pendingAllocationEligibility(projectionValue) {
    const decision = isRecord(projectionValue?.allocation_decision) ? projectionValue.allocation_decision : {};
    const status = text(decision.status).toUpperCase();
    if (status !== "PENDING") {
      return {
        status,
        pending_event_id: "",
        eligible: false,
        reason: status ? "Only a pending allocation decision can be reviewed." : "No pending allocation decision is recorded.",
      };
    }
    const pendingEventId = text(decision.event_id);
    return {
      status,
      pending_event_id: pendingEventId,
      eligible: Boolean(pendingEventId),
      reason: pendingEventId ? "" : "Pending allocation review is unavailable because the source event ID is missing.",
    };
  }

  function pendingAllocationRequest(projectionValue, retryId) {
    const eligibility = pendingAllocationEligibility(projectionValue);
    const id = text(retryId);
    if (!eligibility.eligible || !id) return null;
    return { retry_id: id, pending_event_id: eligibility.pending_event_id };
  }

  function normalizeAllocationRetries(value) {
    if (!Array.isArray(value)) return [];
    return value.filter(isRecord).map((retry, index) => ({
      ...retry,
      retry_id: text(retry.retry_id),
      pending_event_id: text(retry.pending_event_id),
      status: text(retry.status) || "Status unavailable",
      plan_id: text(retry.plan_id),
      state_revision: text(retry.state_revision),
      operations: Array.isArray(retry.operations) ? retry.operations : [],
      _index: index,
    })).filter((retry) => retry.retry_id || retry.pending_event_id);
  }

  function allocationRetryForDecision(projectionValue, submittedRetryId = "") {
    if (!isRecord(projectionValue) || !isRecord(projectionValue.allocation_decision)) return null;
    const decision = projectionValue.allocation_decision;
    const retries = normalizeAllocationRetries(projectionValue.allocation_retries);
    const requestedRetryId = text(submittedRetryId);
    if (requestedRetryId) return retries.find((retry) => retry.retry_id === requestedRetryId) || null;
    const decisionRetryId = text(decision.retry_id);
    if (decisionRetryId) return retries.find((retry) => retry.retry_id === decisionRetryId) || null;
    const pendingEventId = text(decision.event_id);
    return [...retries].reverse().find((retry) => pendingEventId && retry.pending_event_id === pendingEventId) || null;
  }

  function dispatchEligibilityText(value) {
    const source = text(value).toUpperCase();
    const labels = {
      FINAL_REMAINDER_ALLOWED: "Eligible for an allowed final remainder",
      MEETS_MINIMUM: "Meets the minimum dispatch quantity",
      NO_DISPATCH_REMAINING: "No dispatch remains for this order",
      NOT_EXECUTABLE: "Not executable from the current stock",
    };
    return labels[source] || (source ? `Source status: ${pretty(source)}` : "");
  }

  function allocationReviewOutcome(projectionValue, submittedRetryId) {
    const retry = allocationRetryForDecision(projectionValue, submittedRetryId);
    if (!retry) {
      return {
        status: "UNKNOWN_OUTCOME",
        tone: "error",
        message: "Pending allocation review outcome is unavailable. No pick or dispatch claim can be made.",
      };
    }
    const status = text(retry.status).toUpperCase();
    const decisionStatus = text(projectionValue?.allocation_decision?.status).toUpperCase();
    const operationStatuses = retry.operations
      .filter(isRecord)
      .map((operation) => text(operation.status).toUpperCase());
    if (status === "UNKNOWN_OUTCOME" || operationStatuses.includes("UNKNOWN_OUTCOME")) {
      return {
        status,
        tone: "error",
        message: "Pending allocation review has an unknown native outcome. No pick or dispatch claim can be made; review the source before retrying.",
      };
    }
    if (status === "BLOCKED" || operationStatuses.includes("BLOCKED")) {
      return {
        status,
        tone: "error",
        message: "Pending allocation review was blocked before completion. Dispatch remains separate; review the source before continuing.",
      };
    }
    if (status === "APPLIED") {
      return {
        status,
        tone: "success",
        message: decisionStatus === "SELECTED"
          ? "Pending allocation review selected the plan and verified pick preparation. Dispatch remains a separate step."
          : "Pending allocation review verified pick preparation. Dispatch remains a separate step.",
      };
    }
    if (status === "PENDING") {
      return {
        status,
        tone: "error",
        message: "Pending allocation review remains pending. Pick preparation is not confirmed.",
      };
    }
    return {
      status: status || "UNKNOWN_OUTCOME",
      tone: "error",
      message: `Pending allocation review returned ${pretty(status || "an unknown status")}. No pick or dispatch claim can be made.`,
    };
  }

  function pendingAllocationActionState(projectionValue, action, { sourceReady = true, panelVisible = true } = {}) {
    const eligibility = pendingAllocationEligibility(projectionValue);
    const contractState = contractPanelState(projectionValue?.feasible_allocation_plan, projectionValue?.allocation_decision);
    const eligible = Boolean(projectionValue?.available === true && freshActionsAllowed(projectionValue) && contractState === "PENDING"
      && eligibility.eligible && sourceReady && panelVisible);
    const matches = Boolean(isRecord(action)
      && text(action.caseId) === text(projectionValue?.case_id)
      && text(action.pendingEventId) === eligibility.pending_event_id);
    const inFlight = Boolean(eligible && matches && action.inFlight === true);
    return {
      eligible,
      in_flight: inFlight,
      disabled: !eligible || inFlight,
      label: inFlight ? "Reviewing pending allocation…" : "Review pending allocation",
    };
  }

  function shouldRetainPendingAllocationRetry(requestError, outcomeStatus = "") {
    if (requestError) {
      const status = Number(requestError.status);
      return !(Number.isFinite(status) && status >= 400 && status < 500);
    }
    return text(outcomeStatus).toUpperCase() === "UNKNOWN_OUTCOME";
  }

  function allocationQuantity(allocation, keys) {
    return numberFromKeys(allocation, keys);
  }

  function fulfillmentBenchmark(next) {
    if (!isRecord(next) || next.available !== true || !isRecord(next.quantities) || !Array.isArray(next.allocations)) {
      return { status: "UNAVAILABLE", reason: "The current source does not provide comparable fulfillment facts." };
    }
    const targets = next.allocations.map((allocation) =>
      allocationQuantity(allocation, ["ordered", "requested", "requested_quantity", "demand", "quantity"])
    );
    if (!targets.length || targets.some((value) => !finite(value) || value < 0)) {
      return { status: "UNAVAILABLE", reason: "Customer commitment quantities are unavailable from the current source." };
    }
    const target = targets.reduce((total, value) => total + value, 0);
    const dispatched = quantity(next, "dispatched");
    const confirmed = quantity(next, "delivery_confirmed");
    if (!finite(dispatched) || !finite(confirmed) || target <= 0) {
      return { status: "UNAVAILABLE", reason: "Current dispatch or delivery-confirmation quantities are unavailable." };
    }
    return {
      status: "CURRENT",
      target,
      dispatched,
      confirmed,
      unit: displayUnit(next.quantities.uom),
      order_count: targets.length,
      synthetic: next.synthetic_input === true,
    };
  }

  function alertStatus(alert) {
    return firstText(alert, ["status", "state"]).toUpperCase();
  }
  function isResolvedAlert(alert) {
    return /RESOLVED|CLOSED|DONE/.test(alertStatus(alert));
  }
  function alertStage(alert) {
    const code = firstText(alert, ["code", "kind", "message", "detail"]).toUpperCase();
    if (/QUALITY|INSPECTION|HOLD|SPEC/.test(code)) return "inspection";
    if (/SHORT|MISSING|RECEIV|ARRIV|LOT|BATCH/.test(code)) return "arrival";
    if (/ALLOC|RESERV|CUSTOMER|CONTRACT/.test(code)) return "allocation";
    if (/PICK/.test(code)) return "picked";
    if (/DISPATCH|SHIP|CARRIER/.test(code)) return "dispatch";
    if (/DELIVERY|POD/.test(code)) return "delivery";
    return "";
  }
  function activeAlertStages(next) {
    if (!Array.isArray(next?.alerts)) return {};
    return next.alerts.reduce((stages, alert, index) => {
      if (!isRecord(alert) || isResolvedAlert(alert)) return stages;
      const stage = alertStage(alert);
      if (stage && !stages[stage]) stages[stage] = { index, code: firstText(alert, ["code", "kind"]) || "Active alert" };
      return stages;
    }, {});
  }

  function flowStageFacts(next, stage) {
    const unit = displayUnit(next?.quantities?.uom);
    const current = quantity(next, stage.metric);
    const dispatched = quantity(next, "dispatched");
    const ordered = quantity(next, "ordered");
    if (stage.key === "inspection") {
      const held = quantity(next, "held");
      if (finite(held) && held > 0) return { current: `${formatNumber(held)} held now`, cumulative: "Review inspection evidence", complete: false };
      if (finite(dispatched) && dispatched > 0) return { current: "No current hold", cumulative: `${formatNumber(dispatched)} released to fulfillment`, complete: true };
      return { current: finite(current) ? `${formatNumber(current)} usable now` : "Inspection status unknown", cumulative: "Quality evidence", complete: stageProof(next, stage) };
    }
    if (stage.key === "allocation") {
      const pending = pendingAllocationEligibility(next);
      if (pending.status === "PENDING") {
        return {
          current: finite(current) ? `${formatNumber(current)} proposed` : "Proposed allocation quantity unknown",
          cumulative: "Decision pending · no allocation prepared",
          complete: false,
        };
      }
      const target = fulfillmentBenchmark(next);
      if (target.status === "CURRENT" && target.dispatched >= target.target) return { current: "No stock awaiting allocation", cumulative: `${formatNumber(target.target)} / ${formatNumber(target.target)} committed`, complete: true };
      return { current: finite(current) ? `${formatNumber(current)} allocated now` : "Allocation status unknown", cumulative: stage.detail, complete: stageProof(next, stage) };
    }
    if (stage.key === "picked") {
      const picked = (Array.isArray(next?.allocations) ? next.allocations : []).reduce((total, allocation) => {
        const value = allocationQuantity(allocation, ["picked", "picked_quantity", "picked_qty"]);
        return finite(value) ? total + value : total;
      }, 0);
      return { current: picked > 0 ? `${formatNumber(picked)} picked cumulatively` : "Picked evidence pending", cumulative: picked > 0 ? `Recorded in current case · ${unit}` : stage.detail, complete: picked > 0 || pickedEvidenceRecorded(next) };
    }
    if (stage.key === "delivery") {
      const label = finite(current)
        ? next.synthetic_input === true ? `${formatNumber(current)} declared synthetic carrier confirmations` : `${formatNumber(current)} recorded confirmations`
        : "Delivery confirmation unknown";
      return { current: label, cumulative: finite(ordered) ? `${formatNumber(current)} / ${formatNumber(ordered)} ${unit}` : stage.detail, complete: finite(current) && current > 0 };
    }
    if (stage.key === "dispatch") {
      return { current: finite(dispatched) ? `${formatNumber(dispatched)} dispatched cumulatively` : "Dispatch status unknown", cumulative: finite(ordered) ? `${formatNumber(dispatched)} / ${formatNumber(ordered)} ${unit}` : stage.detail, complete: finite(dispatched) && dispatched > 0 };
    }
    return { current: finite(current) ? `${formatNumber(current)} ${unit}` : `${stage.detail} unknown`, cumulative: stage.detail, complete: stageProof(next, stage) };
  }

  function createVoiceController({ recognitionFactory, speechSynthesisApi, utteranceFactory, input, setStatus, dictateButton, readButton, stopButton } = {}) {
    const updateStatus = (value) => { if (typeof setStatus === "function") setStatus(value); };
    let recognition = null;
    try { recognition = typeof recognitionFactory === "function" ? recognitionFactory() : null; } catch (_) { recognition = null; }
    const synthesis = speechSynthesisApi && typeof speechSynthesisApi.speak === "function" ? speechSynthesisApi : null;
    let listening = false;
    let reading = false;
    let answer = "";
    const setButtons = () => {
      if (dictateButton) { dictateButton.disabled = !recognition; dictateButton.setAttribute?.("aria-pressed", String(listening)); }
      if (readButton) readButton.disabled = !synthesis || !answer || reading;
      if (stopButton) stopButton.hidden = !reading;
    };
    if (recognition) {
      recognition.lang = "en-US";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      recognition.onresult = (event) => {
        const result = event?.results?.[event.results.length - 1];
        const transcript = text(result?.[0]?.transcript);
        if (transcript && input) input.value = [text(input.value), transcript].filter(Boolean).join(text(input.value) ? " " : "");
        input?.focus?.();
        updateStatus(transcript ? "Dictation added. Review it, then press Ask to send." : "No English dictation was captured. You can type your question.");
      };
      recognition.onerror = (event) => {
        listening = false;
        setButtons();
        updateStatus(event?.error === "not-allowed" || event?.error === "service-not-allowed"
          ? "Microphone permission was denied. Typing remains available."
          : "Dictation is unavailable. Typing remains available.");
      };
      recognition.onend = () => { listening = false; setButtons(); };
    }
    const controller = {
      support() { return { dictation: Boolean(recognition), reading: Boolean(synthesis) }; },
      toggleDictation() {
        if (!recognition) { updateStatus("English dictation is not supported in this browser. Typing remains available."); return false; }
        if (listening) { recognition.stop?.(); listening = false; updateStatus("Dictation stopped. Review the question before sending."); }
        else { listening = true; recognition.start?.(); updateStatus("Listening for English dictation. It will not send automatically."); }
        setButtons(); return true;
      },
      setAnswer(value) {
        const nextAnswer = cleanAnswer(value);
        if (nextAnswer !== answer && reading) {
          synthesis?.cancel?.();
          reading = false;
        }
        answer = nextAnswer;
        setButtons();
      },
      readAnswer() {
        if (!synthesis || !answer || typeof utteranceFactory !== "function") { updateStatus("Answer reading is unavailable in this browser."); return false; }
        try {
          const utterance = utteranceFactory(answer); utterance.lang = "en-US";
          utterance.onend = () => { reading = false; setButtons(); updateStatus("Answer reading finished."); };
          utterance.onerror = () => { reading = false; setButtons(); updateStatus("Answer reading stopped. You can read the text above."); };
          reading = true; synthesis.speak(utterance); setButtons(); updateStatus("Reading the answer in English."); return true;
        } catch (_) { reading = false; setButtons(); updateStatus("Answer reading is unavailable in this browser."); return false; }
      },
      stopReading() { if (!synthesis) return false; synthesis.cancel?.(); reading = false; setButtons(); updateStatus("Answer reading stopped."); return true; },
    };
    setButtons();
    return controller;
  }

  function unwrapProjection(value) {
    if (!isRecord(value)) return null;
    for (const key of ["distributor_operations", "projection", "operation", "result"]) {
      if (isRecord(value[key]) && ("quantities" in value[key] || "available" in value[key] || "stage" in value[key])) return value[key];
    }
    return ("quantities" in value || "available" in value || "stage" in value) ? value : null;
  }

  function projectionSourceState(next) {
    if (!isRecord(next) || next.available === true) return "CURRENT";
    return text(next.stage).toUpperCase() === "DISABLED" || !text(next.case_id)
      ? "DISABLED"
      : "SOURCE_UNAVAILABLE";
  }

  function cleanAnswer(value) {
    return text(value)
      .replace(/<thinking>[\s\S]*?<\/thinking>/gi, "")
      .replace(/<analysis>[\s\S]*?<\/analysis>/gi, "")
      .replace(/<reasoning>[\s\S]*?<\/reasoning>/gi, "")
      .trim();
  }

  function markdownTableCells(value) {
    const line = text(value);
    if (!line.includes("|")) return null;
    const trimmed = line.replace(/^\|/, "").replace(/\|$/, "");
    const cells = trimmed.split("|").map((cell) => cell.trim());
    return cells.length >= 2 ? cells : null;
  }

  function markdownTableDivider(value) {
    const cells = markdownTableCells(value);
    return Boolean(cells && cells.every((cell) => /^:?-{3,}:?$/.test(cell)));
  }

  function markdownBlocks(value) {
    const answer = typeof value === "string" ? value.trim() : "";
    if (!answer) return [];
    const lines = answer.replace(/\r\n?/g, "\n").split("\n");
    const blocks = [];
    let paragraph = [];
    const flushParagraph = () => {
      if (!paragraph.length) return;
      blocks.push({ type: "paragraph", text: paragraph.join(" ") });
      paragraph = [];
    };
    for (let index = 0; index < lines.length;) {
      const line = lines[index];
      const trimmed = line.trim();
      if (!trimmed) {
        flushParagraph();
        index += 1;
        continue;
      }
      const heading = trimmed.match(/^(#{1,3})\s+(.+?)\s*$/);
      if (heading) {
        flushParagraph();
        blocks.push({ type: "heading", level: heading[1].length, text: heading[2].replace(/\s+#+\s*$/, "") });
        index += 1;
        continue;
      }
      const header = markdownTableCells(trimmed);
      if (header && index + 1 < lines.length && markdownTableDivider(lines[index + 1])) {
        flushParagraph();
        const rows = [];
        index += 2;
        while (index < lines.length) {
          const row = markdownTableCells(lines[index]);
          if (!row || row.length !== header.length) break;
          rows.push(row);
          index += 1;
        }
        blocks.push({ type: "table", headers: header, rows });
        continue;
      }
      const bullet = trimmed.match(/^[-*+]\s+(.+)$/);
      if (bullet) {
        flushParagraph();
        const items = [];
        while (index < lines.length) {
          const item = lines[index].trim().match(/^[-*+]\s+(.+)$/);
          if (!item) break;
          items.push(item[1]);
          index += 1;
        }
        blocks.push({ type: "list", items });
        continue;
      }
      paragraph.push(trimmed);
      index += 1;
    }
    flushParagraph();
    return blocks;
  }

  function statusTone(value) {
    const status = text(value).toUpperCase();
    if (/HOLD|FAIL|ERROR|UNKNOWN|UNAVAILABLE|MISSING|CONFLICT|REJECT/.test(status)) return "coral";
    if (/PASS|COMPLETE|CONFIRMED|DELIVERED|READY|RELEASE|USABLE/.test(status)) return "lime";
    if (/DISABLED|PENDING|WAIT|REVIEW|PROCESS/.test(status)) return "amber";
    return "neutral";
  }

  function recommendedAction(code) {
    const value = text(code).toUpperCase();
    if (/SHORT|MISSING|QUANTITY|COUNT/.test(value)) return "Verify the inner count and open a supplier or carrier discrepancy task.";
    if (/QUALITY|INSPECTION|MEASURE|SPEC/.test(value)) return "Hold the lot and review the inspection evidence against its acceptance spec.";
    if (/LOT|BATCH|TRACE|IDENTITY|COUNTER/.test(value)) return "Quarantine the affected lot and verify its traceability with the source or manufacturer.";
    if (/DELIVERY|POD|SHIPMENT/.test(value)) return "Review the shipment evidence; delivery needs an explicit confirmation event.";
    return "Review the evidence and affected customer orders before changing the operation.";
  }

  function buildEventPayload({ type, values = {}, evidenceRef, now, eventId, synthetic = true }) {
    const eventType = canonicalType(type);
    if (!eventType) throw new Error("Choose a supported evidence template.");
    const commonEvidence = text(evidenceRef);
    if (!commonEvidence) throw new Error("Enter an evidence ID before processing the event.");
    const payload = {
      event_id: text(eventId) || `demo-event-${Date.now()}`,
      type: eventType,
      occurred_at: text(now) || new Date().toISOString(),
      evidence_ref: commonEvidence,
      synthetic: synthetic === true,
    };
    const fields = {};
    for (const definition of FIELD_DEFS[eventType]) {
      const raw = values[definition.key];
      if (NUMBER_FIELDS.has(definition.key)) {
        if (raw === undefined || raw === null || text(String(raw)) === "") throw new Error(`${definition.label} is required.`);
        const number = Number(raw);
        if (!Number.isFinite(number) || number < 0) throw new Error(`${definition.label} must be a non-negative number.`);
        fields[definition.key] = number;
      } else {
        const value = text(raw);
        if (!value) throw new Error(`${definition.label} is required.`);
        fields[definition.key] = value;
      }
    }
    Object.assign(payload, fields);
    return payload;
  }

  function deliveryCompletionLabel(next) {
    if (!isRecord(next) || next.available !== true || !isRecord(next.quantities)) return "";
    const sourceStatus = text(next.source_status).toUpperCase();
    // The public projection elides source_status after deriving `available`; when it is present,
    // it must still explicitly confirm the current source.
    if (sourceStatus && sourceStatus !== "CURRENT") return "";
    const quantities = next.quantities;
    const ordered = numberFrom(quantities.ordered);
    if (!finite(ordered) || ordered <= 0) return "";
    if (!["received", "dispatched", "delivery_confirmed"].every((key) => numberFrom(quantities[key]) === ordered)) return "";
    if (!["held", "missing", "usable", "allocated"].every((key) => numberFrom(quantities[key]) === 0)) return "";
    const openAlerts = Array.isArray(next.alerts)
      ? next.alerts.filter((alert) => isRecord(alert) && firstText(alert, ["status", "state"]).toUpperCase() === "OPEN").length
      : 0;
    const completion = next.synthetic_input === true ? "Carrier confirmation declared" : "Delivery confirmed";
    return `${completion} · ${openAlerts} alert${openAlerts === 1 ? "" : "s"} to review`;
  }

  function evidenceStatusLabel(next) {
    if (!isRecord(next)) return "EVIDENCE SOURCE LOADING";
    const evidenceMode = isRecord(next.evidence_mode) ? next.evidence_mode : {};
    const modeStatus = text(evidenceMode.status).toUpperCase();
    if (isRetainedEvidence(evidenceMode)) {
      const asOf = text(evidenceMode.as_of);
      return Number.isFinite(Date.parse(asOf))
        ? `RETAINED EVIDENCE · as of ${formatDate(asOf)}`
        : "RETAINED EVIDENCE";
    }
    if (modeStatus.includes("UNAVAILABLE") || projectionSourceState(next) === "SOURCE_UNAVAILABLE") return "SOURCE UNAVAILABLE";
    if (projectionSourceState(next) === "DISABLED") return "OPERATION NOT CONFIGURED";
    if (modeStatus === "CURRENT") return "CURRENT ERP PROJECTION";
    return next.available === true ? "EVIDENCE FRESHNESS UNKNOWN" : "EVIDENCE SOURCE LOADING";
  }

  function agentProviderDisplay(next) {
    const conversation = isRecord(next?.conversation) ? next.conversation : {};
    const status = (firstText(conversation, ["status", "state"]) || firstText(next, ["conversation_status"])).toUpperCase();
    const provider = firstProvider(conversation, ["provider_label", "provider", "model"])
      || firstProvider(next, ["conversation_provider", "provider", "model"]);
    return provider || (/UNAVAILABLE|ERROR|FAILED|DISABLED/.test(status) ? "Unavailable" : "Ask agent");
  }

  function carrierConfirmationLabel(next, confirmation = quantity(next, "delivery_confirmed"), requested = quantity(next, "ordered")) {
    const confirmed = finite(confirmation) ? formatNumber(confirmation) : "Unknown";
    const target = finite(requested) ? ` / ${formatNumber(requested)}` : "";
    return next?.synthetic_input === true
      ? `Carrier confirmation declared ${confirmed}${target}`
      : `Delivery confirmation recorded ${confirmed}${target}`;
  }

  function sameCurrencyLineTotal(orders) {
    if (!Array.isArray(orders) || !orders.length) return null;
    let currency = "";
    let amount = 0;
    for (const order of orders) {
      const line = isRecord(order?.line) ? order.line : {};
      const lineAmount = numberFrom(line.net_amount);
      const lineCurrency = text(order?.currency);
      if (!finite(lineAmount) || !lineCurrency) return null;
      if (currency && currency !== lineCurrency) return null;
      currency = lineCurrency;
      amount += lineAmount;
    }
    return { amount, currency };
  }

  function orderValueDetails(next) {
    const financials = normalizeFinancials(next?.financials);
    const purchaseOrder = financials.purchase_order;
    const total = purchaseOrder ? sameCurrencyLineTotal([purchaseOrder]) : null;
    if (!isRecord(next) || next.available !== true || financials.status !== "CURRENT" || !total) {
      return {
        value: "Unavailable",
        label: "Purchase order line amount unavailable",
        note: "No amount is inferred when the accepted source does not provide a purchase order line amount.",
      };
    }
    const retained = isRetainedEvidence(next.evidence_mode);
    return {
      value: formatMoney(total.amount, total.currency),
      label: retained ? "Retained purchase order line amount" : "Purchase order line amount",
      note: retained
        ? "Retained accepted ERP evidence. CURRENT means the amount was available in that recorded snapshot, not a fresh source read. Order value only; not revenue, invoice, or payment."
        : "Current ERP source order line amount. Order value only; not revenue, invoice, or payment.",
    };
  }

  function allocationDigest(next) {
    if (!Array.isArray(next?.allocations)) return "Unknown";
    const rows = next.allocations.map((allocation) => {
      const order = firstText(allocation, ["customer_order", "sales_order", "order_name", "order", "name"]);
      const allocated = numberFromKeys(allocation, ["allocated", "reserved", "reservation_quantity"]);
      return order && finite(allocated) ? `${order} ${formatNumber(allocated)}` : "";
    }).filter(Boolean);
    return rows.length ? rows.join(" · ") : "Unknown";
  }

  const exported = {
    buildEventPayload,
    cleanAnswer,
    markdownBlocks,
    conversationAnswer,
    providerLabel,
    retainConversationProjection,
    shouldPreserveTemplateFields,
    formatNumber,
    isRetainedEvidence,
    conversationInferenceCapability,
    retainedEvidenceLabel,
    erpEvidenceSourceLabel,
    sourceAwareErpText,
    freshActionsAllowed,
    normalizeEconomicProposal,
    economicProposalFrom,
    economicSnapshotValues,
    economicPostageDetails,
    economicPostageDifference,
    normalizeProjection,
    normalizeHandoffs,
    groupHandoffs,
    normalizeFinancials,
    financialStatusMessage,
    financialOrderSummary,
    invoiceRecordSummary,
    normalizeContractPlan,
    contractPlanRows,
    contractDecisionState,
    contractPanelState,
    pendingAllocationEligibility,
    pendingAllocationRequest,
    normalizeAllocationRetries,
    allocationRetryForDecision,
    dispatchEligibilityText,
    allocationReviewOutcome,
    pendingAllocationActionState,
    shouldRetainPendingAllocationRetry,
    fulfillmentBenchmark,
    activeAlertStages,
    flowStageFacts,
    createVoiceController,
    normalizeTemplate,
    normalizeTemplates,
    recommendedAction,
    statusTone,
    deliverySummary,
    arrivalQuantitySummary,
    deliveryCompletionLabel,
    evidenceStatusLabel,
    agentProviderDisplay,
    carrierConfirmationLabel,
    sameCurrencyLineTotal,
    orderValueDetails,
    allocationDigest,
    recentActivityEvents,
    unwrapProjection,
    projectionSourceState,
    proposalActionDetail,
    approvalReadback,
    opsTargetRoute,
    runAskQuestion,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = exported;
  if (typeof window !== "undefined") window.Missing20DistributorOperations = exported;
  if (typeof document === "undefined") return;

  const $ = (id) => document.getElementById(id);
  const content = $("ops-content");
  const disabled = $("ops-disabled");
  const sourceState = $("ops-source-state");
  const templateSelect = $("ops-template-select");
  let projection = null;
  let selectedTemplate = null;
  let loading = false;
  let refreshQueued = false;
  let processingEvent = false;
  let asking = false;
  let pollTimer = null;
  let lastProjectionAt = "";
  let retainedConversation = null;
  let voiceController = null;
  let pendingAllocationAction = null;
  let allocationFeedback = null;
  let preparedProposal = null;
  let economicConfigured = false;
  let preparingEconomic = false;
  let selectedPhoto = null;
  let photoPreviewUrl = "";
  let selectedPhotoAttachmentId = "";
  let selectedPhotoLot = "";
  let selectedPhotoPurpose = "overview";
  let selectedPhotoSupersedesAttachmentId = "";
  let photoAnalysisPending = false;
  let photoAnalysisFeedback = { message: "", tone: "" };
  let evidenceDrawerTrigger = null;

  function setText(id, value) {
    const node = $(id);
    if (node) node.textContent = value == null ? "" : String(value);
    return node;
  }
  function setConnection(label, tone = "cyan") {
    setText("ops-connection-label", label);
    const dot = $("ops-connection-dot");
    if (dot) dot.className = `status-dot status-dot-${tone}`;
  }
  function renderRefreshState({ retryPending = false } = {}) {
    const status = evidenceStatusLabel(projection);
    const upper = status.toUpperCase();
    const concise = /UNAVAILABLE|ERROR|FAILED|DISABLED/.test(upper)
      ? "Needs attention"
      : isRetainedEvidence(projection?.evidence_mode) ? "Retained" : "Synced";
    setText("ops-evidence-retention", retryPending ? "Syncing" : concise);
    setText("ops-refresh-state", retryPending ? "Syncing" : concise);
  }
  function showSourceError(error, { configuredSourceFailure = false } = {}) {
    const retained = isRetainedEvidence(projection?.evidence_mode);
    sourceState.hidden = false;
    setText("ops-source-title", retained ? "Retained operation evidence remains available" : "Current operation source unavailable");
    setText("ops-source-detail", retained
      ? "The retained as-of projection remains visible; fresh operation facts were not requested or inferred."
      : error?.message || "The source did not return a usable projection. Quantities are unknown.");
    setConnection(retained ? "Retained evidence" : "Unavailable", retained ? "cyan" : "danger");
    if (retained) {
      renderRefreshState({ retryPending: Boolean(lastProjectionAt) });
    } else {
      setText("ops-evidence-retention", "Needs attention");
      setText("ops-refresh-state", "Needs attention");
      document.body.dataset.operationsState = "unavailable";
      renderUnavailablePresentation();
    }
    if (!projection || configuredSourceFailure) {
      content.hidden = true;
      disabled.hidden = false;
      disabled.querySelector("h2").textContent = configuredSourceFailure ? "Current operation source unavailable" : "Operation source unavailable";
      disabled.querySelector("p").textContent = "No quantities, allocation, benchmark, or delivery state are inferred until the source responds.";
    }
    updateEventButton();
    syncFreshEventControls(projection);
    updateAskButton();
  }
  function clearSourceError() {
    sourceState.hidden = true;
    const retained = Boolean(retainedEvidenceLabel(projection?.evidence_mode, projection));
    setConnection(retained ? "Retained" : "Synced", retained ? "cyan" : "lime");
    renderRefreshState();
    updateEventButton();
    syncFreshEventControls(projection);
    updateAskButton();
  }
  function displayQuantity(value) { return finite(value) ? formatNumber(value) : "Unknown"; }
  function quantity(projectionValue, key) {
    return numberFrom(projectionValue?.quantities?.[key]);
  }
  function setQuantityCard(key, value, unit) {
    const card = document.querySelector(`[data-quantity-card="${key}"]`);
    const valueNode = $(`ops-quantity-${key}`);
    if (!valueNode) return;
    const known = finite(value);
    valueNode.textContent = displayQuantity(value);
    card?.classList.toggle("is-unknown", !known);
    const unitNode = $(`ops-quantity-${key}-unit`);
    if (unitNode && unit) unitNode.textContent = unit;
  }
  function cartonsSummary(value) {
    if (finite(value)) return `${formatNumber(value)} observed`;
    if (!isRecord(value)) return "Unknown";
    const observed = numberFromKeys(value, ["observed", "received", "actual", "count"]);
    const expected = numberFromKeys(value, ["expected", "ordered", "planned"]);
    if (finite(observed) && finite(expected)) return `${formatNumber(observed)} observed · ${formatNumber(expected)} expected`;
    if (finite(observed)) return `${formatNumber(observed)} observed`;
    if (finite(expected)) return `${formatNumber(expected)} expected`;
    return "Unknown";
  }
  function renderQuantities(next) {
    const q = next.quantities || {};
    const unit = displayUnit(q.uom, "Unit not confirmed");
    const allocationPending = pendingAllocationEligibility(next).status === "PENDING";
    const cartons = cartonsSummary(q.cartons);
    const cartonsNode = $("ops-quantity-cartons");
    const cartonsCard = document.querySelector('[data-quantity-card="cartons"]');
    if (cartonsNode) cartonsNode.textContent = cartons;
    cartonsCard?.classList.toggle("is-unknown", cartons === "Unknown");
    for (const key of ["ordered", "received", "usable", "held", "missing", "allocated", "dispatched", "delivery_confirmed"]) {
      setQuantityCard(key, quantity(next, key), key === "delivery_confirmed"
        ? next.synthetic_input === true ? "declared carrier event" : "explicit event"
        : key === "allocated" && allocationPending ? "proposed plan" : unit);
    }
    const allocatedLabel = $("ops-quantity-allocated-label");
    if (allocatedLabel) allocatedLabel.textContent = allocationPending ? "Proposed allocation" : "Allocated";
    setText("ops-quantity-delivery-confirmed-label", next.synthetic_input === true ? "Carrier confirmation declared" : "Delivery confirmation");
    setText("ops-uom-note", text(q.uom)
      ? `Parts are shown in stock UOM ${unit}; cartons remain a separate outer-package observation.`
      : "Stock UOM is not confirmed; cartons and part quantities remain separate observations.");
  }

  function purchaseOrderRecord(next) {
    return Array.isArray(next?.documents)
      ? next.documents.find((record) => /^purchase order$/i.test(firstText(record, ["kind", "doctype", "type"]))) || null
      : null;
  }

  function purchaseOrderIdentifier(next) {
    const purchaseOrder = purchaseOrderRecord(next);
    return purchaseOrder ? firstText(purchaseOrder, ["name", "record_id", "id"]) : "";
  }

  function directPurchaseOrderIdentifier(next) {
    const purchaseOrder = next?.purchase_order;
    if (typeof purchaseOrder === "string") return text(purchaseOrder);
    if (isRecord(purchaseOrder)) return firstText(purchaseOrder, ["name", "record_id", "id", "purchase_order"]);
    return firstText(next, ["purchase_order_id", "po_number", "po"]);
  }

  function purchaseOrderDisplay(next) {
    const identifier = purchaseOrderIdentifier(next) || directPurchaseOrderIdentifier(next);
    if (!identifier) return "";
    return /^PO(?:\d|\s|-|$)/i.test(identifier) ? identifier : `PO ${identifier}`;
  }

  function renderHeaderIncidentState(next) {
    const node = $("ops-header-incident-state");
    if (!node) return;
    const purchaseOrder = purchaseOrderDisplay(next);
    if (purchaseOrder) node.textContent = purchaseOrder;
    else if (economicConfigured && economicProposalFrom(next)) node.textContent = "SYNTHETIC POC";
    else node.textContent = "Operation";
  }

  function renderHero(next) {
    const unit = displayUnit(next?.quantities?.uom);
    const usable = quantity(next, "usable");
    const held = quantity(next, "held");
    const received = quantity(next, "received");
    const dispatched = quantity(next, "dispatched");
    const awaitingRelease = quantity(next, "awaiting_release");
    const purchaseOrder = purchaseOrderDisplay(next);
    const available = next?.available === true;
    const view = document.body.dataset.opsView || "dashboard";
    const title = !available
      ? "Operation facts unavailable"
      : view === "agent"
        ? "Investigate this order"
        : view === "operations"
          ? "Receive & fulfill"
          : finite(usable)
            ? usable > 0 ? `${formatNumber(usable)} ${unit} ready to ship` : finite(dispatched) && dispatched > 0 ? `${formatNumber(dispatched)} ${unit} dispatched` : `${formatNumber(usable)} ${unit} ready to ship`
            : finite(received)
              ? `${formatNumber(received)} ${unit} received`
              : finite(dispatched)
                ? `${formatNumber(dispatched)} ${unit} dispatched`
                : "Order facts awaiting source evidence";
    const copy = !available
      ? "Current order facts are unavailable."
      : view === "agent"
        ? "Review the evidence and ask the agent what should move next."
        : view === "operations"
          ? "Capture receiving evidence, confirm the exact action, and hand it to a manager."
          : finite(dispatched) && dispatched > 0
            ? `${formatNumber(dispatched)} ${unit} dispatched${finite(awaitingRelease) && awaitingRelease > 0 ? ` · ${formatNumber(awaitingRelease)} awaiting release` : finite(held) && held > 0 ? ` · ${formatNumber(held)} awaiting release` : ""}`
            : finite(held) && held > 0
              ? `${formatNumber(held)} ${unit} awaiting inspection`
              : finite(received) && finite(dispatched)
                ? `${formatNumber(received)} ${unit} received · ${formatNumber(dispatched)} dispatched`
              : purchaseOrder
                ? `Order ${purchaseOrder}`
                : "Current order status";
    const context = view === "agent" ? "Investigate this order" : view === "operations" ? "Receive & fulfill" : "Overview";
    setText("ops-hero-context", context);
    setText("ops-title", title);
    setText("ops-hero-copy", copy);
    setText("ops-hero-case", next?.case_id || "Case unavailable");
    setText("ops-hero-state", evidenceStatusLabel(next));
  }

  function renderOrderValue(next) {
    const details = orderValueDetails(next);
    const dispatched = quantity(next, "dispatched");
    const confirmed = quantity(next, "delivery_confirmed");
    setText("ops-order-value", details.value);
    setText("ops-order-value-label", details.label);
    setText("ops-order-dispatch", finite(dispatched) ? `Dispatch ${formatNumber(dispatched)}` : "Unknown");
    const allocated = quantity(next, "allocated");
    setText("ops-order-allocations", finite(allocated) ? displayQuantity(allocated) : "Unknown");
    const investigate = $("ops-order-value-investigate");
    if (investigate) investigate.hidden = !(economicConfigured && economicProposalFrom(next));
    const confirmation = finite(confirmed)
      ? `${carrierConfirmationLabel(next, confirmed, quantity(next, "ordered"))}${next?.synthetic_input === true ? "; declared synthetic carrier confirmation, not independently verified receipt." : "."}`
      : "Delivery confirmation is unavailable from the accepted source.";
    setText("ops-order-value-note", `${details.note} ${confirmation}`);
  }

  function appendEvidenceDrawerFact(parent, label, value, href = "") {
    const row = document.createElement("div");
    const title = document.createElement("strong"); title.textContent = label;
    const safeLink = safeHref(href);
    const detail = safeLink ? document.createElement("a") : document.createElement("span");
    detail.textContent = value;
    if (safeLink) {
      detail.href = safeLink;
      detail.target = "_blank";
      detail.rel = "noopener noreferrer";
    }
    row.append(title, detail);
    parent.append(row);
  }

  function renderEvidenceDrawer(next) {
    const list = $("ops-evidence-drawer-facts");
    if (!list) return;
    const unit = displayUnit(next?.quantities?.uom);
    const received = quantity(next, "received");
    const dispatched = quantity(next, "dispatched");
    const confirmed = quantity(next, "delivery_confirmed");
    const photos = photoAttachmentList(next);
    const purchaseOrderRecordValue = purchaseOrderRecord(next);
    const purchaseOrder = purchaseOrderDisplay(next);
    setText("ops-evidence-drawer-status", evidenceStatusLabel(next));
    list.replaceChildren();
    appendEvidenceDrawerFact(list, "Case", next?.case_id || "Case identifier unavailable");
    appendEvidenceDrawerFact(list, "Purchase order", purchaseOrder || "Purchase order unavailable", purchaseOrderRecordValue?.url || purchaseOrderRecordValue?.href);
    appendEvidenceDrawerFact(list, "Evidence state", evidenceStatusLabel(next));
    appendEvidenceDrawerFact(list, "Receiving", finite(received) ? `${formatNumber(received)} ${unit}` : "Unknown");
    appendEvidenceDrawerFact(list, "Dispatch", finite(dispatched) ? `${formatNumber(dispatched)} ${unit}` : "Unknown");
    appendEvidenceDrawerFact(list, "Carrier confirmation", finite(confirmed)
      ? carrierConfirmationLabel(next, confirmed, quantity(next, "ordered"))
      : "Unknown");
    appendEvidenceDrawerFact(list, "Photo evidence", photos.length
      ? `${photos.length} attached receiving evidence photo${photos.length === 1 ? "" : "s"}; manual photo · not analyzed.`
      : "No same-case source-backed photo is available.");
    groupHandoffs(next?.handoffs).forEach((group) => {
      const latest = group.latest;
      appendEvidenceDrawerFact(
        list,
        `${group.provider} readback`,
        latest.record_id || `${pretty(latest.status || "Status unavailable")} record`,
        latest.safe_url,
      );
    });
    const proposal = economicProposalFrom(next);
    if (economicConfigured && proposal) {
      const sources = economicSourceEntries(proposal);
      appendEvidenceDrawerFact(list, "Economic proposal", pretty(proposal.status || "Status unavailable"));
      if (isRecord(proposal.proposal_effect)) {
        const effect = Object.entries(proposal.proposal_effect)
          .map(([key, value]) => `${pretty(key)} ${economicValueText(value, "")}`)
          .filter((value) => !value.endsWith(" "))
          .join(" · ");
        if (effect) appendEvidenceDrawerFact(list, "Economic proposal effect", effect);
      }
      sources.forEach((source) => {
        const label = firstText(source, ["label", "source_id"]) || "Economic source";
        const detail = [
          firstText(source, ["kind"]),
          firstText(source, ["checked_at"]),
          safeHref(firstText(source, ["ref", "url", "href"])) ? "" : firstText(source, ["ref", "url", "href"]),
        ].filter(Boolean).join(" · ") || "Source reference recorded";
        appendEvidenceDrawerFact(list, `Economic evidence · ${label}`, detail, firstText(source, ["ref", "url", "href"]));
      });
    }
  }

  function setEconomicFeedback(message, tone = "") {
    const feedback = $("ops-economic-feedback");
    if (!feedback) return;
    feedback.className = `ops-feedback${tone ? ` is-${tone}` : ""}`;
    feedback.textContent = message || "";
  }

  function renderEconomicSource(parent, source, index) {
    const label = firstText(source, ["label", "source_id"]) || `Source ${index + 1}`;
    const ref = firstText(source, ["ref", "url", "href"]);
    const kind = firstText(source, ["kind"]);
    const checkedAt = firstText(source, ["checked_at"]);
    const badge = document.createElement("span"); badge.className = "ops-economic-source";
    const icon = document.createElement("i"); icon.className = "ph ph-link-simple"; icon.setAttribute("aria-hidden", "true");
    const detail = [kind, checkedAt, safeHref(ref) ? "" : ref].filter(Boolean).join(" · ");
    const labelNode = safeHref(ref) ? document.createElement("a") : document.createElement("span");
    labelNode.textContent = label;
    if (safeHref(ref)) {
      labelNode.href = safeHref(ref);
      labelNode.target = "_blank";
      labelNode.rel = "noopener noreferrer";
      labelNode.title = ref;
    }
    badge.append(icon, labelNode);
    if (detail) {
      const detailNode = document.createElement("small"); detailNode.textContent = detail; badge.append(detailNode);
    }
    parent.append(badge);
  }

  function renderEconomicModel(proposal) {
    const model = isRecord(proposal?.model) ? proposal.model : {};
    const status = text(model.status).toUpperCase();
    const provider = isRecord(model.provider) ? model.provider : {};
    const usage = isRecord(model.usage) ? model.usage : {};
    const stale = economicModelIsStale(model);
    const identity = [
      firstText(model, ["provider"]) || firstText(provider, ["provider"]),
      firstText(model, ["model_id", "model"]) || firstText(provider, ["model", "model_id"]),
      firstText(provider, ["region"]),
      finite(numberFrom(usage.elapsed_ms)) ? `${formatNumber(numberFrom(usage.elapsed_ms))} ms` : "",
    ].filter(Boolean).join(" · ");
    // Keep provider, model, region, and timing in the source projection only.
    setText("ops-economic-model-identity", "");
    setText("ops-economic-model-title", "Agent recommendation");
    const decision = economicValueText(model.decision, "Decision unavailable from the source.");
    const modelFailure = /MODEL_BUDGET_EXHAUSTED|BUDGET_EXHAUSTED/i.test(`${status} ${decision}`);
    setText("ops-economic-model-decision", modelFailure
      ? "The recommendation is unavailable right now. Dispatch checks remain available below."
      : decision);
    const note = $("ops-economic-model-note");
    if (note) {
      const notRun = status === "NOT_RUN";
      note.hidden = !notRun && !stale;
      note.textContent = notRun
        ? "Model capabilities were not run for this proposal; the dispatch checks below remain source-provided."
        : stale
          ? "This recommendation is a prior snapshot; the current dispatch state is shown below."
          : "";
    }
    const citations = $("ops-economic-model-citations");
    if (citations) {
      citations.replaceChildren();
      const values = Array.isArray(model.citations)
        ? model.citations
        : model.citations == null ? [] : [model.citations];
      values.forEach((citation, index) => {
        const record = isRecord(citation) ? citation : {};
        const label = firstText(record, ["label", "title", "source_id", "id"]) || economicValueText(citation, `Citation ${index + 1}`);
        const ref = firstText(record, ["ref", "url", "href", "source_ref"]);
        const badge = document.createElement("span"); badge.className = "ops-economic-citation";
        const icon = document.createElement("i"); icon.className = "ph ph-quotes"; icon.setAttribute("aria-hidden", "true");
        const labelNode = safeHref(ref) ? document.createElement("a") : document.createElement("span");
        labelNode.textContent = label;
        if (safeHref(ref)) {
          labelNode.href = safeHref(ref);
          labelNode.target = "_blank";
          labelNode.rel = "noopener noreferrer";
          labelNode.title = ref;
        }
        badge.append(icon, labelNode);
        citations.append(badge);
      });
      if (!values.length) citations.append(emptyList("Model citations unavailable from the source."));
    }
    const trace = $("ops-economic-model-trace");
    const traceValue = $("ops-economic-model-trace-value");
    const hasTrace = model.trace !== undefined && model.trace !== null && economicStructuredText(model.trace, "") !== "";
    if (trace && traceValue) {
      trace.hidden = !hasTrace;
      traceValue.textContent = hasTrace ? economicStructuredText(model.trace) : "";
    }
  }

  function renderEconomicGate(proposal) {
    const gate = isRecord(proposal?.deterministic_gate) ? proposal.deterministic_gate : {};
    const status = text(gate.status).toUpperCase();
    const badge = $("ops-economic-gate-status");
    if (badge) {
      const tone = /FAIL|BLOCK|ERROR|REJECT/.test(status) ? "coral" : /PASS|READY|ALLOW|EXECUT/.test(status) ? "lime" : "amber";
      badge.className = `state-badge state-${tone}`;
      badge.textContent = status ? pretty(status) : "Status unavailable";
    }
    const details = $("ops-economic-gate-details");
    if (!details) return;
    details.replaceChildren();
    const reasons = economicValueText(gate.reasons, "Reasons unavailable from source.");
    const values = [
      ["Stock snapshot", economicSnapshotText(gate.stock_snapshot)],
      ["Contract snapshot", economicSnapshotText(gate.contract_snapshot)],
      ["Time snapshot", economicSnapshotText(gate.time_snapshot)],
    ];
    values.forEach(([label, value]) => {
      const item = document.createElement("div"); item.className = "ops-economic-gate-detail";
      const title = document.createElement("strong"); title.textContent = label;
      const detail = document.createElement("span"); detail.textContent = value;
      item.append(title, detail); details.append(item);
    });
    const reasonsItem = document.createElement("div"); reasonsItem.className = "ops-economic-gate-detail ops-economic-gate-reasons";
    const reasonsTitle = document.createElement("strong"); reasonsTitle.textContent = "Reasons";
    const reasonsDetail = document.createElement("span"); reasonsDetail.textContent = reasons;
    reasonsItem.append(reasonsTitle, reasonsDetail); details.append(reasonsItem);
  }

  function renderEconomicCandidate(candidate, next) {
    const id = firstText(candidate, ["candidate_id", "id"]);
    const state = economicCandidateState(candidate);
    const dispatches = Array.isArray(candidate.dispatches) ? candidate.dispatches.filter(isRecord) : [];
    const shipmentQuantities = Array.isArray(candidate.shipment_quantities) ? candidate.shipment_quantities : [];
    const card = document.createElement("article"); card.className = "ops-economic-candidate";
    const header = document.createElement("header"); header.className = "ops-economic-candidate-header";
    const heading = document.createElement("div"); heading.className = "ops-economic-candidate-heading";
    const label = document.createElement("strong"); label.className = "ops-economic-candidate-label";
    const mappedLabel = id === "split20"
      ? `Send ${economicQuantityText(shipmentQuantities[0])} now, ${economicQuantityText(shipmentQuantities[1])} later`
      : id === "consolidation25"
        ? `Wait and send all ${economicQuantityText(shipmentQuantities[0] ?? candidate.shipment_quantities)}`
        : "";
    label.textContent = mappedLabel || firstText(candidate, ["label", "title"]) || (id ? pretty(id) : "Dispatch candidate");
    heading.append(label);
    if (id) {
      const idNode = document.createElement("small"); idNode.className = "ops-economic-candidate-id"; idNode.textContent = id; heading.append(idNode);
    }
    const status = document.createElement("span"); status.className = `state-badge state-${state.tone}`; status.textContent = state.label;
    header.append(heading, status); card.append(header);

    const quantityBox = document.createElement("div"); quantityBox.className = "ops-economic-quantity";
    const quantityLabel = document.createElement("span"); quantityLabel.textContent = "Shipment quantities";
    const quantityValue = document.createElement("strong"); quantityValue.textContent = economicQuantityText(candidate.shipment_quantities);
    quantityBox.append(quantityLabel, quantityValue); card.append(quantityBox);

    const facts = document.createElement("div"); facts.className = "ops-economic-facts";
    const postage = economicPostageDetails(candidate);
    const postageFact = document.createElement("div"); postageFact.className = "ops-economic-fact";
    const postageLabel = document.createElement("span"); postageLabel.textContent = "Estimated postage";
    const postageValue = document.createElement("strong"); postageValue.textContent = postage.amountText;
    postageFact.append(postageLabel, postageValue);
    const postageDetail = document.createElement("small"); postageDetail.textContent = [
      postage.label || "Postage estimate supplied by the source.",
      safeHref(postage.sourceRef) ? "" : postage.sourceRef,
    ].filter(Boolean).join(" · ");
    if (safeHref(postage.sourceRef)) {
      const sourceLink = document.createElement("a"); sourceLink.href = safeHref(postage.sourceRef); sourceLink.target = "_blank"; sourceLink.rel = "noopener noreferrer"; sourceLink.textContent = postageDetail.textContent; sourceLink.title = postage.sourceRef;
      postageDetail.replaceChildren(sourceLink);
    }
    const deadlineFact = document.createElement("div"); deadlineFact.className = "ops-economic-fact";
    const deadlineLabel = document.createElement("span"); deadlineLabel.textContent = dispatches.length > 1 ? "First dispatch deadline" : "Dispatch deadline";
    const deadline = firstText(candidate, ["dispatch_deadline"]) || firstText(dispatches[0], ["deadline"]);
    const deadlineValue = document.createElement("strong"); deadlineValue.textContent = economicDateText(deadline, "Deadline unavailable from source.");
    deadlineFact.append(deadlineLabel, deadlineValue);
    facts.append(postageFact, deadlineFact); card.append(facts);

    const candidateDetails = document.createElement("details"); candidateDetails.className = "ops-economic-candidate-details";
    const candidateDetailsSummary = document.createElement("summary"); candidateDetailsSummary.textContent = "View conditions and estimate details";
    candidateDetails.append(candidateDetailsSummary, postageDetail);
    if (dispatches.length > 1) {
      const tail = dispatches[dispatches.length - 1];
      const tailFact = document.createElement("div"); tailFact.className = "ops-economic-fact";
      const tailLabel = document.createElement("span"); tailLabel.textContent = "Tail dispatch deadline";
      const tailDeadline = document.createElement("strong"); tailDeadline.textContent = economicDateText(tail.deadline, "Deadline unavailable from source.");
      const tailDetail = document.createElement("small"); tailDetail.textContent = [
        finite(numberFrom(tail.quantity)) ? `Quantity ${formatNumber(numberFrom(tail.quantity))}` : "",
        firstText(tail, ["lot"]) ? `Lot ${firstText(tail, ["lot"])}` : "",
      ].filter(Boolean).join(" · ");
      tailFact.append(tailLabel, tailDeadline);
      if (tailDetail.textContent) candidateDetails.append(tailDetail);
      facts.append(tailFact);
    }

    const conditions = document.createElement("p"); conditions.className = "ops-economic-conditions"; conditions.textContent = `Conditions: ${economicConditionsText(candidate.conditions)}`; candidateDetails.append(conditions);
    if (isRecord(candidate.proposal_effect)) {
      const effect = document.createElement("p"); effect.className = "ops-economic-effect";
      const effectSummary = economicEffectSummary({ proposal_effect: candidate.proposal_effect }, next);
      effect.textContent = effectSummary
        ? `Proposal effect: ${effectSummary}`
        : "Proposal effect: source detail unavailable.";
      candidateDetails.append(effect);
    }
    card.append(candidateDetails);
    const actions = document.createElement("div"); actions.className = "ops-economic-candidate-actions";
    if (state.label === "Executable" && id) {
      const button = document.createElement("button"); button.type = "button"; button.className = "button button-primary"; button.dataset.candidateId = id;
      button.innerHTML = '<i class="ph ph-package" aria-hidden="true"></i>Prepare this dispatch';
      button.addEventListener("click", () => { void prepareEconomicProposal(id); });
      actions.append(button);
    } else {
      const note = document.createElement("span"); note.className = "ops-economic-unavailable"; note.textContent = state.label === "Conditional" ? "Prepare when the dispatch checks are satisfied." : "Candidate support is unavailable from the source."; actions.append(note);
    }
    card.append(actions);
    return card;
  }

  function renderEconomicProposal(next) {
    const panel = $("ops-economic-panel");
    const proposal = economicProposalFrom(next);
    if (!panel) return;
    if (!economicConfigured || !proposal) {
      panel.hidden = true;
      return;
    }
    panel.hidden = false;
    const status = text(proposal.status).toUpperCase();
    const statusBadge = $("ops-economic-status");
    if (statusBadge) {
      statusBadge.className = `state-badge state-${economicStatusTone(status)}`;
      statusBadge.textContent = status ? pretty(status) : "Status unavailable";
    }
    const snapshot = economicSnapshotValues(next, proposal);
    const appliedStatus = economicEffectStatus(proposal, next);
    const dispatchedQuantity = finite(snapshot.dispatched) && snapshot.dispatched > 0
      ? snapshot.dispatched
      : economicEffectQuantity(proposal, next);
    const hasCompletedDispatch = /^(APPLIED|ALREADY_APPLIED)$/.test(appliedStatus)
      || finite(snapshot.dispatched) && snapshot.dispatched > 0;
    const subtitle = (hasCompletedDispatch
      ? [
        finite(dispatchedQuantity) ? `${formatNumber(dispatchedQuantity)} dispatched` : "",
        finite(snapshot.awaiting_release) ? `${formatNumber(snapshot.awaiting_release)} awaiting release` : "",
      ]
      : [
        finite(snapshot.ordered) ? `${formatNumber(snapshot.ordered)} ordered` : "",
        finite(snapshot.ready) ? `${formatNumber(snapshot.ready)} ready` : "",
        finite(snapshot.awaiting_release) ? `${formatNumber(snapshot.awaiting_release)} awaiting release` : "",
      ]).filter(Boolean);
    setText("ops-economic-subtitle", subtitle.length
      ? `${subtitle.join(" · ")}. Compare a supported dispatch with a conditional consolidation path.`
      : "Compare dispatch paths against the current order evidence.");
    const selection = $("ops-economic-selection");
    if (selection) {
      const selected = text(proposal.selected_candidate_id);
      const effect = economicEffectSummary(proposal, next);
      selection.textContent = [
        selected ? `Selected candidate: ${selected}` : "No candidate selected; review the dispatch checks before preparing one.",
        effect ? `Proposal effect readback: ${effect}` : "",
      ].filter(Boolean).join(" · ");
    }
    const candidates = $("ops-economic-candidates");
    if (candidates) {
      const values = Array.isArray(proposal.candidates) ? proposal.candidates : [];
      candidates.replaceChildren(...(values.length ? values.map((candidate) => renderEconomicCandidate(candidate, next)) : [emptyList("No dispatch candidates were supplied by the source.")]));
      candidates.querySelectorAll("button[data-candidate-id]").forEach((button) => {
        button.disabled = preparingEconomic || next?.available !== true;
        if (preparingEconomic) button.setAttribute("aria-busy", "true"); else button.removeAttribute("aria-busy");
      });
    }
    const difference = $("ops-economic-difference");
    const postageDifference = economicPostageDifference(proposal);
    if (difference) {
      difference.replaceChildren();
      difference.hidden = !postageDifference;
      if (postageDifference) {
        const label = document.createElement("span"); label.textContent = "Estimated postage difference · estimate only";
        const amount = document.createElement("strong"); amount.textContent = `${postageDifference.currency} ${economicAmountText(postageDifference.amount)}`;
        const note = document.createElement("span"); note.textContent = "Not savings achieved.";
        difference.append(label, amount, note);
      }
    }
    const compare = $("ops-economic-compare");
    if (compare) compare.disabled = preparingEconomic;
    const sources = $("ops-economic-sources");
    if (sources) {
      sources.replaceChildren();
      const values = economicSourceEntries(proposal);
      values.forEach((source, index) => renderEconomicSource(sources, source, index));
      if (!values.length) sources.append(emptyList("No economic source evidence references were supplied."));
    }
    renderEconomicModel(proposal);
    renderEconomicGate(proposal);
    if (/^(APPLIED|ALREADY_APPLIED)$/.test(appliedStatus)) {
      setEconomicFeedback(
        `${economicEffectSummary(proposal, next) || `Native readback ${pretty(appliedStatus)}`}. Current native readback is shown below; no physical delivery or postage payment occurred.`,
        "success",
      );
    }
  }

  function economicProposalInResponse(value) {
    const records = [value, value?.distributor_operations, value?.projection, value?.operation, value?.result];
    for (const record of records) {
      const proposal = economicProposalFrom(record) || economicProposalFrom(unwrapProjection(record));
      if (proposal) return proposal;
    }
    return null;
  }

  function preparedProposalInResponse(value) {
    const records = [value, value?.distributor_operations, value?.projection, value?.operation, value?.result];
    for (const record of records) {
      if (isRecord(record?.prepared_proposal)) return record.prepared_proposal;
      const projectionValue = unwrapProjection(record);
      if (isRecord(projectionValue?.prepared_proposal)) return projectionValue.prepared_proposal;
    }
    return null;
  }

  function economicResponseProjection(value) {
    const base = unwrapProjection(value) || projection;
    if (!isRecord(base)) return null;
    const next = { ...base };
    const proposal = economicProposalInResponse(value);
    const prepared = preparedProposalInResponse(value);
    if (proposal) next.economic_proposal = proposal;
    if (prepared) next.prepared_proposal = prepared;
    return next;
  }

  function openEvidenceDrawer(trigger) {
    const drawer = $("ops-evidence-drawer");
    const backdrop = $("ops-evidence-drawer-backdrop");
    if (!drawer || !backdrop) return;
    evidenceDrawerTrigger = trigger || document.activeElement;
    renderEvidenceDrawer(projection || normalizeProjection({}));
    backdrop.hidden = false;
    drawer.hidden = false;
    document.body.classList.add("has-evidence-drawer");
    $("ops-open-evidence-drawer")?.setAttribute("aria-expanded", "true");
    window.requestAnimationFrame(() => $("ops-evidence-drawer-close")?.focus());
  }

  function closeEvidenceDrawer() {
    const drawer = $("ops-evidence-drawer");
    const backdrop = $("ops-evidence-drawer-backdrop");
    if (!drawer || drawer.hidden) return;
    drawer.hidden = true;
    if (backdrop) backdrop.hidden = true;
    document.body.classList.remove("has-evidence-drawer");
    $("ops-open-evidence-drawer")?.setAttribute("aria-expanded", "false");
    const trigger = evidenceDrawerTrigger;
    evidenceDrawerTrigger = null;
    if (trigger && document.contains(trigger) && typeof trigger.focus === "function") trigger.focus();
  }

  function openFullOperationsEvidence() {
    closeEvidenceDrawer();
    focusOpsTarget("ops-details");
  }

  function renderUnavailablePresentation() {
    const unavailable = normalizeProjection({
      available: false,
      case_id: projection?.case_id || "",
      stage: "SOURCE_UNAVAILABLE",
      evidence_mode: { status: "UNAVAILABLE" },
      quantities: {},
      allocations: [],
      alerts: [],
      events: [],
      documents: [],
      available_event_templates: [],
    });
    renderHero(unavailable);
    renderQuantities(unavailable);
    renderStages(unavailable);
    renderBenchmark(unavailable);
    renderOrderValue(unavailable);
    renderEvidenceDrawer(unavailable);
    setText("ops-flow-message", "Current operation facts are unavailable. No quantity or delivery value is retained as current.");
    const stageBadge = $("ops-stage-badge");
    if (stageBadge) {
      stageBadge.className = "state-badge state-coral";
      stageBadge.textContent = "Source unavailable";
    }
  }

  function renderBenchmark(next) {
    const benchmark = fulfillmentBenchmark(next);
    const sourceLabel = erpEvidenceSourceLabel(next?.evidence_mode);
    const retained = isRetainedEvidence(next?.evidence_mode);
    const grid = $("ops-benchmark-grid");
    const badge = $("ops-benchmark-state");
    if (!grid || !badge) return;
    if (benchmark.status !== "CURRENT") {
      badge.className = "state-badge state-neutral"; badge.textContent = "Comparison unavailable";
      setText("ops-benchmark-note", "No comparison baseline is available for this case.");
      grid.replaceChildren(emptyList("No comparison baseline available.")); return;
    }
    badge.className = "state-badge state-cyan"; badge.textContent = retained ? "Retained case only" : "Current case only";
    const card = (label, actual, descriptor) => {
      const node = document.createElement("article"); node.className = "ops-benchmark-card";
      const title = document.createElement("span"); title.textContent = label;
      const value = document.createElement("strong"); value.textContent = `${formatNumber(actual)} / ${formatNumber(benchmark.target)}`;
      const note = document.createElement("small"); note.textContent = `${descriptor} · ${benchmark.unit}`;
      const progress = document.createElement("progress"); progress.max = benchmark.target; progress.value = Math.min(actual, benchmark.target); progress.setAttribute("aria-label", `${label}: ${formatNumber(actual)} of ${formatNumber(benchmark.target)} ${benchmark.unit}`);
      node.append(title, value, note, progress); return node;
    };
    grid.replaceChildren(
      card("Customer commitment", benchmark.target, `${benchmark.order_count} current order${benchmark.order_count === 1 ? "" : "s"}`),
      card("Native dispatch", benchmark.dispatched, "Recorded dispatch"),
      card(benchmark.synthetic ? "Carrier confirmation declared" : "Delivery confirmation recorded", benchmark.confirmed, benchmark.synthetic ? "Declared synthetic carrier confirmation; not independently verified receipt" : "Recorded event"),
    );
    setText("ops-benchmark-note", `${sourceLabel} · Current case only. Historical comparison is unavailable.`);
  }

  function allocationPicked(next) {
    return next.allocations.some((allocation) => finite(numberFromKeys(allocation, ["picked", "picked_quantity", "picked_qty"])) && numberFromKeys(allocation, ["picked", "picked_quantity", "picked_qty"]) > 0);
  }
  function pickedEvidenceRecorded(next, order = "") {
    return next.events.some((event) => {
      if (canonicalType(event.type || event.event_type || event.kind) !== "picked") return false;
      const eventOrder = firstText(event, ["customer_order", "sales_order"]);
      if (order && eventOrder !== order) return false;
      return /APPLIED|COMPLETE|SUCCESS|RECORDED/i.test(firstText(event, ["status", "state"]));
    });
  }
  function stageMatches(stage, key) {
    const value = text(stage).toUpperCase();
    const patterns = {
      arrival: /RECEIV|ARRIV|INBOUND/,
      inspection: /INSPECT|QUALITY|HOLD|REVIEW|RELEASE/,
      allocation: /ALLOC|RESERV|ORDER/,
      picked: /PICK/,
      dispatch: /DISPATCH|SHIP|DELIVER/,
      delivery: /DELIVERY_CONFIRMED|DELIVERED|POD|COMPLETE/,
    };
    return patterns[key]?.test(value) || false;
  }
  function stageProof(next, stage) {
    const value = quantity(next, stage.metric);
    if (stage.key === "arrival") return finite(value) && value > 0;
    if (stage.key === "picked") {
      return allocationPicked(next) || pickedEvidenceRecorded(next);
    }
    if (stage.key === "inspection") {
      return finite(value) && value > 0 || next.lots.some((lot) => /PASS|FAIL|HOLD|REJECT|RELEASE|INSPECT/i.test(firstText(lot, ["inspection_result", "quality_result", "result", "inspection_status"])));
    }
    if (stage.key === "delivery") return finite(value) && value > 0;
    return finite(value) && value > 0 || stageMatches(next.stage, stage.key);
  }
  function stageHeld(next, stage) {
    return stage.key === "inspection" && quantity(next, "held") !== null && quantity(next, "held") > 0;
  }
  function renderStages(next) {
    const list = $("ops-stage-list");
    const alertStages = activeAlertStages(next);
    list.replaceChildren(...STAGES.map((stage) => {
      const item = document.createElement("li");
      item.className = "ops-stage";
      const facts = flowStageFacts(next, stage);
      const isComplete = facts.complete;
      const alert = alertStages[stage.key];
      if (isComplete) item.classList.add("is-complete");
      if (stageHeld(next, stage)) item.classList.add("is-held");
      if (alert) item.classList.add("is-alert");
      if (!isComplete && stageMatches(next.stage, stage.key)) item.classList.add("is-current");
      const marker = document.createElement("span");
      marker.className = "ops-stage-marker";
      marker.innerHTML = `<i class="ph ${isComplete ? "ph-check" : stage.icon}" aria-hidden="true"></i>`;
      const title = document.createElement("strong"); title.textContent = stage.label;
      const detail = document.createElement("small");
      detail.textContent = facts.current;
      const cumulative = document.createElement("small"); cumulative.className = "ops-stage-cumulative"; cumulative.textContent = facts.cumulative;
      item.append(marker, title, detail, cumulative);
      if (alert) {
        const evidence = document.createElement("a");
        evidence.className = "ops-stage-alert-link";
        evidence.href = `#ops-alert-${alert.index}`;
        evidence.textContent = alertStage(alert) === "inspection" ? "Review hold" : "Review alert";
        evidence.addEventListener("click", (event) => {
          event.preventDefault();
          focusOpsTarget(`ops-alert-${alert.index}`);
        });
        item.append(evidence);
      }
      return item;
    }));
  }

  function requestedOpsView() {
    const requested = text(new URLSearchParams(window.location.search).get("view")).toLowerCase();
    if (["dashboard", "agent", "operations"].includes(requested)) return requested;
    const hash = text(window.location.hash).toLowerCase();
    if (["#ops-chat-panel", "#ops-overview", "#ops-economic-panel"].includes(hash)) return "agent";
    if (["#ops-flow-panel", "#ops-alerts-panel", "#ops-details", "#ops-documents-panel", "#ops-handoffs-panel", "#ops-evidence-panel", "#ops-photo-intake", "#ops-proposal-panel"].includes(hash)) return "operations";
    return "dashboard";
  }

  function setOpsView(view, { scrollTarget = "" } = {}) {
    const normalized = ["dashboard", "agent", "operations"].includes(view) ? view : "dashboard";
    document.body.dataset.opsView = normalized;
    document.querySelectorAll("[data-ops-view-link]").forEach((link) => {
      const selected = link.dataset.opsViewLink === normalized;
      link.classList.toggle("is-selected", selected);
      if (selected) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
    if (projection) {
      renderHero(projection);
      renderPhotos(projection);
    }
    if (normalized === "agent" && scrollTarget === "ops-economic-panel") {
      const economicPanel = $("ops-economic-panel");
      const economicToggle = $("ops-economic-toggle");
      economicPanel?.classList.add("is-expanded");
      economicToggle?.setAttribute("aria-expanded", "true");
    }
    if (scrollTarget) {
      window.requestAnimationFrame(() => $(scrollTarget)?.scrollIntoView({ behavior: "smooth", block: "start" }));
    }
  }

  function toggleCollapsiblePanel(panelId, toggleId) {
    const panel = $(panelId);
    const toggle = $(toggleId);
    if (!panel || !toggle) return;
    const expanded = panel.classList.toggle("is-expanded");
    toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
  }

  function bindCollapsiblePanel(panelId, toggleId) {
    const toggle = $(toggleId);
    if (!toggle) return;
    toggle.addEventListener("click", (event) => {
      if (event.target.closest("a, button")) return;
      toggleCollapsiblePanel(panelId, toggleId);
    });
    toggle.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      toggleCollapsiblePanel(panelId, toggleId);
    });
  }

  function focusOpsTarget(target) {
    const node = $(target);
    if (!node) return;
    const route = opsTargetRoute(target, window.location.href);
    if (!route) return;
    const currentHref = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    if (route.href !== currentHref) window.history.pushState({}, "", route.href);
    setOpsView(route.view, { scrollTarget: route.target });
  }

  function networkNode({ key, icon, label, detail, target, alert = false, className = "" }) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `ops-network-node ${className}`.trim();
    button.dataset.networkKey = key;
    if (alert) button.classList.add("is-alert");
    const iconNode = document.createElement("i");
    iconNode.className = `ph ${icon}`;
    iconNode.setAttribute("aria-hidden", "true");
    const copy = document.createElement("span");
    const title = document.createElement("strong"); title.textContent = label;
    const meta = document.createElement("span"); meta.textContent = detail;
    copy.append(title, meta);
    button.append(iconNode, copy);
    if (target) button.addEventListener("click", () => focusOpsTarget(target));
    return button;
  }

  function renderOverview(next) {
    const graph = $("ops-overview-graph");
    if (!graph) return;
    const activeAlerts = next.alerts.filter((alert) => !isResolvedAlert(alert));
    const incidentAlerts = next.alerts.filter(isRecord);
    const handoffGroups = groupHandoffs(next.handoffs);
    const sources = [];
    if (next._provided.documents) {
      sources.push({
        key: "erp",
        icon: "ph-buildings",
        label: "ERP evidence",
        detail: `${next.documents.length} linked record${next.documents.length === 1 ? "" : "s"}`,
        target: "ops-documents-panel",
        alert: Boolean(incidentAlerts.length && next.documents.length),
      });
    }
    handoffGroups.forEach((group, index) => {
      sources.push({
        key: `handoff-${index}`,
        icon: "ph-arrows-left-right",
        label: group.provider,
        detail: pretty(group.latest.status || "No readback"),
        target: "ops-handoffs-panel",
        alert: Boolean(incidentAlerts.length && /ERROR|PENDING|UNKNOWN/i.test(group.latest.status)),
      });
    });
    const network = document.createElement("div"); network.className = "ops-network";
    const sourceColumn = document.createElement("div"); sourceColumn.className = "ops-network-column";
    const sourceKicker = document.createElement("span"); sourceKicker.className = "ops-network-kicker"; sourceKicker.textContent = "Same-case source records";
    const sourceStack = document.createElement("div"); sourceStack.className = "ops-network-source-stack";
    if (sources.length) sources.forEach((source) => sourceStack.append(networkNode({ ...source, className: "ops-network-source" })));
    else sourceStack.append(emptyList("No same-case source record is available."));
    sourceColumn.append(sourceKicker, sourceStack);

    const agentColumn = document.createElement("div"); agentColumn.className = "ops-network-column ops-network-agent-wrap";
    const agentKicker = document.createElement("span"); agentKicker.className = "ops-network-kicker"; agentKicker.textContent = "Reasoning layer";
    const agentProvider = agentProviderDisplay(next);
    const agent = networkNode({ key: "agent", icon: "ph-sparkle", label: "Agent board", detail: agentProvider, target: "ops-chat-panel", className: "ops-network-agent" });
    agentColumn.append(agentKicker, agent);
    if (incidentAlerts.length) {
      const incident = document.createElement("div"); incident.className = "ops-network-incident";
      const incidentIcon = document.createElement("i"); incidentIcon.className = "ph ph-warning"; incidentIcon.setAttribute("aria-hidden", "true");
      const incidentAlert = activeAlerts[0] || incidentAlerts.find((alert) => /LOT|BATCH|SHORT|MISMATCH|QUALITY|INSPECTION/i.test(firstText(alert, ["code", "kind", "message", "detail"]))) || incidentAlerts[0];
      const incidentMessage = activeAlerts.length
        ? `${activeAlerts.length} issue${activeAlerts.length === 1 ? "" : "s"} to review`
        : "Issue resolved";
      incident.append(incidentIcon, document.createTextNode(incidentMessage));
      agentColumn.append(incident);
    }

    const managerColumn = document.createElement("div"); managerColumn.className = "ops-network-column ops-network-manager-wrap";
    const managerKicker = document.createElement("span"); managerKicker.className = "ops-network-kicker"; managerKicker.textContent = "Control";
    const proposalStatus = firstText(next.prepared_proposal, ["status"]);
    const managerDetail = proposalStatus ? proposalActionDetail(next.prepared_proposal, next.evidence_mode) : isRetainedEvidence(next.evidence_mode) ? "Recorded completion · manager confirmation" : "Bounded action · manager approval";
    const manager = networkNode({ key: "manager", icon: "ph-shield-check", label: "Manager gate", detail: managerDetail, target: "ops-evidence-panel", className: "ops-network-manager" });
    managerColumn.append(managerKicker, manager);
    network.append(sourceColumn, agentColumn, managerColumn);
    graph.replaceChildren(network);
    setText("ops-overview-case", `${next.case_id || "Case unavailable"} · ${purchaseOrderDisplay(next) || "PO unavailable"}`);
    setText("ops-alert-focus-link", next._provided.alerts && activeAlerts.length === 0 ? "Review resolved incident" : "Focus active alert");
    setText("ops-overview-copy", activeAlerts.length ? "Open incident evidence is highlighted." : incidentAlerts.length ? "Resolved incident evidence is retained." : "Source records flow into read-only reasoning and manager control.");
  }

  function renderSignalSources(next) {
    const list = $("ops-signal-source-list");
    if (!list) return;
    const groups = groupHandoffs(next.handoffs);
    const documentRecord = next.documents.find((record) => isRecord(record)) || null;
    const entries = [];
    if (next._provided.documents) {
      entries.push({
        label: "ERP evidence",
        detail: documentRecord ? firstText(documentRecord, ["name", "record_id", "id"]) || "Linked document" : "No linked document",
        status: documentRecord ? "RECORDED" : "NO RECORD",
      });
    }
    groups.forEach((group) => entries.push({
      label: group.provider,
      detail: group.latest.record_id || "Readback recorded",
      status: pretty(group.latest.status || "No readback"),
    }));
    const linked = entries.filter((entry) => !/^NO (READBACK|RECORD)$/.test(entry.status)).length;
    setText("ops-signal-source-count", entries.length ? `${linked} recorded · ${entries.length} source${entries.length === 1 ? "" : "s"}` : "No source records");
    if (!entries.length) { list.replaceChildren(emptyList("No same-case source record is available.")); return; }
    list.replaceChildren(...entries.map((entry) => {
      const row = document.createElement("div"); row.className = "ops-signal-source";
      const identity = document.createElement("div");
      const title = document.createElement("strong"); title.textContent = entry.label;
      const detail = document.createElement("small"); detail.textContent = entry.detail;
      identity.append(title, detail);
      const status = document.createElement("span"); status.className = `ops-signal-source-status${/NO (READBACK|RECORD)/.test(entry.status) ? " is-muted" : ""}`; status.textContent = entry.status;
      row.append(identity, status);
      return row;
    }));
  }

  function renderAgentTools(next) {
    const list = $("ops-agent-tools");
    if (!list) return;
    const groups = groupHandoffs(next.handoffs);
    const recordsAvailable = next.documents.length > 0;
    const collaborationAvailable = groups.length > 0;
    const tools = [
      ["read_control_context", next.available ? "AVAILABLE" : "UNAVAILABLE"],
      ["read_erp_evidence", recordsAvailable ? "AVAILABLE" : "NO RECORDS"],
      ["read_collaboration_evidence", collaborationAvailable ? "AVAILABLE" : "NO RECORDS"],
      ["manager_gate", isRetainedEvidence(next.evidence_mode) ? "CONFIRMATION" : "APPROVAL"],
    ];
    list.replaceChildren(...tools.map(([label, status]) => {
      const row = document.createElement("div"); row.className = "ops-agent-tool";
      const name = document.createElement("span"); name.textContent = label;
      const state = document.createElement("small"); state.textContent = status;
      row.append(name, state);
      return row;
    }));
    const activity = $("ops-agent-activity-copy");
    if (!activity) return;
    const latestEvent = [...next.events].reverse().find((event) => isRecord(event));
    const latestCopy = latestEvent ? eventSummary(latestEvent, next) : "No source events recorded";
    activity.textContent = `${next.events.length} source event${next.events.length === 1 ? "" : "s"} · ${latestCopy}`;
  }

  function metricBlock(label, value, className = "") {
    const wrapper = document.createElement("div");
    if (className) wrapper.className = `ops-list-value ${className}`;
    else wrapper.className = "ops-list-value";
    const strong = document.createElement("strong"); strong.textContent = value;
    const small = document.createElement("small"); small.textContent = label;
    wrapper.append(strong, small);
    return wrapper;
  }
  function emptyList(message) {
    const node = document.createElement("p"); node.className = "ops-empty"; node.textContent = message; return node;
  }
  function renderLots(next) {
    const list = $("ops-lots-list");
    const sourceLabel = erpEvidenceSourceLabel(next?.evidence_mode);
    setText("ops-lots-count", next._provided.lots ? `${next.lots.length} lot${next.lots.length === 1 ? "" : "s"}` : "Unknown");
    if (!next._provided.lots) { list.replaceChildren(emptyList(`Lot and inspection data is unavailable from the ${sourceLabel}.`)); return; }
    if (!next.lots.length) { list.replaceChildren(emptyList("No lot records in the current operation.")); return; }
    list.replaceChildren(...next.lots.map((lot) => {
      const row = document.createElement("div"); row.className = "ops-list-row";
      const id = firstText(lot, ["lot", "lot_id", "batch", "batch_no", "name"]) || "Lot not identified";
      const status = firstText(lot, ["status", "inspection_result", "quality_result", "result"]) || "Status unavailable";
      const received = numberFromKeys(lot, ["received", "quantity", "observed_quantity", "count"]);
      const usable = numberFromKeys(lot, ["usable", "accepted", "accepted_quantity"]);
      const held = numberFromKeys(lot, ["held", "rejected", "rejected_quantity", "quarantine"]);
      const inspection = isRecord(lot.inspection) ? lot.inspection : lot.quality;
      const test = isRecord(inspection)
        ? [firstText(inspection, ["result", "status"]), firstText(inspection, ["metric"]), text(inspection.measured) ? `measured ${inspection.measured}` : ""].filter(Boolean).join(" · ")
        : status;
      const first = document.createElement("div");
      const title = document.createElement("strong"); title.textContent = id;
      const note = document.createElement("small"); note.textContent = status;
      first.append(title, note);
      row.append(first, metricBlock("Received", displayQuantity(received)), metricBlock("Usable", displayQuantity(usable), usable === null ? "" : "is-positive"), metricBlock("Held / inspection", held === null ? test : `${displayQuantity(held)} · ${test}`, held > 0 ? "is-alert" : ""));
      return row;
    }));
  }

  function allocationLabel(allocation) {
    const source = firstText(allocation, ["source", "kind", "allocation_type", "reservation_status", "reservation"]);
    if (allocation.planned === true || allocation.is_plan === true || /PLAN/i.test(source)) return "Planned allocation";
    if (allocation.native_reservation === true || /RESERV/i.test(source)) return "Native reservation";
    return "Allocation record";
  }
  function deliverySummary(delivery, requested, synthetic = false) {
    if (!finite(delivery)) return synthetic ? "Carrier confirmation declared unknown" : "Delivery confirmed unknown";
    const label = synthetic ? "Carrier confirmation declared" : "Delivery confirmed";
    return finite(requested)
      ? `${label} ${displayQuantity(delivery)} / ${displayQuantity(requested)}`
      : `${label} ${displayQuantity(delivery)}`;
  }
  function contractFlag(value, affirmative, negative) {
    return value === true ? affirmative : value === false ? negative : "Unknown";
  }
  function appendContractDetail(parent, label, value) {
    if (!value) return;
    const row = document.createElement("div");
    const labelNode = document.createElement("strong"); labelNode.textContent = label;
    row.append(labelNode, document.createTextNode(value));
    parent.append(row);
  }
  function renderContractAllocation(next) {
    const panel = $("ops-contract-panel");
    if (!panel) return;
    const plan = normalizeContractPlan(next.feasible_allocation_plan);
    const rows = contractPlanRows(plan);
    if (!plan || !rows.length) {
      panel.hidden = true;
      $("ops-contract-rows")?.replaceChildren();
      $("ops-contract-decision")?.replaceChildren();
      return;
    }
    panel.hidden = false;
    const state = contractPanelState(plan, next.allocation_decision);
    const decision = isRecord(next.allocation_decision) ? next.allocation_decision : {};
    const rawStatus = text(decision.status).toUpperCase();
    const pending = pendingAllocationEligibility(next);
    const retry = allocationRetryForDecision(next);
    const badge = $("ops-contract-state");
    if (badge) {
      badge.className = `state-badge state-${state === "SELECTED" ? "cyan" : state === "COMPLETE" ? "lime" : "amber"}`;
      badge.textContent = state === "SELECTED" ? "Plan selected" : state === "COMPLETE" ? "Current plan complete" : state === "PENDING" ? "Decision pending" : "Decision unavailable";
    }
    const candidateRule = "Minimum dispatch quantities apply only to positive new candidates; an order with no dispatch remaining does not block other candidates.";
    setText("ops-contract-note", state === "COMPLETE"
      ? "No additional allocation is currently needed. Any retained selection below is historical evidence; pick and dispatch facts remain in the fulfillment rows."
      : state === "SELECTED"
      ? `Date first; customer priority breaks ties. The server calculated this feasible plan from the contract terms. Selection is a decision record; it does not itself create a pick or dispatch. ${candidateRule}`
      : `Date first; customer priority breaks ties. The server calculated this feasible plan from the contract terms. Actual pick and dispatch evidence remains in the fulfillment rows below. ${candidateRule}`);
    const meta = $("ops-contract-meta");
    if (meta) {
      const unit = displayUnit(next.quantities?.uom, "unit");
      meta.textContent = `Contract policy v1 · Planned additional quantity ${displayQuantity(numberFrom(plan.new_quantity))} ${unit}`;
    }
    const list = $("ops-contract-rows");
    if (list) {
      list.replaceChildren(...rows.map((row) => {
        const item = document.createElement("div"); item.className = "ops-contract-row";
        const identity = document.createElement("div");
        const order = document.createElement("strong"); order.textContent = row.customer_order || "Order unavailable";
        const promise = document.createElement("small"); promise.textContent = `Promised ${row.promised_delivery_at || "Date unavailable"} · Customer priority ${displayQuantity(row.customer_priority)}`;
        identity.append(order, promise);
        const terms = [
          `Minimum ${displayQuantity(row.minimum_dispatch_quantity)}`,
          `Partial ${contractFlag(row.partial_dispatch, "Yes", "No")}`,
          `Final remainder ${contractFlag(row.allow_final_remainder, "allowed", "not allowed")}`,
          row.dispatch_eligibility ? `Dispatch ${dispatchEligibilityText(row.dispatch_eligibility)}` : "",
        ].filter(Boolean).join(" · ");
        const planned = `Total ${displayQuantity(row.quantity)} · Prepared commitment ${displayQuantity(row.prepared_commitment)} · New to prepare ${displayQuantity(row.new_quantity)}`;
        item.append(identity, metricBlock("Contract terms", terms), metricBlock("Plan quantities", planned), metricBlock("Remaining after dispatch", displayQuantity(row.remaining_after_dispatch)));
        return item;
      }));
    }
    const decisionNode = $("ops-contract-decision");
    if (!decisionNode) return;
    decisionNode.className = `ops-contract-decision${state === "SELECTED" || state === "COMPLETE" ? " is-selected" : ""}`;
    decisionNode.replaceChildren();
    const heading = document.createElement("strong");
    heading.textContent = state === "SELECTED" ? "Agent decision: plan selected" : state === "COMPLETE" ? "Retained historical selection" : state === "PENDING" ? "Agent decision: pending" : "Agent decision: unavailable";
    const copy = document.createElement("p");
    copy.textContent = state === "COMPLETE"
      ? rawStatus === "SELECTED" ? "This is an earlier selection; the current feasible plan has no additional quantity to prepare." : "The current feasible plan has no additional quantity to prepare."
      : state === "SELECTED"
      ? "This plan selection does not itself create an ERP pick or dispatch."
      : state === "PENDING"
      ? "The source has a feasible proposal, but no allocation decision was selected or prepared. Review the pending decision before any pick or dispatch."
      : rawStatus === "SELECTED"
        ? "The recorded selection does not match this current plan, so it is not treated as selected."
        : "No selected decision is recorded for this plan.";
    const details = document.createElement("div"); details.className = "ops-contract-decision-details";
    if (state === "PENDING") {
      appendContractDetail(details, "Eligibility", pending.eligible ? "Review required · source event is available" : pending.reason);
    }
    appendContractDetail(details, "Rationale", firstText(decision, ["rationale"]));
    const refs = Array.isArray(decision.contract_refs) ? decision.contract_refs.map((ref) => text(ref)).filter(Boolean).join(", ") : "";
    appendContractDetail(details, "Contract refs", refs);
    appendContractDetail(details, "Decision event", firstText(decision, ["event_id"]));
    appendContractDetail(details, "Agent source", providerLabel(decision.provider));
    if (retry) appendContractDetail(details, "Review status", pretty(retry.status));
    decisionNode.append(heading, copy);
    if (details.childNodes.length) decisionNode.append(details);

    const action = document.createElement("div");
    action.id = "ops-pending-allocation-action";
    action.className = "ops-pending-allocation-action";
    const actionButton = document.createElement("button");
    actionButton.id = "ops-reselect-pending-allocation";
    actionButton.className = "button button-primary";
    actionButton.type = "button";
    actionButton.innerHTML = '<i class="ph ph-arrow-counter-clockwise" aria-hidden="true"></i><span data-allocation-action-label>Review pending allocation</span>';
    actionButton.addEventListener("click", () => { void reviewPendingAllocation(); });
    action.append(actionButton);
    decisionNode.append(action);
    const feedback = document.createElement("p");
    feedback.id = "ops-allocation-feedback";
    feedback.className = "ops-feedback";
    feedback.setAttribute("role", "status");
    feedback.setAttribute("aria-live", "polite");
    decisionNode.append(feedback);
    updatePendingAllocationAction(next);
  }
  function renderAllocations(next) {
    const list = $("ops-orders-list");
    const sourceLabel = erpEvidenceSourceLabel(next?.evidence_mode);
    renderContractAllocation(next);
    const allocationPending = pendingAllocationEligibility(next).status === "PENDING";
    setText("ops-orders-count", next._provided.allocations ? `${next.allocations.length} order${next.allocations.length === 1 ? "" : "s"}` : "Unknown");
    if (!next._provided.allocations) { list.replaceChildren(emptyList(`Customer allocation data is unavailable from the ${sourceLabel}.`)); return; }
    if (!next.allocations.length) { list.replaceChildren(emptyList("No customer allocation evidence in the current operation.")); return; }
    list.replaceChildren(...next.allocations.map((allocation) => {
      const row = document.createElement("div"); row.className = "ops-list-row";
      const order = firstText(allocation, ["customer_order", "sales_order", "order_name", "order", "name"]) || "Order not identified";
      const customer = firstText(allocation, ["customer", "customer_name", "customer_id"]);
      const requested = numberFromKeys(allocation, ["ordered", "requested", "requested_quantity", "demand", "quantity"]);
      const allocated = numberFromKeys(allocation, ["allocated", "reserved", "reservation_quantity"]);
      const explicitBackorder = numberFromKeys(allocation, ["backorder", "backordered", "remaining", "unfulfilled"]);
      const backorder = finite(explicitBackorder) ? explicitBackorder : finite(requested) && finite(allocated) ? Math.max(0, requested - allocated) : null;
      const picked = numberFromKeys(allocation, ["picked", "picked_quantity", "picked_qty"]);
      const dispatched = numberFromKeys(allocation, ["dispatched", "dispatched_quantity"]);
      const delivery = numberFromKeys(allocation, ["delivery_confirmed", "delivery_quantity"]);
      const status = firstText(allocation, ["status", "phase"]) || "Status unavailable";
      const first = document.createElement("div");
      const title = document.createElement("strong"); title.textContent = order;
      const note = document.createElement("small"); note.textContent = `${customer ? `${customer} · ` : ""}${allocationPending ? "Proposed allocation" : allocationLabel(allocation)} · ${status}`;
      first.append(title, note);
      const outbound = [
        finite(picked) ? `Picked ${displayQuantity(picked)}` : pickedEvidenceRecorded(next, order) ? "Picked recorded" : "Picked unknown",
        finite(dispatched) ? `Dispatched ${displayQuantity(dispatched)}` : "Dispatched unknown",
        deliverySummary(delivery, requested, next.synthetic_input === true),
      ].join(" · ");
      row.append(first, metricBlock(allocationPending ? "Proposed" : "Allocated", displayQuantity(allocated), allocated > 0 ? "is-positive" : ""), metricBlock("Backorder", displayQuantity(backorder), backorder > 0 ? "is-alert" : ""), metricBlock("Outbound evidence", outbound));
      return row;
    }));
  }

  function renderAlerts(next) {
    const list = $("ops-alerts-list");
    const sourceLabel = erpEvidenceSourceLabel(next?.evidence_mode);
    const alerts = next.alerts.filter((alert) => !isResolvedAlert(alert));
    const resolved = next.alerts.filter((alert) => isResolvedAlert(alert));
    const history = $("ops-resolved-alerts");
    const historyList = $("ops-resolved-alerts-list");
    setText("ops-alerts-count", next._provided.alerts ? `${alerts.length} active alert${alerts.length === 1 ? "" : "s"}` : "Unknown");
    if (history) history.hidden = !resolved.length;
    if (historyList) {
      setText("ops-resolved-alerts-summary", `Resolved evidence history · ${resolved.length}`);
      historyList.replaceChildren(...resolved.map((alert) => {
        const row = document.createElement("div"); row.className = "ops-resolved-alert-row";
        const code = document.createElement("strong"); code.textContent = firstText(alert, ["code", "kind"]) || "Resolved alert";
        const detail = document.createElement("span"); detail.textContent = firstText(alert, ["message", "detail"]) || "Resolved source alert.";
        row.append(code, detail); return row;
      }));
    }
    if (!next._provided.alerts) { list.replaceChildren(emptyList(`Manager alert data is unavailable from the ${sourceLabel}.`)); return; }
    if (!alerts.length) { list.replaceChildren(emptyList("No active manager alerts in the current projection.")); return; }
    list.replaceChildren(...alerts.map((alert) => {
      const card = document.createElement("article"); card.className = "ops-alert-card";
      card.id = `ops-alert-${next.alerts.indexOf(alert)}`;
      const head = document.createElement("div"); head.className = "ops-alert-head";
      const code = document.createElement("strong"); code.className = "ops-alert-code"; code.textContent = firstText(alert, ["code", "kind"]) || "Alert";
      const badge = document.createElement("span"); badge.className = `state-badge state-${statusTone(firstText(alert, ["code", "kind"]))}`; badge.textContent = alert.synthetic === true ? "Synthetic evidence" : alert.derived === true ? "Derived date check" : "Source alert";
      head.append(code, badge);
      const message = document.createElement("p"); message.textContent = firstText(alert, ["message", "detail"]) || "Alert detail unavailable.";
      const meta = document.createElement("div"); meta.className = "ops-alert-meta";
      const action = firstText(alert, ["action", "recommended_action"]) || recommendedAction(firstText(alert, ["code", "kind"]));
      const orders = Array.isArray(alert.orders) ? alert.orders.map((order) => text(order)).filter(Boolean).join(", ") : firstText(alert, ["orders", "affected_orders"]);
      const evidence = firstText(alert, ["evidence_ref", "evidence_id"]);
      const appendMeta = (label, value, link = false) => {
        if (!value) return;
        const row = document.createElement("div");
        const labelNode = document.createElement("strong"); labelNode.textContent = label;
        row.append(labelNode, document.createTextNode(" "));
        if (link && safeHref(value)) { const anchor = document.createElement("a"); anchor.href = safeHref(value); anchor.target = "_blank"; anchor.rel = "noopener noreferrer"; anchor.textContent = value; row.append(anchor); }
        else { row.append(document.createTextNode(value)); }
        meta.append(row);
      };
      appendMeta("Action", action);
      appendMeta("Affected orders", orders || "No linked orders");
      appendMeta("Lot / quantity", [firstText(alert, ["lot", "batch"]), finite(numberFrom(alert.quantity)) ? displayQuantity(numberFrom(alert.quantity)) : ""].filter(Boolean).join(" · "));
      appendMeta("Evidence", evidence || "Evidence reference unavailable", Boolean(evidence && /^https?:\/\//i.test(evidence)));
      card.append(head, message, meta);
      return card;
    }));
  }

  function safeHref(value) {
    const href = text(value);
    if (/^https?:\/\//i.test(href) || /^\/(?!\/)/.test(href) || /^#/.test(href)) return href;
    return "";
  }
  function appendHandoffLink(parent, label, handoff) {
    const row = document.createElement("div");
    const href = handoff.safe_url;
    if (href) {
      const anchor = document.createElement("a");
      anchor.href = href; anchor.target = "_blank"; anchor.rel = "noopener noreferrer";
      anchor.textContent = `${label}${handoff.record_id ? ` · ${handoff.record_id}` : ""}`;
      row.append(anchor);
    } else {
      row.textContent = `${label}: link unavailable`;
    }
    parent.append(row);
  }
  function renderHandoffs(next) {
    const list = $("ops-handoffs-list");
    if (!list) return;
    const groups = groupHandoffs(next.handoffs);
    setText("ops-handoffs-count", groups.length ? `${groups.length} system${groups.length === 1 ? "" : "s"}` : "No verified links");
    if (!groups.length) {
      list.replaceChildren(emptyList("No linked external case record verified yet."));
      return;
    }
    list.replaceChildren(...groups.map((group) => {
      const latest = group.latest;
      const card = document.createElement("article"); card.className = "ops-handoff-card";
      const head = document.createElement("div"); head.className = "ops-handoff-head";
      const provider = document.createElement("strong"); provider.textContent = group.provider;
      const badge = document.createElement("span"); badge.className = `state-badge state-${statusTone(latest.status)}`; badge.textContent = pretty(latest.status);
      head.append(provider, badge);
      const latestVerified = latest.status.toUpperCase() === "VERIFIED";
      const timestamp = document.createElement("small"); timestamp.className = "ops-handoff-meta";
      timestamp.textContent = latest.updated_at
        ? `${latestVerified ? "Retained verification timestamp" : "Last recorded attempt"} ${formatDate(latest.updated_at)}`
        : `${latestVerified ? "Retained verification timestamp" : "Last recorded attempt"} unavailable`;
      const record = document.createElement("small"); record.className = "ops-handoff-record";
      record.textContent = latest.record_id ? `Latest record ${latest.record_id}` : "Latest record ID unavailable";
      const links = document.createElement("div"); links.className = "ops-handoff-links";
      appendHandoffLink(links, latestVerified ? "Verified evidence" : "Latest attempt evidence", latest);
      if (group.last_verified && group.last_verified !== latest) {
        const history = document.createElement("p"); history.className = "ops-handoff-history";
        history.textContent = `Last verified link is historical; latest status is ${pretty(latest.status)}.`;
        appendHandoffLink(links, "Last verified evidence", group.last_verified);
        card.append(head, timestamp, record, links, history);
      } else {
        card.append(head, timestamp, record, links);
      }
      if (latest.last_failure) {
        const failure = document.createElement("p"); failure.className = "ops-handoff-failure";
        failure.textContent = `Last failure: ${latest.last_failure}`;
        card.append(failure);
      }
      return card;
    }));
  }
  function renderDocuments(next) {
    const list = $("ops-documents-list");
    const sourceLabel = erpEvidenceSourceLabel(next?.evidence_mode);
    setText("ops-documents-count", next._provided.documents ? `${next.documents.length} record${next.documents.length === 1 ? "" : "s"}` : "Unknown");
    if (!next._provided.documents) { list.replaceChildren(emptyList(`Native ERP document data is unavailable from the ${sourceLabel}.`)); return; }
    if (!next.documents.length) { list.replaceChildren(emptyList(`No linked ERP documents in the ${sourceLabel}.`)); return; }
    list.replaceChildren(...next.documents.map((documentRecord) => {
      const row = document.createElement("div"); row.className = "ops-document";
      const body = document.createElement("div");
      const name = firstText(documentRecord, ["name", "record_id", "id"]) || "ERP document";
      const kind = firstText(documentRecord, ["kind", "doctype", "type"]) || "Native record";
      const title = document.createElement("strong"); title.textContent = name;
      const note = document.createElement("small"); note.textContent = kind;
      body.append(title, note);
      const href = safeHref(documentRecord.url || documentRecord.href);
      const documentStatus = firstText(documentRecord, ["status"]) || "Status unavailable";
      if (href) { const anchor = document.createElement("a"); anchor.className = "ops-document-status"; anchor.href = href; anchor.target = "_blank"; anchor.rel = "noopener noreferrer"; anchor.textContent = `${documentStatus} · Open record`; row.append(body, anchor); }
      else { const status = document.createElement("span"); status.className = "ops-document-status"; status.textContent = documentStatus; row.append(body, status); }
      return row;
    }));
  }

  function appendFinancialDocument(parent, documentRecord) {
    const name = firstText(documentRecord, ["name", "record_id", "id"]) || "ERP document";
    const href = safeHref(documentRecord.url || documentRecord.href);
    if (href) {
      const anchor = document.createElement("a");
      anchor.href = href; anchor.target = "_blank"; anchor.rel = "noopener noreferrer";
      anchor.textContent = name; parent.append(anchor);
    } else {
      const label = document.createElement("span");
      label.textContent = `${name} · link unavailable`; parent.append(label);
    }
  }

  function financialOrderCard(order, label, unit) {
    const card = document.createElement("article"); card.className = "ops-financial-card";
    const documentRecord = isRecord(order.document) ? order.document : {};
    const heading = document.createElement("div"); heading.className = "ops-financial-heading";
    const identity = document.createElement("div");
    const kind = document.createElement("small"); kind.textContent = firstText(documentRecord, ["kind", "doctype", "type"]) || label;
    const name = document.createElement("strong"); name.textContent = label;
    const link = document.createElement("span"); link.className = "ops-financial-document";
    appendFinancialDocument(link, documentRecord);
    identity.append(kind, name, link);
    const status = document.createElement("span"); status.className = "ops-financial-status";
    status.textContent = `Status: ${firstText(documentRecord, ["status"]) || "Status unavailable"}`;
    heading.append(identity, status);
    const party = firstText(order, ["supplier", "customer"]);
    const partyNode = document.createElement("p"); partyNode.className = "ops-financial-party";
    partyNode.textContent = `${label.startsWith("Sales") ? "Customer" : "Supplier"}: ${party || "Party unavailable"}`;
    const detail = document.createElement("p"); detail.className = "ops-financial-detail";
    detail.textContent = financialOrderSummary(order, unit);
    const currency = document.createElement("small"); currency.className = "ops-financial-meta";
    currency.textContent = `Currency: ${text(order.currency) || "Currency unavailable"}`;
    card.append(heading, partyNode, detail, currency);
    return card;
  }

  function financialInvoiceCard(record) {
    const card = document.createElement("article"); card.className = "ops-financial-card ops-financial-invoice";
    const documentRecord = isRecord(record.document) ? record.document : {};
    const heading = document.createElement("div"); heading.className = "ops-financial-heading";
    const identity = document.createElement("div");
    const kind = document.createElement("small"); kind.textContent = firstText(documentRecord, ["kind", "doctype", "type"]) || "Invoice";
    const name = document.createElement("strong"); name.textContent = firstText(documentRecord, ["name", "record_id", "id"]) || "Invoice record";
    const link = document.createElement("span"); link.className = "ops-financial-document";
    appendFinancialDocument(link, documentRecord);
    identity.append(kind, name, link);
    const status = document.createElement("span"); status.className = "ops-financial-status";
    status.textContent = firstText(documentRecord, ["status"]) || "Status unavailable";
    heading.append(identity, status);
    const detail = document.createElement("p"); detail.className = "ops-financial-detail";
    detail.textContent = invoiceRecordSummary(record);
    card.append(heading, detail);
    return card;
  }

  function renderInvoiceGroup(parent, title, group, unit, evidenceMode = null) {
    const section = document.createElement("section"); section.className = "ops-financial-group";
    const heading = document.createElement("div"); heading.className = "ops-financial-group-heading";
    const titleNode = document.createElement("strong"); titleNode.textContent = title;
    const badge = document.createElement("span");
    const retained = isRetainedEvidence(evidenceMode);
    badge.className = `state-badge state-${group.status === "CURRENT" ? retained ? "cyan" : "lime" : group.status === "MISSING" ? "amber" : "coral"}`;
    badge.textContent = retained && group.status === "CURRENT" ? "Retained snapshot" : pretty(group.status);
    heading.append(titleNode, badge);
    const note = document.createElement("p"); note.className = "ops-financial-note";
    const sourceLabel = erpEvidenceSourceLabel(evidenceMode);
    const sourceSentence = `${sourceLabel[0].toUpperCase()}${sourceLabel.slice(1)}`;
    note.textContent = group.status === "CURRENT" && group.records.length
      ? retained
        ? `Invoice records are retained accepted ERP evidence. CURRENT means records were available in the recorded snapshot, not a fresh source read.`
        : `Invoice records read from the ${sourceLabel}.`
      : group.status === "CURRENT"
        ? retained
          ? `The retained accepted ERP snapshot returned no invoice records.`
          : `${sourceSentence} returned no invoice records.`
        : financialStatusMessage(group.status, title.startsWith("Sales") ? "Sales" : "Purchase", evidenceMode);
    section.append(heading, note);
    if (group.status === "CURRENT" && group.records.length) {
      const records = document.createElement("div"); records.className = "ops-financial-records";
      records.append(...group.records.map((record) => financialInvoiceCard(record, unit)));
      section.append(records);
    }
    parent.append(section);
  }

  function renderFinancials(next) {
    const panel = $("ops-financials-panel");
    if (!panel) return;
    if (!next._provided.financials) {
      panel.hidden = true;
      return;
    }
    const financials = normalizeFinancials(next.financials);
    const sourceLabel = erpEvidenceSourceLabel(next?.evidence_mode);
    const retained = isRetainedEvidence(next.evidence_mode);
    panel.hidden = false;
    const status = $("ops-financials-status");
    if (status) {
      status.className = `state-badge state-${financials.status === "CURRENT" ? retained ? "cyan" : "lime" : "coral"}`;
      status.textContent = retained && financials.status === "CURRENT" ? "Retained snapshot" : pretty(financials.status);
    }
    setText("ops-financials-note", financials.status === "CURRENT"
      ? retained
        ? "Commercial records are retained accepted ERP evidence. CURRENT means records were available in the recorded snapshot, not a fresh source read. Sales order line amounts are order values; they are not revenue. Invoice totals and outstanding amounts are invoice-level amounts."
        : `Commercial records are read from the ${sourceLabel}. Sales order line amounts are order values; they are not revenue. Invoice totals and outstanding amounts are invoice-level amounts.`
      : `Commercial evidence is unavailable from the ${sourceLabel}. No amounts are inferred.`);
    const orders = $("ops-financial-orders");
    const invoices = $("ops-financial-invoices");
    orders.replaceChildren(); invoices.replaceChildren();
    if (financials.status !== "CURRENT") {
      orders.append(emptyList(`Source order lines are unavailable from the ${sourceLabel}.`));
      invoices.append(emptyList(`Invoice records are unavailable from the ${sourceLabel}.`));
      return;
    }
    const unit = displayUnit(next.quantities?.uom);
    if (financials.purchase_order) {
      orders.append(financialOrderCard(financials.purchase_order, "Purchase order", unit));
    }
    for (const order of financials.sales_orders) {
      const name = firstText(order.document, ["name", "record_id", "id"]) || "Sales order";
      orders.append(financialOrderCard(order, `Sales order · ${name}`, unit));
    }
    if (!orders.childNodes.length) orders.append(emptyList(`No source order lines returned from the ${sourceLabel}.`));
    renderInvoiceGroup(invoices, "Purchase invoices", financials.purchase_invoices, unit, next.evidence_mode);
    if (financials.sales_invoices.length) {
      for (const row of financials.sales_invoices) {
        renderInvoiceGroup(invoices, `Sales invoices · ${row.customer_order || "Order unavailable"}`, normalizeInvoiceGroup(row), unit, next.evidence_mode);
      }
    } else {
      invoices.append(emptyList(`No sales invoice groups returned from the ${sourceLabel}.`));
    }
  }

  function arrivalQuantitySummary(event, next) {
    const observed = numberFrom(event.observed_stock_quantity);
    if (!finite(observed)) return "Quantity count unknown";
    const unit = displayUnit(next?.quantities?.stock_uom || next?.quantities?.uom || event.stock_uom || event.uom, "");
    return `${formatNumber(observed)}${unit ? ` ${unit}` : ""} counted`;
  }
  function eventSummary(event, next) {
    const type = canonicalType(event.type || event.event_type || event.kind);
    if (type === "arrival") return [finite(numberFrom(event.cartons)) ? `${formatNumber(numberFrom(event.cartons))} cartons` : "Cartons unknown", arrivalQuantitySummary(event, next), firstText(event, ["lot", "batch"])].filter(Boolean).join(" · ");
    if (type === "inspection") return [firstText(event, ["result", "status"]) || "Inspection result unknown", firstText(event, ["scope"]), firstText(event, ["metric"]), event.measured !== undefined ? `measured ${event.measured}` : ""].filter(Boolean).join(" · ");
    if (type === "picked") return [firstText(event, ["customer_order", "sales_order"]) || "Order unknown", finite(numberFrom(event.quantity)) ? `${formatNumber(numberFrom(event.quantity))} picked` : "Picked quantity unknown", firstText(event, ["lot", "batch"])].filter(Boolean).join(" · ");
    if (type === "carrier_pickup") return `${firstText(event, ["shipment_id", "shipment"]) || "Shipment unknown"} · pickup evidence`;
    if (type === "delivery") return `${firstText(event, ["shipment_id", "shipment"]) || "Shipment unknown"} · explicit delivery evidence`;
    return firstText(event, ["message", "evidence_ref"]) || "Event details unavailable";
  }

  function recentActivityEvents(value) {
    if (!Array.isArray(value)) return [];
    return value.map((event, index) => ({ event, index })).sort((left, right) => {
      const leftTime = Date.parse(left.event?.occurred_at || "");
      const rightTime = Date.parse(right.event?.occurred_at || "");
      if (Number.isFinite(leftTime) && Number.isFinite(rightTime) && leftTime !== rightTime) return rightTime - leftTime;
      if (Number.isFinite(leftTime) !== Number.isFinite(rightTime)) return Number.isFinite(leftTime) ? -1 : 1;
      return right.index - left.index;
    });
  }

  function renderEvents(next) {
    const list = $("ops-events-list");
    setText("ops-events-count", next._provided.events ? `${next.events.length} event${next.events.length === 1 ? "" : "s"}` : "Unknown");
    if (!next._provided.events) { list.replaceChildren(emptyList("Source activity is unavailable from the current projection.")); return; }
    if (!next.events.length) { list.replaceChildren(emptyList("No source events recorded yet.")); return; }
    const events = recentActivityEvents(next.events);
    list.replaceChildren(...events.map(({ event }) => {
      const item = document.createElement("li"); item.className = "ops-activity-item";
      const time = document.createElement("time"); time.className = "ops-activity-time"; time.textContent = formatDate(event.occurred_at);
      const copy = document.createElement("div"); copy.className = "ops-activity-copy";
      const title = document.createElement("strong"); title.textContent = pretty(canonicalType(event.type || event.event_type || event.kind) || event.type || event.kind || "Source event");
      const detail = document.createElement("p"); detail.textContent = eventSummary(event, next);
      const meta = document.createElement("small"); meta.textContent = `${event.synthetic === true ? "Simulated evidence" : "Source event"}${firstText(event, ["evidence_ref", "evidence_id"]) ? ` · ${firstText(event, ["evidence_ref", "evidence_id"])}` : ""}`;
      copy.append(title, detail, meta); item.append(time, copy); return item;
    }));
  }

  function conversationAnswer(conversation) {
    if (isRecord(conversation)) {
      for (const key of ["answer", "latest_answer", "text", "response", "message"]) {
        const answer = cleanAnswer(conversation[key]);
        if (answer) return answer;
      }
    }
    const messages = Array.isArray(conversation)
      ? conversation
      : isRecord(conversation) && Array.isArray(conversation.messages) ? conversation.messages : [];
    for (const message of [...messages].reverse()) {
        if (!isRecord(message)) continue;
        const role = text(message.role || message.author).toLowerCase();
        if (role && !/assistant|agent|system/.test(role)) continue;
        const answer = cleanAnswer(message.answer || message.content || message.text || message.message);
        if (answer) return answer;
    }
    return "";
  }
  function providerLabel(value) {
    if (typeof value === "string") return text(value);
    if (!isRecord(value)) return "";
    const provider = text(value.provider) || text(value.mode) || text(value.transport);
    const model = text(value.model) || text(value.model_id);
    return [provider, model].filter(Boolean).join(" · ");
  }
  function firstProvider(record, keys) {
    if (!isRecord(record)) return "";
    for (const key of keys) {
      const value = providerLabel(record[key]);
      if (value) return value;
    }
    return "";
  }
  function conversationProjectionState(next) {
    const conversation = next?.conversation;
    const rawStatus = (firstText(conversation, ["status", "state"]) || firstText(next, ["conversation_status"])).toUpperCase();
    const message = cleanAnswer(firstText(conversation, ["error", "detail", "message"]) || firstText(next, ["conversation_message"]));
    const status = rawStatus || (message ? "UNAVAILABLE" : "");
    const answer = conversationAnswer(conversation) || cleanAnswer(next?.answer || next?.answer_text);
    return { status, message, answer, hasState: Boolean(answer || /UNAVAILABLE|ERROR|FAILED|DISABLED/.test(status)) };
  }
  function retainConversationProjection(next, previous = null) {
    const caseId = text(next?.case_id);
    const prior = isRecord(previous) && text(previous.caseId) === caseId ? previous : null;
    const state = conversationProjectionState(next);
    if (caseId && state.hasState) {
      let conversation = Array.isArray(next.conversation)
        ? [...next.conversation]
        : isRecord(next.conversation) ? { ...next.conversation } : {};
      if (state.answer && !conversationAnswer(conversation)) {
        conversation = Array.isArray(conversation)
          ? [...conversation, { role: "assistant", answer: state.answer }]
          : { ...conversation, answer: state.answer };
      }
      return {
        projection: next,
        memory: {
          caseId,
          conversation,
          conversation_status: text(next.conversation_status) || state.status,
          conversation_message: text(next.conversation_message) || state.message,
          conversation_provider: text(next.conversation_provider),
          conversation_context: text(next.conversation_context),
        },
      };
    }
    if (!prior) return { projection: next, memory: null };
    const merged = {
      ...next,
      conversation: Array.isArray(prior.conversation)
        ? [...prior.conversation]
        : isRecord(prior.conversation) ? { ...prior.conversation } : {},
    };
    for (const key of ["conversation_status", "conversation_message", "conversation_provider", "conversation_context"]) {
      if (prior[key]) merged[key] = prior[key];
    }
    return { projection: merged, memory: prior };
  }

  function appendInlineMarkdown(parent, value) {
    const parts = String(value ?? "").split(/(\*\*[^*\n]+\*\*)/g);
    for (const part of parts) {
      if (!part) continue;
      if (/^\*\*[^*\n]+\*\*$/.test(part)) {
        const strong = document.createElement("strong");
        strong.textContent = part.slice(2, -2);
        parent.append(strong);
      } else {
        parent.append(document.createTextNode(part));
      }
    }
  }

  function renderMarkdownAnswer(answerNode, answer) {
    const content = document.createElement("div");
    content.className = "ops-markdown";
    const blocks = markdownBlocks(answer);
    for (const block of blocks) {
      if (block.type === "heading") {
        const heading = document.createElement(`h${Math.min(5, block.level + 2)}`);
        appendInlineMarkdown(heading, block.text);
        content.append(heading);
      } else if (block.type === "list") {
        const list = document.createElement("ul");
        for (const item of block.items) {
          const listItem = document.createElement("li");
          appendInlineMarkdown(listItem, item);
          list.append(listItem);
        }
        content.append(list);
      } else if (block.type === "table") {
        const wrapper = document.createElement("div");
        wrapper.className = "ops-markdown-table-wrap";
        const table = document.createElement("table");
        table.setAttribute("aria-label", "Agent answer table");
        const head = document.createElement("thead");
        const headerRow = document.createElement("tr");
        for (const label of block.headers) {
          const cell = document.createElement("th");
          cell.scope = "col";
          appendInlineMarkdown(cell, label);
          headerRow.append(cell);
        }
        head.append(headerRow);
        table.append(head);
        if (block.rows.length) {
          const body = document.createElement("tbody");
          for (const row of block.rows) {
            const tableRow = document.createElement("tr");
            for (const value of row) {
              const cell = document.createElement("td");
              appendInlineMarkdown(cell, value);
              tableRow.append(cell);
            }
            body.append(tableRow);
          }
          table.append(body);
        }
        wrapper.append(table);
        content.append(wrapper);
      } else {
        const paragraph = document.createElement("p");
        appendInlineMarkdown(paragraph, block.text);
        content.append(paragraph);
      }
    }
    if (!content.childNodes.length) {
      const paragraph = document.createElement("p");
      paragraph.textContent = String(answer ?? "");
      content.append(paragraph);
    }
    answerNode.replaceChildren(content);
  }

  function renderConversation(next) {
    const conversation = next.conversation || {};
    const status = (firstText(conversation, ["status", "state"]) || firstText(next, ["conversation_status"])).toUpperCase();
    const provider = agentProviderDisplay(next);
    const sourceLabel = erpEvidenceSourceLabel(next?.evidence_mode);
    const context = firstText(conversation, ["context_label", "context", "source_summary"]) || firstText(next, ["conversation_context"]) || sourceLabel;
    setText("ops-chat-provider", provider);
    setText("ops-chat-context", context);
    const answerNode = $("ops-chat-answer"); answerNode.classList.remove("is-error");
    if (/UNAVAILABLE|ERROR|FAILED|DISABLED/.test(status)) {
      voiceController?.setAnswer("");
      answerNode.classList.add("is-error");
      const message = cleanAnswer(firstText(conversation, ["error", "detail", "message"]) || firstText(next, ["conversation_message"])) || "Read-only conversation is unavailable from the current bridge.";
      const paragraph = document.createElement("p"); paragraph.textContent = message; answerNode.replaceChildren(paragraph); return;
    }
    const answer = conversationAnswer(conversation);
    if (answer) { voiceController?.setAnswer(answer); renderMarkdownAnswer(answerNode, answer); return; }
    voiceController?.setAnswer("");
    const paragraph = document.createElement("p"); paragraph.className = "ops-empty"; paragraph.textContent = "Ask a read-only question about quantities, lots, customers, or delivery evidence."; answerNode.replaceChildren(paragraph);
  }

  function selectedTemplateFromProjection(next) {
    if (!selectedTemplate) return null;
    return next.available_event_templates.find((template) => template.type === selectedTemplate.type) || null;
  }
  function renderTemplateSummary(template) {
    const summary = $("ops-template-summary");
    if (!summary) return;
    if (!template) {
      summary.replaceChildren(Object.assign(document.createElement("span"), { textContent: "No event is selected." }));
      return;
    }
    const heading = document.createElement("strong"); heading.textContent = template.label;
    const detail = document.createElement("span"); detail.textContent = `${template.description} · Source: ${template.source}`;
    summary.replaceChildren(heading, detail);
  }
  function renderTemplateFields(template) {
    selectedTemplate = template;
    const fieldsNode = $("ops-template-fields"); fieldsNode.replaceChildren();
    renderTemplateSummary(template);
    if (!template) {
      const emptyEvidence = $("ops-evidence-ref");
      if (emptyEvidence) emptyEvidence.value = "";
      updateEventButton();
      return;
    }
    for (const definition of FIELD_DEFS[template.type]) {
      const label = document.createElement("label"); label.className = "ops-field"; label.htmlFor = `ops-field-${definition.key}`; label.textContent = definition.label;
      let input;
      if (definition.type === "select") {
        input = document.createElement("select");
        definition.options.forEach((option) => { const node = document.createElement("option"); node.value = option; node.textContent = option; input.append(node); });
      } else {
        input = document.createElement("input"); input.type = definition.type; if (definition.min) input.min = definition.min; if (definition.step) input.step = definition.step; if (definition.placeholder) input.placeholder = definition.placeholder;
      }
      input.id = `ops-field-${definition.key}`; input.dataset.fieldKey = definition.key; input.required = true;
      const value = templateDefault(template, definition.key);
      if (value !== "") input.value = String(value);
      input.addEventListener("input", updateEventButton);
      input.addEventListener("change", updateEventButton);
      label.append(input); fieldsNode.append(label);
    }
    const evidenceDefault = templateDefault(template, "evidence_ref");
    const evidenceNode = $("ops-evidence-ref");
    if (evidenceNode) evidenceNode.value = evidenceDefault;
    updateEventButton();
  }
  function renderTemplates(next, { resetFields = false } = {}) {
    const existing = selectedTemplate?.type || templateSelect.value;
    const currentType = selectedTemplate?.type;
    const fieldsRendered = Boolean($("ops-template-fields")?.querySelector("[data-field-key]"));
    templateSelect.replaceChildren();
    const placeholder = document.createElement("option"); placeholder.value = ""; placeholder.textContent = next._provided.available_event_templates ? "Choose an approved event…" : "No event templates available"; templateSelect.append(placeholder);
    for (const template of next.available_event_templates) {
      const option = document.createElement("option"); option.value = template.type; option.textContent = template.label; templateSelect.append(option);
    }
    const match = next.available_event_templates.find((template) => template.type === existing) || null;
    templateSelect.value = match ? match.type : "";
    if (match && shouldPreserveTemplateFields({ currentType, nextType: match.type, fieldsRendered, resetFields })) {
      selectedTemplate = match;
      renderTemplateSummary(match);
    } else if (match) renderTemplateFields(match); else renderTemplateFields(null);
    templateSelect.disabled = !next.available_event_templates.length || !next.available || !freshActionsAllowed(next);
    syncFreshEventControls(next);
    updateEventButton();
  }
  function readTemplateValues() {
    return Object.fromEntries([...document.querySelectorAll("#ops-template-fields [data-field-key]")].map((node) => [node.dataset.fieldKey, node.value]));
  }
  function updateEventButton() {
    const button = $("ops-process-event");
    if (button) button.disabled = processingEvent || photoAnalysisPending || !projection?.available || !freshActionsAllowed(projection) || !selectedTemplate || !sourceState?.hidden;
  }
  function syncFreshEventControls(next = projection) {
    const form = $("ops-event-form");
    if (!form) return;
    const enabled = Boolean(next?.available === true && freshActionsAllowed(next) && sourceState?.hidden);
    form.querySelectorAll("input, select, button").forEach((control) => { control.disabled = !enabled; });
    const select = $("ops-template-select");
    if (select) select.disabled = !enabled || !Array.isArray(next?.available_event_templates) || !next.available_event_templates.length;
  }

  function proposalSourceLabel(source) {
    return text(source) === "RETAINED_ALLOCATION_RECOMMENDATION"
      ? "Retained allocation recommendation; it does not write."
      : "Operator-declared event; the agent did not create it.";
  }

  function proposalActionDetail(proposal, evidenceMode = null) {
    if (!isRecord(proposal)) return "No pending proposal";
    const status = text(proposal.status).toUpperCase();
    const retained = isRetainedEvidence(evidenceMode || proposal.evidence_mode);
    if (status === "APPLIED") return retained ? "Recorded completion confirmed" : "Approved operation applied";
    if (status === "PENDING_MANAGER_APPROVAL") return retained ? "Recorded completion awaiting confirmation" : "Proposal awaiting manager review";
    return status ? `Proposal status: ${pretty(status)}` : "Proposal status unavailable";
  }

  function approvalReadback(next) {
    const direct = isRecord(next?.approval_evidence) ? next.approval_evidence : null;
    const proposal = isRecord(next?.prepared_proposal) ? next.prepared_proposal : null;
    if (direct && (!proposal || text(proposal.status).toUpperCase() === "APPLIED")) return direct;
    const approval = isRecord(proposal?.approval) ? proposal.approval : null;
    if (!approval || text(proposal?.status).toUpperCase() !== "APPLIED") return null;
    return { ...approval, event_id: firstText(proposal.event, ["event_id"]) };
  }

  function renderPreparedProposal(next) {
    const incoming = isRecord(next?.prepared_proposal) ? next.prepared_proposal : null;
    if (incoming && text(incoming.proposal_id)) preparedProposal = incoming;
    const panel = $("ops-proposal-panel");
    const button = $("ops-approve-proposal");
    if (!panel || !button) return;
    const proposal = preparedProposal;
    const proposalStatus = text(proposal?.status).toUpperCase();
    const confirmationPending = proposalStatus === "PENDING_MANAGER_APPROVAL";
    const applied = proposalStatus === "APPLIED";
    const recordedOutcome = Boolean(proposal && proposalStatus) && !confirmationPending && !applied;
    const retained = isRetainedEvidence(next?.evidence_mode);
    const retainedLabel = recordedOutcome ? "Recorded event outcome" : "Recorded completion";
    setText("ops-manager-gate-label", retained ? retainedLabel : "Manager gate");
    setText("ops-evidence-title", recordedOutcome ? `Recorded event ${pretty(proposalStatus)}` : retained ? "Confirm recorded completion" : "Process evidence");
    setText("ops-evidence-copy", recordedOutcome
      ? `The recorded event outcome is ${pretty(proposalStatus || "unavailable")}; it cannot be confirmed as completed.`
      : retained
      ? "Review the recorded completion and confirm the exact retained case revision."
      : "Prepare one bounded action from operator-declared evidence, then confirm the exact case revision.");
    setText("ops-gate-note", recordedOutcome
      ? "No confirmation or fresh native execution is available for this recorded outcome."
      : retained
      ? "Manager confirmation recovers a recorded completed event; it does not create a fresh native operation."
      : "Manager approval stays bounded to the prepared case revision.");
    setText("ops-proposal-label", retained ? retainedLabel : "Manager approval");
    setText("ops-proposal-title", recordedOutcome ? `Recorded event ${pretty(proposalStatus)}` : retained ? "Confirm recorded completion" : "Prepared same-case operation");
    setText("ops-approve-label", recordedOutcome ? "Confirmation unavailable" : retained ? "Confirm recorded completion" : "Approve and execute");
    const readback = $("ops-approval-readback");
    const approval = approvalReadback(next);
    if (readback) {
      readback.hidden = !approval;
      readback.textContent = approval
        ? retained
          ? `Recorded completion confirmed by ${text(approval.manager_id) || "manager unavailable"} at ${formatDate(approval.approved_at)}.`
          : `Approved by ${text(approval.manager_id) || "manager unavailable"} at ${formatDate(approval.approved_at)}.`
        : "";
    }
    panel.hidden = !proposal || text(proposal.status) === "APPLIED" || text(proposal.case_id) && text(proposal.case_id) !== text(next?.case_id);
    if (panel.hidden) return;
    const event = isRecord(proposal.event) ? proposal.event : {};
    const fields = Object.entries(event)
      .filter(([key]) => !["event_id", "type", "occurred_at", "synthetic", "evidence_ref", "pick_evidence_ref"].includes(key))
      .map(([key, value]) => `${pretty(key)}: ${Array.isArray(value) ? value.join(", ") : String(value)}`);
    setText("ops-proposal-summary", [
      `PO ${text(proposal.purchase_order) || text(next?.purchase_order) || "unavailable"}`,
      pretty(event.type || "operation"),
      ...fields,
    ].join(" · "));
    button.disabled = processingEvent || !confirmationPending || !next?.available || !sourceState?.hidden || !text($("ops-manager-id")?.value) || (!retained && !freshActionsAllowed(next));
  }

  function photoAttachmentList(next) {
    return Array.isArray(next?.photo_attachments) ? next.photo_attachments.filter(isRecord) : [];
  }

  function photoAnalysisEnabled(next) {
    return next?.photo_analysis_enabled === true;
  }

  function photoPurposeLabel(value) {
    const purpose = text(value).toLowerCase();
    if (purpose === "overview") return "Overall receiving view";
    if (purpose === "label") return "Product / lot label";
    if (purpose === "detail") return "Close detail / condition";
    return purpose ? pretty(purpose) : "Purpose unavailable";
  }

  function photoPurposeGuidance(value) {
    const purpose = text(value).toLowerCase();
    if (purpose === "label") return "Use a close, readable label view to compare the observed item and lot with the current ERP scope.";
    if (purpose === "detail") return "Use a close detail view for a specific visible condition; it does not clear quality or update stock.";
    return "Use a complete receiving view for visible condition and framing; it does not establish hidden contents or quantity.";
  }

  function photoReviewSourceLabel(value) {
    const status = text(value).toUpperCase();
    if (status === "CURRENT") return "Current ERP source";
    if (status === "RETAINED_AS_OF" || status === "RETAINED") return "Retained ERP evidence";
    if (status.includes("UNAVAILABLE")) return "ERP source unavailable";
    return status ? pretty(status) : "ERP source status unavailable";
  }

  function photoReviewLotText(value) {
    if (typeof value === "string") return text(value) || "Lot unavailable";
    if (!isRecord(value)) return "No current ERP lot selected";
    const lot = firstText(value, ["lot", "lot_id", "name", "id"]);
    const status = firstText(value, ["status", "inspection_result", "quality_result"]);
    const received = numberFromKeys(value, ["received", "received_quantity"]);
    const usable = numberFromKeys(value, ["usable", "usable_quantity"]);
    const held = numberFromKeys(value, ["held", "held_quantity"]);
    return [
      lot || "Lot unavailable",
      status ? pretty(status) : "",
      finite(received) ? `${formatNumber(received)} received` : "",
      finite(usable) ? `${formatNumber(usable)} usable` : "",
      finite(held) ? `${formatNumber(held)} held` : "",
    ].filter(Boolean).join(" · ");
  }

  function photoReviewQuantitiesText(value) {
    if (!isRecord(value)) return "Quantities unavailable from source.";
    const uom = displayUnit(value.uom);
    const usable = numberFromKeys(value, ["usable", "usable_quantity"]);
    const held = numberFromKeys(value, ["held", "held_quantity"]);
    return [
      finite(usable) ? `${formatNumber(usable)} usable ${uom}` : "Usable quantity unavailable",
      finite(held) ? `${formatNumber(held)} held ${uom}` : "Held quantity unavailable",
    ].join(" · ");
  }

  function photoReviewPolicyText(value) {
    if (typeof value === "string") return text(value);
    if (!isRecord(value)) return "";
    const specification = text(value.synthetic_specification);
    const source = firstText(value, ["specification_source"]);
    const criteria = isRecord(value.inspection_criteria)
      ? Object.entries(value.inspection_criteria)
        .filter(([, bounds]) => isRecord(bounds))
        .map(([name, bounds]) => {
          const minimum = numberFromKeys(bounds, ["minimum", "min"]);
          const maximum = numberFromKeys(bounds, ["maximum", "max"]);
          return `${pretty(name)}${finite(minimum) ? ` ≥ ${formatNumber(minimum)}` : ""}${finite(maximum) ? ` ≤ ${formatNumber(maximum)}` : ""}`;
        })
        .filter(Boolean)
        .slice(0, 3)
      : [];
    return [
      specification ? `Specification source ${pretty(specification)}` : "",
      source && source !== specification ? `Policy source ${pretty(source)}` : "",
      criteria.length ? `Inspection bounds: ${criteria.join("; ")}` : "",
      value.inspection_required === true ? "Inspection required by current policy" : "",
    ].filter(Boolean).join(" · ");
  }

  function photoReviewObservationText(value) {
    if (typeof value === "string") return text(value);
    if (!isRecord(value)) return "";
    const assessment = isRecord(value.assessment) ? value.assessment : {};
    const condition = firstText(value, ["visible_condition"]) || firstText(assessment, ["visible_condition"]);
    const visibility = firstText(value, ["visibility", "label_visibility", "detail_visibility"])
      || firstText(assessment, ["visibility", "label_visibility", "detail_visibility"]);
    const recommendation = firstText(value, ["recommendation_code"]);
    const lot = firstText(value, ["linked_lot"]);
    const issues = Array.isArray(assessment.issues) ? assessment.issues.map((item) => text(item)).filter(Boolean).slice(0, 2) : [];
    const observations = Array.isArray(assessment.observations) ? assessment.observations.map((item) => text(item)).filter(Boolean).slice(0, 2) : [];
    return [
      condition ? photoConditionLabel(condition) : "",
      visibility ? photoVisibilityLabel(visibility) : "",
      recommendation ? pretty(recommendation) : "",
      lot ? `lot ${lot}` : "",
      issues.length ? `issues: ${issues.join("; ")}` : "",
      observations.length ? `observations: ${observations.join("; ")}` : "",
    ].filter(Boolean).join(" · ");
  }

  function photoReviewOrderText(value) {
    if (typeof value === "string") return { label: text(value) || "Affected order", quantity: "Still fulfillable quantity unavailable" };
    if (!isRecord(value)) return null;
    const label = firstText(value, ["order_id", "customer_order", "sales_order", "order", "id", "name"]) || "Affected order";
    const customer = firstText(value, ["customer", "customer_name"]);
    const quantity = numberFromKeys(value, ["still_fulfillable_quantity", "fulfillable_quantity", "fulfillable"]);
    const requested = numberFromKeys(value, ["requested_quantity"]);
    const allocated = numberFromKeys(value, ["allocated"]);
    const backordered = numberFromKeys(value, ["backordered"]);
    const dispatched = numberFromKeys(value, ["dispatched"]);
    const authority = firstText(value, ["still_fulfillable_authority"]);
    const uom = displayUnit(firstText(value, ["uom", "unit", "unit_label"]), "");
    return {
      label: customer ? `${label} · ${customer}` : label,
      quantity: finite(quantity)
        ? `${formatNumber(quantity)} still fulfillable${uom ? ` ${uom}` : ""}${authority ? ` · ${pretty(authority)}` : ""}`
        : [
          finite(requested) ? `${formatNumber(requested)} requested` : "",
          finite(allocated) ? `${formatNumber(allocated)} allocated` : "",
          finite(backordered) ? `${formatNumber(backordered)} backordered` : "",
          finite(dispatched) ? `${formatNumber(dispatched)} dispatched` : "",
        ].filter(Boolean).join(" · ") || "ERP order quantities unavailable",
    };
  }

  function openEconomicFlow() {
    const url = new URL(window.location.href);
    url.searchParams.set("view", "agent");
    url.hash = "ops-economic-panel";
    window.history.pushState({}, "", `${url.pathname}${url.search}${url.hash}`);
    setOpsView("agent", { scrollTarget: "ops-economic-panel" });
  }

  function renderPhotoReviewCard(parent, next, attachment = null) {
    if (!parent) return;
    const card = isRecord(next?.photo_review_card) ? next.photo_review_card : null;
    parent.replaceChildren();
    parent.hidden = !card;
    if (!card) return;
    const header = document.createElement("header"); header.className = "ops-photo-review-header";
    const heading = document.createElement("div");
    const title = document.createElement("strong"); title.textContent = "Receiving check";
    const revision = firstText(card, ["source_revision"]);
    const revisionLabel = revision.length > 16 ? `${revision.slice(0, 12)}…` : revision;
    const detail = document.createElement("small"); detail.textContent = [photoReviewSourceLabel(card.source_status), revisionLabel ? `source ${revisionLabel}` : ""].filter(Boolean).join(" · ");
    if (revision) detail.title = revision;
    heading.append(title, detail);
    const badge = document.createElement("span"); badge.className = "state-badge state-cyan"; badge.textContent = photoReviewSourceLabel(card.source_status);
    header.append(heading, badge); parent.append(header);
    const facts = document.createElement("div"); facts.className = "ops-photo-review-facts";
    const factsValues = [
      ["Configured item", typeof card.configured_item === "string" ? text(card.configured_item) : firstText(card.configured_item, ["item_code", "label", "id"]) || "Item scope unavailable"],
      ["Latest analyzed ERP lot", photoReviewLotText(card.selected_lot)],
      ["Current quantity", photoReviewQuantitiesText(card.quantities)],
    ];
    const linkedAnalysis = isRecord(attachment?.analysis) ? attachment.analysis : null;
    if (linkedAnalysis) {
      const linkedLot = firstText(linkedAnalysis, ["linked_lot"]);
      const linkedSource = firstText(linkedAnalysis, ["linkage_source"]).toUpperCase();
      const freshness = photoAdviceFreshnessLabel(linkedAnalysis, card);
      factsValues.push([
        "Photo ERP link",
        [linkedSource === "OPERATOR_SELECTED" && linkedLot
          ? `Operator-selected lot ${linkedLot}`
          : "No operator-selected lot linked to this analysis", freshness ? `· ${freshness}` : ""].filter(Boolean).join(" "),
      ]);
    } else if (isRecord(card.analysis_context) && (card.analysis_context.attachment_id || card.analysis_context.linked_lot || card.analysis_context.purpose)) {
      const context = card.analysis_context;
      const contextLot = firstText(context, ["linked_lot"]);
      const contextPurpose = firstText(context, ["purpose"]);
      const freshness = photoAdviceFreshnessLabel(context, card);
      factsValues.push([
        "Latest photo scope",
        [contextPurpose ? photoPurposeLabel(contextPurpose) : "", contextLot ? `lot ${contextLot}` : "", freshness].filter(Boolean).join(" · "),
      ]);
    }
    factsValues.forEach(([label, value]) => {
      const fact = document.createElement("div"); fact.className = "ops-photo-review-fact";
      const name = document.createElement("strong"); name.textContent = label;
      const valueNode = document.createElement("span"); valueNode.textContent = value;
      fact.append(name, valueNode); facts.append(fact);
    });
    parent.append(facts);
    const policy = photoReviewPolicyText(card.quality_policy);
    if (policy) {
      const policyNode = document.createElement("p"); policyNode.className = "ops-photo-review-policy";
      const specification = isRecord(card.quality_policy) ? text(card.quality_policy.synthetic_specification).toUpperCase() : "";
      const specificationSource = isRecord(card.quality_policy) ? firstText(card.quality_policy, ["specification_source"]).toUpperCase() : "";
      const syntheticSpecification = specification === "SYNTHETIC_CONFIG"
        || specificationSource === "SYNTHETIC_CONFIG"
        || (isRecord(card.quality_policy) && card.quality_policy.synthetic_specification === true);
      const label = document.createElement("strong");
      label.textContent = syntheticSpecification ? "Synthetic quality specification: " : "Configured quality policy: ";
      policyNode.append(label, document.createTextNode(policy)); parent.append(policyNode);
    }
    const observations = Array.isArray(card.current_observations) ? card.current_observations.map(photoReviewObservationText).filter(Boolean) : [];
    if (observations.length) {
      const observationNode = document.createElement("div"); observationNode.className = "ops-photo-review-observations";
      const label = document.createElement("strong"); label.textContent = "Current photo observations";
      const list = document.createElement("ul"); observations.slice(0, 4).forEach((item) => { const row = document.createElement("li"); row.textContent = item; list.append(row); });
      observationNode.append(label, list); parent.append(observationNode);
    }
    const orders = Array.isArray(card.affected_orders) ? card.affected_orders.map(photoReviewOrderText).filter(Boolean) : [];
    if (orders.length) {
      const ordersNode = document.createElement("div"); ordersNode.className = "ops-photo-review-orders";
      const label = document.createElement("strong"); label.textContent = "Affected orders"; ordersNode.append(label);
      orders.slice(0, 5).forEach((order) => {
        const row = document.createElement("div"); row.className = "ops-photo-review-order";
        const name = document.createElement("strong"); name.textContent = order.label;
        const quantity = document.createElement("span"); quantity.textContent = order.quantity;
        row.append(name, quantity); ordersNode.append(row);
      });
      parent.append(ordersNode);
    }
    if (economicConfigured || isRecord(next?.economic_proposal)) {
      const cta = document.createElement("button"); cta.type = "button"; cta.className = "button button-quiet ops-photo-review-cta";
      cta.textContent = "Open economic decision"; cta.addEventListener("click", openEconomicFlow); parent.append(cta);
    }
  }

  function photoLotIdentifier(lot) {
    return firstText(lot, ["lot", "lot_id", "name", "id"]);
  }

  function photoLotQuantity(lot) {
    return numberFromKeys(lot, ["received", "received_quantity"]);
  }

  function photoAnalysisFor(next, attachmentId) {
    if (!attachmentId) return null;
    const photo = photoAttachmentList(next).find((item) => text(item.attachment_id) === text(attachmentId));
    return isRecord(photo?.analysis) ? photo.analysis : null;
  }

  function photoAnalysisStatus(analysis) {
    return text(analysis?.status).toUpperCase();
  }

  function photoConditionLabel(value) {
    const condition = text(value).toLowerCase();
    if (condition === "visible_damage") return "visible damage flagged";
    if (condition === "unclear") return "condition unclear";
    if (condition === "no_visible_damage") return "no visible damage observed";
    return condition ? pretty(condition) : "condition unavailable";
  }

  function photoVisibilityLabel(value) {
    const visibility = text(value).toLowerCase();
    if (visibility === "clear") return "clear view";
    if (visibility === "occluded") return "occluded view";
    if (visibility === "cropped") return "cropped view";
    if (visibility === "no_goods") return "goods not visible";
    if (visibility === "unclear") return "view unclear";
    return visibility ? pretty(visibility) : "visibility unavailable";
  }

  function photoAnalysisObservation(analysis) {
    const assessment = isRecord(analysis?.assessment) ? analysis.assessment : {};
    const issues = Array.isArray(assessment.issues)
      ? assessment.issues.map((item) => text(item)).filter(Boolean).slice(0, 3)
      : [];
    const observations = Array.isArray(assessment.observations)
      ? assessment.observations.map((item) => text(item)).filter(Boolean).slice(0, 3)
      : text(assessment.observations) ? [text(assessment.observations)] : [];
    const labelVisibility = firstText(assessment, ["label_visibility"]);
    const detailVisibility = firstText(assessment, ["detail_visibility"]);
    const labels = [
      firstText(assessment, ["item_code"]) ? `Photo label item ${firstText(assessment, ["item_code"])}` : "",
      firstText(assessment, ["supplier_lot"]) ? `Photo label lot ${firstText(assessment, ["supplier_lot"])}` : "",
    ].filter(Boolean);
    const parts = [
      firstText(assessment, ["visible_condition"]) ? `Visible condition: ${photoConditionLabel(assessment.visible_condition)}` : "",
      firstText(assessment, ["visibility"]) ? `Visibility: ${photoVisibilityLabel(assessment.visibility)}` : "",
      issues.length ? `Observed issue: ${issues.join("; ")}` : "",
      observations.length ? `Observed detail: ${observations.join("; ")}` : "",
      labelVisibility ? `Label visibility: ${pretty(labelVisibility)}` : "",
      detailVisibility ? `Detail visibility: ${pretty(detailVisibility)}` : "",
      ...labels,
    ].filter(Boolean);
    return parts.join(" · ") || "No visible observation was returned by the source.";
  }

  function photoAnalysisSummary(analysis) {
    const assessment = isRecord(analysis?.assessment) ? analysis.assessment : {};
    const condition = firstText(assessment, ["visible_condition"]);
    const visibility = firstText(assessment, ["visibility", "label_visibility", "detail_visibility"]);
    return [
      condition ? `Visible condition: ${photoConditionLabel(condition)}` : "",
      visibility ? `Visibility: ${photoVisibilityLabel(visibility)}` : "",
    ].filter(Boolean).join(" · ") || "No concise visible finding was returned by the source.";
  }

  function photoCheckStatus(value) {
    const status = text(value).toUpperCase();
    if (["MATCH", "MISMATCH", "UNKNOWN", "NOT_APPLICABLE"].includes(status)) return status;
    return "UNKNOWN";
  }

  function photoNextAction(analysis) {
    const action = isRecord(analysis?.next_action) ? analysis.next_action : {};
    return {
      code: firstText(action, ["code"]).toUpperCase(),
      message: firstText(action, ["message"]),
      suggestedPurpose: firstText(action, ["suggested_purpose"]).toLowerCase(),
    };
  }

  function photoAdviceFreshnessLabel(analysis, card) {
    if (!isRecord(analysis) || analysis.advisory_current !== false) return "";
    const nextAction = firstText(analysis.next_action, ["code"]).toUpperCase();
    const superseded = firstText(analysis, ["superseded_by_attachment_id"]);
    if (superseded) return "Replaced by a newer photo";
    if (nextAction === "VERIFY_IDENTITY") return "Excluded from current advice";
    const currentRevision = firstText(card, ["source_revision"]);
    const analysisRevision = firstText(analysis, ["source_revision"]);
    if (currentRevision && analysisRevision && currentRevision !== analysisRevision) return "Earlier ERP state";
    return "Excluded from current advice";
  }

  function renderPhotoChecks(parent, analysis) {
    const checks = isRecord(analysis?.checks) ? analysis.checks : {};
    const entries = [["item_code", "Item identity"], ["lot", "Lot identity"]]
      .map(([key, label]) => ({ key, label, check: isRecord(checks[key]) ? checks[key] : null }))
      .filter((entry) => entry.check);
    if (!entries.length) return;
    const wrapper = document.createElement("div"); wrapper.className = "ops-photo-checks";
    const heading = document.createElement("strong"); heading.textContent = "Observed identity against ERP"; wrapper.append(heading);
    entries.forEach(({ label, check }) => {
      const row = document.createElement("div"); row.className = "ops-photo-check";
      const name = document.createElement("strong"); name.textContent = label;
      const status = photoCheckStatus(check.status);
      const badge = document.createElement("span"); badge.className = `state-badge state-${status === "MATCH" ? "lime" : status === "MISMATCH" ? "coral" : status === "UNKNOWN" ? "amber" : "neutral"}`; badge.textContent = pretty(status);
      const detail = document.createElement("small");
      const observed = firstText(check, ["observed"]);
      const expected = firstText(check, ["expected"]);
      detail.textContent = [observed ? `Observed ${observed}` : "Observed unavailable", expected ? `ERP ${expected}` : "ERP unavailable", check.requires_review === true ? "Review required" : ""].filter(Boolean).join(" · ");
      row.append(name, badge, detail); wrapper.append(row);
    });
    parent.append(wrapper);
  }

  function photoRecommendation(analysis) {
    const recommendation = isRecord(analysis?.recommendation) ? analysis.recommendation : {};
    const code = firstText(recommendation, ["code"]).toUpperCase();
    const fallback = {
      REQUIRE_INSPECTION: "Inspection recommended before release.",
      RETAKE: "Retake the photo with the complete receiving unit visible.",
      NO_VISIBLE_DAMAGE_NOT_QUALITY_CLEARANCE: "No visible damage observed; this is not quality clearance.",
      ANALYSIS_UNAVAILABLE: "Photo analysis is unavailable; retry or use manual inspection.",
    };
    return {
      code,
      message: firstText(recommendation, ["message"]) || fallback[code] || "Recommendation unavailable from the source.",
      imageLabelLot: firstText(recommendation, ["image_label_lot"]),
      labelLotConflict: recommendation.label_lot_conflict === true,
    };
  }

  function photoModelValue(value) {
    if (typeof value === "string") return text(value);
    return firstText(value, ["model_id", "model", "provider", "name"]);
  }

  function photoUsageText(value) {
    if (!isRecord(value)) return "";
    const input = numberFromKeys(value, ["input_tokens", "inputTokens", "prompt_tokens"]);
    const output = numberFromKeys(value, ["output_tokens", "outputTokens", "completion_tokens"]);
    const total = numberFromKeys(value, ["total_tokens", "totalTokens"]);
    return [
      finite(input) ? `input ${formatNumber(input)}` : "",
      finite(output) ? `output ${formatNumber(output)}` : "",
      finite(total) ? `total ${formatNumber(total)}` : "",
    ].filter(Boolean).join(", ");
  }

  function photoAnalysisProvenance(analysis) {
    const model = photoModelValue(analysis?.model);
    const provider = photoModelValue(analysis?.provider);
    const transport = firstText(analysis, ["transport"]);
    const latency = numberFrom(analysis?.latency_ms);
    const observedAt = firstText(analysis, ["observed_at"]);
    const sourceRevision = firstText(analysis, ["source_revision"]);
    const usage = photoUsageText(analysis?.usage);
    return [
      model ? `Model ${model}` : "",
      provider ? `Provider ${provider}` : "",
      transport ? `Transport ${transport}` : "",
      finite(latency) ? `Latency ${formatNumber(latency)} ms` : "",
      observedAt ? `Observed ${formatDate(observedAt)}` : "",
      sourceRevision ? `ERP source revision ${sourceRevision}` : "",
      usage ? `Usage ${usage}` : "",
    ].filter(Boolean).join(" · ");
  }

  function photoLinkedQuantityText(analysis, next) {
    const quantityValue = numberFrom(analysis?.linked_quantity);
    const unit = displayUnit(next?.quantities?.uom);
    return finite(quantityValue) ? `${formatNumber(quantityValue)} ${unit}` : "ERP quantity unavailable from the source.";
  }

  function renderPhotoAnalysisStages(parent, analysis) {
    if (!Array.isArray(analysis?.stages) || !analysis.stages.length) return;
    const details = document.createElement("details"); details.className = "ops-photo-analysis-stages";
    const summary = document.createElement("summary"); summary.textContent = "View model stages"; details.append(summary);
    const list = document.createElement("ul");
    analysis.stages.filter(isRecord).forEach((stage) => {
      const item = document.createElement("li");
      const stageName = firstText(stage, ["stage"]) || "Model stage";
      const latency = numberFrom(stage.latency_ms);
      const usage = photoUsageText(stage.usage);
      item.textContent = [pretty(stageName), finite(latency) ? `${formatNumber(latency)} ms` : "", usage ? `Usage ${usage}` : ""].filter(Boolean).join(" · ");
      list.append(item);
    });
    if (list.childNodes.length) details.append(list);
    parent.append(details);
  }

  function renderPhotoAnalysisEvidence(parent, analysis) {
    const provenance = photoAnalysisProvenance(analysis);
    const hasStages = Array.isArray(analysis?.stages) && analysis.stages.length > 0;
    if (!provenance && !hasStages) return;
    const details = document.createElement("details"); details.className = "ops-photo-analysis-evidence";
    const summary = document.createElement("summary"); summary.textContent = "View source and model evidence"; details.append(summary);
    if (provenance) {
      const provenanceNode = document.createElement("p"); provenanceNode.className = "ops-photo-analysis-provenance";
      provenanceNode.textContent = provenance; details.append(provenanceNode);
    }
    if (hasStages) {
      const stages = document.createElement("div");
      renderPhotoAnalysisStages(stages, analysis);
      if (stages.firstElementChild) details.append(stages.firstElementChild);
    }
    parent.append(details);
  }

  function renderPhotoAnalysis(parent, photo, next) {
    const analysis = isRecord(photo?.analysis) ? photo.analysis : null;
    const section = document.createElement("section"); section.className = "ops-photo-analysis";
    if (!analysis) {
      const detail = document.createElement("p"); detail.className = "ops-photo-analysis-note";
      detail.textContent = photoAnalysisEnabled(next)
        ? "Not analyzed yet. Choose this photo's ERP lot in Photo intake, then analyze it."
        : "Photo analysis is not configured for this case; this remains manual evidence only.";
      section.append(detail); parent.append(section); return section;
    }
    const status = photoAnalysisStatus(analysis);
    const recommendation = photoRecommendation(analysis);
    const nextAction = photoNextAction(analysis);
    const assessment = isRecord(analysis.assessment) ? analysis.assessment : {};
    const condition = text(assessment.visible_condition).toLowerCase();
    if (condition === "visible_damage" || recommendation.code === "REQUIRE_INSPECTION") section.classList.add("is-damage");
    if (!recommendation.labelLotConflict && (condition === "no_visible_damage" || recommendation.code === "NO_VISIBLE_DAMAGE_NOT_QUALITY_CLEARANCE")) section.classList.add("is-clear");
    if (nextAction.code === "VERIFY_IDENTITY") section.classList.add("is-identity-warning");
    const supersededBy = firstText(analysis, ["superseded_by_attachment_id"]);
    const identityVerification = nextAction.code === "VERIFY_IDENTITY";
    const currentRevision = firstText(next?.photo_review_card, ["source_revision"]);
    const analysisRevision = firstText(analysis, ["source_revision"]);
    const revisionStale = Boolean(currentRevision && analysisRevision && currentRevision !== analysisRevision);
    const replacedByNewerPhoto = status === "COMPLETE" && analysis.advisory_current === false && Boolean(supersededBy);
    const historical = status === "COMPLETE" && analysis.advisory_current === false && !identityVerification && !replacedByNewerPhoto && revisionStale;
    const excludedFromAdvice = status === "COMPLETE" && analysis.advisory_current === false && !replacedByNewerPhoto && !historical;
    if (replacedByNewerPhoto) {
      const freshness = document.createElement("p"); freshness.className = "ops-photo-analysis-stale";
      freshness.textContent = "Replaced by a newer photo.";
      section.append(freshness);
    } else if (historical) {
      const freshness = document.createElement("p"); freshness.className = "ops-photo-analysis-stale";
      freshness.textContent = "Earlier ERP state — reanalyze before using for current decision.";
      section.append(freshness);
    } else if (excludedFromAdvice) {
      const freshness = document.createElement("p"); freshness.className = "ops-photo-analysis-stale";
      freshness.textContent = "Excluded from current advice — resolve the identity check before relying on this observation.";
      section.append(freshness);
    }
    const header = document.createElement("div"); header.className = "ops-photo-analysis-header";
    const title = document.createElement("strong"); title.textContent = status === "COMPLETE" ? "Agent photo observation" : "Photo analysis unavailable";
    const badge = document.createElement("span");
    badge.className = `state-badge state-${status === "COMPLETE" ? "cyan" : status === "UNAVAILABLE" ? "coral" : "neutral"}`;
    badge.textContent = status ? pretty(status) : "Status unavailable";
    header.append(title, badge); section.append(header);
    const analysisPurpose = text(analysis.purpose).toLowerCase();
    if (analysisPurpose) {
      const purpose = document.createElement("p"); purpose.className = "ops-photo-analysis-purpose";
      purpose.textContent = `Analysis purpose: ${photoPurposeLabel(analysisPurpose)}`; section.append(purpose);
    }
    const observation = document.createElement("p"); observation.className = "ops-photo-analysis-observation";
    const observationLabel = document.createElement("strong"); observationLabel.textContent = "Visible finding: ";
    observation.append(observationLabel, document.createTextNode(status === "COMPLETE" ? photoAnalysisSummary(analysis) : "No visible observation was returned.")); section.append(observation);
    renderPhotoChecks(section, analysis);
    const actionCode = nextAction.code || recommendation.code;
    const actionMessage = nextAction.message || recommendation.message;
    if (actionMessage) {
      const action = document.createElement("p"); action.className = "ops-photo-analysis-recommendation";
      const actionLabel = document.createElement("strong"); actionLabel.textContent = `Next action${actionCode ? ` · ${pretty(actionCode)}` : ""}: `;
      action.append(actionLabel, document.createTextNode(actionMessage)); section.append(action);
    }
    const nextPhoto = firstText(assessment, ["next_photo"]);
    if (status === "COMPLETE" && nextPhoto) {
      const guidance = document.createElement("p"); guidance.className = "ops-photo-analysis-note";
      const guidanceLabel = document.createElement("strong"); guidanceLabel.textContent = recommendation.code === "RETAKE" ? "Retake guidance: " : "Suggested next photo: ";
      guidance.append(guidanceLabel, document.createTextNode(nextPhoto)); section.append(guidance);
    }
    if (nextAction.suggestedPurpose) {
      const purpose = document.createElement("p"); purpose.className = "ops-photo-analysis-note";
      purpose.textContent = `Suggested next photo purpose: ${photoPurposeLabel(nextAction.suggestedPurpose)}`; section.append(purpose);
    }
    if (recommendation.labelLotConflict) {
      const conflict = document.createElement("p"); conflict.className = "ops-photo-analysis-note";
      conflict.textContent = recommendation.imageLabelLot
        ? `Photo label lot ${recommendation.imageLabelLot} differs from the selected ERP lot; the operator selection remains in force.`
        : "The photo label differs from the selected ERP lot; the operator selection remains in force.";
      section.append(conflict);
    }
    const details = document.createElement("details"); details.className = "ops-photo-analysis-details";
    const detailsSummary = document.createElement("summary"); detailsSummary.textContent = "View observation details"; details.append(detailsSummary);
    const richObservation = document.createElement("p"); richObservation.className = "ops-photo-analysis-observation";
    const richObservationLabel = document.createElement("strong"); richObservationLabel.textContent = "Observation detail: ";
    richObservation.append(richObservationLabel, document.createTextNode(status === "COMPLETE" ? photoAnalysisObservation(analysis) : "No visible observation was returned.")); details.append(richObservation);
    const recommendationNode = document.createElement("p"); recommendationNode.className = "ops-photo-analysis-recommendation";
    const recommendationLabel = document.createElement("strong"); recommendationLabel.textContent = `Recommendation${recommendation.code ? ` · ${pretty(recommendation.code)}` : ""}: `;
    recommendationNode.append(recommendationLabel, document.createTextNode(recommendation.message)); details.append(recommendationNode);
    const scope = document.createElement("p"); scope.className = "ops-photo-analysis-scope";
    const scopeLabel = document.createElement("strong"); scopeLabel.textContent = historical ? "ERP link at analysis: " : "ERP link: ";
    const linkedLot = firstText(analysis, ["linked_lot"]);
    const linkage = firstText(analysis, ["linkage_source"]).toUpperCase();
    const purpose = text(analysis.purpose).toLowerCase();
    const linkedQuantity = purpose === "label" || purpose === "detail" ? "" : ` · ${photoLinkedQuantityText(analysis, next)}`;
    scope.append(scopeLabel, document.createTextNode(linkage === "OPERATOR_SELECTED" && linkedLot
      ? `Operator-selected lot ${linkedLot}${linkedQuantity}`
      : "No operator-selected ERP lot was linked.")); details.append(scope);
    const note = document.createElement("p"); note.className = "ops-photo-analysis-note";
    note.textContent = "Visible evidence only · hidden contents, dimensions, and quality clearance are not inferred; no stock update occurred.";
    details.append(note);
    renderPhotoAnalysisEvidence(details, analysis);
    section.append(details);
    parent.append(section); return section;
  }

  function renderPhotoPreview(src, alt, caption) {
    const preview = $("ops-photo-preview");
    if (!preview) return;
    const image = document.createElement("img"); image.src = src; image.alt = alt;
    const note = document.createElement("span"); note.textContent = caption;
    preview.replaceChildren(image, note); preview.hidden = false;
  }

  function selectExistingPhoto(photo, next) {
    if (photoAnalysisPending || processingEvent) return;
    const attachmentId = text(photo?.attachment_id);
    if (!attachmentId) return;
    resetSelectedPhoto();
    selectedPhotoAttachmentId = attachmentId;
    const analysis = isRecord(photo?.analysis) ? photo.analysis : null;
    selectedPhotoLot = text(analysis?.linkage_source).toUpperCase() === "OPERATOR_SELECTED"
      ? firstText(analysis, ["linked_lot"])
      : "";
    selectedPhotoPurpose = ["overview", "label", "detail"].includes(text(analysis?.purpose).toLowerCase())
      ? text(analysis.purpose).toLowerCase()
      : "overview";
    selectedPhotoSupersedesAttachmentId = "";
    renderPhotoPreview(
      `${API_PATH}/photo?id=${encodeURIComponent(attachmentId)}`,
      "Attached case receiving photo; visible evidence only",
      "Existing case photo selected · ready to review or retry analysis.",
    );
    renderPhotoIntake(next || projection);
    document.querySelector(".ops-photo-intake-link")?.click();
  }

  function startPhotoReshoot() {
    if (photoAnalysisPending || processingEvent) return;
    const input = $("ops-photo-file");
    if (!input || input.disabled) return;
    const lot = selectedPhotoLot;
    const supersedes = selectedPhotoAttachmentId;
    resetSelectedPhoto();
    selectedPhotoLot = lot;
    selectedPhotoSupersedesAttachmentId = supersedes;
    renderPhotoIntake(projection);
    input.click();
  }

  function renderPhotoLotOptions(next) {
    const select = $("ops-photo-lot");
    if (!select) return;
    const lots = Array.isArray(next?.lots) ? next.lots.filter(isRecord) : [];
    const option = document.createElement("option"); option.value = "";
    option.textContent = lots.length ? "Choose a current ERP lot…" : "No current ERP lots supplied";
    select.replaceChildren(option);
    lots.forEach((lot) => {
      const value = photoLotIdentifier(lot);
      if (!value) return;
      const item = document.createElement("option"); item.value = value;
      const quantityValue = photoLotQuantity(lot);
      item.textContent = finite(quantityValue)
        ? `${value} · ${formatNumber(quantityValue)} received ${displayUnit(next?.quantities?.uom)} in ERP`
        : value;
      select.append(item);
    });
    const valid = [...select.options].some((item) => item.value === selectedPhotoLot);
    if (!valid) selectedPhotoLot = "";
    select.value = selectedPhotoLot;
    select.disabled = !photoAnalysisEnabled(next) || next?.available !== true || photoAnalysisPending || !lots.length;
  }

  function setPhotoAnalysisFeedback(message, tone = "") {
    photoAnalysisFeedback = { message: text(message), tone };
    const feedback = $("ops-photo-analysis-feedback");
    if (!feedback) return;
    feedback.className = `ops-feedback${tone ? ` is-${tone}` : ""}`;
    feedback.textContent = photoAnalysisFeedback.message;
  }

  function renderPhotoPurpose(next) {
    const select = $("ops-photo-purpose");
    const guidance = $("ops-photo-purpose-guidance");
    if (!select) return;
    if (!["overview", "label", "detail"].includes(selectedPhotoPurpose)) selectedPhotoPurpose = "overview";
    select.value = selectedPhotoPurpose;
    select.disabled = photoAnalysisPending || next?.available !== true || !photoAnalysisEnabled(next) || !sourceState?.hidden;
    if (guidance) guidance.textContent = photoPurposeGuidance(selectedPhotoPurpose);
  }

  function renderPhotoIntake(next) {
    renderPhotoPurpose(next);
    renderPhotoLotOptions(next);
    const input = $("ops-photo-file");
    const button = $("ops-photo-analyze");
    const feedback = $("ops-photo-analysis-feedback");
    const reshoot = $("ops-photo-reshoot");
    const enabled = photoAnalysisEnabled(next);
    const hasPhoto = Boolean(selectedPhoto || selectedPhotoAttachmentId);
    const selectedAttachment = selectedPhotoAttachmentId
      ? photoAttachmentList(next).find((item) => text(item.attachment_id) === text(selectedPhotoAttachmentId))
      : null;
    const selectedAnalysis = isRecord(selectedAttachment?.analysis) ? selectedAttachment.analysis : null;
    const selectedStatus = photoAnalysisStatus(selectedAnalysis);
    if (input) input.disabled = photoAnalysisPending || next?.available !== true || !freshActionsAllowed(next);
    if (reshoot) reshoot.disabled = photoAnalysisPending || processingEvent || next?.available !== true || !freshActionsAllowed(next) || !sourceState?.hidden || !hasPhoto;
    if (button) {
      const label = button.querySelector("span");
      if (label) label.textContent = photoAnalysisPending
        ? "Analyzing photo…"
        : selectedStatus === "UNAVAILABLE" ? "Retry analysis" : selectedStatus === "COMPLETE" ? "Analyze again" : "Analyze photo";
      button.disabled = photoAnalysisPending || processingEvent || !enabled || next?.available !== true || !sourceState?.hidden || !hasPhoto || !selectedPhotoLot;
      if (photoAnalysisPending) button.setAttribute("aria-busy", "true"); else button.removeAttribute("aria-busy");
    }
    if (feedback) {
      const defaultMessage = !enabled
        ? "Photo analysis is not configured for this case; the attachment remains manual evidence."
        : !hasPhoto ? "Choose a JPEG or PNG photo to begin."
          : !selectedPhotoLot ? "Choose a current ERP lot to set the analysis scope."
            : "";
      feedback.className = `ops-feedback${photoAnalysisFeedback.tone ? ` is-${photoAnalysisFeedback.tone}` : ""}`;
      feedback.textContent = photoAnalysisPending ? "Analyzing photo…" : photoAnalysisFeedback.message || defaultMessage;
    }
    const result = $("ops-photo-analysis-result");
    if (result) {
      result.replaceChildren();
      result.hidden = !selectedAttachment;
      if (selectedAttachment) renderPhotoAnalysis(result, selectedAttachment, next);
    }
    const inlineReview = $("ops-photo-review-inline");
    renderPhotoReviewCard(inlineReview, next, selectedAttachment);
    const inlineDetails = $("ops-photo-review-inline-details");
    if (inlineDetails) inlineDetails.hidden = Boolean(inlineReview?.hidden);
  }

  function latestPhoto(photos) {
    const overviewPhotos = photos.filter((photo) => text(photo?.analysis?.purpose).toLowerCase() === "overview");
    const candidates = overviewPhotos.length ? overviewPhotos : photos;
    return candidates.reduce((latest, photo) => {
      if (!latest) return photo;
      const currentTime = Date.parse(text(photo.recorded_at));
      const latestTime = Date.parse(text(latest.recorded_at));
      return Number.isFinite(currentTime) && (!Number.isFinite(latestTime) || currentTime >= latestTime) ? photo : latest;
    }, null);
  }

  function renderPhotoDashboardEmpty() {
    const absence = document.createElement("div"); absence.className = "ops-photo-empty";
    const icon = document.createElement("i"); icon.className = "ph ph-camera"; icon.setAttribute("aria-hidden", "true");
    const copy = document.createElement("div");
    const title = document.createElement("strong"); title.textContent = "Check incoming photo";
    const detail = document.createElement("span"); detail.textContent = "Add a receiving photo to review the latest condition.";
    copy.append(title, detail);
    const action = document.createElement("button"); action.type = "button"; action.className = "button button-primary"; action.textContent = "Add photo";
    action.addEventListener("click", () => document.querySelector(".ops-photo-intake-link")?.click());
    absence.append(icon, copy, action);
    return absence;
  }

  function renderDashboardPhoto(photo, next) {
    const card = document.createElement("article"); card.className = "ops-photo-dashboard-card";
    const header = document.createElement("div"); header.className = "ops-photo-dashboard-header";
    const title = document.createElement("strong"); title.textContent = "Latest receiving photo";
    const status = isRecord(photo?.analysis) ? photoAnalysisStatus(photo.analysis) : "NOT_ANALYZED";
    const badge = document.createElement("span"); badge.className = `state-badge state-${status === "COMPLETE" ? "cyan" : status === "UNAVAILABLE" ? "coral" : "neutral"}`;
    badge.textContent = pretty(status);
    header.append(title, badge);
    const preview = document.createElement("div"); preview.className = "ops-photo-dashboard-preview";
    const image = document.createElement("img"); image.src = `${API_PATH}/photo?id=${encodeURIComponent(text(photo.attachment_id))}`;
    image.alt = "Operator-attached receiving photo; visible evidence only"; image.loading = "lazy"; preview.append(image);
    const body = document.createElement("div"); body.className = "ops-photo-dashboard-body";
    const analysis = isRecord(photo?.analysis) ? photo.analysis : null;
    const observation = document.createElement("p"); observation.className = "ops-photo-dashboard-finding";
    if (!analysis) {
      observation.textContent = "Photo attached · ready for a visible receiving check.";
    } else if (status === "COMPLETE") {
      const assessment = isRecord(analysis.assessment) ? analysis.assessment : {};
      const condition = firstText(assessment, ["visible_condition"]);
      const visibility = firstText(assessment, ["visibility", "label_visibility", "detail_visibility"]);
      observation.textContent = [condition ? photoConditionLabel(condition) : "Visible condition recorded", visibility ? photoVisibilityLabel(visibility) : ""].filter(Boolean).join(" · ");
    } else {
      observation.textContent = "Photo analysis is unavailable; review the photo or use manual inspection.";
    }
    const action = document.createElement("button"); action.type = "button"; action.className = "button button-quiet ops-photo-dashboard-action"; action.textContent = "Review in Operations";
    action.addEventListener("click", () => selectExistingPhoto(photo, next));
    body.append(observation, action);
    card.append(header, preview, body);
    return card;
  }

  function renderPhotos(next) {
    const list = $("ops-photos-list");
    if (!list) return;
    const dashboard = document.body.dataset.opsView === "dashboard";
    setText("ops-photos-title", dashboard ? "Receiving check" : "Photo history");
    const historyToggle = $("ops-photo-history-toggle");
    if (historyToggle) historyToggle.setAttribute("aria-expanded", dashboard || document.querySelector("#ops-photos-panel.is-expanded") ? "true" : "false");
    renderPhotoIntake(next);
    const reviewCard = $("ops-photo-review-card");
    if (dashboard) {
      if (reviewCard) { reviewCard.replaceChildren(); reviewCard.hidden = true; }
    } else {
      renderPhotoReviewCard(reviewCard, next);
    }
    const photos = photoAttachmentList(next);
    setText("ops-photos-count", photos.length ? `${photos.length} photo${photos.length === 1 ? "" : "s"}` : "No photos");
    if (!photos.length) {
      if (dashboard) { list.replaceChildren(renderPhotoDashboardEmpty()); return; }
      const absence = document.createElement("div"); absence.className = "ops-evidence-absence";
      const icon = document.createElement("i"); icon.className = "ph ph-image-square"; icon.setAttribute("aria-hidden", "true");
      const copy = document.createElement("div");
      const title = document.createElement("strong"); title.textContent = "No attached receiving evidence";
      const detail = document.createElement("span"); detail.textContent = "No same-case source-backed photo is available. Image claims are not inferred.";
      copy.append(title, detail); absence.append(icon, copy); list.replaceChildren(absence); return;
    }
    if (dashboard) { list.replaceChildren(renderDashboardPhoto(latestPhoto(photos), next)); return; }
    list.replaceChildren(...photos.map((photo) => {
      const card = document.createElement("article"); card.className = "ops-photo-card";
      const preview = document.createElement("button"); preview.type = "button"; preview.className = "ops-photo-open";
      const image = document.createElement("img");
      image.src = `${API_PATH}/photo?id=${encodeURIComponent(text(photo.attachment_id))}`;
      image.alt = "Operator-attached receiving photo; visible evidence only";
      image.loading = "lazy"; preview.append(image);
      preview.setAttribute("aria-label", "Expand attached photo");
      preview.addEventListener("click", () => {
        const expanded = card.classList.toggle("is-expanded");
        preview.setAttribute("aria-label", expanded ? "Collapse attached photo" : "Expand attached photo");
      });
      const copy = document.createElement("div");
      const title = document.createElement("strong"); title.textContent = "Attached receiving evidence";
      const photoPurpose = isRecord(photo.analysis) && text(photo.analysis.purpose)
        ? ` · ${photoPurposeLabel(photo.analysis.purpose)}`
        : "";
      const linkedLot = isRecord(photo.analysis) && text(photo.analysis.linkage_source).toUpperCase() === "OPERATOR_SELECTED"
        ? firstText(photo.analysis, ["linked_lot"])
        : "";
      const linkedLotLabel = linkedLot ? ` · lot ${linkedLot}` : "";
      const supersedes = isRecord(photo.analysis) ? firstText(photo.analysis, ["supersedes_attachment_id"]) : "";
      const history = supersedes ? " · supersedes prior photo" : "";
      const detail = document.createElement("small"); detail.textContent = isRecord(photo.analysis)
        ? `Case photo · ${pretty(photoAnalysisStatus(photo.analysis) || "analysis status unavailable")}${photoPurpose}${linkedLotLabel}${history} · attachment record ${formatDate(photo.recorded_at)}`
        : `Case photo · ${text(photo.interpretation) === "NOT_ANALYZED" ? "not analyzed" : "status unavailable"} · attachment record ${formatDate(photo.recorded_at)}`;
      const review = document.createElement("button"); review.type = "button"; review.className = "button button-quiet ops-photo-review";
      review.textContent = "Review / retry this photo";
      review.disabled = photoAnalysisPending || processingEvent;
      review.addEventListener("click", () => selectExistingPhoto(photo, next));
      copy.append(title, detail, review); card.append(preview, copy); renderPhotoAnalysis(card, photo, next); return card;
    }));
  }

  function resetSelectedPhoto({ clearInput = true } = {}) {
    selectedPhoto = null;
    selectedPhotoAttachmentId = "";
    selectedPhotoLot = "";
    selectedPhotoSupersedesAttachmentId = "";
    photoAnalysisFeedback = { message: "", tone: "" };
    if (photoPreviewUrl) URL.revokeObjectURL(photoPreviewUrl);
    photoPreviewUrl = "";
    const input = $("ops-photo-file"); if (input && clearInput) input.value = "";
    const lot = $("ops-photo-lot"); if (lot) lot.value = "";
    const preview = $("ops-photo-preview"); if (preview) { preview.hidden = true; preview.replaceChildren(); }
  }

  function attachmentId() {
    if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
    throw new Error("This browser cannot create an attachment ID.");
  }

  async function uploadSelectedPhoto() {
    if (!freshActionsAllowed(projection)) throw new Error("Fresh event controls are disabled for this retained operation.");
    if (selectedPhotoAttachmentId) return selectedPhotoAttachmentId;
    if (!selectedPhoto) return "";
    const file = selectedPhoto;
    if (!/image\/(jpeg|png)/.test(file.type)) throw new Error("Choose a JPEG or PNG photo.");
    if (file.size <= 0 || file.size > 5_000_000) throw new Error("Choose a photo smaller than 5 MB.");
    const bytes = new Uint8Array(await file.arrayBuffer());
    let binary = "";
    for (let offset = 0; offset < bytes.length; offset += 0x8000) {
      binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
    }
    const encoded = btoa(binary);
    const id = attachmentId();
    const response = await requestJSON(`${API_PATH}/photo`, {
      method: "POST", body: JSON.stringify({ attachment_id: id, image: encoded, media_type: file.type }),
    });
    selectedPhotoAttachmentId = id;
    const next = unwrapProjection(response); if (next) renderProjection(next);
    renderPhotoPreview(
      `${API_PATH}/photo?id=${encodeURIComponent(id)}`,
      "Saved case receiving photo; visible evidence only",
      "Saved to this case · ready to review or analyze.",
    );
    return id;
  }
  async function analyzeSelectedPhoto() {
    if (photoAnalysisPending) return;
    const source = projection;
    if (!photoAnalysisEnabled(source)) {
      setPhotoAnalysisFeedback("Photo analysis is not configured for this case.", "error"); return;
    }
    if (!source?.available || !sourceState?.hidden || !freshActionsAllowed(source)) {
      setPhotoAnalysisFeedback("Photo analysis is unavailable from the current ERP case.", "error"); return;
    }
    if (!selectedPhoto && !selectedPhotoAttachmentId) {
      setPhotoAnalysisFeedback("Choose a JPEG or PNG photo before analyzing.", "error"); return;
    }
    const lot = text(selectedPhotoLot || $("ops-photo-lot")?.value);
    if (!lot) {
      setPhotoAnalysisFeedback("Choose a current ERP lot to set the analysis scope.", "error"); return;
    }
    selectedPhotoLot = lot;
    photoAnalysisPending = true;
    setPhotoAnalysisFeedback("Analyzing photo…");
    renderPhotoIntake(source);
    try {
      const attachmentId = await uploadSelectedPhoto();
      const request = {
        attachment_id: attachmentId,
        lot,
        purpose: ["overview", "label", "detail"].includes(selectedPhotoPurpose) ? selectedPhotoPurpose : "overview",
      };
      if (selectedPhotoSupersedesAttachmentId) request.supersedes_attachment_id = selectedPhotoSupersedesAttachmentId;
      const response = await requestJSON(`${API_PATH}/analyze-photo`, {
        method: "POST",
        body: JSON.stringify(request),
      });
      selectedPhotoSupersedesAttachmentId = "";
      const next = unwrapProjection(response);
      if (next) renderProjection(next);
      const analysis = photoAnalysisFor(projection, attachmentId);
      const status = photoAnalysisStatus(analysis);
      if (status === "COMPLETE") setPhotoAnalysisFeedback("Photo analyzed. Review the visible observation and recommendation below; no stock update occurred.", "success");
      else if (status === "UNAVAILABLE") setPhotoAnalysisFeedback(photoRecommendation(analysis).message || "Photo analysis is unavailable. Retry the analysis or use manual inspection.", "error");
      else setPhotoAnalysisFeedback("The analysis response did not include a completed observation. Retry the analysis.", "error");
    } catch (error) {
      setPhotoAnalysisFeedback(error.message || "Photo analysis could not be completed from the current case.", "error");
    } finally {
      photoAnalysisPending = false;
      renderPhotoIntake(projection);
    }
  }
  function updateAskButton() {
    const button = $("ops-ask-submit");
    if (button) button.disabled = asking || !projection?.available || !sourceState?.hidden;
  }
  function setAskFeedback(message) {
    const form = $("ops-ask-form");
    let node = $("ops-ask-feedback");
    if (!node && !message) return;
    if (!node && form?.parentNode) {
      node = document.createElement("span");
      node.id = "ops-ask-feedback";
      node.className = "ops-feedback is-error";
      node.setAttribute("role", "status");
      node.setAttribute("aria-live", "polite");
      node.setAttribute("aria-atomic", "true");
      node.style.display = "block";
      node.style.marginTop = "7px";
      form.parentNode.insertBefore(node, form.nextSibling);
    }
    if (node) {
      node.hidden = !message;
      node.textContent = message || "";
    }
  }
  function showAskValidation() {
    setAskFeedback("Enter a question before asking.");
    const input = $("ops-question");
    if (input) {
      input.setAttribute("aria-invalid", "true");
      const describedBy = text(input.getAttribute("aria-describedby"));
      const ids = describedBy ? describedBy.split(/\s+/).filter(Boolean) : [];
      if (!ids.includes("ops-ask-feedback")) ids.push("ops-ask-feedback");
      input.setAttribute("aria-describedby", ids.join(" "));
      input.focus();
    }
  }
  function clearAskValidation() {
    const input = $("ops-question");
    input?.removeAttribute("aria-invalid");
    if (input) {
      const ids = text(input.getAttribute("aria-describedby"))
        .split(/\s+/).filter((id) => id && id !== "ops-ask-feedback");
      if (ids.length) input.setAttribute("aria-describedby", ids.join(" "));
      else input.removeAttribute("aria-describedby");
    }
    setAskFeedback("");
  }
  function setFeedback(message, tone = "") {
    const node = $("ops-event-feedback"); node.className = `ops-feedback${tone ? ` is-${tone}` : ""}`; node.textContent = message;
  }

  function createPendingAllocationRetryId() {
    const cryptoApi = typeof globalThis !== "undefined" ? globalThis.crypto : null;
    if (cryptoApi && typeof cryptoApi.randomUUID === "function") return cryptoApi.randomUUID();
    throw new Error("Pending allocation review is unavailable because this browser cannot create a request ID.");
  }

  function setAllocationFeedback(message, tone = "", context = {}) {
    allocationFeedback = {
      caseId: text(context.caseId) || text(projection?.case_id),
      pendingEventId: text(context.pendingEventId) || pendingAllocationEligibility(projection).pending_event_id,
      message: text(message),
      tone,
    };
    updatePendingAllocationAction(projection);
  }

  function updatePendingAllocationAction(next = projection) {
    const shell = $("ops-pending-allocation-action");
    const button = $("ops-reselect-pending-allocation");
    const feedback = $("ops-allocation-feedback");
    if (!shell || !button) return;
    const panel = $("ops-contract-panel");
    const actionState = pendingAllocationActionState(next, pendingAllocationAction, {
      sourceReady: Boolean(sourceState?.hidden),
      panelVisible: Boolean(panel && !panel.hidden),
    });
    shell.hidden = !actionState.eligible;
    button.disabled = actionState.disabled;
    const label = button.querySelector("[data-allocation-action-label]");
    if (label) label.textContent = actionState.label;
    if (feedback) {
      const showFeedback = Boolean(allocationFeedback && allocationFeedback.caseId === text(next?.case_id));
      feedback.hidden = !showFeedback;
      feedback.className = `ops-feedback ops-allocation-feedback${showFeedback && allocationFeedback.tone ? ` is-${allocationFeedback.tone}` : ""}`;
      feedback.textContent = showFeedback ? allocationFeedback.message : "";
    }
  }

  function syncPendingAllocationState(next, caseChanged = false) {
    const eligibility = pendingAllocationEligibility(next);
    if (caseChanged) {
      pendingAllocationAction = null;
      allocationFeedback = null;
      return;
    }
    if (pendingAllocationAction && pendingAllocationAction.caseId !== text(next?.case_id)) pendingAllocationAction = null;
    if (pendingAllocationAction && eligibility.status === "PENDING" && eligibility.pending_event_id
      && pendingAllocationAction.pendingEventId !== eligibility.pending_event_id) pendingAllocationAction = null;
    if (pendingAllocationAction && !pendingAllocationAction.inFlight && eligibility.status !== "PENDING") pendingAllocationAction = null;
    if (allocationFeedback && allocationFeedback.caseId !== text(next?.case_id)) allocationFeedback = null;
    if (allocationFeedback && eligibility.status === "PENDING" && eligibility.pending_event_id
      && allocationFeedback.pendingEventId && allocationFeedback.pendingEventId !== eligibility.pending_event_id) allocationFeedback = null;
  }

  async function reviewPendingAllocation() {
    const source = projection;
    const eligibility = pendingAllocationEligibility(source);
    if (!source?.available || !freshActionsAllowed(source) || !sourceState?.hidden || !eligibility.eligible
      || contractPanelState(source.feasible_allocation_plan, source.allocation_decision) !== "PENDING") return;
    let action = pendingAllocationAction;
    const sameAction = action
      && action.caseId === text(source.case_id)
      && action.pendingEventId === eligibility.pending_event_id;
    if (!sameAction) {
      try {
        action = {
          caseId: text(source.case_id),
          pendingEventId: eligibility.pending_event_id,
          retryId: createPendingAllocationRetryId(),
          inFlight: false,
        };
        pendingAllocationAction = action;
      } catch (error) {
        setAllocationFeedback(error.message || "Pending allocation review is unavailable.", "error", {
          caseId: text(source.case_id), pendingEventId: eligibility.pending_event_id,
        });
        return;
      }
    }
    if (action.inFlight) return;
    const request = pendingAllocationRequest(source, action.retryId);
    if (!request) {
      setAllocationFeedback(`Pending allocation review is unavailable from the ${erpEvidenceSourceLabel(source?.evidence_mode)}.`, "error", {
        caseId: action.caseId, pendingEventId: action.pendingEventId,
      });
      return;
    }
    action.inFlight = true;
    updatePendingAllocationAction(source);
    let requestError = null;
    try {
      const response = await requestJSON(`${API_PATH}/reselect-pending-allocation`, {
        method: "POST",
        body: JSON.stringify(request),
      });
      const responseProjection = unwrapProjection(response);
      if (responseProjection) renderProjection(responseProjection);
    } catch (error) {
      requestError = error;
    }
    const sourceRefresh = await refresh({ silent: true });
    if (requestError) {
      const detail = requestError.status
        ? `Pending allocation review was rejected: ${requestError.message || "the source rejected the request"}.`
        : "Pending allocation review could not be confirmed. The same request ID will be reused if you retry.";
      setAllocationFeedback(
        sourceRefresh === false ? `${detail} Source refresh also failed.` : detail,
        "error",
        { caseId: action.caseId, pendingEventId: action.pendingEventId },
      );
    } else {
      const outcome = allocationReviewOutcome(projection, action.retryId);
      setAllocationFeedback(
        sourceRefresh === false ? `${outcome.message} Source refresh failed; retry the source connection before continuing.` : outcome.message,
        outcome.tone,
        { caseId: action.caseId, pendingEventId: action.pendingEventId },
      );
    }
    if (pendingAllocationAction === action) {
      action.inFlight = false;
      const outcomeStatus = requestError ? "" : allocationReviewOutcome(projection, action.retryId).status;
      if (!shouldRetainPendingAllocationRetry(requestError, outcomeStatus)) pendingAllocationAction = null;
    }
    updatePendingAllocationAction(projection);
  }

  function renderProjection(value, { skipConversation = asking, resetEventFields = false } = {}) {
    const normalized = normalizeProjection(value);
    const retained = retainConversationProjection(normalized, retainedConversation);
    const next = retained.projection;
    retainedConversation = retained.memory;
    const previousCaseId = projection?.case_id;
    const caseChanged = Boolean(previousCaseId && next.case_id && previousCaseId !== next.case_id);
    syncPendingAllocationState(next, caseChanged);
    projection = next;
    if (next.available) {
      lastProjectionAt = new Date().toISOString();
    }
    renderRefreshState();
    document.body.dataset.operationsState = next.available ? "ready" : "disabled";
    renderHeaderIncidentState(next);
    setText("ops-case-label", purchaseOrderDisplay(next) || next.case_label || (next.available ? "Current operation" : "PO unavailable"));
    setText("ops-case-id", next.case_id || "Case identifier unavailable");
    setText("ops-case-po", purchaseOrderDisplay(next) || "Purchase order unavailable");
    const stageLabel = deliveryCompletionLabel(next) || pretty(next.stage);
    setText("ops-stage-badge", stageLabel);
    const stageBadge = $("ops-stage-badge"); stageBadge.className = `state-badge state-${statusTone(stageLabel)}`; stageBadge.textContent = stageLabel;
    setText("ops-flow-message", firstText(next, ["message", "summary"]) || "Current quantities and evidence from the source projection.");
    setText("ops-synthetic-badge", next.synthetic_input === true ? "Declared synthetic inputs" : "Native source events");
    renderHero(next);
    renderOrderValue(next);
    renderEvidenceDrawer(next);
    renderEconomicProposal(next);
    const sourceStateKind = projectionSourceState(next);
    if (!next.available) {
      voiceController?.setAnswer("");
      if (caseChanged || resetEventFields) renderTemplateFields(null);
      content.hidden = true;
      disabled.hidden = false;
      if (sourceStateKind === "SOURCE_UNAVAILABLE") {
        const sourceAlert = next.alerts.find((alert) => firstText(alert, ["code", "kind"]).toUpperCase() === "SOURCE_UNAVAILABLE");
        showSourceError(
          new Error(firstText(sourceAlert, ["message", "detail"]) || "The configured operation source did not return current facts."),
          { configuredSourceFailure: true },
        );
      } else {
        disabled.querySelector("h2").textContent = "Distributor operations are not configured";
        disabled.querySelector("p").textContent = "This workspace is waiting for its explicit case configuration. No quantities or delivery state are inferred.";
        setConnection("Disabled", "amber");
      }
      updateEventButton();
      syncFreshEventControls(next);
      updateAskButton();
      return;
    }
    disabled.hidden = true;
    content.hidden = false;
    clearSourceError();
    renderQuantities(next);
    renderStages(next);
    renderOverview(next);
    renderSignalSources(next);
    renderAgentTools(next);
    renderBenchmark(next);
    renderTemplates(next, { resetFields: resetEventFields || caseChanged });
    renderLots(next);
    renderAllocations(next);
    renderAlerts(next);
    renderHandoffs(next);
    renderDocuments(next);
    renderFinancials(next);
    renderEvents(next);
    renderPhotos(next);
    renderPreparedProposal(next);
    if (!skipConversation) renderConversation(next);
    updateEventButton();
  }

  async function requestJSON(path, options = {}) {
    const response = await fetch(path, { headers: { Accept: "application/json", "Content-Type": "application/json" }, ...options });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = firstText(payload, ["detail", "message", "error"]) || `Request failed (${response.status})`;
      const error = new Error(detail); error.status = response.status; throw error;
    }
    return payload;
  }

  async function prepareEconomicProposal(candidateId) {
    const proposal = economicProposalFrom(projection);
    const id = text(candidateId);
    const candidate = Array.isArray(proposal?.candidates)
      ? proposal.candidates.find((item) => firstText(item, ["candidate_id", "id"]) === id)
      : null;
    if (preparingEconomic) return;
    if (!economicConfigured || !proposal || projection?.available !== true || !text(projection?.case_id)) {
      setEconomicFeedback("Economic dispatch preparation is unavailable from the current case.", "error");
      return;
    }
    if (!candidate || candidate.executable !== true || !id) {
      setEconomicFeedback("This dispatch remains conditional and cannot be prepared from the current evidence.", "error");
      return;
    }
    preparingEconomic = true;
    setEconomicFeedback("Preparing this dispatch proposal for manager approval…");
    renderEconomicProposal(projection);
    try {
      const response = await requestJSON(`${API_PATH}/prepare-economic-proposal`, {
        method: "POST",
        body: JSON.stringify({ case_id: projection.case_id, selected_candidate_id: id }),
      });
      const next = economicResponseProjection(response);
      if (next) renderProjection(next);
      if (preparedProposalInResponse(response)) focusOpsTarget("ops-proposal-panel");
      setEconomicFeedback(
        preparedProposalInResponse(response)
          ? "Dispatch proposal prepared for manager approval in the existing Manager gate. No physical delivery or postage payment occurred."
          : "Economic proposal readback received. No physical delivery or postage payment occurred.",
        "success",
      );
    } catch (error) {
      setEconomicFeedback(error.message || "Economic dispatch proposal could not be prepared from the current case.", "error");
    } finally {
      preparingEconomic = false;
      renderEconomicProposal(projection);
    }
  }

  async function compareEconomicProposal() {
    if (preparingEconomic) return;
    if (!economicConfigured || !economicProposalFrom(projection) || projection?.available !== true || !text(projection?.case_id)) {
      setEconomicFeedback("Economic comparison is unavailable from the current case.", "error");
      return;
    }
    preparingEconomic = true;
    setEconomicFeedback("Comparing dispatch options with the agent…");
    renderEconomicProposal(projection);
    try {
      const response = await requestJSON(`${API_PATH}/prepare-economic-proposal`, {
        method: "POST",
        body: JSON.stringify({ case_id: projection.case_id }),
      });
      const next = economicResponseProjection(response);
      if (next) renderProjection(next);
      setEconomicFeedback("Economic comparison readback received. Choose a supported candidate to prepare it; no physical delivery or postage payment occurred.", "success");
    } catch (error) {
      setEconomicFeedback(error.message || "Economic comparison could not be read from the current case.", "error");
    } finally {
      preparingEconomic = false;
      renderEconomicProposal(projection);
    }
  }

  async function refresh({ silent = false, periodic = false } = {}) {
    if (loading) { if (!periodic) refreshQueued = true; return null; }
    loading = true;
    if (!silent && !projection) setConnection("Connecting", "cyan");
    try {
      const payload = await requestJSON(API_PATH);
      const configuredProjection = isRecord(payload?.distributor_operations) ? payload.distributor_operations : null;
      if (configuredProjection) economicConfigured = isRecord(configuredProjection.economic_proposal);
      const next = unwrapProjection(payload);
      if (!next) throw new Error("The source returned no distributor operation projection.");
      renderProjection(next);
      return true;
    } catch (error) {
      showSourceError(error);
      return false;
    } finally {
      loading = false;
      if (refreshQueued) { refreshQueued = false; void refresh({ silent: true }); }
    }
  }

  templateSelect.addEventListener("change", () => {
    if (!freshActionsAllowed(projection)) {
      templateSelect.value = "";
      renderTemplateFields(null);
      return;
    }
    const template = projection?.available_event_templates.find((item) => item.type === templateSelect.value) || null;
    renderTemplateFields(template);
  });
  $("ops-event-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (processingEvent || !selectedTemplate || !freshActionsAllowed(projection)) {
      if (!freshActionsAllowed(projection)) setFeedback("Fresh event controls are disabled for this retained operation.", "error");
      return;
    }
    processingEvent = true; updateEventButton(); setFeedback("Preparing the operator-declared event for manager approval…");
    try {
      const payload = buildEventPayload({
        type: selectedTemplate.type,
        values: readTemplateValues(),
        evidenceRef: $("ops-evidence-ref").value,
        now: new Date().toISOString(),
        eventId: typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : undefined,
        synthetic: projection?.synthetic_input === true,
      });
      const photoAttachmentId = await uploadSelectedPhoto();
      const response = await requestJSON(`${API_PATH}/prepare-proposal`, {
        method: "POST",
        body: JSON.stringify({
          proposal_id: typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : attachmentId(),
          case_id: projection.case_id,
          event: payload,
          source: "OPERATOR_DECLARED",
          ...(photoAttachmentId ? { photo_attachment_id: photoAttachmentId } : {}),
        }),
      });
      const next = unwrapProjection(response);
      if (next) renderProjection(next);
      else if (selectedTemplate) renderTemplateFields(selectedTemplate);
      const approvalFeedback = $("ops-proposal-feedback");
      if (approvalFeedback) {
        approvalFeedback.className = "ops-feedback";
        approvalFeedback.textContent = "";
      }
      setFeedback("Proposal prepared. A manager must approve this exact case revision before it can execute.", "success");
    } catch (error) {
      setFeedback(error.message || "Evidence proposal could not be prepared.", "error");
    } finally {
      processingEvent = false; updateEventButton(); renderPreparedProposal(projection);
    }
  });
  $("ops-photo-lot")?.addEventListener("change", (event) => {
    selectedPhotoLot = text(event.currentTarget.value);
    if (photoAnalysisFeedback.tone === "error") setPhotoAnalysisFeedback("");
    renderPhotoIntake(projection);
  });
  $("ops-photo-purpose")?.addEventListener("change", (event) => {
    const purpose = text(event.currentTarget.value).toLowerCase();
    selectedPhotoPurpose = ["overview", "label", "detail"].includes(purpose) ? purpose : "overview";
    renderPhotoIntake(projection);
  });
  $("ops-photo-reshoot")?.addEventListener("click", startPhotoReshoot);
  $("ops-photo-analyze")?.addEventListener("click", () => { void analyzeSelectedPhoto(); });
  $("ops-photo-file")?.addEventListener("change", (event) => {
    const file = event.target.files?.[0] || null;
    const preservedLot = selectedPhotoLot;
    const supersedes = selectedPhotoSupersedesAttachmentId;
    resetSelectedPhoto({ clearInput: false });
    selectedPhotoLot = preservedLot;
    selectedPhotoSupersedesAttachmentId = supersedes;
    if (!file) { renderPhotoIntake(projection); return; }
    if (!freshActionsAllowed(projection)) {
      setFeedback("Fresh event controls are disabled for this retained operation.", "error");
      event.target.value = "";
      renderPhotoIntake(projection);
      return;
    }
    if (!/image\/(jpeg|png)/.test(file.type) || file.size <= 0 || file.size > 5_000_000) {
      setFeedback("Choose a JPEG or PNG photo smaller than 5 MB.", "error");
      setPhotoAnalysisFeedback("Choose a JPEG or PNG photo smaller than 5 MB.", "error");
      event.target.value = "";
      renderPhotoIntake(projection); return;
    }
    selectedPhoto = file; photoPreviewUrl = URL.createObjectURL(file);
    renderPhotoPreview(photoPreviewUrl, "Selected receiving photo; visible evidence only", `${file.name || "Photo selected"} · ready to attach or analyze.`);
    renderPhotoIntake(projection);
  });
  $("ops-manager-id")?.addEventListener("input", () => renderPreparedProposal(projection));
  $("ops-approve-proposal")?.addEventListener("click", async () => {
    const proposal = preparedProposal;
    const managerId = text($("ops-manager-id")?.value);
    const retained = isRetainedEvidence(projection?.evidence_mode);
    if (!proposal || !managerId || processingEvent || (!retained && !freshActionsAllowed(projection))) return;
    processingEvent = true; renderPreparedProposal(projection);
    const feedback = $("ops-proposal-feedback"); feedback.className = "ops-feedback";
    feedback.textContent = retained
      ? "Checking retained evidence and confirming the recorded completed event…"
      : "Checking the current case and executing one approved operation…";
    try {
      const response = await requestJSON(`${API_PATH}/approve-proposal`, {
        method: "POST",
        body: JSON.stringify({ proposal_id: proposal.proposal_id, case_id: projection.case_id, state_revision: proposal.state_revision, manager_id: managerId }),
      });
      const next = economicResponseProjection(response) || unwrapProjection(response);
      preparedProposal = null;
      if (next) renderProjection(next, { resetEventFields: true });
      resetSelectedPhoto();
      feedback.className = "ops-feedback is-success";
      feedback.textContent = retained
        ? "Recorded completed event confirmed. Retained evidence and same-case readback are shown below."
        : "Manager approval recorded. Native operation result and same-case readback are shown below.";
      void refresh({ silent: true });
    } catch (error) {
      feedback.className = "ops-feedback is-error";
      feedback.textContent = retained
        ? "Recorded completion confirmation could not be recorded; retained evidence remains unchanged."
        : error.message || "Approved operation could not execute.";
    } finally {
      processingEvent = false; renderPreparedProposal(projection);
    }
  });
  $("ops-retry").addEventListener("click", () => { void refresh(); });
  $("ops-open-evidence-drawer")?.addEventListener("click", (event) => openEvidenceDrawer(event.currentTarget));
  $("ops-economic-compare")?.addEventListener("click", () => { void compareEconomicProposal(); });
  $("ops-economic-open-evidence")?.addEventListener("click", (event) => openEvidenceDrawer(event.currentTarget));
  $("ops-evidence-drawer-close")?.addEventListener("click", closeEvidenceDrawer);
  $("ops-evidence-drawer-backdrop")?.addEventListener("click", closeEvidenceDrawer);
  $("ops-evidence-drawer-open-operations")?.addEventListener("click", openFullOperationsEvidence);
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !$("ops-evidence-drawer")?.hidden) {
      event.preventDefault();
      closeEvidenceDrawer();
    }
  });
  document.querySelectorAll("[data-ops-view-link]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const view = text(link.dataset.opsViewLink) || "dashboard";
      const url = new URL(link.href, window.location.href);
      window.history.pushState({}, "", `${url.pathname}${url.search}${url.hash}`);
      setOpsView(view, { scrollTarget: text(url.hash).replace(/^#/, "") });
    });
  });
  document.querySelectorAll(".ops-overview-links a").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const target = text(link.getAttribute("href")).replace(/^#/, "");
      if (!target) return;
      focusOpsTarget(target);
    });
  });
  bindCollapsiblePanel("ops-economic-panel", "ops-economic-toggle");
  bindCollapsiblePanel("ops-benchmark-panel", "ops-benchmark-toggle");
  bindCollapsiblePanel("ops-photos-panel", "ops-photo-history-toggle");
  function syncOpsViewFromLocation() {
    const target = text(window.location.hash).replace(/^#/, "");
    setOpsView(requestedOpsView(), { scrollTarget: target });
  }
  window.addEventListener("popstate", syncOpsViewFromLocation);
  window.addEventListener("hashchange", syncOpsViewFromLocation);
  syncOpsViewFromLocation();
  function initializeVoiceControls() {
    const recognitionConstructor = window.SpeechRecognition || window.webkitSpeechRecognition;
    voiceController = createVoiceController({
      recognitionFactory: recognitionConstructor ? () => new recognitionConstructor() : null,
      speechSynthesisApi: window.speechSynthesis,
      utteranceFactory: typeof window.SpeechSynthesisUtterance === "function" ? (answer) => new window.SpeechSynthesisUtterance(answer) : null,
      input: $("ops-question"),
      setStatus: (message) => setText("ops-voice-status", message),
      dictateButton: $("ops-dictate"),
      readButton: $("ops-read-answer"),
      stopButton: $("ops-stop-reading"),
    });
    const support = voiceController.support();
    setText("ops-voice-status", support.dictation || support.reading
      ? "Optional English voice controls are ready. Dictation never sends automatically."
      : "English voice controls are unavailable in this browser. Typing remains available.");
    $("ops-dictate")?.addEventListener("click", () => voiceController.toggleDictation());
    $("ops-read-answer")?.addEventListener("click", () => voiceController.readAnswer());
    $("ops-stop-reading")?.addEventListener("click", () => voiceController.stopReading());
  }
  initializeVoiceControls();
  $("ops-question").addEventListener("input", (event) => {
    if (text(event.currentTarget.value)) clearAskValidation();
  });
  async function requestAskQuestion(question) {
    clearAskValidation();
    asking = true; $("ops-ask-submit").disabled = true; $("ops-ask-submit").textContent = "Asking…";
    const answerNode = $("ops-chat-answer"); answerNode.classList.remove("is-error");
    const waiting = document.createElement("p"); waiting.textContent = isRetainedEvidence(projection?.evidence_mode)
      ? "Reading retained accepted evidence…"
      : "Reading the current operation source…"; answerNode.replaceChildren(waiting);
    try {
      const response = await requestJSON(`${API_PATH}/ask`, { method: "POST", body: JSON.stringify({ question }) });
      const next = unwrapProjection(response);
      if (next) renderProjection(next);
      const responseProjection = next || response;
      const responseConversation = Array.isArray(responseProjection.conversation)
        ? responseProjection.conversation
        : isRecord(responseProjection.conversation) ? responseProjection.conversation : {};
      const answer = cleanAnswer(responseProjection.answer || responseProjection.answer_text || conversationAnswer(responseConversation));
      if (projection) {
        if (Array.isArray(responseConversation) && responseConversation.length) {
          projection.conversation = responseConversation;
        } else if (isRecord(responseConversation) && Object.keys(responseConversation).length) {
          projection.conversation = {
            ...(isRecord(projection.conversation) ? projection.conversation : {}),
            ...responseConversation,
            ...(answer ? { answer } : {}),
          };
        }
        if (answer && conversationAnswer(projection.conversation) !== answer) {
          projection.conversation = Array.isArray(projection.conversation)
            ? [...projection.conversation, { role: "assistant", answer }]
            : { ...(isRecord(projection.conversation) ? projection.conversation : {}), answer };
        }
        for (const key of ["conversation_status", "conversation_message", "conversation_provider", "conversation_context"]) {
          if (responseProjection[key] !== undefined) projection[key] = responseProjection[key];
        }
        const retained = retainConversationProjection(projection, retainedConversation);
        projection = retained.projection;
        retainedConversation = retained.memory;
        renderConversation(projection);
      }
      $("ops-question").value = "";
    } catch (error) {
      answerNode.classList.add("is-error");
      const message = error.message || "Read-only conversation is unavailable.";
      const paragraph = document.createElement("p"); paragraph.textContent = message; answerNode.replaceChildren(paragraph);
      if (projection?.case_id) {
        const unavailable = {
          ...projection,
          conversation: { status: "UNAVAILABLE", message },
          conversation_status: "UNAVAILABLE",
          conversation_message: message,
        };
        const retained = retainConversationProjection(unavailable, retainedConversation);
        projection = retained.projection;
        retainedConversation = retained.memory;
      }
    } finally {
      asking = false; updateAskButton(); $("ops-ask-submit").innerHTML = '<i class="ph ph-chat-circle-dots" aria-hidden="true"></i>Ask';
    }
  }
  $("ops-ask-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const questionInput = $("ops-question");
    await runAskQuestion({
      value: questionInput.value,
      asking,
      available: projection?.available === true,
      onEmpty: showAskValidation,
      request: requestAskQuestion,
    });
  });

  function startPolling() {
    if (pollTimer !== null) window.clearInterval(pollTimer);
    pollTimer = document.visibilityState === "visible" ? window.setInterval(() => void refresh({ silent: true, periodic: true }), 30000) : null;
  }
  document.addEventListener("visibilitychange", () => {
    startPolling();
    if (document.visibilityState === "visible") void refresh({ silent: true, periodic: true });
  });
  window.addEventListener("pagehide", () => { if (pollTimer !== null) window.clearInterval(pollTimer); pollTimer = null; });
  updateEventButton();
  updateAskButton();
  void refresh();
  startPolling();

  if (typeof window !== "undefined") window.Missing20DistributorOperationsState = { get projection() { return projection; }, get lastProjectionAt() { return lastProjectionAt; }, refresh };
})();
