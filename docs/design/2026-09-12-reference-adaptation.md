# Missing20 operations reference adaptation

Date: 2026-09-12

The `/operations` presentation adapts the selected visual reference assets from
`medguard79faf5a`: `miss20-dashboard/styles.css`, `App.jsx`,
`dashboard-look-1.jpg`, `dashboard-look-2.jpg`, and `investigation-look.jpg`.
They informed the calm green-and-neutral palette, monitoring/nav hierarchy,
large first-frame heading, 20px white cards, journey rail, event rail,
order-value card, and clean Investigation view.

The adaptation remains source-driven. The four journey steps render projection
facts for Receiving, Quality, Allocation, and Dispatch. Delivery confirmation
is separate; a synthetic carrier event is labelled as a declared carrier
confirmation, never an independently verified receipt. The PO line amount is
shown only when accepted financial evidence provides it, and is labelled as an
order value rather than revenue, invoice, payment, or profit.

Evidence freshness is visible in the monitoring bar and status ribbon. A
retained projection carries its as-of time; `CURRENT` inside a retained
financial snapshot means a record was available in that snapshot, not that the
source was freshly read. Capability labels describe available read-only
workflow capabilities, not an executed tool trace. Before an Ask returns a
provider, the UI says `Ask agent`.

The evidence drawer surfaces only accepted same-case facts, safely links
available document/readback URLs, closes with Escape or its backdrop, and
returns focus to its trigger. Attached photos keep their manual/not-analyzed
label; the absence state contains no stock image or inferred visual claim.

No reference scenario data, staged timers, fallback answers, historical trend,
financial/revenue/payment claim, or copied application logic was used.
