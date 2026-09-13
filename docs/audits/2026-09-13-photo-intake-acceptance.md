# Photo intake: implementation and verification status

Date: September 13, 2026. Base: `e9854d8`.

**Status: implemented and checked offline; positive real-model acceptance is
blocked by expired AWS credentials.** Browser upload and the real API's
unavailable/retry path were exercised. No successful image interpretation or
photo-informed economic recommendation is claimed for this run.

## Corrected demo premise

The previous economic demonstration's five held units came from a predeclared,
synthetic 10.3 mm inspection result. They were not discovered from a photograph.
That completed PO23 case and its port8931 runtime remain separate.

The new isolated case is `M20-DIST-ECONOMIC-PHOTO-20260913`, PO
`PUR-ORD-2026-00024`, SO `SAL-ORD-2026-00018`. Only three synthetic events were
recorded: receive A20, pass A20's separate whole-lot inspection, and receive B5.
No B5 failure or measurement was entered. Fresh ERP readback shows:

- 25 received; A20 has20 usable; B5 has5 awaiting inspection;0 dispatched.
- Receipts `MAT-PRE-2026-00025` and `MAT-PRE-2026-00026`.
- A20 inspection `MAT-QA-2026-00020` accepted and stock entry
  `MAT-STE-2026-00021` submitted.
- No B5 quality inspection, Delivery Note or Shipment in this case's readback.

Five are already held by the receipt/inspection policy before photo analysis.
A photo can draw attention to visible damage and motivate inspection; it does
not create those five units, establish five defects, or prove a financial saving.

## Implemented path

The operations page uploads an actual JPEG/PNG to its existing same-case
attachment endpoint, then explicitly calls
`POST /api/v1/distributor-operations/analyze-photo` with an attachment ID and an
optional operator-selected ERP lot. The reader receives normalized pixels only,
without filenames, expected defects, ERP quantities or the operator's lot choice.

The existing `StrandsPhotoReader` performs its visibility and, when permitted,
count/condition stages through Bedrock. Its default image model is Amazon Nova
Pro (`us.amazon.nova-pro-v1:0`); this is distinct from the existing Opus4.6 economic
selector. Model/provider, stages, usage and latency are retained only when
returned. There is no synthetic model fallback.

The attachment records its image digest, source revision, observation and
operator-selected association. Linked quantity comes from ERP received quantity,
not hidden carton contents. The analysis path creates no inventory or inspection
event and performs no native ERP write. Unclear/malformed results require review,
retake or retry. A clean-looking photograph is not a quality release. Conflicting
label text requires identity review and does not overwrite the selected lot.

Only current, complete, digest-bound observations enter the economic agent's
existing operational evidence tool. They are optional advisory citations; ERP
status and quantity still determine feasibility. Historical observations remain
visible but are excluded from the current advisory input.

The public development photo and its separate CC BY2.0 attribution are in
[the input README](../demo-inputs/photo-intake/README.md). Its association with
LOT-B5 is an explicitly synthetic POC association. It is not our warehouse
photograph, and its contents are unknown.

## Checks performed and remaining acceptance

- Primary-agent run of the two affected backend suites:63 passed, using
  `PYTHONPATH=.:src .venv/bin/python -m pytest -q
  tests/test_distributor_operations.py tests/test_distributor_economics.py`.
  These include explicit offline reader doubles, not successful live inference.
- Python lint/format, JavaScript syntax and diff checks passed. No UI unit tests
  were added; the user retains final visual review.
- Browser selected the real file and LOT-B5, submitted the actual upload and
  analysis endpoints, and displayed **Retry analysis** after `UNAVAILABLE`.
- Independent API readback retained the original image SHA256
  `c5eb3b53de80c42bd5374bb3b45a99b36daf0e9552758bf0a6b94a1028656146`, linked quantity5,
  no assessment/model result, and `advisory_current:false`. Quantities and the
  three recorded business events were unchanged.
- Browser inspection exposed a blocked blob preview; the server now permits
  local blob images while preserving its other content-security directives.
- After server restart and page reload, the saved image visibly rendered from
  its same-case endpoint. **Review / retry this photo** restored the attachment
  and LOT-B5 without another upload or automatic model call. Its unavailable
  result appeared inline above the manual event fields. A fresh pre-upload blob
  preview and the positive/retake result views still require live-flow acceptance.

The initial standalone real reader probe failed with `LoginRefreshRequired`
because the refresh token expired. A fresh Chrome/CLI authorization was opened
but expired while waiting for login. The browser analysis then returned the
honest unavailable state. The initial test command also failed collection without
the repository on `PYTHONPATH`; the corrected invocation above passed.

Still required: refreshed AWS authorization, a real positive image result, a
real retake/negative input, and a subsequent real economic decision using the
photo citation if relevant. Phone camera capture has not been tested on hardware.
This small development check is not a vision accuracy benchmark, a measured
reduction in human errors, or a completed photo-to-dispatch acceptance.

## Resume without resetting evidence

The isolated server is at `http://127.0.0.1:8932/operations?view=dashboard`.
Configuration: `/private/tmp/logisticpilot-photo-config-20260913.json`.
Runtime: `/private/tmp/logisticpilot-photo-runtime-20260913`.
Use the same demo Bedrock settings as the economic run, with
`MISSING20_OPERATIONS_PHOTO_ANALYSIS=1`; the feature is otherwise disabled.

AWS expiry also left the initial A20 allocation selector `PENDING`; the ERP stock
release itself succeeded. After authentication, use the existing **Review pending
allocation** control, then verify a selected allocation and native prepared pick
before preparing the economic dispatch. The corresponding existing endpoint is
`/api/v1/distributor-operations/reselect-pending-allocation`, with a fresh
`retry_id` and the current pending decision's `pending_event_id`. Do not replay
the synthetic inspection or pretend that the pending selection succeeded.

The economic card's READY state describes stock/contract feasibility, not a
pre-existing native pick or healthy AWS session. No economic action was prepared
or approved in this new case. The previously accepted economic flow remains
documented in [its separate audit](2026-09-13-economic-poc-acceptance.md).
