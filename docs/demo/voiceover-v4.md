# LogisticPilot voiceover v4

Status: proposed narration and shot plan, September 14 UTC / September 13 Pacific. Documentation only; no new case, fresh approval take, audio, Remotion composition or finished film is established by this script. The primary agent must reconcile the narration with the actual rehearsal before generating final audio. This replaces v3's spoken draft, not its evidence and production gates.

## ElevenLabs copy

Copy only the plain text in this block. Paragraphs correspond to the nine shot rows below; do not read the shot notes or claims notes aloud.

```text
Five questionable parts. Twenty ready to go. Should one receiving problem leave the whole customer order waiting? At a small parts distributor, the same person may receive stock, chase inspections, and answer the customer. Every exception adds another round of checking.

LogisticPilot helps that operator investigate the problem and keep eligible orders moving in ERPNext. Here, twenty-five parts arrive in two batches. Twenty have a recorded passing inspection. Five remain on hold. The operator needs a decision they can act on, with the evidence attached.

This demonstration uses a simulated business case, public reference photos, live Bedrock inference, and a real ERPNext demo tenant. I select the held batch and ask the agent to examine its photo.

The Strands agent chooses the photo-analysis tool. The image reader flags visible corrosion, while the agent explains what inspection is still needed. A photograph cannot supply a missing measurement. That matters: the operator gets a useful next step without turning an uncertain image into permission to release stock.

Now I ask: can the other twenty move while these five stay held? The agent uses the current case evidence to connect available stock, inspection status, and customer terms. With partial dispatch allowed, I ask it to prepare that dispatch. It prepares the supported twenty-unit action. This brings the relevant facts and proposed work together, so the operator can review one decision instead of reconstructing it across separate records.

I check the customer order, batch, and quantity, then confirm. The application checks the current evidence before writing the approved operation to ERPNext. The agent prepares the work; the person authorizes it. The five held parts remain outside that approval.

Then we check the result. The native delivery record confirms twenty dispatched. The current batch view still shows five held. The operator can see what actually changed, and what still needs attention, beyond the agent's answer.

Strands handles the reasoning and evidence tools. Our application checks the proposed action, asks for human confirmation, carries it out, and reads the ERP result back.

For this case, twenty units progress to recorded dispatch while five stay held. The business opportunity is to keep eligible orders moving toward billing, while reducing manual cross-checking and repeated entry. Customer savings still need a measured pilot. LogisticPilot gives a small team a clear path from a receiving problem to a reviewed action and a verifiable result.
```

## Planned shots and timing

Editorial target: 4:20, leaving margin under five minutes. Times allow cursor action and reading; they are not measured runtime or model latency. Keep the complete raw take and label any shortened processing waits. Product evidence must be actual screen footage from one case; Remotion may frame it, never replace a missing result.

| Time | Paragraph | Actual screen action or planned graphic | Evidence needed before this narration is usable |
| --- | --- | --- | --- |
| 0:00–0:25 | 1 | Very short title over the real Dashboard; show the product within five seconds. Emphasize the goods and customer order, not a technology logo wall. | Loaded case; no fabricated lost-sale figure or customer testimonial. |
| 0:25–0:50 | 2 | Incident → selected B5 goods card; briefly show A20's separate passing inspection and return to B5. | New case has 25 received, 20 eligible, 5 held and zero dispatched. A20 PASS comes from the recorded inspection, not its clean photo. |
| 0:50–1:10 | 3 | Select the photo already associated with B5 and ask for analysis. If showing a new upload, first accept the actual browser file-choice/upload path. | Licensed image and declared operator lot association. A preloaded attachment must not be depicted as a fresh upload. |
| 1:10–1:45 | 4 | Show actual request, returned observation, and the required inspection. Briefly expose the real photo-analysis tool evidence if readable. | A real Strands request invokes analysis; actual output supports the spoken corrosion finding and missing measurement. If the operator used a direct Analyze button instead, rewrite the tool-selection attribution. |
| 1:45–2:25 | 5 | Ask whether the eligible twenty can move, then request preparation using the supported command. Show the answer's relevant facts and newly prepared card. | New case has documented partial-dispatch terms; a real agent request creates a new supported proposal for those twenty units. Reusing PO25's old proposal does not pass. Do not imply the agent prepared a form that an operator filled manually. |
| 2:25–2:55 | 6 | Hold the exact order/batch/quantity card legibly; one human confirmation; show the returned execution state. | Fresh proposal, current evidence and one authorized same-case execution. No assumed successful take. |
| 2:55–3:25 | 7 | Check ERP; open the actual Delivery Note in authenticated Chrome, then return to the current batch readback. | Native document proves 20 dispatched; separate current batch evidence proves 5 held. Preserve the case's actual IDs across all shots. |
| 3:25–3:40 | 8 | One short diagram: application-supplied ERP evidence → Strands + Bedrock/tools → proposed action → human confirmation → ERP write/readback. The Strands node groups reasoning components; it does not assert an agent or invocation count. | About 15 seconds; never more than 20. Show application checks around action execution. No Graph/Swarm, historical SaaS handoffs or AgentCore deployment implied. |
| 3:40–4:20 | 9 | Return to the actual 20 dispatched / 5 held result. End on the operator's next inspection step and product name. | A demo ERP dispatch result, not physical delivery or earned revenue. No percentage-efficiency, invented hours saved or realized postage savings. |

