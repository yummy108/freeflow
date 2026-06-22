"""Deep research using Gemini 2.5 Flash with Google Search grounding.
FREE tier: 1,500 requests/day, 500 RPD with grounding.
"""
import json
import requests
from typing import List, Dict, Any
from .utils import log, env, retry


def deep_research(topic: str, depth: int = 3) -> Dict[str, Any]:
    """Use Gemini 2.5 Flash w/ Google Search grounding for real research."""
    api_key = env("GEMINI_API_KEY")
    if not api_key:
        log.warning("GEMINI_API_KEY not set, using fallback research")
        return _fallback_research(topic)

    log.info(f"🔍 Researching: {topic}")

    prompt = f"""You are a research assistant. Research this topic thoroughly:

TOPIC: {topic}

Use Google Search to find the latest, most accurate, surprising facts.

Return STRICT JSON (no markdown, no preamble) with this structure:
{{
  "title": "Catchy, clickable video title (max 80 chars)",
  "description": "1-sentence video description",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "key_facts": [
    {{"fact": "specific surprising fact", "source": "where you found it"}},
    ...6-10 facts total, in order of how compelling they are
  ],
  "hook": "A 1-sentence attention-grabbing opener for the video",
  "thumbnail_prompt": "1-sentence vivid visual description for thumbnail",
  "outline": [
    "Scene 1: brief description of what to show",
    "Scene 2: brief description",
    ...5-8 scenes
  ]
}}

Only verifiable facts. Cite sources when possible. Today's date is 2026-06-22."""

    def call():
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 4000,
            },
        }
        r = requests.post(url, json=body, timeout=120)
        r.raise_for_status()
        return r.json()

    try:
        data = retry(call, retries=2)
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        # Strip markdown code fences if any
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip().rstrip("`").strip()
        return json.loads(text)
    except Exception as e:
        log.warning(f"Gemini research failed: {e}, using fallback")
        return _fallback_research(topic)


def _fallback_research(topic: str) -> Dict[str, Any]:
    """No-key fallback using DuckDuckGo Instant Answer + Wikipedia."""
    log.info("Using DuckDuckGo + Wikipedia fallback research")
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(topic, max_results=8):
                results.append({"title": r.get("title", ""), "body": r.get("body", ""), "href": r.get("href", "")})
        facts = [r["body"][:200] for r in results[:8] if r.get("body")]
    except ImportError:
        facts = [f"{topic} is a fascinating subject with many surprising aspects."]
        results = []

    return {
        "title": topic.title()[:80],
        "description": f"A quick dive into {topic}.",
        "tags": [topic.lower().replace(" ", "-"), "education", "facts", "ai", "video"],
        "key_facts": [{"fact": f, "source": "DuckDuckGo"} for f in facts[:8]],
        "hook": f"Did you know these surprising things about {topic}?",
        "thumbnail_prompt": f"cinematic dramatic visual related to {topic}, 4K, no text",
        "outline": [
            f"Introduction: what is {topic}?",
            f"History and origin of {topic}",
            f"Most surprising facts about {topic}",
            f"Why {topic} matters today",
            f"The future of {topic}",
        ],
    }


if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "black holes"
    print(json.dumps(deep_research(topic), indent=2))
