# LogisticPilot — Devpost source of truth

Updated September 13, 2026 UTC. Restore submission 1162519 to LogisticPilot. MedGuard would need a separate qualifying entry. Saving this draft is not final submission.

## Project overview

**Name:** LogisticPilot

**Tagline:** Investigate receiving exceptions, protect affected stock, and keep eligible orders moving with evidence and verified ERP records.

**Track:** Professional Agents

**Repository:** https://github.com/danielwanwx/logisticpilot

**Built with:** Strands Agents SDK, Amazon Bedrock, Claude Opus 4.6, Python, JavaScript, CSS, ERPNext, Frappe, Airtable, Celigo, Jira, Slack, SQLite, Pydantic.

## Project story — paste into Devpost

### Inspiration

A receiving exception is rarely just a missing number. A parts distributor may have stock in its ERP, an inspection report holding one lot, customer contracts with different partial-shipment terms, and updates scattered across collaboration tools. Someone must determine which stock can move and which orders must wait.

LogisticPilot is built for that operations professional. Our question: **When an incoming lot has a shortage and a failed sample, how can the team protect affected inventory while continuing the orders that the evidence and contracts permit?**

### What it does

1. Record quantity, lot and inspection evidence with its source and time.
2. Distinguish a shortage from a quality hold, and a failed sample from a whole-lot defect claim.
3. Use a Strands agent to interpret the case and select among explicit customer-contract options.
4. Apply deterministic quantity, evidence and approval checks before supported ERP actions.
5. Read back native results and retain linked Airtable, Jira and Slack-via-Celigo handoffs.

The demonstrated case is PO20: 40 parts ordered; an initial 20-part lot, an 18-part lot with a two-part shortage and a failed sample, a declared passing whole-lot retest, and a two-part replacement. The recorded execution dispatches 20, 5, 13 and 2 parts across four shipments, fulfilling customer orders A25 and B15. The failed two-unit sample conservatively holds LOT-B; it does not prove all 18 units defective.

### How we built it

The workspace uses Python, JavaScript and CSS. Its current conversation uses Strands Agents SDK with Claude Opus 4.6 on Amazon Bedrock. The agent explains evidence and contract choices. Application code calculates quantities, validates allowed operations, binds approvals to the exact case and revision, executes bounded ERPNext demo actions, and reads back native results.

ERPNext owns inventory and document facts. Airtable and Jira retain case context; Celigo carries the Slack notification. Collaboration text is not inventory authority. The model advises, the application checks, and the operator decides through an explicit gate.

The current review workspace displays a dated, retained PO20 snapshot and makes real read-only model calls. Tool badges identify available capabilities; they are not a claim that every tool executed on every answer. Historical native execution and current retained review are documented separately. AgentCore Runtime was demonstrated in an earlier deployment; this dashboard uses direct Bedrock transport.

### Challenges we ran into

The hardest problem was preserving meaning: a failed sample versus an entirely defective lot, recorded dispatch versus physical delivery, order value versus payment, and historical completion versus a new approval.

We added source timestamps, synthetic-input labels, exact proposal/revision binding, local replay recovery and visible provider failures. A new multi-agent Graph experiment has not produced a completed held-out result. We retain its failures and do not claim a multi-agent accuracy improvement.

### Accomplishments we're proud of

The isolated PO20 workflow produced actual ERPNext receipt, inspection, release, pick, delivery-note and shipment records. A fresh read-only ERP check on September 13 corroborated 40 received and 40 dispatched, with no remaining held stock or shortage. Historical same-case readbacks include Airtable, Jira and Slack through Celigo. The restored workspace keeps the evidence inspectable and answers real questions through Strands/Bedrock.

Our contribution is the specific connection between evidence disagreement, affected inventory, contract-eligible fulfillment and checked execution. We do not claim to be the first supply-chain assistant or to replace a WMS.

### What we learned

Agent usefulness depends on making an uncertain situation understandable and reviewable. More agents are not automatically better. The useful next evaluation is whether an agent improves decisions over a rules-only baseline on unseen evidence conflicts, while respecting the same authority boundaries.

### What's next

First, finish reproducible judge access and compact decision-focused answers. Then evaluate held-out quality/contract conflicts against rules-only and single-agent baselines. A distributor pilot should measure review time, unnecessary holds, correct escalations and duplicate actions before claiming impact.

This investigate–constrain–approve–verify structure could support supplier-document or returns exceptions, but each needs its own source mapping, action policy and evaluation. Trend monitoring also needs longitudinal history and meaningful denominators; it is not a demonstrated current feature.

### Demo boundaries and provenance

All business inputs are purpose-built demo data. Inspections and carrier confirmations are declared synthetic records, not independent physical inspection or customer-receipt proof. The illustrative photo is manually attached, not analyzed. PO20 has a USD160 purchase-order value and USD150/USD90 customer-order values; we claim no payment, revenue or production impact. Missing linked invoices do not rule out advance payments.

LogisticPilot was formerly The Missing 20: the same project with retained Git history, whose initial repository commit is dated August 24, 2026. Third-party libraries and photo fixtures retain their licenses and attribution. See the current claim manifest and dated audits for exact evidence boundaries.

## Testing instructions

Read README.md and docs/submission/current-claim-manifest.md in the public repository. The current product is /operations, described in docs/runbooks/current-operations.md. It requires authorized private ERPNext and Bedrock connections, a matching case configuration and runtime journal. A clean clone does not include those records. A free judge-access route has not yet been verified; these notes are not complete judging access.

In the configured retained workspace, inspect Dashboard quantities and source timestamps, open the evidence drawer, and ask: "Did the failed sample prove all 18 parts defective?" or "Does no linked invoice prove there was no advance payment?" Answers are real Strands/Bedrock calls over retained evidence. Fresh operations are disabled. The older make judge-demo checks a separate historical evidence path, not a fresh PO20 execution.

## Assets and remaining release fields

- Architecture: docs/architecture/logisticpilot-submission.png, with SVG source beside it. It distinguishes historical native execution from current retained review and separately proven AgentCore.
- Gallery: actual dashboard, investigation, evidence drawer and mobile screenshots from dated audits.
- Reviewed local film: logisticpilot-final-proof-gap-fixed-264.1s.mp4, 264.20 seconds; see [film review](video-v1/SOL-FINAL-FILM-REVIEW.md). Public YouTube/Vimeo URL still required.
- Public demo: not verified. Localhost is not judge access.
- Entrant certifications and final Submit: uncompleted.

## Supporting records

- [Current claim manifest](current-claim-manifest.md)
- [Award-readiness review](../audits/2026-09-13-award-readiness.md)
- [Independent closure review](../audits/2026-09-13-independent-closure-review.md)
- [Official dual-entry rules](../research/2026-09-13-multiple-submissions-rules.md)
