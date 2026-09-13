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
| First dispatch deadline | 2026-09-14 15:00 America/Los_Angeles; at least 10 units; dispatch, not arrival |
| Split final-remainder deadline | 2026-09-16 15:00 America/Los_Angeles; dispatch, not arrival |
| Consolidated dispatch deadline | 2026-09-14 15:00 America/Los_Angeles for all 25; dispatch, not arrival |

## Dispatch candidates

1. **Split:** send 20 units by the first dispatch deadline, then the remaining
   5 by the split final-remainder deadline.
2. **Consolidated:** wait and send all 25 by the consolidated dispatch deadline
   if the remaining 5 are released in time.

The consolidated candidate is considered only if the 5 units clear future
quality release or become available from stock before the consolidated dispatch
deadline. Remaining-5 release time is unknown; waiting does not establish a
confirmed saving or guarantee total order completion.

## Fictional customer terms

- A partial dispatch is allowed when the first shipment contains at least 10
  units.
- The first dispatch must occur by 2026-09-14 15:00 America/Los_Angeles.
- If split, the final 5 must dispatch by 2026-09-16 15:00
  America/Los_Angeles.
- If consolidated, all 25 must dispatch by 2026-09-14 15:00
  America/Los_Angeles.
- These are dispatch deadlines, not arrival guarantees.
- No late penalty is specified or invented here.

These terms are synthetic POC inputs, not a contract, purchase order, invoice,
or proof of customer consent.
