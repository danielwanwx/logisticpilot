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
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
MEDIA = Path("/Users/danielwan/Documents/LogisticPilot-media")
OUTPUT = MEDIA / "logisticpilot-devpost-final-v1.mp4"
WORK = Path("/private/tmp/logisticpilot-final-take05")
CROP = "crop=1527:859:196:133,scale=1920:1080:flags=lanczos,setsar=1"
# The opening file's audio ends at 47.018667 seconds; narration intentionally
# begins at the next millisecond, after the untouched opening audio finishes.
NARRATION_START = 47.019
OPENING_AUDIO_DURATION = 47.018667
NARRATION_TEMPO = 1.20
BODY_DURATION = 237.497
FINAL_DURATION = 284.516
AUDIO_FADE_SECONDS = 0.015


@dataclass(frozen=True)
class NarrationSegment:
    """A speech-safe source slice placed at an auditable final-film time."""

    label: str
    scene: str
    source_start: float
    source_end: float
    final_start: float
    tempo: float

    @property
    def duration(self) -> float:
        return (self.source_end - self.source_start) / self.tempo


# Whisper/silencedetect-safe anchors from the recorded TAKE05 voiceover.  These
# slices are contiguous: the full narration remains intact, while the live
# visuals change at the matching source meaning rather than at a global 1.29x
# timestamp.  The displayed final starts round to 47.019, 63.862, 68.397,
# 81.425, 103.466, 124.850, 145.592, 155.233, 168.126, 184.277, 201.376,
# 216.090, 229.322, 242.261, and 266.459 seconds.
NARRATION_SEGMENTS = (
    NarrationSegment("baseline", "01-baseline", 0.000, 20.211, 47.019000, 1.20),
    NarrationSegment("upload", "02-upload", 20.211, 25.653, 63.861500, 1.20),
    NarrationSegment("nova", "03-nova-result", 25.653, 41.287, 68.396500, 1.20),
    NarrationSegment("agent-evidence", "04-05-agent-evidence", 41.287, 67.736, 81.424833, 1.20),
    NarrationSegment("agent-consequence", "06-07-agent-consequence", 67.736, 93.397, 103.465667, 1.20),
    NarrationSegment("agent-plan", "08-09-agent-plan", 93.397, 118.288, 124.849500, 1.20),
    NarrationSegment("approval-review", "10-approval-review", 118.288, 129.857, 145.592000, 1.20),
    NarrationSegment("after-manager", "11-approval-ready", 129.857, 145.328, 155.233167, 1.20),
    NarrationSegment("applied-result", "12-final-dashboard", 145.328, 164.710, 168.125667, 1.20),
    NarrationSegment("erp", "13-erpnext-readback", 164.710, 185.228, 184.277333, 1.20),
    NarrationSegment("airtable", "14-airtable-readback", 185.228, 202.885, 201.375667, 1.20),
    NarrationSegment("jira", "15-jira-readback", 202.885, 218.763, 216.089500, 1.20),
    NarrationSegment("slack", "16-slack-readback", 218.763, 234.290, 229.321500, 1.20),
    NarrationSegment("economic-close", "17-dashboard-close", 234.290, 263.328, 242.260667, 1.20),
    NarrationSegment("closing-summary", "18-end-card", 263.328, 284.995875, 266.459000, 1.20),
)


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
    source_duration: float | None = None,
) -> Path:
    destination = WORK / f"{name}.mp4"
    source_duration = duration if source_duration is None else source_duration
    if not 0 < source_duration <= duration:
        raise ValueError(f"{name}: source duration must be in (0, output duration]")
    # ScreenCaptureKit writes a VFR stream.  Trim *after* normalising timestamps
    # and frame rate; input-level -t otherwise produces nondeterministic lengths.
    command = ["ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", str(source)]
    filter_complex = (
        f"[0:v]setpts=PTS-STARTPTS,{CROP},fps=30,trim=duration={source_duration:.6f},setpts=PTS-STARTPTS[base]"
    )
    if source_duration < duration:
        filter_complex += (
            f";[base]tpad=stop_mode=clone:stop_duration={duration - source_duration:.6f},"
            f"trim=duration={duration:.6f},setpts=PTS-STARTPTS[timed]"
        )
    else:
        filter_complex += f";[base]trim=duration={duration:.6f},setpts=PTS-STARTPTS[timed]"
    if confirmation_toast is None:
        filter_complex += ";[timed]null[v]"
    else:
        toast_start = duration - 2.5
        command.extend(["-loop", "1", "-framerate", "30", "-i", str(confirmation_toast)])
        filter_complex += (
            ";[timed][1:v]overlay=0:0:format=auto:"
            f"enable='between(t,{toast_start:.3f},{duration:.3f})',trim=duration={duration:.3f}[v]"
        )
    command.extend([
        "-filter_complex", filter_complex,
        "-map", "[v]", "-an", "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(destination),
    ])
    run(*command)
    return destination


