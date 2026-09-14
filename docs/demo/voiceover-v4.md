# LogisticPilot voiceover v4

Status: narration reconciled with the primary agent's successful PO26 / SO20 rehearsal after recovery, September 14 UTC / September 13 Pacific. Ready to begin recording production. The fresh preparation, one confirmation and ERP readback passed; screenshots were inspected inline, but no standalone image assets or raw video were saved. Audio, Remotion composition, final playback and submission remain separate work. This replaces v3's spoken draft, not its production gates.

## ElevenLabs copy

Copy only the plain text in this block. Paragraphs correspond to the nine shot rows below; do not read the shot notes or claims notes aloud.

```text
Five questionable parts. Twenty ready to go. Should one receiving problem leave the whole customer order waiting? At a small parts distributor, the same person may receive stock, chase inspections, and answer the customer. Every exception adds another round of checking.

LogisticPilot helps that operator investigate the problem and keep eligible orders moving in ERPNext. Here, twenty-five parts arrive in two batches. Twenty have a recorded passing inspection. Five remain on hold. The operator needs a decision they can act on, with the evidence attached.

This demonstration uses a simulated business case, public reference photos, live Bedrock inference, and a real ERPNext demo tenant. I upload the held batch's photo and ask the agent to examine it. It asks me to confirm the batch again. I confirm it.

The Strands agent chooses the photo-analysis tool. The image reader flags visible corrosion, while the agent explains what inspection is still needed. A photograph cannot supply a missing measurement. That matters: the operator gets a useful next step without turning an uncertain image into permission to release stock.

Now I ask: can the other twenty move while these five stay held? The agent connects current stock, inspection status, and customer terms. With partial dispatch allowed, I ask it to prepare that dispatch. The order briefly fails to load. When it returns, I ask again. It prepares the supported twenty-unit action. The operator can now review the facts and proposed work together, instead of reconstructing the decision across separate records.

I check the customer order, batch, and quantity, then confirm. The application checks the current evidence before writing the approved operation to ERPNext. The agent prepares the work; the person authorizes it. The five held parts remain outside that approval.

Then we check the result. The native delivery record confirms twenty dispatched. The current batch view still shows five held. The operator can see what actually changed, and what still needs attention, beyond the agent's answer.

Strands handles the reasoning and evidence tools. Our application checks the proposed action, asks for human confirmation, carries it out, and reads the ERP result back.

For this case, twenty units progress to recorded dispatch while five stay held. The business opportunity is to keep eligible orders moving toward billing, while reducing manual cross-checking and repeated entry. Customer savings still need a measured pilot. LogisticPilot gives a small team a clear path from a receiving problem to a reviewed action and a verifiable result.
```

## Planned shots and timing

Editorial target: 4:40, leaving margin under five minutes. Times allow cursor action and reading; they are not measured runtime or model latency. Preserve the complete raw take when recording begins and label shortened processing waits. Product evidence must remain in one case; Remotion may frame it, never replace a missing result. PO26's screenshots were inspected inline, not saved as a recording asset pack. Its current result can be filmed now; a continuous before/after screen recording requires another isolated case and its own actual IDs. Do not replay PO26's completed action or reset its displayed quantities.

