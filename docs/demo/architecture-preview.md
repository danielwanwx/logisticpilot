# LogisticPilot architecture segment

Standalone architecture preview requested September 13 Pacific / September 14 UTC. This is an explanatory animation, not product footage. The product's live evidence is in the [fresh rehearsal](../audits/2026-09-14-fresh-rehearsal.md).

## Narration

> An operator brings a photo and a question. Our Strands agent uses image analysis and the current ERP evidence to propose the next step. LogisticPilot checks the action. A person confirms it. Then we update ERPNext and read back the result: twenty dispatched, five still held.

中文含义：操作员提供照片和问题。Strands Agent 结合图像分析与当前 ERP 证据提出下一步。平台检查操作，由人确认，再更新 ERPNext 并重新读取结果：二十件发运，五件继续待检。

Four visual stages: **Photo + ERP facts → Strands agent → Check + confirm → ERPNext write/readback**. The last beat shows the verified POC result. Keep the picture focused on this sequence, with the approved green/neutral product palette and large, readable labels.

## Evidence and review

- The application supplies the bounded current ERP evidence packet; evidence-tool use does not imply a new external ERP call for every tool invocation.
- The image contributes observations, not quality clearance. A20's passing inspection already existed; B5 remained held throughout the rehearsal.
- The model proposes; application checks and human confirmation precede ERP execution. Native document readback verifies the recorded result.
- Independent narrative review found no material claim blocker. This architecture illustration need not replay the rehearsal's extra lot question or failed read, but must not be labeled live footage.
- Twenty dispatched / five held is the connected POC outcome, not physical delivery, earned revenue or measured customer ROI. No Graph, Swarm or AgentCore deployment is asserted.

## Voice asset

Generated through the user's signed-in ElevenLabs Text to Speech page, using the already selected **Christopher — Tender, Kind and Steady**, **Eleven v3**, Generation 1. The browser generated two alternatives in one request; Generation 1 is the selected preview take.

The downloaded MP3 is 21.159125 seconds, 44.1 kHz mono, and passed a complete FFmpeg decode. Only the public-facing narration was submitted. No voice cloning or account changes were performed.

Remotion composition and reproducible commands belong in `video/architecture-preview/`. Rendered review media remains outside Git in `/Users/danielwan/Documents/LogisticPilot-media/`. Final visual acceptance belongs to the user.

## Delivered preview and acceptance

- Video: `/Users/danielwan/Documents/LogisticPilot-media/architecture-preview-v1.mp4`.
- Remotion timeline: 700 frames, 30 fps, 1920 × 1080 (23.333 seconds). MP4 container duration: 23.381 seconds; H.264 video and AAC audio.
- The primary reviewer independently verified metadata and decoded the complete MP4 with FFmpeg without errors.
- Browser playback progressed to the end at 23.381 seconds with no media error and audio unmuted. The middle-stage and final-result frames were visually inspected in the browser; rendered first and final stills were also reviewed for text legibility and clipping.
- The supplied ElevenLabs MP3 and bundled narration have matching SHA-256 hashes. Motion and captions follow the recorded phrase timings, with a short final result hold.
- Source includes pinned Remotion dependencies, local narration and font assets, full Geist font license, and reproducible render commands. Rendered media and dependencies are excluded from Git.

This delivers the standalone architecture segment for user review, not the complete competition film.
