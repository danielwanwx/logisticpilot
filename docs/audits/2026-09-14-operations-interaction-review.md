# Dashboard / Operations interaction review — September 14, 2026

Independent read-only product review of `http://127.0.0.1:8933/operations`, using a dedicated real Chrome tab and CUA screenshots. Baseline loaded assets: `distributor-operations.js?v=20260913-two-view-v9`, matching CSS, and `style.css?v=source-driven-final-v32`. No reload was performed after opening this baseline; later implementation changes require separate verification. View navigation stayed within the loaded app. Viewport screenshots were 1512 × 823.

Case observed: PO `PUR-ORD-2026-00025`, SO `SAL-ORD-2026-00019`, 25 received, LOT-A20 already dispatched (20), LOT-B5 held (5), allocation now 0. Execution was already APPLIED before this review. No write, approval, photo analysis, upload, or Agent question was submitted. Only this Markdown file was changed; the primary agent owns implementation and delivery.

## Findings

### P1 — Completed execution and current dispatch blockers appear contradictory

Opening **View decision details** shows “Selected plan: 20 now, 5 later”, “Native readback APPLIED”, approval identity/time, and the three native document IDs. Immediately below, **AGENT RECOMMENDATION** says “No agent comparison yet”, and **DISPATCH CHECKS** says “NEEDS EVIDENCE” with `RAW_A20_USABLE_STOCK_INSUFFICIENT` and `RAW_SO25_ALLOCATION_INSUFFICIENT`. Screenshots show all three sections together. The present 0-stock/allocation state can be correct after execution, but the UI makes the completed plan look unsupported or failed. Label the completed execution separately from a new dispatch's current prerequisites; show or explicitly distinguish historical decision evidence. Do not imply a fresh comparison was performed.

### P1 — The hold route does not land on the affected lot/diagnosis

Dashboard **Review hold** changes the URL to `?view=operations#ops-alert-1`, but the screenshot remains at the top of Receiving. The visible context says “LOT-A20, LOT-B5” and “25 units received · 0 usable”; Findings is below the fold. Findings then shows “5 held · Inspection needed” and SO19 with 5 backordered, without naming LOT-B5. The explicit LOT-B5 → held 5 → affected SO19 relation only becomes visible inside **Inspection details** or photo history. Put the affected lot and its held quantity alongside Findings and make the hold link target that visible incident. Retain compact copy.

### P1 — Native execution documents are not actionable readback links

Dashboard “ERP evidence MAT-DN-2026-00024 RECORDED” is plain text. **View execution details** names Delivery Note, Pick List and Shipment in a small paragraph, also plain text. The evidence drawer renders the native document objects, URLs, approval and proposal data as one long JSON-like text run. The drawer's PO link works, but the execution record cannot be opened from those displayed IDs. Give each native execution record a concise external link and keep raw internals out of the business detail. An actual external purchase order was opened successfully; no authentication blocker exists for that tested route.

### P1 — Background refresh closes nested evidence during review

On two occasions, an opened photo observation/source disclosure was replaced while reading; the next click found a detached node, and the refreshed accessibility state showed all photo observation disclosures collapsed while **View photo history** remained open. This was observed without reloading or navigating away. It interrupts the exact evidence walkthrough a recording needs. Preserve nested disclosure state across projection refreshes, or avoid replacing unchanged history content. This is an observed interaction failure; its implementation cause was not investigated.

### P2 — Inspection details uses only a narrow fraction of the receiving card

The expanded inline inspection panel is approximately 300px wide inside a roughly 790px card, with over 400px unused to its right. Three tiny fact columns wrap the configured item and lot into many lines, and the fourth photo-scope fact occupies another row. The operator must scroll through the narrow panel to reach the affected order and **Open economic decision**. The same information in photo history spans the full card and is substantially more legible. Let this focused disclosure use the available width, without changing the approved composition.

### P2 — Evidence history is dense and starts with superseded material

Seven photo cards render in three narrow columns. The latest close-detail photo is at the end; superseded LOT-X9 label and sky photograph appear before it. Each card repeats identity, guidance and caveats, making it hard to locate the currently relevant evidence. Keep the history available, but lead with the selected/latest relevant photo and a concise result. Expanded source/model information is correctly on demand, although long revision strings still wrap awkwardly.

### P2 — Source drawer and full-evidence destination do not explain the decision

**Supporting evidence** shows named contract, quality and fit sources as nonclickable synthetic references; only USPS is a working external link. These chips do not reveal the actual cost comparison or fit numbers. **Open full operations evidence** changes the hash to `#ops-details` without revealing an additional visible evidence section. The drawer also says “7 attached receiving evidence photos; manual photo · not analyzed” although the seven history cards contain COMPLETE analyses; distinguish the selected intake state from stored analysis history.

