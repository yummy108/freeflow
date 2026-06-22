"""Video assembly — combines visuals + audio + subtitles + music into final MP4.
Uses MoviePy (FFmpeg under the hood).
"""
import os
import subprocess
from typing import List, Dict
from .utils import log, ensure_dir


def probe_duration(path: str) -> float:
    """Get media duration using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "json", path],
            capture_output=True, text=True, check=True,
        )
        import json
        return float(json.loads(result.stdout)["format"]["duration"])
    except Exception as e:
        log.warning(f"Could not probe {path}: {e}")
        return 5.0


def probe_size(path: str) -> tuple:
    """Get media dimensions."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", path],
            capture_output=True, text=True, check=True,
        )
        import json
        s = json.loads(result.stdout)["streams"][0]
        return (s["width"], s["height"])
    except Exception:
        return (1920, 1080)


def assemble_video(
    scenes: List[Dict],
    visual_assets: List[Dict],  # {scene_id, path, duration?}
    audio_assets: List[Dict],   # {scene_id, path}
    bgm_path: str,
    subtitle_path: str,          # .ass file
    out_path: str,
    aspect: str = "16:9",
    fps: int = 30,
) -> str:
    """Build final MP4 by stitching all scenes."""
    ensure_dir(os.path.dirname(out_path) or ".")
    log.info(f"🎞️ Assembling video → {out_path}")

    res_map = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)}
    W, H = res_map.get(aspect, (1920, 1080))

    # Build per-scene video clips using FFmpeg (more reliable than MoviePy for varied inputs)
    scene_clips = []
    audio_clips = []
    total_dur = 0.0
    scene_video_paths = []

    for scene in scenes:
        scene_id = scene["id"]
        # Find visual
        visual = next((v for v in visual_assets if v.get("scene_id") == scene_id), None)
        # Find audio
        audio = next((a for a in audio_assets if a.get("scene_id") == scene_id), None)

        if not audio or not os.path.exists(audio["path"]):
            log.warning(f"No audio for scene {scene_id}, skipping")
            continue

        audio_dur = probe_duration(audio["path"])
        target_dur = audio_dur  # match narration length exactly

        scene_video_path = os.path.join(
            os.path.dirname(out_path) or ".",
            f"scene_clip_{scene_id:02d}.mp4"
        )

        if visual and os.path.exists(visual["path"]):
            # Use FFmpeg to scale + crop the visual to match aspect + audio duration
            input_path = visual["path"]
            if visual.get("source") == "pexels" or input_path.endswith(".mp4"):
                cmd = [
                    "ffmpeg", "-y",
                    "-i", input_path,
                    "-i", audio["path"],
                    "-t", str(target_dur),
                    "-vf",
                    f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                    f"crop={W}:{H},"
                    f"fps={fps},"
                    f"format=yuv420p",
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "22",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "44100",
                    "-ac", "2",
                    "-shortest",
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    scene_video_path,
                ]
            else:
                # Image - create Ken Burns effect
                iw, ih = probe_size(input_path)
                # Zoom-in slightly for movement
                zoom = 1.05
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", input_path,
                    "-i", audio["path"],
                    "-t", str(target_dur),
                    "-vf",
                    f"scale={int(W*zoom)}:{int(H*zoom)}:force_original_aspect_ratio=increase,"
                    f"crop={int(W*zoom)}:{int(H*zoom)},"
                    f"zoompan=z='min(zoom+0.0008,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                    f"d={int(target_dur*fps)}:s={W}x{H}:fps={fps},"
                    f"format=yuv420p",
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "22",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "44100",
                    "-ac", "2",
                    "-shortest",
                    scene_video_path,
                ]
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                scene_video_paths.append(scene_video_path)
                total_dur += target_dur
            except subprocess.CalledProcessError as e:
                log.error(f"FFmpeg failed for scene {scene_id}: {e.stderr.decode() if e.stderr else e}")
                # Try fallback with image-only (no audio)
                continue
        else:
            # No visual at all — create colored background with text
            on_screen_text = scene.get("on_screen_text", "")
            narration = scene.get("narration", "")
            text = on_screen_text or narration[:60]
            # Use lavfi color source + drawtext
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=0x1a1a3e:s={W}x{H}:d={target_dur}:r={fps}",
                "-i", audio["path"],
                "-vf",
                f"drawtext=text='{text}':fontcolor=white:fontsize={int(H*0.05)}:"
                f"x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=0x00000080:boxborderw=20,"
                f"format=yuv420p",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "22",
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "44100",
                "-ac", "2",
                "-shortest",
                scene_video_path,
            ]
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                scene_video_paths.append(scene_video_path)
                total_dur += target_dur
            except subprocess.CalledProcessError as e:
                log.error(f"Placeholder failed for scene {scene_id}: {e.stderr.decode() if e.stderr else e}")

    if not scene_video_paths:
        raise RuntimeError("No scene clips generated. Check logs.")

    # Concatenate all scene clips
    concat_list_path = os.path.join(os.path.dirname(out_path) or ".", "concat_list.txt")
    with open(concat_list_path, "w") as f:
        for p in scene_video_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")

    concat_path = os.path.join(os.path.dirname(out_path) or ".", "concat_intermediate.mp4")
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        concat_path,
    ], capture_output=True, check=True)

    # Add BGM + subtitles
    final_cmd = [
        "ffmpeg", "-y",
        "-i", concat_path,
        "-i", bgm_path,
        "-filter_complex",
        f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{total_dur:.2f},"
        f"volume=0.15[bgm];"
        f"[0:a][bgm]amix=inputs=2:duration=shortest:dropout_transition=0[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-vf", f"subtitles='{subtitle_path}':fontsdir=/usr/share/fonts/truetype/dejavu",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-ac", "2",
        "-movflags", "+faststart",
        "-shortest",
        out_path,
    ]
    try:
        subprocess.run(final_cmd, capture_output=True, check=True)
        log.info(f"✅ Final video: {out_path} ({os.path.getsize(out_path) / 1024 / 1024:.1f} MB)")
    except subprocess.CalledProcessError as e:
        log.error(f"Final assembly failed: {e.stderr.decode() if e.stderr else e}")
        # Fallback: just concat without subtitles
        subprocess.run([
            "ffmpeg", "-y",
            "-i", concat_path,
            "-i", bgm_path,
            "-filter_complex",
            f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{total_dur:.2f},volume=0.15[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=shortest[audio]",
            "-map", "0:v",
            "-map", "[audio]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            out_path,
        ], capture_output=True, check=True)
        log.warning("Built video without subtitles due to error")

    # Cleanup
    for p in scene_video_paths + [concat_path]:
        try: os.remove(p)
        except OSError: pass
    try: os.remove(concat_list_path)
    except OSError: pass

    return out_path


if __name__ == "__main__":
    # Quick smoke test
    print("assemble module loaded. Use via md_to_video.py")
