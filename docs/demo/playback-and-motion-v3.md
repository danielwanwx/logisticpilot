# Playback and motion correction

## Historical native-video failure

The user's second playback report was reproduced in the earlier direct-MP4 preview. At 25.14 seconds and again at 38.75 seconds, the native media element reported active playback, ready state 4 and no error, but the visible video area was blank. This invalidates the earlier assumption that one successful playback and a restored end poster established reliable viewing.

The same MP4 played visibly in Chrome, including its opening and the architecture at 33.26 seconds. This points to a browser-specific video rendering problem; it does not establish the exact underlying compositor or decoder cause. A valid file, advancing time and absence of a media error do not prove visible video.

## Current correction

The interactive preview uses the actual React composition in [Remotion Player](https://www.remotion.dev/docs/player). The scene is rendered as DOM/SVG with the current ElevenLabs Evan audio; it does not depend on an H.264 video surface for the picture. The latest downloadable film artifact is `/Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v3.mp4`, a 47.018667-second 1920 × 1080 H.264 High / yuv420p limited-range BT.709, 30 fps file with 48 kHz stereo AAC. Its SHA-256 is `146eef143a71f6879c00bbeb78499426981726cb94953d5217da860a7d8d11ff`; the poster `/Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v3-poster.jpg` has SHA-256 `eb4f8733ab88d33074436c0a5cd4c74b1997acf0c732a0c8a0cdeaf1ec40bcda`. This is the same authored composition, not a screenshot slideshow substituted for video.

The opening motion now shows one operator's receiving, inspection, and customer-order responsibilities without connector lines; twenty-five tiles split into twenty eligible and five awaiting inspection; and one evidence packet moving from photo to agent to a distribution spine for the app destinations. These are explanatory graphics. The real upload, agent responses and same-case ERPNext/Airtable/Jira/Slack operations still require actual recording.

## Acceptance evidence

Browser acceptance of the Remotion Player reached `readyState=4` with audio unmuted and `currentTime` advancing. The first-scene no-line card composition and the evidence-spine correction were visually checked in rendered stills at `/Users/danielwan/Documents/LogisticPilot-media/motion-v4-first-scene/` and `/Users/danielwan/Documents/LogisticPilot-media/motion-v3-stills/frame-0550.png`. The v3 MP4 metadata and complete FFmpeg decode passed. Full live footage and a fresh same-case multi-app recording have not yet been recorded.
