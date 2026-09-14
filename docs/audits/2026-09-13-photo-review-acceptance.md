# Purpose-specific receiving photo review

Date: September 13, 2026. Baseline: `e9d355f`. Backend milestone: `bfe8adc`.
Six live photo checks completed with the limitations below. UI workflow
acceptance is recorded separately; user visual approval remains pending.

## Isolated review case

`M20-DIST-ECONOMIC-REVIEW-20260913`, PO `PUR-ORD-2026-00025`,
SO `SAL-ORD-2026-00019`. Native demo dependencies were created with the existing
economic-poc provisioner after its dry plan and read-only source check.
Configuration: `/private/tmp/logisticpilot-review-config-20260913.json`.
Previous PO23 and PO24 dispatches remain separate and are not reset.

Activate only A20 receipt, its explicitly synthetic whole-lot PASS inspection,
and B5 receipt. Do not apply the provisioner's optional B5 FAIL inspection.
Expected pre-dispatch state: received25 / usable20 / held5 / dispatched0.
Receiving policy creates the five-unit hold; no photograph proves five defects.

Live setup readback confirmed received25 / usable20 / held5 / allocated20 /
dispatched0. A20 is USABLE and B5 is PENDING_INSPECTION, with no B5 failed
inspection. Native documents are Pick List `STO-PICK-2026-00022` (Draft),
receipts `MAT-PRE-2026-00027` and `MAT-PRE-2026-00028`, accepted A20 inspection
`MAT-QA-2026-00021`, and transfer `MAT-STE-2026-00022`. Raw setup responses
are retained locally as `/private/tmp/logisticpilot-review-*-result.json`.

## Frozen live-input checks

Reader: Strands / Bedrock, explicit `us.anthropic.claude-opus-4-6-v1`,
us-west-2, existing demo profile. Original pixels and inspection purpose are
inputs; expected results below, image titles and answer-bearing filenames are not.

| Case | Input and requested purpose | Expected supported behavior |
| --- | --- | --- |
| L1 | photo-review/input-01.png; label; operator LOT-B5 | Read the declared item/LOT-B5/quantity5; exact identity match; no physical count or quality release |
| L2 | photo-review/input-02.png; label; operator LOT-B5 | Read LOT-X9, surface identity mismatch and require verification; exclude this association from current economic advice |
| D1 | photo-review/input-03.jpg; detail | Review visible local fracture/surface concern even though adjacent nut is cropped; no precise dimensional approval or receiving count |
| D2 | existing p02.jpg bearing; detail | Review the visible surface without fabricating hidden damage, SKU or dimensions; no quality release |
| O1 | existing p06.jpg sky; overview | No goods/count; actionable request for actual receiving goods |
| O2 | existing carton input-01.jpg; overview | Visible carton observation and condition; never infer its contents |

The six selected inputs are development acceptance examples, not a held-out
accuracy benchmark. L1/L2 are rendered synthetic label documents, not phone
photographs. D1 and D2 are different public objects and must not be represented
as the same part's two views or as the contents of O2's carton.
Sources and licenses: [new inputs](../demo-inputs/photo-review/README.md),
[existing public fixtures](../../tests/fixtures/photo_receiving/README.md),
[carton](../demo-inputs/photo-intake/README.md).

One initial invocation per case. Preserve failures; at most one justified
correction/recheck for a concrete implementation defect before revisiting the
mechanism. Do not reroll a perception failure until a desired answer appears.
Schema/purpose-cache regressions can use explicitly offline reader doubles;
their counts are not live model evaluations.

## Real model results recorded so far

All calls below used the configured Opus reader with actual image pixels.
Each was the first invocation for its case. L1 used the API after browser file
chooser automation stalled; that does not establish browser-upload acceptance.

| Case | Observed result | Reader latency |
| --- | --- | --- |
| L1 | Printed item and LOT-B5 matched ERP scope; declared quantity5 remained a label observation; replaced L2 in current advice without releasing inventory | 10.537 s |
| L2 | Printed item matched; LOT-X9 mismatched selected LOT-B5; VERIFY_IDENTITY; excluded from current advisory observations | 10.903 s |
| D1 | Local detail assessed despite cropped neighboring component; visible damage with corrosion/scoring/pitting observations; operator inspection requested | 13.536 s |
| D2 | Clear bearing detail, no visible damage, no count or quality release | 12.409 s |
| O1 | No goods, no objects/count; concrete request to photograph receiving goods | 7.378 s |
| O2 | One visible carton, denting/crushing observed, no readable SKU/lot or inferred contents | 22.590 s |

