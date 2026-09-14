# LogisticPilot TAKE05 final video build

## Output

- Final render: `/Users/danielwan/Documents/LogisticPilot-media/logisticpilot-devpost-final-v1.mp4`
- Canvas: 1920×1080, H.264 video and AAC audio.
- Intent: a single synthetic POC receiving case carried through live product and connected-system screens.

## Timeline

1. **0:00–0:47.019 — Architecture opener.** Existing narrated opener explains the small-business receiving problem and the evidence → Strands/Bedrock → controlled action → readback boundary.
2. **Live workspace.** Retained source ranges show baseline, actual photo upload, live Nova Pro result, three visible Strands/Bedrock questions and answers, then the manager-ready panel. Response waits are deliberately removed in the edit. There is no persistent on-screen badge. A brief runtime/readback confirmation cue appears only at the end of the manager-ready panel before the recorded system readbacks.
3. **Result and cross-app readbacks.** The recorded dashboard shows 20 dispatched, 5 held, 0 missing. The same TAKE05 result is then shown in ERPNext, Airtable, Jira QRC-10 and Slack, before returning to the dashboard.
4. **12-second close.** The end card restates the demonstrated decision: 20 dispatched, 5 held and four systems verified.

The live narration starts after the opener, uses the supplied Evan voice track at 1.29× to fit the edit, and reaches its closing words during the end card.

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

- Published final duration: **267.946 seconds** (4:27.946). Video is H.264 at 1920×1080 and 30 fps; audio is AAC.
- Full video and audio decode with `ffmpeg` passed.
- The raw source at **393 seconds** showed a Chrome autofill popup with identities. The replacement raw interval, **400.000–423.927 seconds**, was inspected clear of that popup while preserving the 23.927-second approval-ready duration.
- Final frames at **196 s**, **199 s** and **201 s** show neither Chrome autofill identities nor a persistent live badge. The approval-to-dashboard transition was checked at **218 s** (the brief confirmation toast) and **220.1 s** (dashboard).
- Visual checks also covered the ERPNext, Airtable, Jira and Slack readbacks, plus the end card.
