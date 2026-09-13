# Shipping Cost Comparison

> **SYNTHETIC POC — NOT A REAL CUSTOMER TRANSACTION**

Case: `LP-POC-COST-01`

Customer: **Demo Parts Customer A**

Scope: same fictional US domestic address ID `DEMO-US-DEST-A` (not an actual street) and 25-unit total in both candidates. Evaluation snapshot: 2026-09-13 09:00 America/Los_Angeles; latest agreed dispatch: 2026-09-14 15:00 America/Los_Angeles (dispatch, not arrival).

## Rate and packaging assumption

The USPS domestic Retail Medium Flat Rate Box rate used here is **$24.80 per
box**, checked 2026-09-13 and effective 2026-07-12, from [official USPS Notice 123](https://pe.usps.com/text/dmm300/Notice123.htm).

| Package assumption | Units | Boxes | Status |
| --- | ---: | ---: | --- |
| A20 | 20 | 1 | Operator-declared synthetic fit assumption |
| A5 | 5 | 1 | Operator-declared synthetic fit assumption |
| A25 | 25 | 1 | Operator-declared synthetic fit assumption |

Each package is assumed to fit one genuine USPS domestic Medium Flat Rate Box,
weigh no more than 70 lb, and be nonhazardous. Physical fit and weight are not
verified.

## Scenario arithmetic

| Candidate | Dispatches | Postage-only estimate |
| --- | --- | ---: |
| Split | 20 now + 5 later = 2 boxes | 2 × $24.80 = **$49.60** |
| Consolidated | 25 after release = 1 box | 1 × $24.80 = **$24.80** |

Estimated delta: **$24.80** lower for consolidation (postage only).

This is an estimate, not real paid savings. Extra services, surcharges, taxes,
and any non-USPS costs are excluded. No shipment is booked. [USPS Priority Mail delivery time is not guaranteed](https://pe.usps.com/text/dmm300/123.htm).

Consolidation remains conditional on the unconfirmed release of the remaining 5
through future quality release or stock by that dispatch deadline. There is no
confirmed fulfillment saving yet.
