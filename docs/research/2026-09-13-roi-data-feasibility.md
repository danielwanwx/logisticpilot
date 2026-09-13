# LogisticPilot ROI data feasibility

September 13, 2026 UTC. Read-only repository assessment at `HEAD 2d43bb5`.
This inventory distinguishes fields supported by current product code, fields
available only through older LogisticPilot paths, fields that would require new
ERPNext reads, and tenant data already corroborated by dated evidence. It did
not query ERPNext, open a browser, call a model, inspect credentials, or verify
tenant-wide history. The pre-existing tracked modification to
`src/the_missing_20/agents/live_advisory.py` was not inspected or changed.

The tenant-evidence column is constrained by the
[current claim manifest](../submission/current-claim-manifest.md) and the
[current operations runbook](../runbooks/current-operations.md). “Verified”
means those dated artifacts corroborate the named case fact. It does not mean
the tenant has complete historical coverage for a rate, baseline, or causal ROI
claim.

## Availability legend

- **Current** — wired to the current DistributorOperations `/operations` path.
- **Legacy** — implemented in another LogisticPilot path but not wired to the
  current distributor workspace.
- **ERP-only/new** — the required ERPNext DocTypes and fields are identifiable,
  but no accepted current reader and metric exists.
- **Unavailable** — decisive source data or a defensible metric definition is
  absent.

## Metric availability matrix

