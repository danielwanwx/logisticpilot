#!/usr/bin/env python3
"""Build the locked LogisticPilot TAKE05 Devpost film from recorded live footage.

This is deliberately a small, reproducible ffmpeg edit: source ranges are explicit,
all Chrome capture is cropped with the approved viewport rectangle, and a brief
confirmation cue appears only at the end of the recorded manager-ready panel.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
MEDIA = Path("/Users/danielwan/Documents/LogisticPilot-media")
OUTPUT = MEDIA / "logisticpilot-devpost-final-v1.mp4"
WORK = Path("/private/tmp/logisticpilot-final-take05")
CROP = "crop=1527:859:196:133,scale=1920:1080:flags=lanczos,setsar=1"
VOICE_SPEED = "1.29"
BODY_DURATION = 220.927
FINAL_DURATION = 267.946


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, check=True)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def make_confirmation_toast(path: Path) -> None:
    canvas = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    box = (510, 932, 1410, 1022)
    draw.rounded_rectangle(box, radius=20, fill=(246, 250, 247, 246), outline=(133, 189, 149, 235), width=2)
    draw.text(
        (960, 958),
        "Manager approval recorded · execution readback follows",
        anchor="mm",
        font=font(22, True),
        fill=(17, 73, 42, 255),
    )
    draw.text(
        (960, 989),
        "TAKE05 runtime journal",
        anchor="mm",
        font=font(16),
        fill=(82, 112, 92, 255),
    )
    canvas.save(path)


def make_live_clip(
    name: str,
    source: Path,
    start: float,
    duration: float,
    confirmation_toast: Path | None = None,
) -> Path:
    destination = WORK / f"{name}.mp4"
    # ScreenCaptureKit writes a VFR stream.  Trim *after* normalising timestamps
    # and frame rate; input-level -t otherwise produces nondeterministic lengths.
    command = ["ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", str(source)]
    filter_complex = (
        f"[0:v]setpts=PTS-STARTPTS,{CROP},fps=30,trim=duration={duration:.3f},setpts=PTS-STARTPTS[base]"
    )
    if confirmation_toast is None:
        filter_complex += f";[base]trim=duration={duration:.3f}[v]"
    else:
        toast_start = duration - 2.5
        command.extend(["-loop", "1", "-framerate", "30", "-i", str(confirmation_toast)])
        filter_complex += (
            ";[base][1:v]overlay=0:0:format=auto:"
            f"enable='between(t,{toast_start:.3f},{duration:.3f})',trim=duration={duration:.3f}[v]"
        )
    command.extend([
        "-filter_complex", filter_complex,
        "-map", "[v]", "-an", "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(destination),
    ])
    run(*command)
    return destination


def make_graphic_clip(name: str, source: Path, start: float, duration: float) -> Path:
    destination = WORK / f"{name}.mp4"
    run(
        "ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", str(source),
        "-vf",
        "setpts=PTS-STARTPTS,scale=1920:1080:force_original_aspect_ratio=decrease,"
        f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0b1f16,setsar=1,fps=30,trim=duration={duration:.3f},setpts=PTS-STARTPTS",
        "-an", "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(destination),
    )
    return destination


def main() -> int:
    candidate = WORK / "logisticpilot-devpost-final-v1-candidate.mp4"
    if len(sys.argv) == 2 and sys.argv[1] == "--publish":
        if not candidate.exists():
            raise FileNotFoundError(f"No verified candidate to publish: {candidate}")
        candidate.replace(OUTPUT)
        print(f"Published {OUTPUT}")
        return 0
    if len(sys.argv) != 1:
        raise SystemExit("usage: build_final_take05.py [--publish]")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe are required")
    required = {
        "opening": MEDIA / "opening-architecture-v3.mp4",
        "main": MEDIA / "live-demo-take-06-window-raw.mov",
        "proof": MEDIA / "live-demo-take-06-proof-raw.mov",
        "jira": MEDIA / "live-demo-take-06-jira-raw.mov",
        "slack": MEDIA / "live-demo-take-06-slack-raw.mov",
        "end": MEDIA / "competition-end-card-v1.mp4",
        "voice": MEDIA / "live-demo-take05-voiceover-evan.mp3",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing input media:\n" + "\n".join(missing))
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    confirmation_toast = WORK / "approval-confirmation-toast.png"
    make_confirmation_toast(confirmation_toast)

    # These ranges retain the causal live flow: upload -> Nova observation ->
    # three Strands questions/answers -> manager-ready approval. Network/model
    # response waits are removed in the edit.
    live_ranges = [
        ("01-baseline", required["main"], 0, 20),
        ("02-upload", required["main"], 25, 19),
        ("03-nova-result", required["main"], 90, 14),
        ("04-agent-question-1", required["main"], 115, 12),
        ("05-agent-answer-1", required["main"], 150, 14),
        ("06-agent-question-2", required["main"], 180, 10),
        ("07-agent-answer-2", required["main"], 210, 14),
        ("08-agent-question-3", required["main"], 240, 11),
        ("09-agent-answer-3", required["main"], 275, 16),
        ("10-approval-review", required["main"], 340, 19),
        ("11-approval-ready", required["main"], 400, 23.927),
        ("12-final-dashboard", required["proof"], 0, 5),
        ("13-erpnext-readback", required["proof"], 18, 6),
        ("14-airtable-readback", required["proof"], 31, 6),
        ("15-jira-readback", required["jira"], 37, 6),
        ("16-slack-readback", required["slack"], 12, 6),
        ("17-dashboard-close", required["proof"], 0, 7),
    ]
    clips = [
        make_live_clip(
            name,
            source,
            start,
            duration,
            confirmation_toast if name == "11-approval-ready" else None,
        )
        for name, source, start, duration in live_ranges
    ]
    clips.append(make_graphic_clip("18-end-card", required["end"], 0, 12))

    # Every source fragment is already CFR and zero-based.  Still concatenate
    # through the filter graph rather than stream-copying a list: macOS VFR
    # capture timestamps otherwise caused the last 12-second graphic to vanish.
    body = WORK / "body.mp4"
    body_inputs: list[str] = ["ffmpeg", "-y"]
    for clip in clips:
        body_inputs.extend(["-i", str(clip)])
    body_labels = "".join(f"[{index}:v]" for index in range(len(clips)))
    body_inputs.extend([
        "-filter_complex",
        f"{body_labels}concat=n={len(clips)}:v=1:a=0[joined];"
        f"[joined]trim=duration={BODY_DURATION:.3f},setpts=PTS-STARTPTS[v]",
        "-map", "[v]", "-an", "-r", "30", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(body),
    ])
    run(*body_inputs)

    # Build the audio separately.  Rendering the delayed MP3 inside the video
    # concat caused ffmpeg's shortest-output gate to cut the closing card early
    # on this macOS build, even though the filtered audio itself was longer.
    mixed_audio = WORK / "mixed-audio.m4a"
    run(
        "ffmpeg", "-y", "-i", str(required["opening"]), "-i", str(required["voice"]),
        "-filter_complex",
        "[0:a]afade=t=out:st=46.72:d=0.28[opener];"
        f"[1:a]atempo={VOICE_SPEED},adelay=47019|47019,afade=t=out:st=267.65:d=0.28[voice];"
        f"[opener][voice]amix=inputs=2:duration=longest:dropout_transition=0,apad=pad_dur=60,atrim=duration={FINAL_DURATION:.3f}[a]",
        "-map", "[a]", "-c:a", "aac", "-b:a", "192k", str(mixed_audio),
    )

    # Opener keeps its existing visuals; the separately rendered narration starts
    # at its end and the visual concat supplies the authoritative final duration.
    run(
        "ffmpeg", "-y", "-i", str(required["opening"]), "-i", str(body), "-i", str(mixed_audio),
        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
        "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart",
        "-t", f"{FINAL_DURATION:.3f}", str(candidate),
    )
    run("ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,codec_type,width,height", "-of", "json", str(candidate))
    for second in (257, 263, 267):
        run("ffmpeg", "-y", "-v", "error", "-ss", str(second), "-i", str(candidate), "-frames:v", "1", str(WORK / f"verify-{second}.png"))
    print(f"Candidate ready for visual verification: {candidate}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
