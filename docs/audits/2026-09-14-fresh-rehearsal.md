# Fresh recording rehearsal — PO26

Date: September 14, 2026 UTC / September 13 Pacific. Product baseline: `d992345`; documentation baseline at rehearsal start: `7128e8f`. The primary agent drove the actual Chrome UI against the local server on port 8934, live Bedrock and the real ERPNext demo tenant. No application code was changed for this rehearsal.

**Result: the selected business path completed after recovery.** Actual browser upload, agent-requested image analysis, eligibility reasoning, a newly prepared twenty-unit action, one human-confirmation control and native ERP readback were exercised on one new case. Two first-attempt defects remain below. This is not a claim that every feature passed or that a finished competition video exists.

## Case and baseline

- Case: `M20-DIST-ECONOMIC-REHEARSAL-20260914`.
- Purchase order: `PUR-ORD-2026-00026`; customer order: `SAL-ORD-2026-00020`.
- Starting inventory: 25 received; LOT-A20 has 20 usable units and a recorded whole-lot passing inspection; LOT-B5 has 5 units pending inspection; 20 allocated; 0 dispatched; 0 carrier-confirmed.
- Exactly three starting events: A20 arrival, A20 inspection PASS with declared 10 mm measurement, B5 arrival. No B5 failed inspection was inserted.
- The ordinary allocation path had selected stock and created draft Pick List `STO-PICK-2026-00023`. There was **no prepared economic proposal**. The fresh preparation acceptance below is distinct from reusing that allocation record or PO25's old proposal.
- The existing provisioner created an isolated, explicitly synthetic business scenario. The accepted PO25 preview on port 8933 was preserved.

## Browser actions and observed results

| Step | Actual action | Observed result |
| --- | --- | --- |
| 1 | Open Dashboard, then Review hold | Same SO20 and selected B5 context reached Operations; baseline was 20 eligible / 5 held / 0 dispatched. |
| 2 | Agent Upload → Chrome file chooser → `input-03.jpg` | Actual upload saved the public rusted-fastener photo. This was not a preloaded-image walkthrough. |
| 3 | Ask “Look at this LOT-B5 photo. What can you tell me, and what still needs checking?” | Incorrectly asked “Which lot does this photo belong to?” despite the explicit lot. Failure preserved. |
| 4 | Reply “This photo belongs to LOT-B5. Please inspect it.” | Live image analysis completed. The observation detail reported rust on bolts/nuts, a broken bolt and worn nuts. Recommendation required inspection. B5 remained held; no stock release or invented measurement. |
| 5 | Ask “Can the other stock move while this batch stays on hold?” | UI supplied B5 context. Agent identified A20's 20 quality-cleared units as eligible for partial dispatch, B5's 5 still held, and the remaining diameter check of 9.9–10.1 mm. |
| 6 | Ask “Prepare the eligible LOT-A20 dispatch for this customer order, keeping LOT-B5 on hold.” | First attempt failed before model/action preparation because current ERP evidence was unavailable. Local journal inspection found zero new proposals. The UI temporarily showed an order-loading error, then automatically returned to Synced. |
| 7 | Repeat that same request once after recovery | New Confirm Picked card appeared for PO26 / SO20 / LOT-A20 / 20 units. No manual event or quantity form was filled by the operator. |
| 8 | Review exact card, enter `POC reviewer`, click Confirm action once | Execution returned APPLIED. No second confirmation click or duplicate dispatch was attempted. |
| 9 | Check ERP, open ERP records, follow actual Delivery Note URL in signed-in Chrome | Fresh workspace read showed 20 dispatched / 5 held. Native Delivery Note `MAT-DN-2026-00025` showed 20 units, status To Bill and submitted activity. |
| 10 | Return to Dashboard | 20 dispatched, 5 awaiting release, four events total; newest event is the A20 twenty-unit Picked event. Carrier confirmation remains zero. |

Native execution records: Delivery Note `MAT-DN-2026-00025`, Pick List `STO-PICK-2026-00023`, Shipment `SHIPMENT-00023`. Execution event: `M20-DIST-ECONOMIC-REHEARSAL-20260914-PICK-SPLIT20`. Approval was recorded September 13, 10:50 PM Pacific; the separately requested ERP read displayed 10:51 PM. The native Delivery Note is not proof of carrier delivery, payment or earned revenue; the current batch view supplies the separate five-unit hold evidence.

