# Independent closure review — PO20, retained runtime, and public claims

**Date:** September 13, 2026

**Method:** Read-only review of the repository's public artifacts, implementation, and
dated audits. No browser, provider, ERP, private-runtime, or external-system access
was used for this review. It therefore assesses what the recorded evidence supports;
it does not recertify any external record or public submission.

## Decision

The evidence supports a **bounded historical PO20 demo operation** and a separate,
**read-only retained-evidence workspace**. It does not support describing the current
workspace as a live execution of the PO20 operation, or treating a retained agent
answer as a new cross-system readback.

The strongest defensible public statement is:

> In an isolated demo, the recorded PO20 workflow received and dispatched 40 parts,
> allocated A25/B15, and recorded synthetic delivery confirmations. The current
> workspace inspects retained evidence and can answer about that record without
> changing it. The demo does not prove physical customer receipt, invoice payment,
> revenue recognition, production reliability, or a multi-agent accuracy gain.

That conclusion is narrower than a release or award judgment. A passing test suite,
an implementation review, or the local-film review does not establish award
readiness, public publication, or general operational reliability.

## Evidence boundary and source hierarchy

The sources have different scopes and should not be used interchangeably.

| Evidence line | What it can support | What it cannot support |
| --- | --- | --- |
| [PO20 rehearsal ledger](../submission/video-v1/REHEARSAL-V2.md) and [PO20 journal review](../submission/video-v1/SOL-REVIEW-V2.md) | The documented historical PO20 sequence, named records, manager-attributed local events, same-case application readbacks, and declared final quantities. | A fresh independent read today; continuous capture of every transition; independently authenticated human identity; physical delivery. |
| [September 12 runtime restoration](2026-09-12-runtime-restoration.md) | A fresh read-only ERP observation of 40 received / 40 dispatched and A25/B15 before and after inspection; retained-mode source labeling and no-write behavior. | That the retained agent performed a fresh source read for every answer or re-executed the PO20 workflow. |
| [Opus restoration](2026-09-12-opus-restoration.md) | Three retained-evidence, read-only Opus answers with correct important distinctions and explicit provider selection. | Population accuracy, a Nova comparison, or a live cross-app tool trace for those turns. |
| [Receiving-evals development record](2026-09-12-receiving-evals-development.md) | Honest stopped development usage, failed structured-output boundaries, and budget accounting. | A completed decision, held-out result, Graph benefit, or multi-agent improvement. |
| [September 7 hero manifest](../../artifacts/audits/2026-09-07-current-hero-proof.json) | A real native historical execution with a delivery note, sales invoice, and USD 42,000 billed in its named case. | Any PO20 receipt, dispatch, invoice, payment, or revenue fact. Its case is `M20-ECU-2026-00011-LOT-A`, not PO20. |
| [Operations adapter](../../src/the_missing_20/adapters/distributor_operations.py) | The application design: exact proposal/case/revision binding, durable event identity, retained-mode marking, and preservation of non-success outcomes. | That a particular external action occurred; implementation alone is not execution evidence. |

The local [final film review](../submission/video-v1/SOL-FINAL-FILM-REVIEW.md) reports a
reviewed film and preserves the synthetic-delivery/finance limits. It also explicitly
says that a public upload, Devpost preview, attestation, and submission are pending.
That is presentation evidence, not a substitute for the native operation record.

## What the historical PO20 record supports

The following assessment preserves the difference between a documented historical
operation and the later retained UI.