| # | Candidate metric | Code and required ERPNext records | Missing join or data | Tenant data actually verified |
| ---: | --- | --- | --- | --- |
| 1 | Ordered, received, and missing quantity | **Current** [`distributor_erp.py::_snapshot`](../../src/the_missing_20/adapters/distributor_erp.py): Purchase Order Item `qty`, `received_qty`; Purchase Receipt Item `qty`; configured receipt markers. | Cross-PO history and complete pagination. | PO20: 40 ordered, 40 received, 0 missing; receipt sequence 20, 18, replacement 2. |
| 2 | Usable versus quality-held quantity | **Current** `distributor_erp.py::_snapshot`: Purchase Receipt warehouse, Stock Entry quality transfer, and Quality Inspection status. | This is configured-case stock, not enterprise Bin balance. | Historical LOT-B18 hold and release; completed PO20 has 0 held. |
| 3 | Quality-hold percentage | **Legacy** [`operational_metrics.py::business_impact`](../../src/the_missing_20/adapters/operational_metrics.py): `quality_hold / expected`; Purchase Receipt `rejected_qty` and release Stock Entry. | The current distributor stages receipts in quarantine instead of using Purchase Receipt rejected quantity; no current metric wiring. | The hold event is verified; no accepted percentage series. |
| 4 | Quality-hold value | **Legacy** `operational_metrics.py`: held quantity × PO unit cost. | No current value projection or historical time series; currency and UOM must agree. | PO20 inputs are verified at USD 4 per unit and 18 units held historically; no accepted historical value metric. |
| 5 | First-inspection lot failure frequency | **ERP-only/new**: Quality Inspection `name`, `inspection_type`, `item_code`, `batch_no`, `status`, `sample_size`, `reference_type`, `reference_name`, and readings; Stock Entry, receipt, PO, and supplier linkage. | No cross-case reader, first-versus-retest classification, supplier/specification/method cohort, complete denominator, or as-of cutoff. | PO20 has one verified first sample failure and later retest; no comparable-lot cohort. |
| 6 | Retest or replacement closure rate | **ERP-only/new**: Quality Inspection, Stock Entry, batch, and replacement receipt identities. | Original, retest, and replacement events must be classified without erasing the original failure; no denominator exists. | One PO20 retest and replacement pass are verified; no rate. |
| 7 | Sampled-unit nonconformance rate | **Unavailable**: current Quality Inspection supplies `sample_size` and a measurement/result, but no failing-unit count. | A failed sample cannot establish how many sampled units failed, much less the condition of the whole lot. | Not verified or derivable. |
| 8 | Receipt-to-first-inspection lead time or hold age | **Legacy field access** in [`erpnext_source.py::_business_metadata`](../../src/the_missing_20/adapters/erpnext_source.py): `posting_date`, `posting_time`, `transaction_date`, `creation`, and `modified`; equivalent Quality Inspection timestamps would also be required. | The current distributor projection omits Quality Inspection and Stock Entry timestamps and has no cross-record clock definition. | Not verified as a metric. |
| 9 | Supplier delivery completion | **Legacy** `operational_metrics.py`: received quantity / PO ordered quantity using Purchase Order and Purchase Receipt. | A rate needs a complete supplier cohort, horizon, cancellations, and returns. | One PO20 completion is verified; no supplier-level rate. |
| 10 | Supplier on-time delivery | **Legacy field access**: PO Item `schedule_date`; Purchase Receipt `posting_date` and `posting_time`. | Exact PO-line-to-PR-line join, promised-date revisions, timezone, returns, and a complete cohort. | Not verified. |
| 11 | Purchase receipt rejection rate | **Legacy** `erpnext_source.py::_purchase_summary`: Purchase Receipt Item `qty`, `received_qty`, `rejected_qty`, and `rejected_warehouse`. | The current distributor requires `rejected_qty=0` and stages quality-controlled stock in quarantine; its denominator/history is absent. | Not verified for PO20. |
| 12 | Supplier return quantity or value | **Partial Legacy guards** in [`normal_receipt_billing_source.py`](../../src/the_missing_20/adapters/normal_receipt_billing_source.py): Purchase Receipt and Purchase Invoice `is_return`, `return_against`, with exact PO/PR child links. `operational_metrics.py` handles signed return quantities defensively. | No aggregate return metric, credit valuation, return reason, claim/CAPA join, or current wiring. | No tenant return is verified. |
| 13 | Supplier claim incidence, recovery, or credit | **Unavailable/new**: would require an Issue or supplier-quality/CAPA record joined to a return Purchase Receipt, Purchase Invoice credit note, and possibly GL/Payment records. | No claim identity, status, reason, recovery amount, or native supplier-quality action exists in the current product. | None verified. |
| 14 | Purchase price variance | **Legacy** `operational_metrics.py::_price_comparison`: PO and Purchase Invoice Items `purchase_order`, `po_detail`, `item_code`, `uom`, `qty`, `net_rate`/`net_amount`, and currency. | Exact invoice lines and comparable UOM/currency; current `/operations` reads invoice totals but does not compute PPV. | PO price is verified; no linked PO20 Purchase Invoice or variance is verified. |
| 15 | Accounts-payable invoice hold value | **Legacy** `operational_metrics.py`: Purchase Invoice `on_hold` or payment-hold status and `grand_total`. | Complete invoice scope, currency, hold reason, and hold history. | No linked PO20 Purchase Invoice is verified; current evidence supports order amounts only. |
| 16 | Configured-case usable inventory or availability | **Current** `distributor_erp.py::_snapshot` usable quantity after quality release and dispatch; **Legacy** case balance and inventory-availability percentage. | Case balance is not enterprise available-to-promise. | PO20 case quantities are verified. |
| 17 | Enterprise on-hand or available-to-promise | **Legacy input support** in `operational_metrics.py` for a verified `stock_balance.on_hand` and `available_to_promise`. | Current distributor does not query Bin or Stock Ledger Entry; warehouse, company, item, and reservation scope are required. | Not verified for the current case. |
| 18 | Working capital at risk | **Legacy** `operational_metrics.py`: `(quality_hold + unresolved_receipt) × PO unit cost`. | This is snapshot exposure, not carrying cost; currency/UOM compatibility and time history are required. | Inputs are partly verified; no accepted PO20 working-capital metric exists. |
| 19 | Average inventory value or carrying cost | **ERP-only/new**: Stock Ledger Entry or reliable Bin snapshots, valuation/procurement cost, and a disclosed holding-cost rate. | Complete opening balance, transfers, returns, valuation method, time weighting, and an assumption ledger. | Not verified. |
| 20 | Backorder or shortage quantity | **Current** allocation rows expose requested, allocated, dispatched, and backorder quantities; `_snapshot` exposes missing receipt quantity. | Backorder semantics are configured-case policy, not all tenant demand. | PO20 A/B completion and the historical shortage are verified. |
| 21 | Order fill or dispatch rate | **Current** Sales Order requested quantity plus submitted Delivery Note quantity. | A rate needs a defined cohort/horizon and cancellation handling. | PO20 A25/B15 and Delivery Notes 20/5/13/2 are verified. |
| 22 | OTIF or perfect line fulfillment | **ERP-only/new**: Sales Order Item promised/delivery dates, Delivery Note posting time, and authoritative customer receipt or POD. | Current Delivery Note and Shipment prove dispatch, not customer receipt; retained delivery confirmations are synthetic. | Dispatch is verified; OTIF and physical customer receipt are not. |
| 23 | Dispatched order-line value | **Current inputs** in `distributor_erp.py::_financial_order`: Sales Order Item `qty`, `rate`, `net_amount`, currency, plus submitted Delivery Note quantity. | The current product does not calculate this field; it must remain order-line value, not revenue. | SO line amounts USD 150 and USD 90 and the Delivery Notes are verified; A20 × USD 6 = USD 120 is derivable. |
| 24 | Booked customer-order value | **Current** financial projection exposes Sales Order line net amount; **Legacy** `operational_metrics.py` calls the same concept `booked_revenue`. | Product language must retain commitment/order-value semantics. | USD 150 + USD 90 of customer-order line value is verified. |
| 25 | Billed net sales or invoice outstanding | **Current read support** in `distributor_erp.py::_related_invoices`: exact Sales Invoice-to-SO/`so_detail` link, `docstatus`, currency, `grand_total`, and `outstanding_amount`; **Legacy** net billed sales. | Current projection omits payments/GL and line net amount; returns, credit notes, tax scope, and horizon must be complete. | No linked PO20 Sales Invoice is verified. |
| 26 | Revenue protected or accelerated | **ERP-only plus evaluation**: Sales Order, Delivery Note, Sales Invoice timestamps, and a matched control or cancellation reason. | Requires a fixed cohort/horizon and counterfactual. If both branches ultimately bill, the result may be timing only. | Not verified. |
| 27 | Gross or contribution margin | **Unavailable/new**: Sales Invoice line net sales, Delivery Note/Stock Ledger/GL cost of goods, freight, variable labor, and returns. | No accepted cost allocation or GL read exists in the current distributor. PO-to-SO spread is not margin. | Not verified. |
| 28 | Cash conversion, DSO, or cash acceleration | **Unavailable/new**: Payment Entry, Payment Ledger or GL, invoice due/posting dates, and bank-clearance evidence. | No payment/bank reader, matched horizon, or opening AR/AP balance. | Not verified. |
| 29 | Model latency, tokens, and inference cost | **Current partial** [`distributor_allocation.py`](../../src/the_missing_20/agents/distributor_allocation.py) stores `usage.elapsed_ms` plus budget-ledger usage in the allocation decision. [`real_strands_matrix.py`](../../src/the_missing_20/evaluation/real_strands_matrix.py) records provider, tool calls, `latency_ms`, usage, and rubric results for the older evaluation path. | Current read-only Ask omits usage/latency from its visible conversation projection; infrastructure and review costs are absent. | Historical real model selections and some cost evidence are documented, but no production per-case cost baseline is verified. |
| 30 | Verified-case success, decision error, retry/rework, and active human time | **Partial current audit data** in [`distributor_operations.py`](../../src/the_missing_20/adapters/distributor_operations.py): event `occurred_at`, journal `recorded_at`, proposal `approved_at`, event results, and allocation retry rows. **Legacy evaluation** scores tools, citations, disposition, and unsafe claims. | No complete cross-case telemetry, declared task start/end, active-work intervals, touches, app switches, corrections, operator cohort, or matched control. Wall-clock/provider latency is not human effort. | PO20 has a 19-event journal and local replay evidence; no matched human time or error-reduction result is verified. |