## Controls actually exercised

| Area | Clicks / verified result |
| --- | --- |
| Dashboard navigation | Dashboard, Operations and logo links; **Check incoming photo**, **Review in Operations**, **Review next action**, **Review hold**. Photo links reach `#ops-photo-intake`; action link reaches `#ops-economic-panel`; hold destination issue described above. |
| Dashboard disclosures | Receiving check collapsed and expanded; evidence drawer opened and closed; Ask Agent drawer opened, focused the question field, and closed. No question submitted. |
| Receiving disclosures | **Edit photo details**, ERP lot and purpose dropdowns, **Inspection details**, **View photo history**, **Edit details** opened and closed. Both lot options and all three photo purposes inspected. |
| Manual event templates | Selected Arrival, Inspection, Picked, Carrier Pickup and Delivery one at a time; verified their corresponding fields. Restored “Choose an approved event…”. Did not prepare anything. |
| All seven photo cards | Clicked each image expansion and collapse; clicked **Review / retry this photo** on each and verified selected-photo intake/result. This selects existing evidence without analysis. Opened each **View observation details**, nested **View source and model evidence**, and nested **View model stages**; inspected content then closed. Latest selected-photo inline copies of these disclosures also inspected. |
| Photo findings inspected | LOT-X9 mismatch; corroded components; LOT-A20 no visible damage; irrelevant sky photograph; damaged carton overview; matching LOT-B5 label; latest damaged/open carton detail. All retain the boundary that visible damage/no damage is not quality clearance. |
| Inspection navigation | **Open economic decision** reached action panel and expanded it. Receiving thumbnail **View receiving photo history** revealed history. |
| Action disclosures | **Next action** toggle, **View execution details**, **Supporting evidence**, **View decision details** opened/reviewed/closed. **Open evidence drawer** and **Open full operations evidence** exercised. |
| External read | Drawer PO link opened real ERPNext PO25. Verified supplier, To Bill, quantity 25, USD 4/unit and USD 100 total. USPS link opened Notice 123, effective July 12, 2026. No login prompt. |
| Benchmarks | Scrolled and visually inspected always-expanded trends and eight weekly records; “Demo history” and current-order metrics are visibly separated. No interactive chart controls were exposed. |

The seven image-expansion states were verified, but expansion can move later images below the current viewport rather than keeping the enlarged image in view; screenshots of some intermediate cards captured the space before the expanded image. All seven image contents were visible in the history thumbnails or selected-photo intake, with full expanded screenshots for the mismatch label, sky and latest carton.

Not exercised: Upload/file chooser, Take another photo, Analyze photo, Prepare for approval, approval/execution buttons, Agent suggestions/Ask, microphone Dictate, or disabled Read. These either mutate/cost money, open the known problematic chooser, require microphone permission, or were unavailable. Native Delivery Note/Pick List/Shipment and SO/lot records were not opened because this baseline exposes no direct clickable link to them. No claim of external dispatch-document verification is made here. This audit does not test a pre-approval case or narrow-screen layout. Review-created Chrome tabs were closed; unrelated user tabs were untouched.

## Proposed recording sequence — 2 minutes 50 seconds

1. **0:00–0:20, Dashboard:** “One customer order for 25 components. Twenty have dispatched; five remain held.” Show journey and current quantities. Treat allocation/usable as current availability, not cumulative throughput.
2. **0:20–0:45, Operations incident:** Follow the hold to LOT-B5, its five held units and SO19's five-unit remainder. Show the relationship explicitly after the navigation/context fixes. Do not narrate this as a fresh incident on an unrelated order.
3. **0:45–1:15, evidence:** Select one relevant LOT-B5 photo and its concise damage result, then show inspection status. Explain that a photo flags exterior condition; operator inspection controls release. Avoid the full seven-card history during the main story.
4. **1:15–1:45, Agent diagnosis:** Use the primary agent's separately verified current-case answer to explain the held remainder and next inspection step. Do not claim this audit submitted or validated that answer. Keep the answer short enough to read on screen.
5. **1:45–2:25, action and ERP:** Show the already-applied split plan, explicit approval and execution result. Open its linked Delivery Note or Shipment after links are implemented and independently verified. Do not replay dispatch against this already-dispatched case. The tested PO link can establish order identity but cannot substitute for dispatch readback.
6. **2:25–2:50, outcome:** Return to 20 dispatched / 5 held. Close with the specific remaining inspection task. If benchmarks appear, identify them verbally as illustrative demo history; do not claim measured agent savings.

Recording readiness: the visual identity and two-view structure are coherent, and the real PO link works. Resolve the four P1 clarity/interaction findings and separately verify the native dispatch link plus the actual Agent answer before recording this sequence.
