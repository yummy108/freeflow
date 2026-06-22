"""Mode 1: MD → Video pipeline orchestrator.
Reads a markdown file (either a script or just a topic), turns it into a full video.

Usage:
  python -m pipeline.md_to_video --md path/to/script.md [--voice en-US-AriaNeural] [--style mixed]
  python -m pipeline.md_to_video --topic "Latest AI breakthroughs"
"""
import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.utils import load_config, log, ensure_dir, slugify, short_id
from pipeline.research import deep_research, _fallback_research
from pipeline.script_gen import generate_script, _template_script
from pipeline.tts import synth_scenes, AVAILABLE_VOICES
from pipeline.visuals import fetch_visuals_for_scenes
from pipeline.image_gen import generate_for_scenes
from pipeline.music import fetch_bgm, loop_to_duration
from pipeline.subtitles import make_subtitles_for_scenes
from pipeline.assemble import assemble_video, probe_duration
from pipeline.publish import publish_to_release, update_video_index


def run(
    md_path: str = None,
    topic: str = None,
    voice: str = None,
    style: str = "mixed",
    aspect: str = "16:9",
    config_path: str = "pipeline/config.yaml",
    upload: bool = True,
) -> str:
    """Main entry point. Returns the output video path."""
    config = load_config(config_path)
    voice = voice or config["tts"]["default_voice"]
    if voice not in AVAILABLE_VOICES:
        log.warning(f"Voice {voice} not in known list, attempting anyway")

    # ===== Setup workdir =====
    base = config["output"]["workdir"]
    workdir = os.path.join(base, short_id(8))
    ensure_dir(workdir)
    audio_dir = os.path.join(workdir, "audio")
    visual_dir = os.path.join(workdir, "visuals")
    image_dir = os.path.join(workdir, "images")
    music_dir = os.path.join(workdir, "music")
    subs_dir = os.path.join(workdir, "subs")
    for d in [audio_dir, visual_dir, image_dir, music_dir, subs_dir]:
        ensure_dir(d)

    # ===== Stage 1: Get research / script content =====
    log.info("=" * 60)
    log.info("🎬 FreeFlow Pipeline Started")
    log.info("=" * 60)

    if md_path and os.path.exists(md_path):
        log.info(f"📄 Reading MD file: {md_path}")
        md_content = Path(md_path).read_text(encoding="utf-8")

        # Decide: is this a full script (with scenes/durations), or just a topic?
        if looks_like_full_script(md_content):
            log.info("📜 MD looks like a full script, skipping LLM generation")
            script = parse_md_to_script(md_content)
        else:
            log.info("🔍 MD looks like a topic — researching & generating script")
            research = md_to_research(md_content)
            script = generate_script(research, config)
    elif topic:
        log.info(f"🔍 Researching topic: {topic}")
        research = deep_research(topic)
        script = generate_script(research, config)
    else:
        raise ValueError("Provide either --md or --topic")

    log.info(f"📝 Script: {script.get('title')} ({len(script.get('scenes', []))} scenes)")

    # Save script.json for debugging
    with open(os.path.join(workdir, "script.json"), "w") as f:
        json.dump(script, f, indent=2)

    # ===== Stage 2: TTS =====
    log.info("=" * 60)
    log.info("🗣️ Stage 2: Voice synthesis")
    style_prompt = config.get("tts", {}).get("style_prompt")
    prefer_engine = config.get("tts", {}).get("prefer_engine", "gemini")
    # Use script-defined style if not set globally
    if not style_prompt and script.get("background_music_mood"):
        style_prompt = None  # let TTS use default
    audio_assets = synth_scenes(
        script["scenes"], audio_dir, voice=voice,
        style_prompt=style_prompt, prefer=prefer_engine,
    )
    log.info(f"✅ Generated {len([a for a in audio_assets if not a.get('combined')])} scene audio files")

    # ===== Stage 3: Visuals =====
    log.info("=" * 60)
    log.info("🎨 Stage 3: Visuals (video + AI images)")

    visual_assets = []
    image_assets = []
    orientation = "portrait" if aspect == "9:16" else "landscape"

    if style in ("stock", "mixed"):
        try:
            visual_assets = fetch_visuals_for_scenes(script["scenes"], visual_dir, orientation=orientation)
        except Exception as e:
            log.warning(f"Stock visual fetch failed: {e}")

    # Fill in missing visuals with AI images
    if style in ("ai", "mixed") or not visual_assets:
        try:
            res = config.get("image", {})
            width, height = config["video"]["resolution"].get(aspect, [1920, 1080])
            image_assets = generate_for_scenes(
                script["scenes"], image_dir,
                width=width, height=height,
                model=res.get("model", "flux")
            )
        except Exception as e:
            log.warning(f"AI image gen failed: {e}")

    # Merge: for each scene, pick visual (video) or image
    final_visual_assets = []
    for scene in script["scenes"]:
        scene_id = scene["id"]
        v = next((x for x in visual_assets if x.get("scene_id") == scene_id and x.get("source") == "pexels" and os.path.exists(x.get("path", ""))), None)
        if v:
            final_visual_assets.append(v)
        else:
            img = next((x for x in image_assets if x.get("scene_id") == scene_id), None)
            if img:
                final_visual_assets.append(img)

    log.info(f"✅ {len(final_visual_assets)} visuals ready (videos + images)")

    # ===== Stage 4: Music =====
    log.info("=" * 60)
    log.info("🎵 Stage 4: Background music")
    mood = script.get("background_music_mood", "cinematic")
    bgm_raw = fetch_bgm(mood, os.path.join(music_dir, "bgm_raw.mp3"))

    # Calculate total voice duration to loop BGM
    total_dur = 0.0
    for a in audio_assets:
        if not a.get("combined") and os.path.exists(a["path"]):
            total_dur += probe_duration(a["path"])

    bgm_path = loop_to_duration(bgm_raw, total_dur + 5, os.path.join(music_dir, "bgm_looped.mp3"))
    log.info(f"✅ BGM ready ({total_dur + 5:.1f}s)")

    # ===== Stage 5: Subtitles =====
    log.info("=" * 60)
    log.info("📝 Stage 5: Subtitles")
    sub_config = config.get("subtitles", {})
    sub_assets = make_subtitles_for_scenes(
        script["scenes"], audio_dir, subs_dir,
        words_per_line=sub_config.get("words_per_line", 3),
        font=sub_config.get("font", "Arial-Bold"),
        fontsize=sub_config.get("fontsize", 60),
        aspect=aspect,
    )
    log.info(f"✅ Subtitles generated")

    # ===== Stage 6: Assemble =====
    log.info("=" * 60)
    log.info("🎞️ Stage 6: Video assembly")
    out_path = os.path.join(workdir, "final.mp4")
    final_path = assemble_video(
        scenes=script["scenes"],
        visual_assets=final_visual_assets,
        audio_assets=audio_assets,
        bgm_path=bgm_path,
        subtitle_path=sub_assets["combined_ass"],
        out_path=out_path,
        aspect=aspect,
        fps=config.get("video", {}).get("fps", 30),
    )

    # ===== Stage 7: Publish =====
    log.info("=" * 60)
    log.info("📤 Stage 7: Publishing")
    if upload and os.path.exists(final_path):
        url = publish_to_release(
            video_path=final_path,
            title=script.get("title", "FreeFlow Video"),
            description=script.get("description", ""),
            tag=f"video-{short_id(8)}",
        )
        update_video_index(url, script.get("title", ""), topic or md_path or "")
        if url:
            log.info(f"🎉 DONE! Video URL: {url}")
            return url
        else:
            log.info(f"🎉 DONE! Local file: {final_path}")
            return final_path
    else:
        log.info(f"🎉 DONE! Local file: {final_path}")
        return final_path