| Time | Paragraph | Actual screen action or planned graphic | Evidence needed before this narration is usable |
| --- | --- | --- | --- |
| 0:00–0:25 | 1 | Very short title over the real Dashboard; show the product within five seconds. Emphasize the goods and customer order, not a technology logo wall. | Loaded case; no fabricated lost-sale figure or customer testimonial. |
| 0:25–0:50 | 2 | Incident → selected B5 goods card; briefly show A20's separate passing inspection and return to B5. | Accepted rehearsal baseline: 25 received, 20 eligible/allocated, 5 held and zero dispatched. A20 PASS comes from the recorded inspection, not its clean photo. |
| 0:50–1:20 | 3 | Agent Upload → real file choice of licensed input03 → question → redundant batch question and operator confirmation. | Browser upload passed. Keep the extra confirmation visible; the operator had already supplied B5. A preloaded image is not a new upload. |
| 1:20–1:50 | 4 | Actual photo-analysis result; then the explanation of the remaining inspection. | Live analysis completed after the confirmation. The initial chat answer was generic; concrete findings appeared in the subsequent eligibility answer. Do not merge those into an invented first answer. |
| 1:50–2:45 | 5 | Eligibility question/answer → explicit preparation request → brief unavailable-state evidence → recovered view → identical retry → new action card. | First request produced zero proposals. The retry created the new PO26 / SO20 / A20 / 20 proposal without manual action-field entry. Preserve the recovery; shorten waits with a caption, not by inventing seamless success. |
| 2:45–3:15 | 6 | Exact order/batch/quantity card; one confirmation as POC reviewer; returned APPLIED state. | The primary agent accepted this operation once and inspected screenshots inline. Capture assets for the film remain to be recorded. |
| 3:15–3:50 | 7 | Check ERP → actual native Delivery Note in authenticated Chrome → current batch/Dashboard readback. | DN25 proves 20 dispatched; separate current view proves 5 held. Preserve the exact case and native IDs below. |
| 3:50–4:04 | 8 | One short diagram: application-supplied ERP evidence → Strands + Bedrock/tools → proposed action → human confirmation → ERP write/readback. The Strands node groups reasoning components; it does not assert an agent or invocation count. | About 14 seconds. Show application checks around action execution. No Graph/Swarm, historical SaaS handoffs or AgentCore deployment implied. |
| 4:04–4:40 | 9 | Actual 20 dispatched / 5 held result; end on the remaining inspection and product name. | A demo ERP dispatch result, not physical delivery or earned revenue. No percentage-efficiency, invented hours saved or realized postage savings. |

## Questions and rehearsal decision

Use ordinary requests, not a pasted expected answer. A suitable sequence is: “Look at this batch photo. What can you tell me, and what still needs checking?”; “Can the other stock move while this batch stays held?”; then the actual supported preparation request established by rehearsal. Adapt wording to the active batch and implementation without inserting the desired conclusions into the prompt.

The fresh-case path **passed after recovery** on PO26 / SO20. The wording above describes that accepted sequence, including the redundant batch confirmation and one failed preparation attempt. A new capture must follow its actual events: do not recreate the defects deliberately, and revise those two sentences if a new take differs. PO26 is now completed; for a live result walkthrough, narrate preparation and confirmation in past tense and show its current records. For a continuous new before/after take, use another isolated case. Never mix PO25's records with PO26's outcome.

## Claims notes — not spoken

- The application reads ERP before supplying the agent's bounded current case packet. Reading that packet through a tool is not a separate external ERP request on every tool invocation. Fresh proposal creation passed on the identical retry after the first source-read failure; no manual action-field entry supplied the proposal.
- The contextual assistant can pass an explicit supported preparation request through `PREPARE_ECONOMIC_SPLIT20` to `prepare_economic_proposal`, which invokes the existing Strands economic selector with four evidence tools. This is more than a claim that only one model-agent invocation exists, but it is not Graph/Swarm orchestration. Bedrock-backed photo analysis is also part of the current path. Review, Ask, Act and Verify are workflow stages, not four agents. No spoken agent count is needed.
- Revenue opportunity means progressing eligible fulfillment toward possible billing. The recorded case does not establish invoicing, earned revenue or physical delivery. Task reduction is the proposed value of gathering evidence and preparing supported work in context; no manual baseline, customer time saving or customer ROI has been measured.
- Keep postage out of this main narration. The selected split does not realize the illustrative $24.80 consolidation saving. Keep synthetic weekly history out of the impact proof.
- Evidence: [fresh rehearsal](../audits/2026-09-14-fresh-rehearsal.md), [current claim manifest](../submission/current-claim-manifest.md), [earlier assistant and ERP acceptance](../audits/2026-09-13-operations-assistant-acceptance.md), [goods flow acceptance](../audits/2026-09-14-incident-context-acceptance.md), [production gates](recording-brief-v3.md), [independent script review](../audits/2026-09-14-script-judge-review.md).

