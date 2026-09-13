# Pro Forma Shipping Cost Statement

> **SYNTHETIC POC — NOT A REAL CUSTOMER TRANSACTION**
>
> **PRO FORMA — NOT PAID / NOT A CARRIER INVOICE**

Case: `LP-POC-COST-01`

Customer: **Demo Parts Customer A**

Destination: fictional US domestic address ID `DEMO-US-DEST-A` (same for both; not an actual street).

Purpose: compare two hypothetical dispatch plans for the same 25-unit order and
customer/address. Evaluation snapshot: 2026-09-13 09:00 America/Los_Angeles. The
first dispatch deadline is 2026-09-14 15:00 America/Los_Angeles for at least 10
units; if split, the final 5 must dispatch by 2026-09-16 15:00
America/Los_Angeles; if consolidated, all 25 must dispatch by 2026-09-14 15:00
America/Los_Angeles. These are dispatch deadlines, not arrival guarantees.

No shipping is booked, purchased, or represented as paid. The USPS rate is a
real published rate; the customer, order, terms, packaging, and amounts below
are synthetic scenario data.

| Scenario line | Quantity | Boxes | Rate | Scenario amount |
| --- | ---: | ---: | ---: | ---: |
| Split: first dispatch by Sep 14 deadline | 20 units | 1 | $24.80 | $24.80 |
| Split: final dispatch by Sep 16 deadline | 5 units | 1 | $24.80 | $24.80 |
| **Split total** | **25 units** | **2** |  | **$49.60** |
| Consolidated: all 25 by Sep 14 deadline, if released | 25 units | 1 | $24.80 | $24.80 |
| **Estimated postage-only delta** |  | **1 box fewer** |  | **$24.80** |

The rate is USPS domestic Retail Medium Flat Rate Box, checked 2026-09-13,
effective 2026-07-12, per [official USPS Notice 123](https://pe.usps.com/text/dmm300/Notice123.htm).
Extra services are excluded, and [Priority Mail delivery time is not guaranteed](https://pe.usps.com/text/dmm300/123.htm).

The consolidated line is usable only if the remaining 5 units pass future quality
release or become available from stock by the Sep 14 dispatch deadline; their
release time is unknown. The $24.80 delta is an estimate, not a confirmed
fulfillment saving. No late penalty or guaranteed total completion is assumed.