The durable local proof identifies the fresh proposal as `economic-76e4566cd3cce217460d9fb0f7534bd0`, prepared at `2026-09-14T05:48:31.735746Z` and applied with approval recorded at `05:50:36.155074Z`. The economic selector recorded Bedrock `us.anthropic.claude-opus-4-6-v1` through Strands in us-west-2, selected split20, and invoked `read_contract_evidence`, `read_quality_evidence`, `read_cost_evidence` and `read_operational_snapshot`, citing five evidence IDs. Its recorded model duration was 36,864 ms; that is not the full browser task duration. These tools read the application-supplied evidence packet rather than making four independent external ERP reads. The final journal has four events and no B5 inspection/FAIL event. The private final proof is retained at `/private/tmp/logisticpilot-rehearsal-20260914-final-proof.json`.

Screenshots of the baseline, confirmation card, native Delivery Note and resulting Dashboard were inspected inline in the task. No standalone screenshot files or continuous raw video were saved by this rehearsal; do not claim these are an existing recording asset pack.

## Failures and recording implications

1. **Redundant batch question.** The model photo-request schema makes `lot_citation` optional, while the adapter requires a matching literal human citation when multiple lots exist. The durable first row and guard branch support a citation-validation failure, not an actually missing lot. Raw structured citation output was not retained, so omission versus mismatch cannot be distinguished. Explicit follow-up recovered. Keep this in the evidence; do not narrate the question as a useful discovery of missing information.
2. **Temporary ERP-read failure before preparation.** The request stopped on a non-CURRENT source snapshot, before creating a proposal. The exact transport cause was not persisted; timeout versus another source-read failure is undetermined. The workspace recovered automatically and one identical retry succeeded. This preserved the action boundary but remains a usability/reliability defect. Do not describe a seamless first attempt or secretly substitute earlier success.
3. **Photo answer is too generic initially.** The returned first analysis chat sentence emphasized inspection limits; specific visual findings were in the observation detail and subsequent eligibility answer. The film must show those actual details if it narrates rust. Visual findings are model observations, not certified labels for every part.
4. **Long processing waits and ERP clutter.** Real calls took noticeable time. Preserve complete capture on the recording take and label shortened processing waits. The native ERP screenshot had a Getting Started overlay; close it before filming. Do not fix this by synthesizing a cleaner ERP result screen.

These are retained defects, not application fixes delivered by this audit. The demo is functional with recovery; it is not a production reliability acceptance. No UI unit tests were added.

## Story and claim acceptance

The strongest story is an operator deciding what can move without losing the held stock: **five questionable parts should not automatically delay the other twenty**. Strands contributes contextual reasoning and tool/action selection. The application supplies ERP evidence, validates the proposed operation, enforces confirmation, executes and reads back. The supported preparation path can invoke the separate economic selector; do not turn workflow stages into a claim of four agents, Graph or Swarm orchestration.

The result proves twenty units progressed to recorded dispatch while five stayed held. Reducing repeated cross-checks and moving eligible orders toward billing are plausible customer benefits; customer hours, increased profit, defect-rate improvements and realized ROI were not measured. The native USD 120 delivery amount, USD 100 purchase-line amount and illustrative postage/history data must not become a savings counter or earned-revenue claim.

Use the [reviewed voiceover](../demo/voiceover-v4.md) and [independent judge review](2026-09-14-script-judge-review.md). The independent reviewer assesses narrative and supplied evidence; it did not independently execute this ERP case. Official five-criterion alignment is documented there; no award probability or official score is established.

## Recording decision

**Proceed to recording preparation and a rough cut.** The requested full interactive rehearsal is complete. Both PO25 and PO26 are now completed records; a new before/after take needs a new isolated instance, not replay of a completed approval. Preserve the same three-event baseline, licensed input and supported question/action sequence. Do not create a B5 FAIL event just to strengthen the story.

Use actual screen capture for the product, Remotion for brief framing/architecture/captions, and ElevenLabs for the final reviewed narration. No audio generation, raw video, composition render, final playback, public video or free judge test route was accepted in this rehearsal. Final film and submission acceptance remain distinct from this business-path result.

Public photo provenance: [photo intake sources](../demo-inputs/photo-intake/README.md). Private setup/configuration/runtime evidence remains outside Git under the task's temporary directory; no credentials or runtime database are included in this audit.