| Portion of the loop | Supported historical record | Honest claim boundary |
| --- | --- | --- |
| Receiving and shortage | `MAT-PRE-2026-00019`, `MAT-PRE-2026-00020`, and `MAT-PRE-2026-00021` are named in the V2 rehearsal: 20, then 18 of 20, then a 2-part replacement. | These are declared demo receipt facts and historical native-readback claims. They do not prove a physical carton count outside the isolated demo. |
| Quality hold and release | The rehearsal names the failed sample / hold path for LOT-B18, whole-lot retest `MAT-QA-2026-00016`, and release `MAT-STE-2026-00017`; it explicitly rejects treating the sample failure as proof all 18 units were defective. | Measurement reports are declared records. Neither the model nor this review performed a physical inspection or establishes a per-unit measurement distribution. |
| Contract allocation | The rehearsal records three real Bedrock Opus contract selections: A20, then A5/B13, then B2. The code calculates and validates allowable quantities outside the model. | This supports a bounded advisory-plus-deterministic selection path. It is not a held-out accuracy result or proof that the same contract choice is generally correct. |
| Dispatch and allocation | Delivery notes `MAT-DN-2026-00018` through `MAT-DN-2026-00021` and Shipments 16–19 carry 20, 5, 13, and 2, totaling A25/B15. The V2 journal review reports 19 event IDs and distinct proposal-to-event links. | It supports the recorded native-document and local-journal sequence. It does not establish a carrier's or customer's independent delivery result. |
| Delivery evidence | The final PO20 projection is recorded as 40 **synthetic** delivery confirmations. | Do not say customers physically received the parts, that carrier proof-of-delivery was independently verified, or that delivery was externally confirmed. |
| Cross-app readback | The V2 rehearsal records an Airtable record, Jira `QRC-5`, and a Slack update through Celigo with matching final quantities. | These are historical same-case readback claims. The retained runtime does not make their current availability or content a fresh fact unless it executes and displays a new source call. |
| Human authority | The PO20 journal review reports manager/timestamp attribution for the durable local proposals; the adapter requires an exact proposal, case, revision, and `manager_id`. | This proves an application-level recorded approval boundary, not a separately verified enterprise identity, employment role, or independent human intent. |
| Replay behavior | The journal review found unique PO20 event IDs and no duplicate local event/proposal result; the adapter rejects a reused event ID with different canonical payload and preserves `BLOCKED`/`UNKNOWN_OUTCOME`. | Say “no duplicate was found in this local journal” or “exact local replay is guarded.” Do not claim end-to-end exactly-once behavior across ERP, Celigo, Slack, Airtable, Jira, or arbitrary provider failures. |
| Finance | PO20 is documented as PO USD 160, customer orders USD 150 and USD 90, `To Bill`, and USD 0 advance; no PO20 invoice was created. | Do not call order value revenue, billed revenue, payment, cash collection, or order-to-cash. USD 42,000 and `ACC-SINV-2026-00006` belong only to the separate September 7 case. |

The V2 journal review is appropriately explicit that its own local-database inspection
does not establish the separate browser conversation, SaaS views, or an AWS invocation
trace. That limitation should remain visible rather than being collapsed into one
unqualified “full loop” claim.

## Is the current loop provable?

**Partly, with an important split:**

- The current end-state scalar facts are supported by the September 12 fresh,
  read-only ERP observation: 40 received, 40 dispatched, A25/B15, with no business
  record change during inspection.
- The historical PO20 operation is supported as a documented demo sequence by the
  rehearsal, the bounded local-journal audit, and the recorded same-case readbacks.
- The current browser runtime is supported as a retained, no-write inspection and
  reasoning surface. The reviewed retained turns use a supplied source snapshot and
  can have zero additional source-tool calls; capability labels are not evidence that
  every connected tool was called in that turn.

The complete causal loop is therefore **not independently provable from the current
retained UI alone**. A viewer needs the historical operation evidence for receipt,
quality, approvals, native document creation, and cross-app readback; the UI is useful
for inspecting that history, not for converting it into a new live execution.

## Material claim risks before restoring Devpost copy

### P0 — no canonical current claim ledger

Several linked documents identify themselves as current while describing different
cases or a superseded runtime state. The top of
[`finalization-tracker.md`](../submission/finalization-tracker.md) still describes a
Bedrock access denial even though the later same-day
[Opus restoration](2026-09-12-opus-restoration.md) records an explicit successful
Opus path. The [evidence matrix](../submission/evidence-matrix.md) remains a
September 9, 20-unit/USD 42,000 historical snapshot, and
[known limitations](../submission/known-limitations.md) presents PO18 as its current
40-part loop.

This is a documentation-governance blocker for public copy: a judge following the
README's “current ledger” link can receive contradictory answers about the case,
model availability, and current scope. It is not evidence that the PO20 records are
wrong.

### P1 — historical cases are easy to blend into PO20

The repository contains at least three similarly shaped evidence lines: the September
7 `M20-ECU-2026-00011-LOT-A` billed 20-unit case, PO18/older 40-part work, and PO20.
The README does label the USD 42,000 evidence separately, which is good. Any Devpost
or video sentence that places “20/20 delivered,” “USD 42,000 billed,” an invoice, or
“order-to-cash” beside PO20 without naming the September 7 case would be misleading.

### P1 — delivery and finance wording must remain deliberately narrow

PO20’s delivery confirmations are synthetic, and its current commercial facts are
order values with `To Bill` status and zero advance paid. Claims such as “customers
received,” “delivery verified,” “payment collected,” “revenue generated,” or “closed
the order-to-cash loop” exceed the recorded PO20 evidence.

