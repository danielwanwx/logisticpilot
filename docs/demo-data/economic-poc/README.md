# Economic POC Evidence Packet

> **SYNTHETIC POC — NOT A REAL CUSTOMER TRANSACTION**

Case: `LP-POC-COST-01`

`LP-POC-COST-01` is the synthetic evidence-packet alias, not an ERP case ID.
The `economic-poc` provisioner maps each isolated instance to a distinct runtime
case such as `M20-DIST-ECONOMIC-ECON-20260913`; the generated configuration
carries both identities. A UI or API readback must preserve that distinction.

Customer: **Demo Parts Customer A**

Destination: fictional US domestic address ID `DEMO-US-DEST-A` (same for both candidates; not an actual street).

This packet is a small first candidate for testing whether waiting to consolidate
one outbound order could reduce postage. It is evidence for a hackathon POC, not
proof of strong ROI or a full implementation.

## Scope

- Total order quantity: **25 units**.
- **20 units** are quality-qualified and available now; **5 units** are not yet
  released.
- Split candidate: dispatch 20 by the first dispatch deadline, then 5 by the
  final-remainder dispatch deadline.
- Consolidated candidate: dispatch all 25 by the same first dispatch deadline
  if the remaining 5 are released in time.
- Both candidates use the same customer, `DEMO-US-DEST-A`, and total quantity.
- Demo Parts Customer B and any second customer are excluded.

The fictional terms allow a first dispatch of at least 10 units by **2026-09-14
15:00 America/Los_Angeles**. If the order is split, the final 5 must dispatch by
**2026-09-16 15:00 America/Los_Angeles**. If all 25 are consolidated, all 25
must dispatch by the same **2026-09-14 15:00 America/Los_Angeles** deadline.
Evaluation snapshot: **2026-09-13 09:00 America/Los_Angeles**. Both timestamps
are dispatch deadlines, not arrival guarantees. The release time for the
remaining 5 is unknown; no late penalty or guaranteed total completion is
assumed. Waiting is conditional on future quality release or stock.

## Evidence levels

| Level | Included evidence |
| --- | --- |
| Public | USPS Notice 123 rate and USPS Priority Mail delivery-time caveat |
| Synthetic | Customer, order, terms, package-fit assumption, and scenario arithmetic |
| Verified integration, September 13 | Real Bedrock comparison, exact 20-unit approval, native ERP documents and independent readback; see the acceptance audit |
| Unverified physical outcomes | Package fit, carrier pickup, customer receipt, booking/payment and realized savings |

Machine integration acceptance: an app readback must preserve this case ID,
same customer/address, quantities, deadlines, USPS rate provenance, and
scenario amounts, while keeping release and savings conditional. It must not
claim shipping was booked or savings were realized merely because the packet was loaded.

The public USPS Retail Medium Flat Rate Box rate is **$24.80**, checked
2026-09-13, effective 2026-07-12. See [Notice 123](https://pe.usps.com/text/dmm300/Notice123.htm).
Priority Mail delivery time is not guaranteed; see [USPS service standards](https://pe.usps.com/text/dmm300/123.htm).

The package assumption says each A20, A5, or A25 package fits one genuine USPS
domestic Medium Flat Rate Box, is at most 70 lb, and is nonhazardous. This is an
operator-declared synthetic assumption; physical fit is not verified.

The isolated `M20-DIST-ECONOMIC-ECON-20260913` run loaded this packet and verified
20 units through native ERP dispatch on September 13. Five units remain held.
See the [actual acceptance record](../../audits/2026-09-13-economic-poc-acceptance.md).
This is not a carrier booking, payment, physical delivery or realized saving.

Documents:

- [Customer order and terms](customer-order-and-terms.md)
- [Shipping cost comparison](shipping-cost-comparison.md)
- [Pro forma shipping cost statement](shipping-cost-statement.md)
