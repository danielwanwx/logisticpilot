# LogisticPilot: business-impact demo design

September 13, 2026 UTC. **Proposed implementation design, not implemented or measured.** The user accepted the quality-exception fulfillment scenario and requested stronger economic value, efficiency, error reduction, and quality-trend detection. This expands the agreed story; the complete implementation scope below awaits one review.

## Product outcome

Help an ERPNext parts-distribution operator resolve an incoming-quality exception, keep eligible customer commitments moving, and identify repeated supplier-quality problems before the next affected receipt. Replace repetitive evidence gathering, reconciliation and proposal preparation; retain human authority for consequential actions.

The film must show an evidence-dependent decision and its verified consequence. More metrics alone do not establish agent value. Incoming inspection is within this product's scope; manufacturing throughput and production yield require production records not present in the current case.

## Alternatives and choice

1. Add financial and efficiency cards to the current case: fastest, but leaves the agent's incremental contribution unresolved.
2. **Recommended:** add a small evidence investigation joining comparable inspection history, current stock and applicable contract evidence; connect its reviewed conclusion to the existing approval/execution path, and measure that task.
3. Expand into production planning, supplier switching, invoicing and cash collection: potentially richer value, but creates several new business systems before the deadline. Defer.

## Film and visible results

| Scene | Visible action and evidence | Business meaning |
| --- | --- | --- |
| Opening | A25/B15 demand; 38 received; LOT-A20 qualified and unshipped; LOT-B18 held; 2 missing. Synthetic demo inputs are visible. | One quality incident threatens two customer commitments; some stock remains usable. |
| Investigate | A new accepted inspection revision triggers one bounded investigation. Show actual executed source queries, short cited findings, applicable partial-shipment terms, and comparable first-inspection history. | Reduces manual record collection and identifies recurring risk; measured savings remain separate. |
| Decide | Explain why held LOT-B cannot supply either customer and why the eligible order can use LOT-A20. Show order, lot, quantity, applicable terms and unresolved evidence. | The operator receives an actionable proposal, not only an anomaly summary. |
| Execute | Human reviews the exact proposal. The supported physical-event/dispatch workflow executes only within its approved scope, followed by native ERP readback. | Demonstrates 20 units dispatched while 18 remain held and 2 remain short. A recommendation is not counted as execution. |
| Prevent recurrence | Show the contributing historical reports and a supplier-QA follow-up draft linked to this incident. No message is sent, supplier changed, or stock released automatically. | Makes a recurring pattern actionable before another receipt; avoided future loss remains potential. |
| Measure | A compact card shows observed task correctness, active operator effort where measured, verification time, model cost and failure count. Include a separately labeled changed-contract counterexample. | Establishes bounded value against a fair baseline, without claiming production ROI. |

Keep the main film below five minutes. A later retest/replacement belongs in an explicitly time-separated epilogue only if useful. Historical PO20 cannot be reused with altered chronology: its A20 dispatch preceded LOT-B failure. Create a separate isolated case after the design and external-effect scope are settled; preserve completed PO20.

The historical signal does not justify releasing LOT-A: its own accepted quality evidence and customer terms do. Show two distinct consequences of the investigation: fulfill eligible demand now, and prepare a specific supplier-quality follow-up. Do not block unrelated qualified stock merely because the trend looks worse.

## Impact measures and claim rules

| Measure | Calculation and evidence | Permitted interpretation |
| --- | --- | --- |
| Dispatched quantity and associated order-line amount | Same-case native Delivery Note readback; linked Sales Order unit price and currency. At existing demo terms, 20 × USD 6 = USD 120. | USD 120 of order-line value dispatched. Not incremental revenue, profit, cash collected, or proven loss avoided. Partial A20 does not mean the full A25 order was fulfilled. |
| Operator effort | Active human work measured on comparable tasks with and without the agent; record review/correction effort, failures and incomplete cases. | Observed minutes per task in this small study. Model latency and wall-clock waiting are separate. Without a human measurement, do not display labor saved. |
| Decision quality | Correct permitted allocation, correct lot/quality scope, justified missing-evidence states, unsupported conclusions, and unsafe proposed/executed actions over every attempted case. | Task-level error results. A deterministic gate's safety cannot be attributed entirely to model reasoning. |
| Detection and verified-resolution time | Accepted source-event timestamp → alert; operator task start → native verified result. Preserve ingestion time and source occurrence time separately. | Measured response to observed events. No claim of real-time physical detection or earlier warning than humans without a measured comparator. |
| Potential economic value | Customer-adjustable volume × measured effort reduction × loaded labor rate, less inference and operating/review costs. | Capacity-value estimate with visible assumptions; freed time is not automatically reduced payroll. Avoid summing overlapping revenue, inventory, labor and risk benefits. |

Use a qualitative value chain until the matching measurements exist: faster investigation can reduce delay; scoped decisions can reduce rework and erroneous releases; earlier repeated-risk review can reduce future disruption. These are hypotheses to validate with customers.

## Minimal historical quality slice

Use an explicitly synthetic, inspectable set of independent first-inspection lot records to demonstrate the historical query path. Reuse authorized comparable native history only if its completeness and provenance are verified. Do not describe generated history as months of customer operations.

The proposed demonstration fixture has 20 independent historical lots: ten earlier and ten recent, with one and four first-inspection failures respectively. All share supplier, item, specification version and inspection method. These numbers are fixture design, not observed results. Report **first-inspection batch failure frequency** and both denominators. They do not establish unit defect rate, manufacturing yield, statistical significance, root cause, or forecast accuracy.