## Feasible business loops

The strongest currently demonstrable impact loop is:

```text
incoming quality exception
  → quality hold or release evidence
  → contract-eligible customer allocation
  → reviewed pick and dispatch
  → native Delivery Note and Shipment readback
```

This loop already has the densest same-case source chain: Purchase Order,
Purchase Receipts, Quality Inspections, quality-release Stock Entries, Sales
Orders, Pick Lists, Delivery Notes, Shipments, exact approval state, and a local
journal. A rigorous evaluation can combine held/released/dispatched quantity,
dispatched order-line value, accepted-event-to-verified-readback time, decision
errors/corrections, retries, and total agent cost. Human effort requires a new
matched operator measurement; system latency cannot substitute for it.

Supplier-quality history is a useful adjacent loop, but the repository does not
yet provide a complete supplier/item/specification cohort or a supplier-claim
action/readback. It can support a disclosed synthetic risk signal and a local
QA follow-up draft after new source work, not verified supplier loss avoidance.

Revenue, contribution margin, cash acceleration, and production ROI require a
longer evidence chain: complete Sales Invoice and return/credit-note scope, GL
or Stock Ledger cost evidence, Payment Entry/bank timing, and a matched control
or documented counterfactual. Current evidence supports completed quantities
in one case and its dispatched order-line value, not a time-denominated
throughput improvement. Matched human effort, error reduction, and complete
per-case agent cost still need to be collected; they are proposed comparison
measures, not verified current results.

## Existing reusable boundaries

- [`operational_history.py`](../../src/the_missing_20/adapters/operational_history.py)
  provides append-only observation, provenance, coverage/exclusion, bounded
  queries, and minimum-baseline patterns. Its query and cohort are case-scoped,
  and its schema lacks supplier, lot, first/retest classification, sample scope,
  and inspection readings, so it cannot directly supply cross-lot quality
  history.
- `erpnext_source.py` allowlists business timestamps, quantities, prices,
  currencies, return relationships, and line identities and refuses incomplete
  bounded pages. It belongs to the older evidence path, not the current
  distributor projection.
- `distributor_erp.py` verifies a narrow configured case and exact native record
  relationships. Its safety comes from that scope; tenant-wide metric queries
  need separate completeness, pagination, deduplication, revision, and cohort
  rules rather than relaxing the current adapter.
- The current journal provides durable case events and approval/retry evidence,
  but it is not an operator-work logger or a long-term business warehouse.
