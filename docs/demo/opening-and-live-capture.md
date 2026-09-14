# First-person opening and live capture

The presenter speaks as the builder of LogisticPilot. Start with the operator's problem and what the viewer will see; introduce architecture after that context. Do not invent a personal customer anecdote or measured customer savings.

## Opening narration

I built LogisticPilot for small parts distributors, where one person may handle receiving, inspections, and customer orders. When five parts look questionable, should all twenty-five have to wait?

I'll show you how I upload a photo, ask the agent what can move, and verify the result in the connected apps.

Here's how I built it. Strands and Bedrock combine image analysis with current ERP evidence to propose the next step. My application checks the action, and an operator confirms it. Then it updates ERPNext and reads the result back.

The goal is simple: keep eligible orders moving while the questionable stock stays held.

This is a standalone opening/architecture preview. The full film may place the architecture paragraph after the live demonstration. The live section must establish the promised behavior with actual footage.

## Voice source

Generated in the signed-in ElevenLabs page using Christopher — Tender, Kind and Steady, Eleven v3, Generation 1. Downloaded through Chrome's Save dialog to `/Users/danielwan/Documents/LogisticPilot-media/opening-architecture-elevenlabs-v2.mp3`. Reported duration: 45.087313 seconds, MP3 44.1 kHz mono. Complete FFmpeg decode passed. The first-person script above is the exact submitted text; no voice cloning was used.

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

The rendered `OpeningArchitectureV2` composition is 1410 frames at 30 fps, 1920 × 1080. The MP4 container is 47.061333 seconds with H.264 `yuv420p`, limited-range BT.709 and AAC audio. It is saved as `/Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v2.mp4`; the supplied narration and bundled `public/narration-v2.mp3` have identical SHA-256 hashes.

The primary reviewer inspected the actual source diff and rendered context, architecture and goal frames. The independent award reviewer found no material truth or clarity blocker in the first-person script; the promised multi-app demonstration remains a requirement for the full film. The primary reviewer also independently checked MP4 metadata and decoded the complete file without errors.

The user-facing player is `http://127.0.0.1:3941/opening-preview.html`, served from the local media folder. It uses an actual rendered poster, explicit playback, native controls and a download link. Browser playback is checked in the same in-app browser where the earlier direct-MP4 black frame was reproduced.

Actual playback reached 47.061333 seconds with `ended=true`, audio unmuted, no media error and the poster visible. The initial poster, playing goal frame and final poster were inspected. Final visual approval remains with the user.
