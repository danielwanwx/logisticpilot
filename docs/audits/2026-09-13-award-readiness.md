# LogisticPilot — closed-loop verification and strict judge review

Date: September 13, 2026 UTC / September 12 Pacific. These are internal reviewer scores, not organizer scores or estimated award probabilities.

## Verdict

**The bounded historical PO20 demo loop is supported. The current retained review and real model conversation work. The competition entry is not yet award-ready.** The remaining decisive weaknesses are judge access, public presentation completion, and evidence that agent reasoning adds value beyond deterministic rules on unseen cases.

The product direction remains credible: help an ERPNext parts-distribution operator decide what can ship during a receiving/quality exception, then verify the supported operation. Do not broaden it into a generic logistics copilot or claim novelty merely from multiple agents and SaaS logos.

## What was verified again

| Check | New result and scope |
| --- | --- |
| Fresh source read before browser questions | Real ERPNext adapter returned `CURRENT`: 40 ordered, received and dispatched; zero held, missing and allocated; 5 cartons. |
| Fresh source read after browser questions | Complete adapter response was identical to the before response. No native business action was requested during this audit. Private raw responses are retained outside Git; the public case/document identifiers are in the claim manifest. |
| Real model question 1 | Browser request through Strands/Bedrock `us.anthropic.claude-opus-4-6-v1` distinguished the failed 2-unit sample from whole-lot defect proof, identified the declared passing retest and LOT-B shipments A5/B13, and denied independent physical-delivery proof. |
| Real model question 2 | When explicitly challenged, the answer said missing invoices do not rule out advances, identified the absent Payment Entry/ledger checks, and distinguished USD160/150/90 order values from payment. It did not query live ERP. |
| Answer quality limits | Question 1 was excessively long and included malformed Markdown tables. Question 2 still used overbroad intermediate wording such as “No invoice exists to pay against” before qualifying its evidence scope. The explicit challenge is not evidence that ordinary payment questions are generally reliable. |
| Browser state | Title is LogisticPilot; source banner remains retained/as-of; source drawer opens four case-linked records; Escape closes it. Historical confirmation remains attributed to Synthetic Verification Operator, not a real manager identity. |
| Responsive rendering | Desktop 1440px screenshot inspected; 390px mobile document width equals viewport width, with no horizontal overflow. |
| Focused acceptance | 46 existing operations JavaScript tests passed after the branding edits. No backend logic was changed by this milestone. Earlier 147 full JavaScript and 56 backend operations passes remain dated September 12 evidence, not new runs today. |

New real responses and screenshots: [quality answer](assets/2026-09-13-judge/quality-answer.txt), [financial answer](assets/2026-09-13-judge/finance-answer.txt), [dashboard](assets/2026-09-13-judge/dashboard.png), [evidence drawer](assets/2026-09-13-judge/evidence-drawer.png), [mobile](assets/2026-09-13-judge/mobile.png). These contain declared competition-demo records, not production customer information.

## What “closed loop” means here

Historical case `M20-DIST-COMPONENT-V2-20260910` / `PUR-ORD-2026-00020` recorded receipt 20 + 18 + replacement 2, conservative LOT-B hold after a failed sample, declared whole-lot retest/release, customer-contract selections, and dispatch 20 + 5 + 13 + 2 to A25/B15. Named native ERP documents, a 19-event local journal, and historical same-case collaboration readbacks support that record.

Today's fresh ERP read corroborates its end state. Today's retained UI does not reenact the historical writes or refresh every connected application. Synthetic carrier confirmations do not prove physical receipt. PO/customer order values do not prove invoicing or payment. The fresh adapter's delivery-confirmed default of zero also does not prove nondelivery. This is fulfillment-record closure in a bounded demo, not physical-world or order-to-cash closure.

See the [independent closure review](2026-09-13-independent-closure-review.md), [PO20 rehearsal](../submission/video-v1/REHEARSAL-V2.md), [journal audit](../submission/video-v1/SOL-REVIEW-V2.md), and [current claim manifest](../submission/current-claim-manifest.md). The prior exact historical-confirmation replay test is documented in the [September 12 UI audit](2026-09-12-reference-ui-closed-loop.md); this review did not execute another native business case.

## Five equally weighted criteria

