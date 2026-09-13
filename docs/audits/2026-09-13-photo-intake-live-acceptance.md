# Photo intake: live model follow-up

Date: September 13, 2026. Implementation base: `14475a3`.

AWS authentication was restored through a fresh CLI authorization using the
existing browser session. The CLI exited successfully and the read-only AWS
identity/account preflight passed. Chrome's final callback error did not mean
authorization failed; the CLI result and subsequent live calls established it.

## Preserve the failed baseline

The first successful application inference used the existing Nova Pro reader.
It saw one carton but returned `no_visible_damage`, missing the corner/top
deformation identified in the public development photograph. The application
kept all five B5 units awaiting inspection and did not convert this observation
into a quality release.

We compared the existing reader on the same two normalized public inputs, using
unchanged generic prompts. No image title, expected defect, ERP quantity or lot
choice was supplied to either image model.

| Model | Carton photograph | Sky negative | Reader latency |
| --- | --- | --- | --- |
| Nova Pro | One carton; `no_visible_damage`; no readable item/lot | `no_goods`, no count; its wording incorrectly said no retake was necessary |4.339s carton;1.796s sky |
| Opus4.6 | One carton; `visible_damage`; described denting/crushing on top and upper edges; requested a legible label photograph | `no_goods`, no count; requested an actual goods photograph |21.962s carton;6.601s sky |

Models: `us.amazon.nova-pro-v1:0` and `us.anthropic.claude-opus-4-6-v1` through
Strands/Bedrock in `us-west-2`. Both used the existing framing gate; the clear
carton also reached its second count/condition stage. This is one development
photo plus one negative control, not a held-out benchmark or an accuracy rate.
The slower Opus result supports this demo choice, not a general superiority claim.

The public photo and license are documented in
[the input README](../demo-inputs/photo-intake/README.md). The negative control is
the existing `p06.jpg` from [the photo fixture set](../../tests/fixtures/photo_receiving/README.md).
Raw failed and successful runs remain in private local acceptance artifacts.

## Narrow configuration change

`MISSING20_OPERATIONS_PHOTO_MODEL_ID` selects the operations photo reader only;
the existing default remains Nova Pro. This demo explicitly uses Opus4.6. The
actual returned model remains visible in its observation. The cache includes
the configured reader model, so changing models cannot reuse another model's
completed result as the new invocation. The generic prompts and inventory rules
are unchanged.

The UI also displays a nonempty suggested next photograph on a complete damage
observation, including a request for a clearer label. It does not invent a lot
identity or require the operator to enter the defect before analysis.

## Same-case recovery

Case: `M20-DIST-ECONOMIC-PHOTO-20260913`; PO24 / SO18. The existing allocation
retry succeeded through real Opus after authentication. It selected the exact
20-unit A20 plan and generated native draft pick `STO-PICK-2026-00021`.
The five B5 units still await inspection. No B5 failed measurement was added.

## Browser-to-ERP acceptance

The same saved attachment was selected through **Review / retry this photo**,
with operator-selected LOT-B5. **Analyze again** invoked the configured Opus
reader through the real application endpoint. It returned `COMPLETE`,
`visible_damage`, one carton, no readable item or lot, and a request for a
close-up label photograph. Latency was 21.332 seconds; usage was 5,680 input and
1,054 output tokens. The browser displayed the damage observation, suggested
next photo and ERP association. Fresh API readback had `advisory_current:true`.
Quantities remained 20 usable, 5 held and 0 dispatched; the same three business
events remained. This was a new invocation, not the earlier comparison artifact.

**Compare with agent** ran Strands/Bedrock Opus against four evidence tools:
`read_contract_evidence`, `read_quality_evidence`, `read_cost_evidence` and
`read_operational_snapshot`. Its 28.674-second result explicitly cited
`photo:e31e731e1759114c69283fd4`, described the photo as advisory and ERP's held
status as authoritative. It selected the first 20-unit leg; the five-unit tail
remained conditional on inspection release. Usage was 14,085 input and 2,088
output tokens across four model requests. This is one tool-using selector, not
a multi-agent evaluation.

**Prepare this dispatch** performed another fresh comparison (30.790 seconds)
and prepared the exact LOT-A20 / SO18 / 20-unit event. With the explicit POC
identity `demo-manager`, **Approve and execute** applied that bounded event.
The browser and fresh API projection returned:

- 25 received, 20 dispatched, 5 held, 0 still usable or allocated.
- Pick List `STO-PICK-2026-00021`: Completed.
- Delivery Note `MAT-DN-2026-00023`: To Bill.
- Shipment `SHIPMENT-00021`: Submitted, linked to SO18 / LOT-A20 / 20 units.
- No carrier pickup or customer receipt was asserted; both remain false.

An independent worker then read the native records through a GET-only guarded
executor (31 GETs including the scoped source refresh; zero writes or model
invocations). Pick21, DN23 and Shipment21 all had `docstatus:1`. Pick21 and DN23
each matched SO18, the exact A20 batch and quantity20; DN23 linked Pick21 and
Shipment21 linked DN23. SO18 recorded ordered25 / delivered20. The B5 receipt
recorded its exact batch and quantity5 in the inspection warehouse. The current
scoped source projection separately reported B5 held5 / usable0; this is not a
claim that the verifier independently read a new inspection or stock ledger.

After execution the UI labeled the pre-dispatch recommendation as historical.
Current gates no longer offered another 20-unit preparation because that stock
and allocation had been consumed. No repeat dispatch was submitted in this run.
The photo also became a historical source snapshot after the ERP revision
changed; its successful result remains visible rather than being relabeled as
a fresh observation of the new state.

The $49.60 split / $24.80 consolidated postage amounts are declared POC estimates
from the existing evidence packet. This run paid no postage, booked no carrier,
created no invoice and established no realized savings or recognized revenue.
The observed business outcome is bounded fulfillment of 20 qualified units
while five uncertain units stay out of the outbound shipment.

## Verification and limits

The Terra implementation worker ran both affected backend suites: **64 passed**.
These use offline service/reader doubles and are not 64 live model trials. The
primary agent inspected the actual diff, reran the model-cache regression,
JavaScript syntax check, Python lint and whitespace checks, and exercised the
real browser workflow above. No UI unit tests were added; final visual review
belongs to the user. Phone camera hardware and fresh-upload blob preview remain
outside this acceptance; this run reused the successfully uploaded attachment.
The sky negative was exercised through the real reader probe, not browser upload.

The initial implementation and unavailable-state checks remain in
[the earlier audit](2026-09-13-photo-intake-acceptance.md). Local raw artifacts
include `logisticpilot-photo-opus-app-readback.json`,
`logisticpilot-photo-economic-compare-readback.json`, and
`logisticpilot-photo-final-readback.json` and
`logisticpilot-photo-independent-native-readback.json` under `/private/tmp`; they are not
committed runtime state. The application can now demonstrate photo observation
through a cited decision to approved ERP dispatch, with the limits above.