## Questions and rehearsal decision

Use ordinary requests, not a pasted expected answer. A suitable sequence is: “Look at this batch photo. What can you tell me, and what still needs checking?”; “Can the other stock move while this batch stays held?”; then the actual supported preparation request established by rehearsal. Adapt wording to the active batch and implementation without inserting the desired conclusions into the prompt.

The fresh-case path is **pending**. If preparation or execution fails, preserve that result and use a bounded correction or switch to an honestly labeled completed-case walkthrough. Do not force the script through an unsupported action. For the PO25 backup, change the opening state to “Twenty have already been dispatched; five remain held,” ask what happened and what remains, remove the live preparation/confirmation claims, and show existing native records in past tense. That backup needs its own revised narration before audio generation.

## Claims notes — not spoken

- The application reads ERP before supplying the agent's bounded current case packet. Reading that packet through a tool is not a separate external ERP request on every tool invocation. Current photo-tool use and supported preparation capability are documented, but fresh creation on the recording build remains a rehearsal gate.
- The contextual assistant can pass an explicit supported preparation request through `PREPARE_ECONOMIC_SPLIT20` to `prepare_economic_proposal`, which invokes the existing Strands economic selector with four evidence tools. This is more than a claim that only one model-agent invocation exists, but it is not Graph/Swarm orchestration. Bedrock-backed photo analysis is also part of the current path. Review, Ask, Act and Verify are workflow stages, not four agents. No spoken agent count is needed.
- Revenue opportunity means progressing eligible fulfillment toward possible billing. The recorded case does not establish invoicing, earned revenue or physical delivery. Task reduction is the proposed value of gathering evidence and preparing supported work in context; no manual baseline, customer time saving or customer ROI has been measured.
- Keep postage out of this main narration. The selected split does not realize the illustrative $24.80 consolidation saving. Keep synthetic weekly history out of the impact proof.
- Evidence: [current claim manifest](../submission/current-claim-manifest.md), [assistant and ERP acceptance](../audits/2026-09-13-operations-assistant-acceptance.md), [goods flow acceptance](../audits/2026-09-14-incident-context-acceptance.md), [production gates](recording-brief-v3.md), [independent script review](../audits/2026-09-14-script-judge-review.md).

## 中文改写理由

开头先让评委看到一个人的工作压力：同一个人收货、追检验、答复客户；五件待检不应自动拖住另外二十件。中段明确 Agent 做了什么：选择图片分析工具、结合现有库存与订单条件、准备受约束的操作，而不是只描述用户依次点了哪些页面。审批和外部单据证明工作真的落到了 ERP。

价值表达落在“符合条件的履约继续推进”和“减少人工拼接信息、重复录入的机会”。二十件发运是演示结果，节省多少时间、增加多少收入仍需试点；不要用虚构金额削弱可信度。架构只留约十五秒，用推理、人工审批和实际 ERP 结果讲清职责，不靠 Agent 数量制造技术深度。真实新案例尚未排练通过，最终台词必须服从录屏证据。