def looks_like_full_script(md: str) -> bool:
    """Heuristic: if it has multiple scenes with narration-like structure."""
    lines = md.split("\n")
    has_scene_marker = sum(1 for l in lines if l.strip().startswith(("## Scene", "**Scene", "## SCENE")))
    has_long_paragraphs = sum(1 for l in lines if len(l.strip()) > 100) >= 5
    return has_scene_marker >= 2 or has_long_paragraphs


def parse_md_to_script(md: str) -> dict:
    """Parse a manually-written script MD into our standard format."""
    scenes = []
    current = None
    sid = 0
    for line in md.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("# "):
            title = line[2:].strip()
            continue
        if line.startswith("## ") or line.startswith("**Scene") or line.startswith("## SCENE"):
            if current:
                scenes.append(current)
            sid += 1
            current = {
                "id": sid,
                "duration_estimate": 8,
                "narration": "",
                "visual_query": "",
                "image_prompt": "",
                "on_screen_text": "",
            }
            # Extract any text after the scene marker
            rest = line.lstrip("#").lstrip("*").strip()
            rest = rest.replace("Scene", "", 1).replace("SCENE", "", 1).strip()
            if rest and ":" in rest:
                current["on_screen_text"] = rest.split(":", 1)[-1].strip()[:30]
            elif rest:
                current["visual_query"] = rest
        else:
            if current:
                # First non-empty line becomes narration, second becomes visual_query
                if not current["narration"]:
                    current["narration"] = line
                elif not current["visual_query"]:
                    current["visual_query"] = line
    if current:
        scenes.append(current)

    # Fill missing fields with sensible defaults
    for s in scenes:
        if not s.get("visual_query"):
            s["visual_query"] = (s.get("narration") or "")[:50]
        if not s.get("image_prompt"):
            s["image_prompt"] = (s.get("narration") or "")[:100]

    return {
        "title": title if 'title' in dir() else "FreeFlow Video",
        "description": "Generated with FreeFlow",
        "tags": ["FreeFlow", "AI", "video"],
        "scenes": scenes,
        "thumbnail_text": title[:30] if 'title' in dir() else "VIDEO",
        "background_music_mood": "cinematic",
    }


