"""Text-to-Speech using Google's Gemini TTS API (FREE in AI Studio).
This is the BEST free TTS available — better than Microsoft Edge in quality,
especially for Hindi. Supports 30+ voices, 24 languages, multi-speaker,
emotion tags, style prompts.

PRIMARY: Google Gemini 2.5 Flash TTS via Interactions API (May 2026 endpoint)
FALLBACK: Microsoft Edge TTS (used if Gemini quota exceeded)

Both are 100% FREE. Gemini just needs API key, Edge needs nothing.

API Reference: https://ai.google.dev/gemini-api/docs/interactions/speech-generation
"""
import os
import json
import asyncio
import subprocess
import requests
import edge_tts
from typing import Optional
from .utils import log, ensure_dir, retry


# ====== Available Gemini TTS Voices ======
# Names come from Google AI Studio. Each voice has a distinct personality.
# Full list: https://ai.google.dev/gemini-api/docs/interactions/speech-generation
GEMINI_VOICES = {
    # === Hindi (hi-in) voices — best for our default ===
    "hi-IN-Aoede": "🇮🇳 Aoede (Hindi, warm female)",
    "hi-IN-Kore": "🇮🇳 Kore (Hindi, clear female)",
    "hi-IN-Leda": "🇮🇳 Leda (Hindi, young female)",
    "hi-IN-Charon": "🇮🇳 Charon (Hindi, deep male)",
    "hi-IN-Orus": "🇮🇳 Orus (Hindi, professional male)",
    "hi-IN-Puck": "🇮🇳 Puck (Hindi, energetic male)",
    "hi-IN-Zephyr": "🇮🇳 Zephyr (Hindi, friendly male)",
    "hi-IN-Fenrir": "🇮🇳 Fenrir (Hindi, authoritative male)",
    "hi-IN-Pulcherrima": "🇮🇳 Pulcherrima (Hindi, expressive female)",
    "hi-IN-Sadaltager": "🇮🇳 Sadaltager (Hindi, mature male)",

    # === English voices ===
    "en-US-Aoede": "🇺🇸 Aoede (US English, warm)",
    "en-US-Kore": "🇺🇸 Kore (US English, clear female)",
    "en-US-Charon": "🇺🇸 Charon (US English, deep male)",
    "en-US-Orus": "🇺🇸 Orus (US English, professional male)",
    "en-US-Puck": "🇺🇸 Puck (US English, energetic male)",
    "en-US-Zephyr": "🇺🇸 Zephyr (US English, friendly male)",
    "en-US-Fenrir": "🇺🇸 Fenrir (US English, authoritative)",
    "en-US-Leda": "🇺🇸 Leda (US English, young female)",
    "en-US-Pulcherrima": "🇺🇸 Pulcherrima (US English, expressive)",

    # === Other popular languages ===
    "en-IN-Aoede": "🇮🇳 Aoede (Indian English female)",
    "en-IN-Charon": "🇮🇳 Charon (Indian English male)",
    "es-ES-Aoede": "🇪🇸 Aoede (Spanish)",
    "fr-FR-Aoede": "🇫🇷 Aoede (French)",
    "de-DE-Aoede": "🇩🇪 Aoede (German)",
    "ja-JP-Aoede": "🇯🇵 Aoede (Japanese)",
    "zh-CN-Aoede": "🇨🇳 Aoede (Chinese)",
}


# ====== Microsoft Edge TTS (fallback) ======
EDGE_VOICES = {
    "hi-IN-SwaraNeural": "🇮🇳 Swara (Hindi Female, fallback)",
    "hi-IN-MadhurNeural": "🇮🇳 Madhur (Hindi Male, fallback)",
    "en-US-AriaNeural": "🇺🇸 Aria (US Female, fallback)",
    "en-US-GuyNeural": "🇺🇸 Guy (US Male, fallback)",
    "en-IN-NeerjaNeural": "🇮🇳 Neerja (Indian English Female)",
    "en-IN-PrabhatNeural": "🇮🇳 Prabhat (Indian English Male)",
}


