# LogisticPilot TAKE05 final video build

## Output

- Final render: `/Users/danielwan/Documents/LogisticPilot-media/logisticpilot-devpost-final-v1.mp4`
- Canvas: 1920×1080, H.264 video and AAC audio.
- Intent: a single synthetic POC receiving case carried through live product and connected-system screens.

## Timeline

1. **0:00–0:47.019 — Architecture opener.** Existing narrated opener explains the small-business receiving problem and the evidence → Strands/Bedrock → controlled action → readback boundary.
2. **0:47.019–2:48.126 — Live workspace and approval.** Baseline, actual photo upload, live Nova Pro result, and three visible Strands/Bedrock question-and-answer sequences carry only their matching narration. The manager review and the manager-ready panel carry the human-control wording. There is no persistent on-screen badge. A brief runtime/readback confirmation cue appears only at the end of the manager-ready panel.
3. **2:48.126–4:02.261 — Result and cross-app readbacks.** The dashboard shows 20 dispatched, 5 held, 0 missing. ERPNext, Airtable, Jira QRC-10, and Slack each begin with their own matching spoken explanation; no later-system description precedes the visible system.
4. **4:02.261–4:44.501 — Economic close and end card.** The dashboard begins the economic-value wording; the end card carries its close, the LogisticPilot summary, and the demonstrated decision: 20 dispatched, 5 held, and four systems verified.

The opener is unchanged. The supplied Evan source is rendered as independently delayed
clips at 1.20×, rather than one globally accelerated track. This preserves natural
paragraph pauses while making the visual cuts follow the spoken semantic anchors.
Narration is therefore resynchronized by semantic scene, not by globally accelerating
the finished track. Final duration is **284.501 seconds** (4:44.501). Objective export
verification passed for SHA256
`10aa5fddadf56c411b7bff8fcdba0d8eaf99aa7edcc739efe503053b3f53ea81` with H.264
1920 × 1080 at 30 fps, AAC stereo, and full decode. Independent Astra film/claims
review passed this resynchronized export: q2 at 120s, q3 at 140s, and Jira at 216.1s
were aligned; prior ERPNext/Airtable/Slack, end-card, privacy, crop, and badge checks
remained clean. The off-camera confirmation-click limitation is disclosed.

## Narration timing manifest

Source ranges are speech-safe boundaries taken from the Evan MP3 with `ffmpeg`
`silencedetect` (`-36 dB`, `0.18 s`) and aligned to the approved voiceover transcript.
Final timings use `47.019 + source_time / 1.20`; the source clips are independently
rendered and delayed to these starts.

| Narration paragraph / clause | Source audio | Final audio | Concurrent visual |
| --- | --- | --- | --- |
| Real receiving decision / 25 components / five possibly damaged | 0:00.000–0:20.211 | 0:47.019–1:03.862 | Baseline workspace |
| Receiver takes one photo and uploads it | 0:20.211–0:25.653 | 1:03.862–1:08.397 | Upload |
| Nova reads visible evidence; photo becomes reviewable evidence packet | 0:25.653–0:41.287 | 1:08.397–1:21.425 | Nova result |
| Strands brings together photo, lot, order, and receiving record; separates two lots | 0:41.287–1:07.736 | 1:21.425–1:43.466 | Evidence agent question and answer |
| Agent tests the business consequence and keeps the verified 20 moving | 1:07.736–1:33.397 | 1:43.466–2:04.850 | Consequence agent question and answer |
| Agent proposes the executable, reviewable plan; records remain source of truth | 1:33.397–1:58.288 | 2:04.850–2:25.592 | Executable-plan agent question and answer |
| Control point: agent cannot release alone; manager reviews evidence and action | 1:58.288–2:09.857 | 2:25.592–2:35.233 | Approval review |
| After confirmation: 20 for dispatch, five held; decision tied to order and lots | 2:09.857–2:25.328 | 2:35.233–2:48.126 | Approval-ready panel |
| Applied result and safe, specific operational decision | 2:25.328–2:44.710 | 2:48.126–3:04.277 | Dashboard result |
| ERPNext native delivery record, MAT-DN-2026-00029, and fulfillment ownership | 2:44.710–3:05.228 | 3:04.277–3:21.376 | ERPNext readback |
| Airtable receives the matching quantities without retyping | 3:05.228–3:22.885 | 3:21.376–3:36.090 | Airtable readback |
| Jira QRC-10 carries the quality follow-up and case reference | 3:22.885–3:38.763 | 3:36.090–3:49.322 | Jira readback |
| Slack receives the matching operational update | 3:38.763–3:54.290 | 3:49.322–4:02.261 | Slack readback |
| Economic value: isolate an uncertain lot, avoid duplicate reconciliation, show verifiable evidence | 3:54.290–4:23.328 | 4:02.261–4:26.459 | Dashboard/economic close |
| LogisticPilot summary: physical evidence, systems, human approval, verified records | 4:23.328–4:44.996 | 4:26.459–4:44.501 | End card (starts 4:23.700) |

The visual cut plan is: baseline 0:47.019–1:03.862; upload 1:03.862–1:08.397; Nova 1:08.397–1:21.425; evidence 1:21.425–1:43.466; consequence 1:43.466–2:04.850; executable plan 2:04.850–2:25.592; approval 2:25.592–2:48.126; dashboard result 2:48.126–3:04.277; ERPNext 3:04.277–3:21.376; Airtable 3:21.376–3:36.090; Jira 3:36.090–3:49.322; Slack 3:49.322–4:02.261; dashboard/economic close 4:02.261–4:23.700; end card 4:23.700–4:44.501.

## Truth boundary

- Case: `M20-DIST-ECONOMIC-TAKE05-20260914`.
- Result: 20 dispatched, 5 held, 0 missing.
- ERPNext Delivery Note: `MAT-DN-2026-00029`.
- Jira: `QRC-10`.
- The case is synthetic POC data executed through live systems and model calls.
- Nova Pro observations are advisory. Confirmation in the edit is represented by the recorded manager-ready panel plus the brief runtime/readback confirmation cue; the actual confirmation click is not shown.
- “Dispatched” is a recorded demo-system state. The film does not claim physical delivery, earned revenue, measured savings or production deployment.

## Verification requirements

Run `python3 video/scripts/build_final_take05.py`, then verify:

```text
ffprobe final duration, video codec, audio codec, width and height
ffmpeg full decode to null
12 evenly spaced contact-sheet frames inspected for crop, private browser chrome, legibility and causal order
```

The source recording assets remain outside Git under `/Users/danielwan/Documents/LogisticPilot-media`.

## 2026-09-14 final render verification

Render checks for this resynchronized candidate include a duration/codec/size probe
and full A/V decode. Cue frames were checked at photo upload, Nova result, each Agent
conversation, manager approval, result dashboard, ERPNext, Airtable, Jira, Slack,
economic close, and end card, plus representative privacy/crop frames. Independent
Astra film/claims review passed the exact export, including semantic A/V checks at q2
120s, q3 140s, and Jira 216.1s; prior ERPNext/Airtable/Slack, end-card, privacy, crop,
and badge checks remained clean, and full decode passed.

Corrected visual cue selections for the final export: the q2 answer uses raw220 with a
clean seven-second hold, the q3 answer uses raw340, and the Jira readback uses raw40.
