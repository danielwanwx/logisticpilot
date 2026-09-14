# LogisticPilot architecture preview

This standalone Remotion composition explains the bounded LogisticPilot workflow:

`Photo + ERP facts → Strands agent → Check + confirm → ERPNext write/readback`

It is an architecture illustration, not live product footage. It deliberately distinguishes photo observations from quality clearance, keeps the proposed action behind application checks and person approval, and labels the final `20 dispatched • 5 held` result as the connected POC outcome.

## Current opening preview (V3)

OpeningArchitectureV2 is the current first-person, green/off-white context
opening around the existing architecture illustration. It runs for 47 seconds
at 30 fps (1410 frames): the “Built for small businesses” opening, the
5-held / 20-eligible question, the photo-to-agent-to-connected-apps promise,
the existing four-card architecture, and a short goal hold.

It uses diagrams and simple cards rather than simulated product screens. The
first scene now groups Receiving, Inspection, and Customer orders inside one
operator card without connector lines. The evidence scene uses one clean
agent-to-hub path with a vertical distribution spine for ERPNext, Airtable,
Jira, and Slack. The final goal card says that eligible orders keep moving while
questionable stock stays held.

The current opening voice is ElevenLabs Evan (voice ID
`TWutjvRaJqAX89preB4e`), Eleven v3 Generation 2. The selected source download
has SHA-256
`e342bf33b788c08720b656fa1f24a908db23a621412006d3b87989751ce713da`. It was
time-compressed with the pitch-preserving FFmpeg filter
`atempo=1.10081133`; bundled `public/narration-v2.mp3` is 45.095215 seconds,
44.1 kHz mono MP3 at 128 kbps with SHA-256
`575b1695ad18a036068bef0c2d9b10ffffe63972966204b4451840bb4e5d32e7`.

The latest rendered review MP4 is
`/Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v3.mp4`
with SHA-256
`146eef143a71f6879c00bbeb78499426981726cb94953d5217da860a7d8d11ff`.
Its container duration is 47.018667 seconds; the video is H.264 High,
1920 × 1080, yuv420p limited-range BT.709 at 30 fps, with AAC audio at 48 kHz
stereo. The matching poster is
`/Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v3-poster.jpg`
with SHA-256
`eb4f8733ab88d33074436c0a5cd4c74b1997acf0c732a0c8a0cdeaf1ec40bcda`.

The interactive preview uses the actual `@remotion/player` composition
rendered as DOM/SVG with the bundled audio; the MP4 remains the downloadable
film artifact. Browser acceptance reached readyState 4 with audio unmuted and
currentTime advancing. The no-line first scene and the evidence distribution
spine were visually checked in rendered stills. Full live footage remains a
separate capture task and has not yet been recorded.

Accepted V3 review stills:

~~~bash
cd video/architecture-preview
npm exec -- remotion still src/index.jsx OpeningArchitectureV2 /Users/danielwan/Documents/LogisticPilot-media/motion-v4-first-scene/frame-0060.png --frame=60 --image-format=png --overwrite
npm exec -- remotion still src/index.jsx OpeningArchitectureV2 /Users/danielwan/Documents/LogisticPilot-media/motion-v4-first-scene/frame-0180.png --frame=180 --image-format=png --overwrite
npm exec -- remotion still src/index.jsx OpeningArchitectureV2 /Users/danielwan/Documents/LogisticPilot-media/motion-v3-stills/frame-0550.png --frame=550 --image-format=png --overwrite
~~~

Reproduce the current review MP4 with a distinct intermediate so the faststart
remux never overwrites its own input:

~~~bash
npm exec -- remotion render src/index.jsx OpeningArchitectureV2 /Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v3-remotion.mp4 --codec=h264 --pixel-format=yuv420p --color-space=bt709 --audio-codec=aac --audio-bitrate=192k --crf=17 --concurrency=2 --overwrite
ffmpeg -y -i /Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v3-remotion.mp4 -map 0 -c copy -movflags +faststart -color_primaries bt709 -color_trc bt709 -colorspace bt709 /Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v3.mp4
npm exec -- remotion still src/index.jsx OpeningArchitectureV2 /Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v3-poster.jpg --frame=90 --image-format=jpeg --jpeg-quality=90 --overwrite
~~~

## V1 architecture provenance

`public/narration.mp3` is the supplied, selected **Generation 1** public narration take from the user's signed-in ElevenLabs Text to Speech page: **Christopher — Tender, Kind and Steady**, **Eleven v3**. The source asset was copied without re-encoding from:

`/Users/danielwan/Documents/LogisticPilot-media/architecture-voiceover-elevenlabs-v1.mp3`

Its documented duration is 21.159125 seconds; it is 44.1 kHz mono and had already passed a full FFmpeg decode. The 23.33-second composition gives the spoken result a short readable hold. No voice cloning, narration regeneration, external ERP call, or ERP write is performed by this project.

## Reproduce

From the repository root, install the pinned Remotion dependencies:

```bash
cd video/architecture-preview
npm ci
```

Open Remotion Studio:

```bash
npm run studio
```

Render a portable H.264 preview to the ignored local `out/` directory:

```bash
npm run render
```

Render the four portable review stills:

```bash
npm run still:photo
npm run still:reason
npm run still:confirm
npm run still:result
```

For the final local review artifacts, pass the intended outside-Git path explicitly:

```bash
npm exec -- remotion render src/index.jsx ArchitecturePreview /Users/danielwan/Documents/LogisticPilot-media/architecture-preview-v1.mp4 --codec=h264 --crf=17 --concurrency=2 --overwrite
npm exec -- remotion still src/index.jsx ArchitecturePreview /Users/danielwan/Documents/LogisticPilot-media/architecture-preview-stills/01-photo-and-erp.png --frame=75 --image-format=png --overwrite
```

The generated final review artifacts are intentionally outside the repository:

- `/Users/danielwan/Documents/LogisticPilot-media/architecture-preview-v1.mp4`
- `/Users/danielwan/Documents/LogisticPilot-media/architecture-preview-stills/`

## Source layout

- src/OpeningArchitectureV2.jsx — 47-second narration-timed context opening and reusable architecture wrapper
- `src/ArchitecturePreview.jsx` — visual design, staged animation, exact English captions, and audio placement
- `src/Root.jsx` — the 1920×1080, 30 fps, 700-frame composition registration
- `public/narration.mp3` — supplied public voiceover
- `public/geist-latin.woff2` — verbatim local reuse of `workspace/assets/geist-latin.woff2` for the established product typography; see `FONT-LICENSE.txt`