def make_graphic_clip(
    name: str,
    source: Path,
    start: float,
    duration: float,
    source_duration: float | None = None,
) -> Path:
    destination = WORK / f"{name}.mp4"
    source_duration = duration if source_duration is None else source_duration
    if not 0 < source_duration <= duration:
        raise ValueError(f"{name}: source duration must be in (0, output duration]")
    tail = ""
    if source_duration < duration:
        tail = f",tpad=stop_mode=clone:stop_duration={duration - source_duration:.6f}"
    run(
        "ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", str(source),
        "-vf",
        "setpts=PTS-STARTPTS,scale=1920:1080:force_original_aspect_ratio=decrease,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0b1f16,setsar=1,fps=30,"
        f"trim=duration={source_duration:.6f}{tail},trim=duration={duration:.6f},setpts=PTS-STARTPTS",
        "-an", "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(destination),
    )
    return destination


def tempo_chain(tempo: float) -> str:
    """Keep every atempo stage in ffmpeg's supported 0.5–2.0 range."""
    if tempo <= 0:
        raise ValueError("tempo must be positive")
    stages: list[str] = []
    remainder = tempo
    while remainder > 2.0:
        stages.append("atempo=2.0")
        remainder /= 2.0
    while remainder < 0.5:
        stages.append("atempo=0.5")
        remainder /= 0.5
    stages.append(f"atempo={remainder:.9f}")
    return ",".join(stages)


def validate_narration_manifest() -> float:
    """Fail early if a source word would be omitted, duplicated, or overlapped."""
    if abs(NARRATION_SEGMENTS[0].source_start) > 1e-6:
        raise ValueError("Narration must start at source time 0")
    if abs(NARRATION_SEGMENTS[0].final_start - NARRATION_START) > 1e-6:
        raise ValueError("Narration must start at the end of the opener")
    source_cursor = 0.0
    final_cursor = NARRATION_START
    for segment in NARRATION_SEGMENTS:
        if not 0 < segment.tempo <= 1.25:
            raise ValueError(f"{segment.label}: tempo must stay at or below 1.25")
        if abs(segment.source_start - source_cursor) > 0.001:
            raise ValueError(f"{segment.label}: source manifest is not contiguous")
        if abs(segment.final_start - final_cursor) > 0.001:
            raise ValueError(f"{segment.label}: final start does not match its prior segment")
        source_cursor = segment.source_end
        final_cursor = segment.final_start + segment.duration
    if abs(source_cursor - 284.995875) > 0.001:
        raise ValueError("Narration manifest does not cover the recorded voiceover")
    if final_cursor > FINAL_DURATION + 1e-6:
        raise ValueError("Narration exceeds the final duration")
    return final_cursor


