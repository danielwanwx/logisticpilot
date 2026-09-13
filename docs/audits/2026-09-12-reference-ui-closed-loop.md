# Reference UI closed-loop validation

Status: frontend and bounded local closed-loop validation are complete within the
scope below. This is not a fresh ERP dashboard, a physical delivery confirmation, a
held-out evaluation result, or evidence of multi-agent evaluation gain.

## Runtime and retained-event boundary

Validation used `/private/tmp/m20-restored-runtime-20260912` on port 8930. Its
retained snapshot has `as_of` `2026-09-11T05:51:50.322138Z`; it is not fresh ERP data.
Commit `79faf5a` is the visual-reference commit in the MedGuard repository, not a
The Missing 20 UI commit.

CUA clicked the historical **Confirm** action as `Synthetic Verification Operator —
isolated local replay`, not Daniel. The replay concerned proposal
`e1390bb4-950c-4841-8cff-07f92d3adc83` and event
`45bf34c9-262b-44fb-94a0-f4776d26130a`. That event occurred at
`2026-09-11T05:49:32.840Z` and was recorded at
`2026-09-11T05:51:50.322138Z`; the confirmation replay occurred at
`2026-09-13T03:41:42.908662Z`.

Repeating the exact API request preserved the same `approved_at` value and returned
`recovered: true`. The latest local replay reports `received=40`, `dispatched=40`,
and a synthetic confirmation. A post-freeze reload showed the retained confirmation
actor again without creating a fresh write.

## Read-only ERP comparison

The complete JSON in `/private/tmp/m20-loop-fresh-after-20260912.json` was equal to
the before-network capture. Its `CURRENT` values remain `received=40` and
`dispatched=40`; invoice and payment are not proven. The adapter returned
`delivery_confirmed=0`, which means this adapter response does not verify physical
receipt. It must not be interpreted as proof that no deliveries exist. The synthetic
projection's `40` is distinct from any ERP delivery evidence.

## Final UI answer and retained semantic defect

The final real Opus Ask rendered one semantic HTML table and correctly reported
`A=25` and `B=15`, which reconcile to `40`; it retained the source `as_of` and
said recorded delivery-confirmation values were synthetic and physical delivery
was not independently verified. Earlier real UI answers also identified PO line
`160` and the combined SO line value `240`.

One semantic defect remains. The earlier financial responses overgeneralize from missing invoice
evidence to the absence of payment records. That is unsupported: advance payments can
be recorded against a Sales Order or Purchase Order before an invoice, as documented
by [ERPNext's advance-payment entry guide](https://docs.frappe.io/erpnext/advance-payment-entry).
An unavailable source record is not global proof of no payment. This validation does
not claim that every semantic check passed.

## Browser and visual verification

The evidence drawer's four safe ERP, Airtable, Jira, and Slack links had their URLs
checked without opening an external destination; Escape returned focus. Browser error
and warning logs were empty (`[]`).

Focused UI checks passed 46 tests, the full JavaScript suite passed 147 tests, and
focused backend checks passed 56 tests. Final viewport checks found `scrollWidth`
equal to the viewport at 390, 625, and 1440 pixels. The Investigation view shows all
four source cards readably, with 324-pixel cards at the 390-pixel viewport. No visual
check remains pending.

- [Dashboard at 1440 pixels](assets/2026-09-12-reference-ui/dashboard-1440.png)
- [Mobile dashboard at 390 pixels](assets/2026-09-12-reference-ui/mobile-390.png)
- [Evidence drawer](assets/2026-09-12-reference-ui/evidence-drawer.png)
- [Investigation at desktop width](assets/2026-09-12-reference-ui/investigation.png)
- [Investigation at mobile width](assets/2026-09-12-reference-ui/investigation-mobile.png)
- [Dashboard at 625 pixels](assets/2026-09-12-reference-ui/dashboard-625.png)

The screenshots and local replay support the UI and bounded closed-loop behavior
described here. They do not change the stopped paired-evaluation outcome or create a
held-out result.