def detect_language_code(voice: str) -> str:
    """Extract language code from voice name like 'hi-IN-Aoede' -> 'hi-in'."""
    parts = voice.split("-")
    if len(parts) >= 2:
        return f"{parts[0].lower()}-{parts[1].lower()}"
    return "en-us"


# ====== Google Gemini TTS (Primary) ======

def gemini_tts(
    text: str,
    out_path: str,
    voice: str = "hi-IN-Aoede",
    style_prompt: Optional[str] = None,
    model: str = "gemini-2.5-flash-preview-tts",
) -> str:
    """Generate speech using Google Gemini TTS API.

    Args:
        text: Text to speak
        out_path: Output audio path (.wav or .mp3)
        voice: One of GEMINI_VOICES keys
        style_prompt: Optional style instruction e.g. "Speak in a calm, documentary narrator tone"
        model: "gemini-2.5-flash-preview-tts" (free) or "gemini-2.5-pro-preview-tts" (better quality)
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Get free key at https://aistudio.google.com")

    if voice not in GEMINI_VOICES:
        # Try to use it anyway — user might have a new voice name
        log.warning(f"Voice {voice} not in known list, attempting anyway")

    language_code = detect_language_code(voice)
    voice_name = voice.split("-", 2)[-1] if voice.count("-") >= 2 else voice

    # Use the Interactions API (May 2026 endpoint)
    url = "https://generativelanguage.googleapis.com/v1beta/interactions"
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
        "Api-Revision": "2026-05-20",
    }
    payload = {
        "model": model,
        "input": (style_prompt + "\n\n" if style_prompt else "") + text,
        "response_format": {"type": "audio"},
        "generation_config": {
            "speech_config": [
                {"voice": voice_name}
            ]
        },
        "language_code": language_code,
    }

    log.info(f"🗣️ Gemini TTS: voice={voice}, lang={language_code}, {len(text)} chars")

    def call():
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code == 429:
            raise Exception(f"Quota exceeded (429). Try again later or use fallback. {r.text[:200]}")
        r.raise_for_status()
        return r.json()

    try:
        data = retry(call, retries=2, delay=3)
    except Exception as e:
        log.warning(f"Gemini TTS failed: {e}")
        raise

    # Extract audio (base64 encoded PCM/WAV)
    # The Interactions API returns base64-encoded audio in output_audio
    audio_b64 = None

    # Try multiple response formats
    if "output_audio" in data:
        # New Interactions API format
        audio_b64 = data["output_audio"].get("data") if isinstance(data["output_audio"], dict) else data["output_audio"]
    elif "candidates" in data:
        # Older generateContent format
        for part in data["candidates"][0]["content"]["parts"]:
            if "inlineData" in part:
                audio_b64 = part["inlineData"]["data"]
                break

    if not audio_b64:
        raise RuntimeError(f"No audio in response: {json.dumps(data)[:500]}")

    import base64
    raw_bytes = base64.b64decode(audio_b64)

    # The API returns PCM s16le 24kHz mono — convert to MP3
    ensure_dir(os.path.dirname(out_path) or ".")

    if out_path.endswith(".mp3"):
        # Write PCM to temp file, then convert
        tmp_wav = out_path.rsplit(".", 1)[0] + ".pcm"
        with open(tmp_wav, "wb") as f:
            f.write(raw_bytes)
        # Convert PCM 24kHz mono s16le -> MP3
        cmd = [
            "ffmpeg", "-y",
            "-f", "s16le",
            "-ar", "24000",
            "-ac", "1",
            "-i", tmp_wav,
            "-codec:a", "libmp3lame",
            "-b:a", "192k",
            out_path,
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        os.remove(tmp_wav)
    else:
        with open(out_path, "wb") as f:
            f.write(raw_bytes)

    log.info(f"✅ Saved: {out_path} ({os.path.getsize(out_path) / 1024:.1f} KB)")
    return out_path


def gemini_tts_long_text(text: str, out_path: str, voice: str = "hi-IN-Aoede",
                          style_prompt: Optional[str] = None,
                          max_chunk_chars: int = 1500) -> str:
    """For long text (>1500 chars), split into chunks and concatenate.

    Gemini TTS works best with shorter segments. We split by sentences
    and concatenate the audio files.
    """
    if len(text) <= max_chunk_chars:
        return gemini_tts(text, out_path, voice, style_prompt)

    # Split by Hindi/English sentences
    import re
    sentences = re.split(r'(?<=[।.!?])\s+', text)
    chunks = []
    current = ""
    for s in sentences:
        if len(current) + len(s) > max_chunk_chars and current:
            chunks.append(current.strip())
            current = s
        else:
            current += " " + s if current else s
    if current:
        chunks.append(current.strip())

    log.info(f"📄 Split into {len(chunks)} chunks")

    # Generate each chunk
    chunk_files = []
    for i, chunk in enumerate(chunks):
        chunk_path = out_path.rsplit(".", 1)[0] + f"_chunk_{i:03d}.mp3"
        try:
            gemini_tts(chunk, chunk_path, voice, style_prompt)
            chunk_files.append(chunk_path)
        except Exception as e:
            log.warning(f"Chunk {i} failed: {e}")

    if not chunk_files:
        raise RuntimeError("All chunks failed")

    # Concatenate via FFmpeg
    if len(chunk_files) == 1:
        os.rename(chunk_files[0], out_path)
        return out_path

    concat_list = out_path + ".txt"
    with open(concat_list, "w") as f:
        for cf in chunk_files:
            f.write(f"file '{os.path.abspath(cf)}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        out_path,
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    # Cleanup chunks
    for cf in chunk_files:
        try: os.remove(cf)
        except OSError: pass
    os.remove(concat_list)

    return out_path


# ====== Microsoft Edge TTS (Fallback) ======

async def _edge_synth(text: str, voice: str, out_path: str, rate: str = "+0%"):
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(out_path)


def edge_tts_synth(text: str, out_path: str, voice: str = "hi-IN-SwaraNeural",
                   rate: str = "+0%") -> str:
    """Edge TTS — used as fallback when Gemini quota exceeded."""
    ensure_dir(os.path.dirname(out_path) or ".")
    log.info(f"🗣️ Edge TTS (fallback): voice={voice}")
    asyncio.run(_edge_synth(text, voice, rate, out_path))
    return out_path


# ====== Main Synth Function (with auto-fallback) ======

def synth_speech(
    text: str,
    out_path: str,
    voice: str = "hi-IN-Aoede",
    style_prompt: Optional[str] = None,
    prefer: str = "gemini",  # "gemini" or "edge"
) -> str:
    """Synthesize speech. Tries preferred engine, falls back to other."""
    ensure_dir(os.path.dirname(out_path) or ".")

    if prefer == "gemini":
        try:
            return gemini_tts_long_text(text, out_path, voice, style_prompt)
        except Exception as e:
            log.warning(f"Gemini TTS failed, falling back to Edge: {e}")
            # Map Gemini voice name to Edge equivalent
            edge_voice = map_to_edge_voice(voice)
            return edge_tts_synth(text, out_path, edge_voice)
    else:
        try:
            return edge_tts_synth(text, out_path, voice)
        except Exception as e:
            log.warning(f"Edge TTS failed, falling back to Gemini: {e}")
            # Map Edge voice name to Gemini equivalent
            gemini_voice = map_to_gemini_voice(voice)
            return gemini_tts_long_text(text, out_path, gemini_voice, style_prompt)


def map_to_edge_voice(gemini_voice: str) -> str:
    """Map Gemini voice name to closest Edge TTS equivalent."""
    mapping = {
        "hi-IN-Aoede": "hi-IN-SwaraNeural",
        "hi-IN-Kore": "hi-IN-SwaraNeural",
        "hi-IN-Leda": "hi-IN-SwaraNeural",
        "hi-IN-Charon": "hi-IN-MadhurNeural",
        "hi-IN-Orus": "hi-IN-MadhurNeural",
        "hi-IN-Puck": "hi-IN-MadhurNeural",
        "hi-IN-Zephyr": "hi-IN-MadhurNeural",
        "hi-IN-Fenrir": "hi-IN-MadhurNeural",
        "en-US-Aoede": "en-US-AriaNeural",
        "en-US-Kore": "en-US-AriaNeural",
        "en-US-Charon": "en-US-GuyNeural",
        "en-US-Orus": "en-US-GuyNeural",
        "en-US-Puck": "en-US-GuyNeural",
        "en-IN-Aoede": "en-IN-NeerjaNeural",
        "en-IN-Charon": "en-IN-PrabhatNeural",
    }
    return mapping.get(gemini_voice, "en-US-AriaNeural")


def map_to_gemini_voice(edge_voice: str) -> str:
    """Map Edge voice name to closest Gemini equivalent."""
    mapping = {
        "hi-IN-SwaraNeural": "hi-IN-Aoede",
        "hi-IN-MadhurNeural": "hi-IN-Charon",
        "en-US-AriaNeural": "en-US-Aoede",
        "en-US-GuyNeural": "en-US-Charon",
        "en-IN-NeerjaNeural": "en-IN-Aoede",
        "en-IN-PrabhatNeural": "en-IN-Charon",
    }
    return mapping.get(edge_voice, "hi-IN-Aoede")


# ====== Multi-scene helper for pipeline ======

def synth_scenes(scenes: list, out_dir: str, voice: str = "hi-IN-Aoede",
                 style_prompt: Optional[str] = None,
                 prefer: str = "gemini") -> list:
    """Generate one MP3 per scene + a combined MP3."""
    ensure_dir(out_dir)
    audio_files = []
    full_narration = ""

    log.info(f"🗣️ Synthesizing {len(scenes)} scenes with voice: {voice}")

    for scene in scenes:
        text = scene.get("narration", "").strip()
        if not text:
            continue
        out_path = os.path.join(out_dir, f"scene_{scene['id']:02d}.mp3")
        try:
            synth_speech(text, out_path, voice, style_prompt, prefer=prefer)
            audio_files.append({"scene_id": scene["id"], "path": out_path, "text": text})
            full_narration += text + " "
        except Exception as e:
            log.error(f"Scene {scene['id']} audio failed: {e}")

    # Combined narration
    if full_narration.strip():
        combined_path = os.path.join(out_dir, "full_narration.mp3")
        try:
            synth_speech(full_narration.strip(), combined_path, voice, style_prompt, prefer=prefer)
            audio_files.append({"scene_id": 0, "path": combined_path, "text": full_narration.strip(), "combined": True})
        except Exception as e:
            log.warning(f"Combined audio failed: {e}")

    return audio_files


def get_audio_duration(path: str) -> float:
    """Use ffprobe to get audio duration in seconds."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "json", path],
            capture_output=True, text=True, check=True,
        )
        return float(json.loads(result.stdout)["format"]["duration"])
    except Exception:
        return 5.0


# ====== Compatibility with old code (which imported synth_scenes / synth_text) ======

def synth_text(text: str, out_path: str, voice: str = "hi-IN-Aoede",
               style_prompt: Optional[str] = None) -> str:
    """Quick single-text synthesis."""
    return synth_speech(text, out_path, voice, style_prompt)


# Backwards compatibility alias
AVAILABLE_VOICES = GEMINI_VOICES  # for the frontend dropdown


# ====== CLI for quick testing ======

if __name__ == "__main__":
    import sys
    text = " ".join(sys.argv[1:]) or "नमस्ते दोस्तों! यह Google Gemini TTS का टेस्ट है।"
    out = "/tmp/test_gemini_tts.mp3"
    try:
        synth_speech(text, out, voice="hi-IN-Aoede",
                     style_prompt="Speak in a warm, friendly Hindi tone")
        print(f"✅ Generated: {out}")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure GEMINI_API_KEY is set in your environment.")