## Accepted rehearsal and retained first attempts

Primary-agent evidence received during the fresh PO26 / SO20 rehearsal: 25 received, 20 eligible and allocated, 5 held, zero dispatched at the baseline. The browser Agent Upload path successfully attached licensed input03. The first photo question explicitly named LOT-B5, but the assistant redundantly requested the lot. The operator replied, “This photo belongs to LOT-B5. Please inspect it.” The subsequent live analysis completed and returned observations of rust on bolts and nuts, a broken bolt and worn nuts; these remain model observations, not verified defect labels or a formal failed inspection. The five-unit hold remained in place.

The initial chat response emphasized guardrails rather than the specific findings. The next eligibility answer summarized those findings and correctly identified the twenty cleared units as eligible for partial dispatch, with B5 still requiring the 9.9–10.1 mm diameter check. The first explicit fresh-preparation request failed on a transient non-CURRENT ERP read. The UI briefly reported unavailable operation facts, then recovered; the local journal contained zero new proposals. One identical retry created a fresh proposal. The primary agent reviewed the PO26 / SO20 / LOT-A20 / 20 confirmation card and confirmed once as POC reviewer; execution returned APPLIED.

| Same-case proof | Accepted result reported by the primary agent |
| --- | --- |
| Case | `M20-DIST-ECONOMIC-REHEARSAL-20260914` |
| Purchase / customer order | `PUR-ORD-2026-00026` / `SAL-ORD-2026-00020` |
| Fresh proposal | `economic-76e4566cd3cce217460d9fb0f7534bd0`, prepared at 2026-09-14 05:48:31 UTC; Strands economic selector chose split20 using contract, quality, cost and operational evidence tools with five evidence citations |
| Delivery Note | `MAT-DN-2026-00025`; opened through the actual product link in signed-in Chrome; quantity 20, To Bill, visible Submitted activity, correct new customer |
| Pick List / Shipment | `STO-PICK-2026-00023` / `SHIPMENT-00023` |
| Independent current read | Check ERP, September 13 at 10:51 PM Pacific: 20 dispatched / 5 held |
| Dashboard / event journal | 20 dispatched / 5 awaiting release; four events, comprising the three baseline events plus Picked; no B5 FAIL event |

The Delivery Note's USD 120 amount is a demo document amount, not earned revenue; omit it from the impact claim. Screenshots of the fresh confirmation, native document and final Dashboard were inspected inline, but no standalone image assets or raw video were saved. Preserve the redundant lot confirmation and first failed preparation in the retained evidence and the recovery in this script. The lot-citation validation problem is an application/model-interface defect, not missing information supplied by the operator; raw citation output was not retained, so omission versus mismatch is undetermined. The transport cause of the ERP-read failure is also undetermined. The reviewer reconciled the primary agent's evidence without repeating runtime actions.

## 中文改写理由

开头先让评委看到一个人的工作压力：同一个人收货、追检验、答复客户；五件待检不应自动拖住另外二十件。中段明确 Agent 做了什么：选择图片分析工具、结合现有库存与订单条件、准备受约束的操作，而不是只描述用户依次点了哪些页面。审批和外部单据证明工作真的落到了 ERP。

价值表达落在“符合条件的履约继续推进”和“减少人工拼接信息、重复录入的机会”。二十件发运是演示结果，节省多少时间、增加多少收入仍需试点；不要用虚构金额削弱可信度。架构只留约十四秒，用推理、人工审批和实际 ERP 结果讲清职责，不靠 Agent 数量制造技术深度。新案例已在恢复后跑通，台词保留重复确认批次和一次连接失败，不把成功包装成毫无阻力；现在可以进入录制制作，尚没有最终成片。
