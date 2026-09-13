# Customer Order and Terms

> **SYNTHETIC POC — NOT A REAL CUSTOMER TRANSACTION**

Case: `LP-POC-COST-01`

Customer: **Demo Parts Customer A**

Destination: fictional US domestic address ID `DEMO-US-DEST-A`, identical for both candidates; not an actual street.

## Order facts

| Fact | Value |
| --- | --- |
| Total order | 25 units |
| Available now | 20 units, quality-qualified |
| Not yet released | 5 units |
| Customer B | Excluded |
| Candidate identity | Same customer, address, and total quantity |
| Evaluation snapshot | 2026-09-13 09:00 America/Los_Angeles |
| Latest agreed dispatch | 2026-09-14 15:00 America/Los_Angeles; dispatch, not arrival |

## Dispatch candidates

1. **Split:** send 20 units now, then the remaining 5 later.
2. **Consolidated:** wait and send all 25 after the remaining 5 are released.

The consolidated candidate is considered only if the 5 units clear future
quality release or become available from stock before the latest agreed dispatch
deadline. Remaining-5 release is unconfirmed; waiting does not establish a
confirmed saving.

## Fictional customer terms

- A partial dispatch is allowed when the first shipment contains at least 10
  units.
- The final remainder may dispatch later.
- The order may be consolidated by the latest agreed dispatch deadline above.
- No late penalty is specified or invented here.

These terms are synthetic POC inputs, not a contract, purchase order, invoice,
or proof of customer consent.
