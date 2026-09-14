# First-person opening and live capture

The presenter speaks as the builder of LogisticPilot. Start with the operator's problem and what the viewer will see; introduce architecture after that context. Do not invent a personal customer anecdote or measured customer savings.

## Opening narration

I built LogisticPilot for small businesses, where one person may handle receiving, inspections, and customer orders. When five parts look questionable, should all twenty-five have to wait?

I'll show you how I upload a photo, ask the agent what can move, and verify the result in the connected apps.

Here's how I built it. Strands and Bedrock combine image analysis with current ERP evidence to propose the next step. My application checks the action, and an operator confirms it. Then it updates ERPNext and reads the result back.

The goal is simple: keep eligible orders moving while the questionable stock stays held.

This is a standalone opening/architecture preview. The full film may place the architecture paragraph after the live demonstration. The live section must establish the promised behavior with actual footage.

## Voice source

Generated in the signed-in ElevenLabs page using Evan (voice ID `TWutjvRaJqAX89preB4e`), Eleven v3, Generation 2. The selected source download has SHA-256 `e342bf33b788c08720b656fa1f24a908db23a621412006d3b87989751ce713da`. It was time-compressed with the pitch-preserving FFmpeg filter `atempo=1.10081133`; bundled `public/narration-v2.mp3` is 45.095215 seconds, 44.1 kHz mono MP3 at 128 kbps with SHA-256 `575b1695ad18a036068bef0c2d9b10ffffe63972966204b4451840bb4e5d32e7`. Complete FFmpeg decode passed. The first-person script above is the exact submitted text; no voice cloning was used.

## V1 architecture voice provenance

The earlier V1 architecture preview separately uses Christopher — Tender, Kind and Steady, Eleven v3, Generation 1. Its source remains `/Users/danielwan/Documents/LogisticPilot-media/architecture-voiceover-elevenlabs-v1.mp3`; the bundled `public/narration.mp3` and `architecture-preview-v1.mp4` are retained as the V1 reference artifacts.

## Required live footage

Capture the actual file selection/upload, the agent's request and returned answer, action preparation and one human confirmation, and the actual external-app navigation. Preserve the complete raw request/wait/result sequence outside Git. An edited version may shorten waits with an explicit caption, keeping input, output and chronology intact.

Use one new case for the entire before/after take. PO25 and PO26 are completed cases; do not replay their actions or combine their records with a new case. The existing scenario is fictional POC business evidence processed by live Bedrock and a connected ERPNext demo tenant. Real API execution does not make its input production customer data.

The user also requires Airtable, Jira and Slack. Each must contribute visible evidence for the same case:

| Application | What the capture should demonstrate |
| --- | --- |
| LogisticPilot | Photo upload, grounded conversation, exact action review and current readback |
| ERPNext | Native records showing the newly executed dispatch and the stock still held |
| Airtable | The same case's operational record updated from connected facts |
| Jira | The same case's unresolved exception and progress; held stock must not be marked resolved |
| Slack | The same case's actual coordination notification and its native message link |

Existing distributor handoff configuration can connect all three collaboration apps without a new framework. Current completed PO26 ran without it, so its rehearsal does not prove these handoffs. The existing payload carries case/PO and aggregate quantities, not explicit lot-level photo observations. Do not describe it as distributing the full photo diagnosis.

## Current capture status

The first-person voice asset is complete. Full live footage and a fresh same-case multi-app take have not yet been recorded. A screen-device test is not a product demo recording. New external records, model responses, timings and native links must be recorded in the take manifest when capture actually succeeds.

## Opening preview delivery

The rendered `OpeningArchitectureV2` composition is 1410 frames at 30 fps, 1920 × 1080. The latest MP4 is `/Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v3.mp4` with SHA-256 `28685cacb3e9d5c019f634c1c2107daaf90f910448bcd9c1a76780b00a9f6356`. Its container duration is 47.018667 seconds; it is H.264 High, `yuv420p` limited-range BT.709 at 30 fps with AAC audio at 48 kHz stereo. The matching poster is `/Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v3-poster.jpg` with SHA-256 `470cc2034f37334cbd5bf195c8ef9f208cd4a2c33d5114f355183a35036811c4`.

The primary reviewer inspected the actual source diff and rendered context, architecture and goal frames. The first scene's no-line card composition and the evidence scene's clean distribution spine were visually checked. The promised multi-app demonstration remains a requirement for the full film. The primary reviewer also independently checked MP4 metadata and decoded the complete file without errors.

The user-facing preview is `http://127.0.0.1:3941/opening-preview.html`, served from the local media folder and redirected to the Remotion Player build. It uses the actual `@remotion/player` composition rendered as DOM/SVG with the bundled audio; the MP4 remains the download artifact. Browser acceptance reached readyState 4 with audio unmuted and currentTime advancing. Full live footage remains a separate capture task and has not yet been recorded. Final visual approval remains with the user.