### P1 — evaluation and multi-agent claims are not ready for promotion

The current development record reports zero completed model decisions in the stopped
Nova starts and no held-out case or Graph coordinator result in V8. It follows that
phrases such as “multi-agent workflow outperformed,” “evaluated agent,” or “Graph
validated” should be removed from PO20-facing public copy unless they are explicitly
limited to the separate historical bounded September 6 result with its own case set
and denominator.

### P2 — authority and replay claims need their exact scope

“Manager approved” is supported as a recorded application gate tied to a manager
identifier, proposal, case, and revision. It is not proof of an independently
authenticated enterprise actor. “Replay-safe” is supported for the local event ledger
and exact input identity, not a blanket proof of external exactly-once delivery.

### P2 — film and trace claims need exact nouns

The final local-film review says the film passed its review, while the earlier SOL
review correctly distinguishes an application invocation trace from a verified exact
Bedrock request correlation. Use “application trace” unless an actual correlated
provider trace is visible. Do not say the local film is uploaded, submitted, or
publicly playable until those external facts exist.

## Concrete closure work, in priority order

1. **Publish one PO20 claim manifest before restoring Devpost text.** Put case ID,
   record IDs, source mode, evidence date, and “may say / must not say” beside each
   claim. Make it the only current-link target from the README, Devpost draft, and
   finalization tracker.
2. **Mark or archive stale current-facing documents.** Add a dated historical banner
   to the September 9 evidence matrix and PO18 limitations document; replace the
   stale Bedrock-denial summary in the finalization tracker with a link to the
   restoration result. Do not delete historical evidence merely to make the story
   simpler.
3. **Use PO20-only public copy.** Name `M20-DIST-COMPONENT-V2-20260910`,
   `PUR-ORD-2026-00020`, shipments 16–19, A25/B15, and “synthetic delivery
   confirmation” where needed. Keep USD 42,000/invoice language behind a clearly
   titled separate historical-example section, or omit it from Devpost entirely.
4. **Make the evidence presentation inspectable.** For the final recording or judge
   packet, show native PO20 record IDs, the manager-bound approval/event identity,
   the final readback, and the cross-app record identifiers. Label the snapshot date
   and retained mode. Do not manufacture a new incident or replay the completed case
   just for footage.
5. **Separate product evidence from evaluation evidence.** Keep the stopped
   Graph/Evals work in a development appendix. Only claim an experiment result after
   a frozen model/configuration, completed decisions, retained traces, a disclosed
   cost ledger, and independently authored held-out cases exist.
6. **Preserve a short public limitation block.** It should state: isolated demo data;
   recorded synthetic delivery; no invoice/payment/revenue claim; advisory model;
   deterministic approval/execution controls; and retained UI versus fresh source
   distinctions.

## Closure criteria for a truthful judge packet

The following can be stated today when cited to their named source: PO20’s recorded
40/40/A25/B15 final state; its named native documents and local journal; its synthetic
delivery classification; historical same-case cross-app readbacks; the retained
read-only Opus conversation; and the separate September 7 execution with its own case
identity.

The following should remain unclaimed: physical receipt, customer payment, PO20
revenue, production performance, globally exactly-once behavior, independently
authenticated human authorization, current live cross-app reconciliation from the
retained UI, model generalization, multi-agent improvement, public upload/submission,
or award readiness.

This audit recommends claim consolidation and evidence labeling, not another PO20
execution. The existing completed case should be preserved; a new externally written
recording case would require separate explicit authorization and its own evidence
chain.

## Reviewed sources

- [Repository README](../../README.md)
- [PO20 rehearsal ledger](../submission/video-v1/REHEARSAL-V2.md)
- [PO20 independent journal review](../submission/video-v1/SOL-REVIEW-V2.md)
- [Local final-film review](../submission/video-v1/SOL-FINAL-FILM-REVIEW.md)
- [Devpost draft](../submission/devpost-submission-draft.md)
- [Finalization tracker](../submission/finalization-tracker.md)
- [September 12 runtime restoration](2026-09-12-runtime-restoration.md)
- [September 12 Opus restoration](2026-09-12-opus-restoration.md)
- [September 12 receiving-evals development record](2026-09-12-receiving-evals-development.md)
- [Historical native hero manifest](../../artifacts/audits/2026-09-07-current-hero-proof.json)
- [Current operations adapter](../../src/the_missing_20/adapters/distributor_operations.py)