The official rubric uses five equally weighted criteria; Technical Implementation is the first tie-breaker. Our scale is 0–5 per criterion, totaling 25. [Official rules](https://agentsforhumans.devpost.com/rules)

| Criterion | Score | Strength a judge can inspect | Likely criticism | Concrete next fix |
| --- | ---: | --- | --- | --- |
| Technical Implementation | 3.5/5 | Real Strands/Bedrock, native ERP effects and readback in the historical demo, exact local approval/replay boundaries, honest failure states. | Clean clone cannot reproduce current connected workflow; current questions mainly reason over a supplied snapshot; no completed current held-out Graph result. | Deliver a free, reproducible judge route. Then compare rules-only and one Strands agent on a frozen small unseen conflict set; add Graph only if it wins a measured criterion. |
| Design | 3.5/5 | Coherent green/neutral workspace, quantities/journey/events, mobile layout, source drawer and visible provenance. | A completed case is a weak first-use experience; real answers are long and sometimes render as raw table syntax; historical confirmation can require explanation. | Present one decision card with facts, uncertainty, proposed option and required approval. Put detail behind evidence drawers; rerun the two observed malformed/verbose responses. |
| Potential Impact | 3/5 | Specific operator, exception and outcome; avoids blocking unrelated eligible fulfillment while protecting affected stock. | No distributor interviews, observed baseline review time, adoption evidence or measured operational benefit. | One real operator walkthrough with a clearly disclosed sample; measure time, unnecessary holds and correct escalations against existing work. Do not fabricate ROI. |
| Creativity & Originality | 3/5 | Domain-specific distinction between shortage, sample failure, conservative lot hold and contract-dependent fulfillment; execution/readback closes a useful boundary. | Microsoft/Oracle already pursue supply-chain AI and orchestration. Agent count and integrations are not a moat; the contract options may appear like ordinary workflow rules. | Show a non-obvious evidence conflict that changes the admissible action and a second unseen case demonstrating reasoning value. Narrow the pitch to ERPNext exception handling. |
| Presentation | 2/5 | A reviewed 264.20-second local English film and real screenshots already exist; story can be made concrete around PO20. | No verified public YouTube/Vimeo URL or complete judge-access route; draft was MedGuard at audit start; older linked evidence described other cases. | Restore all Devpost fields/assets, publish the reviewed film through the authorized release process, verify public playback/access, then complete entrant attestations and submission. |

**Current total: 15/25 (60/100).** This is a strict assessment of the current deliverable, not a prediction. Excluding Presentation, the four product/engineering dimensions average 3.25/5. It is a credible integrated prototype with award potential, but a high probability of winning cannot be inferred without knowing the competing submissions and judges' decisions.

The local film review is accepted as a dated independent review, not represented as a new frame-by-frame review during this audit. Likewise, earlier multi-agent experiments are not silently reused as current product acceptance.

## Prioritized gap list

1. **P0 — judge access and required public video.** A private configuration dependency is a real access gap. The rules allow a working website/demo/test build, but require free judging access. Public video is required. Passing local tests does not resolve either gate.
2. **P0 — consistent public claims.** Resolved in this documentation pass by introducing one PO20 claim manifest and marking older matrices/statuses historical. Finish matching Devpost title, story, track, repo and visuals to it; keep final publication distinct from draft saves.
3. **P1 — financial answer overreach.** Prior real ordinary questions inferred missing payment from missing invoices. Today's explicit counterexample produces the right caveat, but still has some absolute invoice wording. Acceptance requires neutral questions plus advance/unapplied-payment cases, with assertions tied to actually queried sources.
4. **P1 — agent increment unproven.** New Graph/Evals work stopped without a held-out decision. Freeze the single-agent baseline and include incomplete evidence, stale approvals, changed partial-shipment terms and conflicting inspection coverage. Report complete/incorrect/abstained separately, plus latency/cost. Do not optimize for agent count.
5. **P1 — low-friction decision experience.** Improve the initial exception view and short answer structure; preserve the observed malformed table as a regression example. Cosmetic polish alone does not solve the workflow gap.
6. **P2 — scope/generalization.** Current source records and operator identity are demo-scoped. Trend monitoring needs history/denominators; new scenarios need explicit policies/connectors. Neither is demonstrated by changing a prompt.

For the remaining weekend, close release gates first, then the financial-language and one-decision interaction defects. Do not start a new broad multi-agent architecture or trend-monitoring product before the entry is reproducibly inspectable.

## Two submissions: permitted, but not automatically a better strategy

The [official rules and FAQ review](../research/2026-09-13-multiple-submissions-rules.md) confirms that one entrant may submit multiple substantially different projects. Each project chooses one track and may win one prize. No published entrant-wide prize cap was found. Shared/prior work must be disclosed; a rename alone does not make a new project. The local repository history begins August 24, inside the event window, but history alone cannot prove the origin of every incorporated component.

LogisticPilot's professional ERP fulfillment workflow and MedGuard's consumer supplement-label/evidence workflow plausibly qualify as different products. That is our inference, not organizer pre-approval. MedGuard's source-of-truth submission copy describes live NIH/openFDA retrieval and human label confirmation, with small curated interaction/dosage references. Camera analysis, whole-cabinet interaction assessment, autonomous monitoring and clinical validation remain outside its demonstrated scope. This turn did not perform a fresh MedGuard model/browser audit, and its old baseline score is not reused as a current score.

**Recommendation:** retain LogisticPilot as the primary entry. Consider a separate MedGuard entry only after LogisticPilot has verified public video and judge access, and only if MedGuard can independently meet those gates without weakening the primary entry. The two outcomes are not independent lottery tickets, so “two projects doubles the chance” is unsupported.
