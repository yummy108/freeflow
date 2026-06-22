"""Script generation using Groq Llama 3.3 70B (FASTEST, 1000 RPD free)
Falls back to Gemini if Groq not available.
"""
import json
import os
import requests
from typing import Dict, Any
from .utils import log, env, retry


def generate_script(research: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Turn research into a structured video script."""
    provider = config.get("llm", {}).get("provider", "groq")
    log.info(f"📝 Generating script via {provider}")

    prompt = build_prompt(research)

    if provider == "groq" and env("GROQ_API_KEY"):
        return _groq_generate(prompt, config)
    elif env("GEMINI_API_KEY"):
        return _gemini_generate(prompt, config)
    else:
        log.warning("No LLM API key, using template script")
        return _template_script(research)


def build_prompt(research: Dict[str, Any]) -> str:
    facts = "\n".join(
        [f"- {f['fact']} (source: {f.get('source', 'web')})" for f in research.get("key_facts", [])]
    )
    outline = "\n".join([f"- {s}" for s in research.get("outline", [])])

    return f"""You are a viral YouTube/TikTok scriptwriter (Vox / Kurzgesagt / Veritasium style).

TOPIC: {research.get('title', 'Unknown')}
DESCRIPTION: {research.get('description', '')}

KEY FACTS (verified by Google Search):
{facts}

OUTLINE:
{outline}

Write a 60-90 second video script (~180 words). The script should:
- Open with a STRONG hook (first 3 seconds must grab attention)
- Be conversational but authoritative
- Use short sentences, easy to speak aloud
- Build curiosity throughout
- End with a memorable takeaway

Return STRICT JSON (no markdown, no preamble):
{{
  "title": "final video title (max 80 chars, with emoji if appropriate)",
  "description": "1-2 sentence description for video platforms",
  "tags": ["5-10 SEO tags"],
  "scenes": [
    {{
      "id": 1,
      "duration_estimate": 8,
      "narration": "1-3 sentences the narrator says during this scene (max 50 words)",
      "visual_query": "specific image/video search query to illustrate this (be vivid)",
      "image_prompt": "AI image generation prompt for this scene if needed",
      "on_screen_text": "optional 2-5 word caption shown on screen"
    }}
    ...
  ],
  "thumbnail_text": "BIG bold text for thumbnail (max 4 words)",
  "background_music_mood": "cinematic|upbeat|mysterious|inspiring|calm"
}}

Generate 5-8 scenes. Each scene should have a vivid visual_query. Make the narration flow naturally across scenes."""


def _groq_generate(prompt: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Groq Llama 3.3 70B — fastest free LLM."""
    api_key = env("GROQ_API_KEY")
    model = config.get("llm", {}).get("groq_model", "llama-3.3-70b-versatile")

    def call():
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": config.get("llm", {}).get("temperature", 0.7),
                "max_tokens": config.get("llm", {}).get("max_tokens", 4000),
                "response_format": {"type": "json_object"},
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()

    try:
        data = retry(call, retries=3)
        text = data["choices"][0]["message"]["content"]
        return json.loads(text)
    except Exception as e:
        log.error(f"Groq failed: {e}")
        if env("GEMINI_API_KEY"):
            return _gemini_generate(prompt, config)
        raise


def _gemini_generate(prompt: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Gemini 2.5 Flash fallback."""
    api_key = env("GEMINI_API_KEY")
    model = config.get("llm", {}).get("gemini_model", "gemini-2.5-flash")

    def call():
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": config.get("llm", {}).get("temperature", 0.7),
                    "maxOutputTokens": config.get("llm", {}).get("max_tokens", 4000),
                    "responseMimeType": "application/json",
                },
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()

    data = retry(call, retries=3)
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text.strip().strip("```").strip("json").strip("```"))


def _template_script(research: Dict[str, Any]) -> Dict[str, Any]:
    """Last-resort template-based script when no API keys are present."""
    facts = research.get("key_facts", [])
    title = research.get("title", "Unknown")
    scenes = []
    narration_pool = []

    # Hook
    hook = research.get("hook") or f"Did you know these things about {title}?"
    scenes.append({
        "id": 1,
        "duration_estimate": 6,
        "narration": hook,
        "visual_query": f"dramatic {title}, cinematic establishing shot",
        "image_prompt": f"cinematic dramatic shot of {title}, 4K, no text",
        "on_screen_text": title.upper()[:20],
    })

    # Each fact becomes a scene
    for i, f in enumerate(facts[:6], start=2):
        fact_text = f["fact"] if isinstance(f, dict) else str(f)
        narration_pool.append(fact_text[:200])
        scenes.append({
            "id": i,
            "duration_estimate": 9,
            "narration": fact_text,
            "visual_query": f"{fact_text[:30]} visual representation",
            "image_prompt": f"vivid illustration of: {fact_text[:80]}, 4K cinematic",
            "on_screen_text": f"FACT #{i-1}",
        })

    # Closing
    scenes.append({
        "id": len(scenes) + 1,
        "duration_estimate": 6,
        "narration": f"If you enjoyed learning about {title}, share this with someone who would love it!",
        "visual_query": f"call to action, subscribe button",
        "image_prompt": f"cinematic outro shot, gradient background",
        "on_screen_text": "SUBSCRIBE",
    })

    return {
        "title": title,
        "description": research.get("description", f"Learn about {title}"),
        "tags": research.get("tags", [title.lower(), "education", "facts"]),
        "scenes": scenes,
        "thumbnail_text": title.upper()[:30],
        "background_music_mood": "cinematic",
    }


if __name__ == "__main__":
    sample = {
        "title": "Black Holes",
        "description": "Mind-blowing black hole facts",
        "key_facts": [
            {"fact": "Black holes bend time around them.", "source": "NASA"},
            {"fact": "The closest black hole is 1,500 light years away.", "source": "ESA"},
            {"fact": "Supermassive black holes have billions of times our sun's mass.", "source": "Wikipedia"},
        ],
        "outline": ["intro", "what is a black hole", "surprising facts", "future research"],
        "hook": "What if I told you black holes can bend time itself?",
        "thumbnail_prompt": "cinematic black hole vortex",
        "tags": ["black holes", "space", "science"],
    }
    script = generate_script(sample, {"llm": {"provider": "groq"}})
    print(json.dumps(script, indent=2))
