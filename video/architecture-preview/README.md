# LogisticPilot architecture preview

This standalone Remotion composition explains the bounded LogisticPilot workflow:

`Photo + ERP facts → Strands agent → Check + confirm → ERPNext write/readback`

It is an architecture illustration, not live product footage. It deliberately distinguishes photo observations from quality clearance, keeps the proposed action behind application checks and person approval, and labels the final `20 dispatched • 5 held` result as the connected POC outcome.

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

- `src/ArchitecturePreview.jsx` — visual design, staged animation, exact English captions, and audio placement
- `src/Root.jsx` — the 1920×1080, 30 fps, 700-frame composition registration
- `public/narration.mp3` — supplied public voiceover
- `public/geist-latin.woff2` — verbatim local reuse of `workspace/assets/geist-latin.woff2` for the established product typography; see `FONT-LICENSE.txt`