def md_to_research(md_content: str) -> dict:
    """Treat MD content as research notes (or just a topic in the first heading)."""
    lines = md_content.strip().split("\n")
    title = lines[0].lstrip("#").strip() if lines and lines[0].startswith("#") else md_content[:80]

    facts = []
    current_fact = ""
    for line in lines:
        if line.strip().startswith(("- ", "* ", "1.", "2.")):
            if current_fact:
                facts.append({"fact": current_fact.strip(), "source": "MD input"})
            current_fact = line.lstrip("-*0123456789. ").strip()
        else:
            current_fact += " " + line.strip()
    if current_fact:
        facts.append({"fact": current_fact.strip(), "source": "MD input"})

    if not facts:
        # Just a topic
        return deep_research(title)

    return {
        "title": title,
        "description": f"A video about {title}.",
        "tags": [w.lower() for w in title.split()[:5]],
        "key_facts": facts[:8],
        "hook": f"Did you know these things about {title}?",
        "thumbnail_prompt": f"cinematic {title}",
        "outline": [f.get("fact", "")[:60] for f in facts[:6]],
    }


def main():
    parser = argparse.ArgumentParser(description="FreeFlow: MD → Video")
    parser.add_argument("--md", help="Path to .md file (script or topic)")
    parser.add_argument("--topic", help="Topic to research & generate")
    parser.add_argument("--voice", help="Edge TTS voice (default: en-US-AriaNeural)")
    parser.add_argument("--style", choices=["stock", "ai", "mixed"], default="mixed")
    parser.add_argument("--aspect", choices=["16:9", "9:16", "1:1"], default="16:9")
    parser.add_argument("--config", default="pipeline/config.yaml")
    parser.add_argument("--no-upload", action="store_true")
    args = parser.parse_args()

    if not args.md and not args.topic:
        parser.error("Provide --md or --topic")

    result = run(
        md_path=args.md,
        topic=args.topic,
        voice=args.voice,
        style=args.style,
        aspect=args.aspect,
        config_path=args.config,
        upload=not args.no_upload,
    )
    print(f"\n🎉 Output: {result}")


if __name__ == "__main__":
    main()
