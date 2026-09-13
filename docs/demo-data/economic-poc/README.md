# Economic POC Evidence Packet

> **SYNTHETIC POC — NOT A REAL CUSTOMER TRANSACTION**

Case: `LP-POC-COST-01`

Customer: **Demo Parts Customer A**

Destination: fictional US domestic address ID `DEMO-US-DEST-A` (same for both candidates; not an actual street).

This packet is a small first candidate for testing whether waiting to consolidate
one outbound order could reduce postage. It is evidence for a hackathon POC, not
proof of strong ROI or a full implementation.

## Scope

- Total order quantity: **25 units**.
- **20 units** are quality-qualified and available now; **5 units** are not yet
  released.
- Split candidate: dispatch 20 now and 5 later.
- Consolidated candidate: dispatch all 25 after the remaining 5 are released.
- Both candidates use the same customer, `DEMO-US-DEST-A`, and total quantity.
- Demo Parts Customer B and any second customer are excluded.

The fictional terms allow a partial dispatch of at least 10 units, the final remainder later, and consolidation by the latest agreed dispatch **2026-09-14 15:00 America/Los_Angeles**. Evaluation snapshot: **2026-09-13 09:00 America/Los_Angeles**. The deadline is dispatch, not arrival; remaining-5 release is unconfirmed. Waiting is conditional on future quality release or stock and that deadline; no late penalty is assumed.

## Evidence levels

| Level | Included evidence |
| --- | --- |
| Public | USPS Notice 123 rate and USPS Priority Mail delivery-time caveat |
| Synthetic | Customer, order, terms, package-fit assumption, and scenario arithmetic |
| Runtime-to-be-verified | Release/stock, dispatch deadline, physical fit, booking/payment, and any app result |

The public USPS Retail Medium Flat Rate Box rate is **$24.80**, checked
2026-09-13, effective 2026-07-12. See [Notice 123](https://pe.usps.com/text/dmm300/Notice123.htm).
Priority Mail delivery time is not guaranteed; see [USPS service standards](https://pe.usps.com/text/dmm300/123.htm).

The package assumption says each A20, A5, or A25 package fits one genuine USPS
domestic Medium Flat Rate Box, is at most 70 lb, and is nonhazardous. This is an
operator-declared synthetic assumption; physical fit is not verified.

The packet is not currently loaded by the app. No actual model or ERP run was
performed for this new case, and no fulfillment savings are confirmed.

Documents:

- [Customer order and terms](customer-order-and-terms.md)
- [Shipping cost comparison](shipping-cost-comparison.md)
- [Pro forma shipping cost statement](shipping-cost-statement.md)
