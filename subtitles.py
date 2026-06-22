"""Subtitle generation using simple word-level timing.
Approach: estimate word durations from audio length, distribute evenly.
For more accurate timing, use faster-whisper (optional).
Outputs both .srt and .ass (styled) subtitle files.
"""
import os
import subprocess
from .utils import log, ensure_dir


def get_audio_duration(path: str) -> float:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "json", path],
            capture_output=True, text=True, check=True,
        )
        import json
        return float(json.loads(result.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def word_timing_from_text(text: str, total_duration: float) -> list:
    """Distribute words across the audio duration.
    Better methods (forced alignment via Whisper) need GPU; this works everywhere.
    """
    words = text.split()
    if not words:
        return []

    # Give slightly more time to longer words
    weights = [max(1, len(w)) for w in words]
    total_weight = sum(weights)
    timings = []
    t = 0.0
    for w, weight in zip(words, weights):
        dur = (weight / total_weight) * total_duration
        timings.append({"word": w, "start": t, "end": t + dur})
        t += dur
    return timings


def group_into_lines(timings: list, words_per_line: int = 3) -> list:
    """Group word timings into subtitle lines."""
    lines = []
    for i in range(0, len(timings), words_per_line):
        chunk = timings[i : i + words_per_line]
        if not chunk:
            continue
        lines.append({
            "text": " ".join(c["word"] for c in chunk),
            "start": chunk[0]["start"],
            "end": chunk[-1]["end"],
        })
    return lines


def write_srt(lines: list, out_path: str) -> str:
    """Write SRT subtitle file."""
    ensure_dir(os.path.dirname(out_path) or ".")
    def fmt(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    with open(out_path, "w", encoding="utf-8") as f:
        for i, line in enumerate(lines, 1):
            f.write(f"{i}\n{fmt(line['start'])} --> {fmt(line['end'])}\n{line['text']}\n\n")
    return out_path


def write_ass(lines: list, out_path: str, font: str = "Noto Sans Devanagari", fontsize: int = 60,
              color: str = "&H00FFFFFF", outline: int = 3, shadow: int = 2,
              resolution_w: int = 1920, resolution_h: int = 1080,
              font_fallback: str = "Arial-Bold") -> str:
    """Write ASS (styled) subtitle file. For Hindi, use Noto Sans Devanagari."""
    ensure_dir(os.path.dirname(out_path) or ".")
    # ASS color format: &HAABBGGRR
    header = f"""[Script Info]
Title: FreeFlow Subtitles
ScriptType: v4.00+
WrapStyle: 2
PlayResX: {resolution_w}
PlayResY: {resolution_h}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{fontsize},{color},{color},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{outline},{shadow},2,40,40,80,1
Style: Fallback,{font_fallback},{fontsize},{color},{color},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{outline},{shadow},2,40,40,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def fmt(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        cs = int((t % 1) * 100)
        return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header)
        for line in lines:
            text = line["text"].replace("\n", "\\N")
            f.write(f"Dialogue: 0,{fmt(line['start'])},{fmt(line['end'])},Default,,0,0,0,,{text}\n")
    return out_path


def make_subtitles_for_scenes(scenes: list, audio_dir: str, out_dir: str,
                              words_per_line: int = 3, font: str = "Arial-Bold",
                              fontsize: int = 60, aspect: str = "16:9") -> dict:
    """Generate subtitles for each scene + a combined subs file."""
    ensure_dir(out_dir)
    all_lines = []
    offset = 0.0
    scene_subs = {}

    for scene in scenes:
        scene_id = scene["id"]
        audio_path = os.path.join(audio_dir, f"scene_{scene_id:02d}.mp3")
        text = scene.get("narration", "")
        if not text or not os.path.exists(audio_path):
            continue

        duration = get_audio_duration(audio_path)
        timings = word_timing_from_text(text, duration)
        lines = group_into_lines(timings, words_per_line)

        # Offset lines for combined subs
        for line in lines:
            line["start"] += offset
            line["end"] += offset
            all_lines.append(line)

        # Per-scene subs
        srt_path = os.path.join(out_dir, f"scene_{scene_id:02d}.srt")
        write_srt(lines, srt_path)
        scene_subs[scene_id] = {"srt": srt_path, "lines": lines}

        offset += duration

    # Combined subs
    combined_srt = os.path.join(out_dir, "full.srt")
    write_srt(all_lines, combined_srt)

    res_map = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)}
    rw, rh = res_map.get(aspect, (1920, 1080))
    combined_ass = os.path.join(out_dir, "full.ass")
    write_ass(all_lines, combined_ass, font=font, fontsize=fontsize, resolution_w=rw, resolution_h=rh)

    log.info(f"📝 Generated subtitles for {len(scene_subs)} scenes")
    return {"combined_srt": combined_srt, "combined_ass": combined_ass, "lines": all_lines, "by_scene": scene_subs}


if __name__ == "__main__":
    scenes = [{"id": 1, "narration": "Hello world this is a test of subtitles"}]
    os.makedirs("/tmp/sub_test", exist_ok=True)
    # Synth a fake audio file for demo
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono:d=4", "/tmp/sub_test/scene_01.mp3"
    ], capture_output=True)
    res = make_subtitles_for_scenes(scenes, "/tmp/sub_test", "/tmp/sub_test")
    print("Combined SRT:", open(res["combined_srt"]).read())
