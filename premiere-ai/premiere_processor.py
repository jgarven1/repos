"""
Premiere AI — core processing module
--------------------------------------
1. Find video files in a folder
2. Transcribe each with Whisper (timestamped segments, cached to disk)
3. Send transcripts to Claude with a natural language editing goal
4. Return a structured edit sequence (list of clips with in/out timecodes)
5. Export as EDL (importable by Premiere Pro, DaVinci Resolve, etc.)
"""

import json
import pathlib
import re

VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv", ".mxf",
    ".m4v", ".wmv", ".flv", ".webm", ".r3d", ".braw",
}
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]
CLAUDE_MODEL   = "claude-sonnet-4-6"
CACHE_DIR_NAME = ".premiere_cache"


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def find_video_files(folder):
    folder = pathlib.Path(folder)
    return sorted(
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
    )


# ---------------------------------------------------------------------------
# Transcript cache
# ---------------------------------------------------------------------------

def cache_path(video_path):
    video_path = pathlib.Path(video_path)
    return video_path.parent / CACHE_DIR_NAME / (video_path.stem + "_transcript.json")


def is_transcribed(video_path):
    return cache_path(video_path).exists()


# ---------------------------------------------------------------------------
# Transcription (Whisper)
# ---------------------------------------------------------------------------

def transcribe_video(video_path, model_name="base", progress_cb=None):
    """
    Transcribe a video file using Whisper. Caches the result so re-running
    skips already-transcribed files.
    Returns list of {start, end, text} segment dicts.
    """
    video_path = pathlib.Path(video_path)
    cp = cache_path(video_path)

    if cp.exists():
        if progress_cb:
            progress_cb(f"Using cached transcript for '{video_path.name}'")
        return json.loads(cp.read_text(encoding="utf-8"))

    try:
        import whisper
    except ImportError:
        raise ImportError(
            "openai-whisper is not installed. Run:\n  pip install openai-whisper\n"
            "FFmpeg must also be installed: https://ffmpeg.org/download.html"
        )

    if progress_cb:
        progress_cb(f"Loading Whisper '{model_name}' model (downloads on first use)…")
    model = whisper.load_model(model_name)

    if progress_cb:
        progress_cb(f"Transcribing '{video_path.name}'…")
    result = model.transcribe(str(video_path), verbose=False)

    segments = [
        {"start": seg["start"], "end": seg["end"], "text": seg["text"].strip()}
        for seg in result["segments"]
    ]

    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps(segments, indent=2), encoding="utf-8")

    if progress_cb:
        progress_cb(f"✓ '{video_path.name}' — {len(segments)} segments")
    return segments


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt_time(seconds):
    """Format seconds as HH:MM:SS.mmm for display."""
    h  = int(seconds // 3600)
    m  = int((seconds % 3600) // 60)
    s  = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def _seconds_to_tc(seconds, fps=29.97):
    """Convert seconds to HH:MM:SS:FF EDL timecode."""
    fps_int = round(fps)
    total_frames = int(seconds * fps)
    frames   = total_frames % fps_int
    total_s  = total_frames // fps_int
    ss = total_s % 60
    mm = (total_s // 60) % 60
    hh = total_s // 3600
    return f"{hh:02d}:{mm:02d}:{ss:02d}:{frames:02d}"


def _reel_name(filename):
    stem  = pathlib.Path(filename).stem
    clean = re.sub(r"[^A-Za-z0-9_]", "_", stem)
    return clean[:8].upper()


def _format_transcript_for_claude(video_name, segments):
    lines = [f"Source: {video_name}"]
    for seg in segments:
        lines.append(
            f"  [{fmt_time(seg['start'])} --> {fmt_time(seg['end'])}] {seg['text']}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Edit sequence generation (Claude)
# ---------------------------------------------------------------------------

_EDIT_PROMPT = """\
You are a professional video editor. Based on the transcripts below and the \
editing goal, select specific clip segments to build an edit sequence.

Editing goal: {goal}

Transcripts (with timestamps):
{transcripts}

Respond with a JSON array ONLY — no markdown, no explanation.
Each element must have:
{{
  "source_file": "<exact filename shown in Source: lines>",
  "in_seconds": <float>,
  "out_seconds": <float>,
  "note": "<brief reason this clip was chosen>"
}}

Rules:
- in_seconds / out_seconds must fall within the provided timestamps
- Add ~0.5 s padding at each end where possible for natural cuts
- Order clips for a coherent final sequence
- Prefer the most relevant and impactful segments
"""


def generate_edit_sequence(transcripts, goal, api_key):
    """
    transcripts : list of {"video_name": str, "segments": list}
    goal        : natural language editing instruction
    api_key     : Anthropic API key
    Returns list of clip dicts: {source_file, in_seconds, out_seconds, note}
    """
    import anthropic as _anthropic

    transcript_text = "\n\n".join(
        _format_transcript_for_claude(t["video_name"], t["segments"])
        for t in transcripts
    )

    client  = _anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": _EDIT_PROMPT.format(goal=goal, transcripts=transcript_text),
        }],
    )

    raw = message.content[0].text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$",       "", raw)
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_edl(clips, output_path, fps=29.97):
    """Write a CMX 3600 EDL file importable by Premiere Pro and DaVinci Resolve."""
    lines = ["TITLE: Claude Edit Sequence", "FCM: NON-DROP FRAME", ""]

    record_pos = 0.0
    for i, clip in enumerate(clips):
        in_s     = float(clip["in_seconds"])
        out_s    = float(clip["out_seconds"])
        duration = out_s - in_s

        src_in  = _seconds_to_tc(in_s,              fps)
        src_out = _seconds_to_tc(out_s,             fps)
        rec_in  = _seconds_to_tc(record_pos,        fps)
        rec_out = _seconds_to_tc(record_pos + duration, fps)
        reel    = _reel_name(clip["source_file"])

        lines.append(
            f"{i+1:03d}  {reel:<8} V     C        "
            f"{src_in} {src_out} {rec_in} {rec_out}"
        )
        lines.append(f"* FROM CLIP NAME: {clip['source_file']}")
        if clip.get("note"):
            lines.append(f"* NOTE: {clip['note']}")
        lines.append("")

        record_pos += duration

    pathlib.Path(output_path).write_text("\n".join(lines), encoding="utf-8")


def export_summary(clips, output_path):
    """Write a human-readable edit sequence summary."""
    lines = ["CLAUDE EDIT SEQUENCE SUMMARY", "=" * 40, ""]

    total = 0.0
    for i, clip in enumerate(clips, 1):
        duration = float(clip["out_seconds"]) - float(clip["in_seconds"])
        total   += duration
        lines += [
            f"Clip {i}: {clip['source_file']}",
            f"  In:       {fmt_time(float(clip['in_seconds']))}",
            f"  Out:      {fmt_time(float(clip['out_seconds']))}",
            f"  Duration: {duration:.1f}s",
        ]
        if clip.get("note"):
            lines.append(f"  Note:     {clip['note']}")
        lines.append("")

    mm, ss = divmod(int(total), 60)
    lines.append(f"Total sequence duration: {total:.1f}s  ({mm}m {ss}s)")
    pathlib.Path(output_path).write_text("\n".join(lines), encoding="utf-8")
