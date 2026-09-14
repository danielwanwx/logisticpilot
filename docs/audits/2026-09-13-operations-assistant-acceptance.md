# Contextual Operations assistant acceptance

Approved design: [workspace and sidebar](../superpowers/specs/2026-09-13-operations-agent-sidebar-design.md).

## Baseline and scope

The authorized live demo case is `M20-DIST-ECONOMIC-REVIEW-20260913`, purchase
order `PUR-ORD-2026-00025`, sales order `SAL-ORD-2026-00019`. Before the change,
ERP readback showed received 25, usable 20, held 5, allocated 20, dispatched 0.
A prior 20-unit economic proposal was already pending approval; it is not a new
result produced by this implementation. Local baseline evidence is retained in
`/private/tmp/logisticpilot-sidebar-before.json`.

The additive assistant reads current evidence, asks for missing physical facts,
can invoke the existing photo analyzer and can prepare existing supported actions.
The model cannot approve or execute ERP operations. The existing approval and
readback path remains authoritative. Synthetic historical benchmarks are separate.

## Focused checks

Root ran eight existing/new assistant and proposal checks, plus scoped Ruff lint
and format checks. They passed. These offline checks cover missing information,
natural-language inspection drafts, numeric citation boundaries, source changes,
an old pending proposal with a newly blocked economic gate, and photo scope.
They do not establish live-model quality or ERP execution acceptance. No UI unit
tests were added.

## Live checks

| Check | Observed result |
| --- | --- |
| Existing AWS session | STS HTTP 200 using the existing demo profile |
| Restarted server ERP read | HTTP 200; 25 received / 20 usable / 5 held / 0 dispatched; 21.1 seconds |
| A1: explanation only | Real Bedrock Opus 4.6 via Strands returned COMPLETE in 31.6 seconds; correctly identified the 20-unit eligible allocation and five-unit hold; preparation NOT_REQUESTED |

A1 evidence: `/private/tmp/logisticpilot-assist-A1.json`. Its output was too long
and included internal identifiers. The assistant presentation prompt was then
tightened to default to at most 80 words in business language. A1 remains retained
as the first observed result, not replaced with a better-looking retry.

## Independent visual review

The independent reviewer inspected actual browser screenshots after the two-view
reload. Receiving/Findings/Next action and the right sidebar were visible. Remaining
issues included raw candidate/event identifiers, model-not-run explanations,
default condition prose and postage-difference spacing. Those findings were sent
to the frontend implementer. An earlier expanded evidence drawer was corrected
in the review: the latest reload starts with its details closed.

## Live continuation

- B2, through the actual browser sidebar: asking to pass LOT-B5 from its photo
  without a measurement produced a refusal and a request for the diameter and
  sample count. No quality disposition was written. The conversation survived
  switching to the Dashboard drawer and reloading.
- C1: a newly attached public P05 fixture with no identified lot produced a
  lot clarification, NOT_REQUESTED preparation, and no image analysis.
- C2: the carton-condition question selected overview and requested a retake.
  This first result is retained; it is not evidence of accurate defect detection.
  Purpose routing was then made explicit and required in the assistant schema.
- C3: one bounded repeat of the same photo/question selected detail and invoked
  the real Bedrock image reader. It returned visible-damage observations and
  REQUIRE_INSPECTION in 69.2 seconds. These are model observations, not verified
  defect labels. Neither call released the five held units.
- Browser request to prepare the cleared 20 units recognized the already-pending
  proposal. This confirms reuse, not creation of a new economic recommendation.
- The authorized demo confirmation was clicked once through the browser with
  identity `POC reviewer`. At 2026-09-14 03:32:22 UTC, native readback showed APPLIED:
  Pick List `STO-PICK-2026-00022`, Delivery Note `MAT-DN-2026-00024`, Shipment
  `SHIPMENT-00022`. Quantities changed to dispatched 20 / held 5 / allocated 0 /
  usable 0 / delivery confirmed 0. This is ERP execution in the demo tenant,
  not physical delivery, carrier booking, paid postage, invoicing or revenue.

Local response evidence: `/private/tmp/logisticpilot-assist-C1.json`,
`/private/tmp/logisticpilot-assist-C2.json`,
`/private/tmp/logisticpilot-assist-C3.json`, and
`/private/tmp/logisticpilot-sidebar-approved.json`.
The public P05 image was attached through the API; browser file-chooser upload
was not validated in this run. Fixture provenance remains in the fixture manifest.

At desktop width 1440, browser measurements confirmed the repaired three-row grid:
Receiving to Findings is 18 px, and Findings to Next action is 18 px. One Agent
panel is visible; source/model/event details start collapsed. Final acceptance
also caught stale-answer duplication during a new question and background refresh
timeouts overwriting the screen during a long approval. These were returned to
the implementer along with the newly observed execution-state copy for correction.
User visual review remains the final aesthetic acceptance.