def make_mixed_audio(opening: Path, voice: Path, destination: Path) -> None:
    """Concatenate exact timeline slices; no delayed global voice/amix gate."""
    narration_end = validate_narration_manifest()
    opening_gap = NARRATION_START - OPENING_AUDIO_DURATION
    tail_gap = FINAL_DURATION - narration_end
    labels = [f"[voice{index}]" for index in range(len(NARRATION_SEGMENTS))]
    filters = [
        f"[0:a]atrim=duration={OPENING_AUDIO_DURATION:.6f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo[opening]",
        f"[1:a]asplit={len(labels)}{''.join(labels)}",
        f"anullsrc=r=48000:cl=stereo:d={opening_gap:.9f}[opening-gap]",
    ]
    timeline_labels = ["[opening]", "[opening-gap]"]
    for index, segment in enumerate(NARRATION_SEGMENTS):
        fade_out_start = max(0.0, segment.duration - AUDIO_FADE_SECONDS)
        label = f"[speech{index}]"
        filters.append(
            f"[voice{index}]atrim=start={segment.source_start:.6f}:end={segment.source_end:.6f},"
            f"asetpts=PTS-STARTPTS,aresample=48000,{tempo_chain(segment.tempo)},"
            f"afade=t=in:st=0:d={AUDIO_FADE_SECONDS:.3f},"
            f"afade=t=out:st={fade_out_start:.6f}:d={AUDIO_FADE_SECONDS:.3f},"
            f"atrim=duration={segment.duration:.9f},asetpts=PTS-STARTPTS{label}"
        )
        timeline_labels.append(label)
    if tail_gap > 0:
        filters.append(f"anullsrc=r=48000:cl=stereo:d={tail_gap:.9f}[tail-gap]")
        timeline_labels.append("[tail-gap]")
    filters.append(
        f"{''.join(timeline_labels)}concat=n={len(timeline_labels)}:v=0:a=1,"
        f"atrim=duration={FINAL_DURATION:.6f},asetpts=PTS-STARTPTS[a]"
    )
    run(
        "ffmpeg", "-y", "-i", str(opening), "-i", str(voice),
        "-filter_complex", ";".join(filters), "-map", "[a]",
        "-c:a", "aac", "-b:a", "192k", str(destination),
    )


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

    # Each cut starts with the narration source meaning it shows.  Static proof
    # panes are held on their last clean frame rather than leaking a future app.
    live_ranges = [
        ("01-baseline", required["main"], 0, 16.842500, None),
        ("02-upload", required["main"], 25, 4.535000, None),
        ("03-nova-result", required["main"], 90, 13.028333, None),
        ("04-agent-question-1", required["main"], 115, 10.000000, None),
        ("05-agent-answer-1", required["main"], 150, 12.040833, None),
        ("06-agent-question-2", required["main"], 180, 9.500000, None),
        ("07-agent-answer-2", required["main"], 220, 11.883833, 7.000000),
        ("08-agent-question-3", required["main"], 240, 9.000000, None),
        ("09-agent-answer-3", required["main"], 340.0, 11.742500, None),
        ("10-approval-review", required["main"], 340, 9.641167, None),
        # This remains within the reviewed clean 400–423.927 manager panel.
        ("11-approval-ready", required["main"], 400, 12.892500, None),
        ("12-final-dashboard", required["proof"], 0, 16.151666, 5.000000),
        ("13-erpnext-readback", required["proof"], 18, 17.098334, 6.000000),
        ("14-airtable-readback", required["proof"], 31, 14.713833, 6.000000),
        ("15-jira-readback", required["jira"], 40.0, 13.232000, 6.000000),
        ("16-slack-readback", required["slack"], 12, 12.939167, 6.000000),
        ("17-dashboard-close", required["proof"], 0, 21.439333, 7.000000),
    ]
    clips = [
        make_live_clip(
            name,
            source,
            start,
            duration,
            confirmation_toast if name == "11-approval-ready" else None,
            source_duration,
        )
        for name, source, start, duration, source_duration in live_ranges
    ]
    # Economic close remains on the dashboard until 263.700; the final summary
    # begins on the end card at 266.459 and the card holds through 284.516.
    clips.append(make_graphic_clip("18-end-card", required["end"], 0, 20.816, 12.0))

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

    # Build the audio separately from independently timed, speech-safe clips.
    # The concat timeline has no amix duration gate, so exact end-card duration
    # cannot be shortened by a delayed global voiceover stream.
    mixed_audio = WORK / "mixed-audio.m4a"
    make_mixed_audio(required["opening"], required["voice"], mixed_audio)

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
