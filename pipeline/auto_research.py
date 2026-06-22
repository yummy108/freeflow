"""Mode 2: Auto-Research Channel — runs every hour via GitHub Actions.
Picks a topic from topics.json, does deep research, generates video.
"""
import os
import sys
import json
import random
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.utils import log, load_config, ensure_dir, short_id
from pipeline.research import deep_research
from pipeline.script_gen import generate_script
from pipeline.md_to_video import run as md_to_video_run


def load_topics(path: str = "pipeline/topics.json") -> list:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        log.warning(f"No topics file at {path}, using defaults")
        return []


def pick_topic(topics: list, used_log: str = "pipeline/used_topics.txt") -> dict:
    """Pick a random topic, avoiding those used recently."""
    if not topics:
        # Default fallback topic
        return {
            "text": "भारत के बारे में अद्भुत तथ्य",
            "category": "facts",
            "language": "hi",
            "voice": "hi-IN-Aoede",
            "style_prompt": "रोचक, उत्साहित, YouTube narrator अंदाज़ में बोलें",
        }

    used = set()
    if os.path.exists(used_log):
        with open(used_log) as f:
            used = set(line.strip() for line in f)

    available = [t for t in topics if t["text"] not in used]
    if not available:
        # All used — reset
        if os.path.exists(used_log):
            os.remove(used_log)
        available = topics

    chosen = random.choice(available)

    # Mark as used
    with open(used_log, "a") as f:
        f.write(chosen["text"] + "\n")

    return chosen


def run(
    voice: str = None,
    style: str = "mixed",
    aspect: str = "16:9",
    manual: bool = False,
    topics_path: str = "pipeline/topics.json",
) -> str:
    """Main auto-research entry point."""
    config = load_config()

    topic = pick_topic(load_topics(topics_path))
    log.info(f"🎯 Auto-research topic: {topic['text']} (category: {topic['category']})")

    # Deep research
    research = deep_research(topic["text"])

    # Save research for reference
    workdir = os.path.join(config["output"]["workdir"], short_id(8))
    ensure_dir(workdir)
    with open(os.path.join(workdir, "research.json"), "w") as f:
        json.dump(research, f, indent=2)

    # Generate script
    script = generate_script(research, config)
    with open(os.path.join(workdir, "script.json"), "w") as f:
        json.dump(script, f, indent=2)

    # Use topic-specific voice + style_prompt
    voice = voice or topic.get("voice") or config["tts"]["default_voice"]
    style_prompt = topic.get("style_prompt") or config.get("tts", {}).get("style_prompt")
    log.info(f"🎙️ Voice: {voice}")
    if style_prompt:
        log.info(f"🎨 Style: {style_prompt[:80]}...")

    # Save topic as temp .md
    tmp_md = os.path.join(workdir, "topic.md")
    with open(tmp_md, "w") as f:
        f.write(f"# {topic['text']}\n\n")
        for fact in research.get("key_facts", []):
            fact_text = fact["fact"] if isinstance(fact, dict) else fact
            f.write(f"- {fact_text}\n")

    url = md_to_video_run(
        md_path=tmp_md,
        topic=topic["text"],
        voice=voice,
        style=style,
        aspect=aspect,
        config_path="pipeline/config.yaml",
        upload=True,
    )

    log.info(f"🎉 Auto-research video published: {url}")
    return url


def main():
    parser = argparse.ArgumentParser(description="FreeFlow: Auto-Research Mode")
    parser.add_argument("--voice", help="Override voice")
    parser.add_argument("--style", choices=["stock", "ai", "mixed"], default="mixed")
    parser.add_argument("--aspect", choices=["16:9", "9:16", "1:1"], default="16:9")
    parser.add_argument("--manual", action="store_true", help="Manual trigger (vs cron)")
    parser.add_argument("--topics", default="pipeline/topics.json")
    args = parser.parse_args()

    result = run(
        voice=args.voice,
        style=args.style,
        aspect=args.aspect,
        manual=args.manual,
        topics_path=args.topics,
    )
    print(f"\n🎉 Auto-research output: {result}")


if __name__ == "__main__":
    main()