Each source record needs a stable lot/report identity, first-inspection timestamp, supplier, item, specification/method, first result, provenance, and source link or inspectable fixture reference. Deduplicate revisions; exclude cancelled records; keep retests separate. A later retest must not erase the original failure. The current incident is excluded from earlier-history comparison windows. Missing or incomparable history returns insufficient evidence.

A disclosed demo policy threshold can trigger review; it is not a learned statistical control limit. Deterministic code computes counts and applies the configured trigger. The agent selects relevant evidence queries, checks comparability and applicability, explains what is and is not supported, joins the result to current commitments, and prepares the next action. There is no autonomous supplier blacklisting or quality release.

## Architecture and interaction boundary

- Keep the current `/operations` visual system and ERP adapter. Add a compact impact panel and a clickable historical signal with an evidence drawer; avoid a separate BI dashboard.
- Expose bounded source-query tools for the relevant history, inspection reports, contract evidence and current state. Queries must select actual records; do not place the complete answer-bearing snapshot, expected outcome, or precomputed plan in the same model input when testing investigation value.
- Keep arithmetic, quantity conservation and execution permission checks deterministic. Model-derived contract interpretation is a cited proposal until reviewed; it must not silently overwrite authoritative structured terms.
- Preserve the current distinction between an operator-declared physical event and an agent recommendation. If linking a recommendation to approval, bind its source revision and exact proposed effect, then verify again before execution. A dispatch still requires the supported pick/evidence preconditions.
- Record actual tool calls, start/end times, model usage, decision and cited source identities. Available-tool badges are not an execution trace. Investigate once per relevant accepted revision; no periodic LLM call per chart point.
- Scope automatic detection to new accepted evidence observed while the operations workspace is active. Reuse its existing refresh path and deduplicate revisions. The present product has no independent background trend monitor; do not claim 24/7 monitoring. Offline source changes are detected when the workspace next reads them, with that latency disclosed.
- Source outages, stale evidence, incomparable history, absent terms or ambiguous scope produce needs-evidence states. A trend cannot override a current quality hold. Approval remains necessary for native effects; provider errors cannot render a success result.

The coordinator's source review found no existing comparable inspection-history dataset or current operations trend wiring. `operational_history.py` belongs to the older AgentPlatform path and groups by case; it lacks supplier/lot/first-inspection fields. Reuse its provenance patterns rather than pretending its records form the new cohort. Existing `fulfillmentBenchmark()` measures configured commitments and dispatch, not historical efficiency. Current native inspections have useful report/scope fields, but cross-case supplier linkage is unverified. Start with a disclosed synthetic linked fixture and a bounded exact-record interface; native historical coverage remains a separate future verification. No new CAPA integration is required for the QA follow-up draft.

## Acceptance and sequencing

1. Freeze baseline and proposed responsibility before calls. Compare the existing rules/workflow with the candidate on the same facts and authority; use a single native Strands agent first. No Graph promotion without demonstrated benefit.
2. Use four independent cases with two candidate repetitions: the approved base case with comparable history and a specific QA follow-up; insufficient history (no invented trend); misleading other-supplier/item/specification records and passing retests (correct cohort, original failure not erased); A partial delivery prohibited (B15 eligible, five left). Preserve the current LOT-B hold in all relevant cases. Keep answer keys outside inputs. Include baseline strengths and all failures; focused deterministic tests also cover insufficient retest scope.
3. If measuring human savings, use matched unseen variants and alternate order to reduce rehearsal effects; report participant/sample count and individual times, not a production percentage. A developer participant makes this a developer pilot. Another agent's timing is not human effort. If no operator study is available, show technical duration/cost and clearly leave human savings unmeasured. Blocking a deliberately unsafe test action demonstrates a control, not observed reduction in human errors.
4. Primary and independent reviewer inspect the actual diff and relevant failure tests. Verify real model behavior separately from deterministic/unit tests. Promote only useful, cited behavior without critical authority/quantity errors.
5. In a separately scoped fresh case, verify the actual interface, approval, native dispatch and readback. Check remaining held/short quantities, replay protection, evidence navigation and changed-contract behavior. Repair already observed routing and empty-question feedback within the UI slice.
6. Supply free judge access to the represented workflow and public video. Preserve any simulated/retained boundaries in both. Those remain open submission requirements, not outcomes of this design.

Implementation routing: coordinator assigns coupled history/query/proposal/telemetry changes to Terra Max and narrow UI changes to Luna Max. Root reviews actual changes and acceptance; independent reviewer challenges business and award claims. Commit and push each coherent verified milestone. No implementation, paid comparison, new ERP record or external message is authorized merely by this document.

## Sources and existing evidence

- [AWS: Measuring success and ROI](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-economics/measuring-success.html), checked September 13 UTC: measure against process costs and operational baselines, including errors, speed and consistency. It does not validate this project's ROI.
- [NIST: Proportions control charts](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc332.htm), checked September 13 UTC: sampled unit nonconformance depends on defective count and sample size under stated assumptions. Our proposed lot-first-inspection metric is explicitly different.
- [ERPNext: Delivery Note](https://docs.frappe.io/erpnext/delivery-note), checked September 13 UTC; the source document boundary is distinct from invoicing and payment.
- [Historical benchmark design](../research/2026-09-08-operational-history-benchmark-design.md), [earlier causal-value plan](../research/2026-09-07-revenue-efficiency-causal-validation.md), [scenario alignment](2026-09-13-demo-scenario-alignment.md), [current claim manifest](../submission/current-claim-manifest.md), [acceptance contract](../audits/2026-09-13-demo-acceptance-contract.md). Earlier automotive dollar values and historic claims do not carry into LogisticPilot's current case.