D1 supports the visible-condition branch, not reliable defect-type recognition:
the model did not explicitly identify the source photograph's broken-bolt
fracture, describing its end face as scoring/gouging. Do not market this as a
validated fracture detector or general industrial quality classifier.

O2 explicitly supersedes O1 in the same case and operator-selected LOT-B5.
Both attachments remain; O1 is no longer current advice. The latest response
still has only the three setup events and received25 / usable20 / held5 /
allocated20 / dispatched0. Raw responses are local
`/private/tmp/logisticpilot-review-{L2,D1,D2,O1,O2}-result.json`.

## Backend review

The focused distributor/public-photo suite passed 76 checks, with Ruff check,
format check and Python compilation passing. These are offline regressions,
separate from the live calls above. Independent review found one cache issue
when injected readers lacked a stable model ID; caching is now bypassed for
those readers. The production Strands reader has an explicit model ID. Root
inspected the correction and restarted the isolated server after the live calls.

## Visual acceptance correction

The user rejected the text-heavy UI before visual acceptance. Restore the
[approved dashboard references](../design/approved-dashboard/README.md) and keep
three distinct responsibilities: Dashboard for status, Investigation for
reasoning/decision comparison, Operations for evidence entry and approved
execution. Keep detailed provenance and traces in drawers or expandable details.
The backend results above do not establish acceptance of the rejected UI.

## Recorded integration acceptance

- Browser navigation shows distinct workspaces: Dashboard has journey/KPIs,
  recent events, a large receiving photo, order-value card and expandable
  benchmark; Investigation has source comparison, Q&A and economic candidates;
  Operations has intake, inspection, approval and native records. Forms and
  approval controls are absent from Investigation and Dashboard.
- Restored the approved desktop composition and placed expanded economic
  comparison across the Investigation width. Detailed source/provenance and
  photo observations are closed disclosures. User visual approval is pending.
- Six actual API photo analyses completed. L1 replaced the wrong-label L2;
  O2 replaced the irrelevant O1. Previous attachments remain inspectable.
  Browser file chooser automation stalled twice; L1 was uploaded/analyzed
  through the actual API instead. Browser upload-to-analysis remains unverified.
- The first browser economic Compare failed honestly with
  `MODEL_BUDGET_EXHAUSTED` / `limit_total_tokens`: four evidence tools ran,
  14,684 input plus 1,835 output tokens were recorded. The failed result is
  retained locally in `/private/tmp/logisticpilot-review-after-compare.json`.
- The subsequent, distinct Prepare request performed its fresh comparison,
  selected `split20` with source citations (including advisory photo findings),
  and prepared a 20-unit LOT-A20 operation. The browser automatically moved from
  Investigation to `?view=operations#ops-proposal-panel`; the actual manager
  confirmation appeared there. It was not approved or executed.
- Readback after preparation still reported received25 / usable20 / held5 /
  allocated20 / dispatched0, three setup events, seven native documents. No
  carrier booking, payment, dispatch or external message was performed.
- Root reviewed the actual UI diff and ran JavaScript syntax and diff checks.
  No UI unit tests were added. The previous PO24 executor acceptance remains a
  separate run, not a dispatch result for this review case.

## Original acceptance checklist

- Browser upload → selected purpose and lot → actual analyze endpoint →
  returned checks/product scope/order impact → visible source/model trace.
- A supplemental photo remains in the same case/lot with its previous evidence
  retained. Superseded or mismatched observations are not silently current advice.
- Photo calls change no stock, native inspection or fulfillment event. Label
  quantities and object counts are not summed across views.
- Current supported photo evidence reaches the real economic selector, and the
  decision refers to live ERP stock/contract conditions.
- Fresh ERP readback supplies the frontend values. Keep the review order's
  20-unit dispatch available for the user's review unless execution is needed
  to resolve a new behavior question; the unchanged executor has prior PO24
  native acceptance. No carrier booking, payment or external messaging.
- Real browser review, backend checks, code diff review, commit and remote SHA
  verification. No UI unit tests; user owns final visual review.
