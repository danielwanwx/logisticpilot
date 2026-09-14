# LogisticPilot architecture preview

This standalone Remotion composition explains the bounded LogisticPilot workflow:

`Photo + ERP facts → Strands agent → Check + confirm → ERPNext write/readback`

It is an architecture illustration, not live product footage. It deliberately distinguishes photo observations from quality clearance, keeps the proposed action behind application checks and person approval, and labels the final `20 dispatched • 5 held` result as the connected POC outcome.

## V2 opening preview

OpeningArchitectureV2 preserves the v1 architecture illustration and adds a
first-person, green/off-white context opening. It runs for 47 seconds at 30 fps
(1410 frames): small-parts distributor context, the 5-held / 20-eligible
question, the photo-to-agent-to-connected-apps promise, then the existing
four-card architecture and a short goal hold.

It deliberately uses diagrams and simple cards, not simulated product screens.
The final goal card says that eligible orders keep moving while questionable
stock stays held. It does not present the historical 20 dispatched • 5 held
readback as a generic end counter; that connected POC result remains explicit
in the v1 preview.

The supplied Generation 1 ElevenLabs take is copied unchanged to
public/narration-v2.mp3 from
/Users/danielwan/Documents/LogisticPilot-media/opening-architecture-elevenlabs-v2.mp3.
It is Christopher / Eleven v3, follows the approved exact script in
docs/demo/opening-and-live-capture.md, and decodes to 45.087313 seconds. The
additional 1.913-second visual hold makes the V2 composition 47 seconds. V1's
public/narration.mp3 remains unchanged.

Accepted V2 review stills:

~~~bash
cd video/architecture-preview
npm exec -- remotion still src/index.jsx OpeningArchitectureV2 /Users/danielwan/Documents/LogisticPilot-media/architecture-preview-v2-stills/01-context.png --frame=120 --image-format=png --overwrite
npm exec -- remotion still src/index.jsx OpeningArchitectureV2 /Users/danielwan/Documents/LogisticPilot-media/architecture-preview-v2-stills/02-architecture.png --frame=815 --image-format=png --overwrite
npm exec -- remotion still src/index.jsx OpeningArchitectureV2 /Users/danielwan/Documents/LogisticPilot-media/architecture-preview-v2-stills/03-goal.png --frame=1300 --image-format=png --overwrite
~~~

The accepted final MP4 is
/Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v2.mp4.
It was rendered as H.264/yuv420p with AAC audio, then remuxed with FFmpeg using
BT.709 stream tags and faststart. A full FFmpeg decode and metadata check passed.
Reproduce the final file with a distinct intermediate so the faststart remux
never overwrites its own input:

~~~bash
npm exec -- remotion render src/index.jsx OpeningArchitectureV2 /Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v2-remotion.mp4 --codec=h264 --pixel-format=yuv420p --color-space=bt709 --audio-codec=aac --audio-bitrate=192k --crf=17 --concurrency=2 --overwrite
ffmpeg -y -i /Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v2-remotion.mp4 -map 0 -c copy -movflags +faststart -color_primaries bt709 -color_trc bt709 -colorspace bt709 /Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v2.mp4
npm exec -- remotion still src/index.jsx OpeningArchitectureV2 /Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v2-poster.jpg --frame=90 --image-format=jpeg --jpeg-quality=90 --overwrite
~~~

## Narration provenance

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
