# LogisticPilot — five-minute recording plan

Target: **4:35–4:50**, English narration. One receiving exception, one customer order, partial fulfillment and a verified external record. This replaces the old Investigation/$42,000 invoice script. Do not mix those cases.

## One sentence

**A receiving problem shouldn’t stop every order. LogisticPilot helps small parts distributors investigate affected stock and keep eligible orders moving.**

## Freeze the case first

The verified reference is PO25 / SO19: 25 received, A20 dispatched, B5 held. It can demonstrate review and the completed result now. It cannot demonstrate a new approval without new work. For a fresh take, use the existing isolated economic-poc provisioner with a new instance and private runtime; record its actual IDs in the take log. Do not reset displayed quantities.

Prepare A20 receipt and its declared passing inspection, then B5 receipt with its policy hold. **Do not inject a failed B5 sample merely to make a photograph seem diagnostic.** Use a licensed image as a disclosed POC input. The operator identifies its batch; actual image analysis supplies an observation, not clearance.

## Timed story

| Time | Screen / real action | English narration and proof |
| --- | --- | --- |
| 0:00–0:25 | Dashboard, B5 incident and 25/20/5 scope. | “For a small distributor, one questionable carton can turn into a morning of checking photos, inspection records and customer orders. Here, five parts need inspection. Twenty other parts can still serve the customer.” |
| 0:25–0:50 | Click the incident into Operations; selected B5, PO and customer order. | “We start with the affected batch. The order, evidence and assistant stay in the same context as I move into the work.” |
| 0:50–1:30 | Attached photo; actual analysis if upload/timing preflight passes; concise finding. | “This is a public image used in our fictional receiving case. The model examines the carton. It can flag an observation and ask for a better view, but it cannot invent a measurement or release the stock.” |
| 1:30–2:10 | Ask what can move while B5 remains held; relevant order/inspection evidence. | “The assistant considers current inventory and order terms together. It explains why the qualified batch can move and what evidence the remaining batch still needs.” |
| 2:10–2:40 | Supported dispatch and conditional consolidation estimate before approval. | “Sending twenty now keeps eligible fulfillment moving. Waiting might use one box instead of two, but only if the five held parts clear in time. This is a cost tradeoff, not a guaranteed saving.” |
| 2:40–3:30 | Exact lot/quantity/order confirmation; confirm once on a fresh case. | “The agent prepares the work. I confirm the exact action. The application checks the latest evidence and writes the bounded operation to our ERPNext demo tenant.” |
| 3:30–4:05 | Check ERP; open actual Delivery Note or Shipment; return to Dashboard. | “The result is checked outside the conversation. Twenty units are recorded as dispatched; five remain held. These are actual records created in the demo tenant—not a success message invented by the model.” |
| 4:05–4:30 | Compact architecture / supporting evidence, then selected-batch brief. | “Strands handles contextual reasoning. The execution harness owns quantities, evidence checks, confirmation and readback. Separate dated evaluations support development; old multi-agent results are not this run.” |
| 4:30–4:45 | Current outcome and unresolved B5 next step. | “LogisticPilot gives a small team one place to investigate the problem, keep eligible orders moving, and verify what actually happened.” |

Do not film every drawer in the final five minutes. Exhaustive clicking is rehearsal work; show evidence that changes the decision. For long real calls, use an honest visible time cut while preserving request, returned result and same-case IDs. Do not substitute scripted success or hide footage from different runs.

## Capability questions

Use at most three primary questions. Do not put expected answers in the model input.

1. “Why is this lot held, and which order is affected?”
2. “Can the other stock move while this lot stays on hold?”
3. “What evidence would let us release this lot?”

For a completed-case take, replace question 2 with “What has been dispatched, and what still needs attention?” A separate draft demonstration may supply a declared POC inspection measurement, but do not approve B5 release if the story ends with five held units.

## Before pressing Record

- One case across Dashboard, selected lot, Agent context and ERP URLs.
- Each disclosure readable and stable during refresh; manual forms remain fallback.
- Photo chooser/upload works if filming a new upload; otherwise identify an already attached image. Confirm batch and image before analysis.
- AWS valid; current GET and a brief answer complete successfully.
- New pending exact-action card if filming execution. Never replay PO25 as a fresh dispatch.
- ERP record opens without a login interruption in the recording browser.
- Rates are estimates, history illustrative, order value is not revenue.
- Runtime under five minutes, English narration, legible captured text.
- Public video and judge access verified separately before submission.

## Completed-case alternative — about three minutes

Use the same opening and incident review, then original execution details and fresh ERP readback. Say “This run recorded twenty dispatched.” This is a valid result walkthrough; a continuous fresh before/after take is stronger. The [independent review](../audits/2026-09-14-operations-interaction-review.md) gives a 2:50 sequence.

## Take log

Record date, build SHA, runtime case, PO/SO, fixture/attachment, model, questions, confirmation identity, document IDs, timing and failures. Keep credentials and raw runtime outside Git. Link a redacted acceptance note and final video once available.
