"""Background music fetcher.
- Pixabay Music: FREE, no key (via their free CDN URLs in topics)
- Suno: AI-generated music, 10 free songs/day
- Fallback: Generate ambient drone with FFmpeg

All audio is royalty-free for personal/commercial use (per Pixabay license).
"""
import os
import subprocess
import urllib.parse
import requests
from .utils import log, ensure_dir


# Curated list of FREE, ROYALTY-FREE Pixabay music URLs.
# You can replace these with your own Pixabay favorites.
# Browse https://pixabay.com/music/ for more.
FREE_BGM_LIBRARY = {
    "cinematic": [
        "https://cdn.pixabay.com/audio/2022/10/25/audio_946bc0cba1.mp3",   # Cinematic ambient
        "https://cdn.pixabay.com/audio/2022/03/15/audio_b0dde2bfa2.mp3",
    ],
    "upbeat": [
        "https://cdn.pixabay.com/audio/2022/01/18/audio_d0c6ff1bdd.mp3",
        "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3",
    ],
    "mysterious": [
        "https://cdn.pixabay.com/audio/2022/11/17/audio_04e25a6c13.mp3",
        "https://cdn.pixabay.com/audio/2022/03/10/audio_1aaeeed9c4.mp3",
    ],
    "inspiring": [
        "https://cdn.pixabay.com/audio/2022/03/19/audio_a93cf23e90.mp3",
    ],
    "calm": [
        "https://cdn.pixabay.com/audio/2022/01/26/audio_d6c10a05b9.mp3",
    ],
}


def fetch_bgm(mood: str = "cinematic", out_path: str = "bgm.mp3") -> str:
    """Download a royalty-free background music track from Pixabay."""
    ensure_dir(os.path.dirname(out_path) or ".")
    urls = FREE_BGM_LIBRARY.get(mood, FREE_BGM_LIBRARY["cinematic"])
    url = urls[0]

    log.info(f"🎵 Fetching BGM ({mood}): {url[:80]}...")
    try:
        r = requests.get(url, timeout=60, stream=True)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
        return out_path
    except Exception as e:
        log.warning(f"Pixabay BGM fetch failed: {e}, generating ambient drone with FFmpeg")
        return _generate_ambient_drone(out_path, duration=120)


def _generate_ambient_drone(out_path: str, duration: int = 120) -> str:
    """Use FFmpeg to synthesize a soft ambient drone (last-resort fallback)."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency=220:duration={duration}",
        "-af", "volume=0.15,aecho=0.8:0.88:1000:0.3",
        "-ar", "44100",
        "-ac", "2",
        out_path,
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        log.info(f"Generated ambient drone: {out_path}")
    except Exception as e:
        log.error(f"FFmpeg drone failed: {e}")
        # Last resort: silent track
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=stereo:d={duration}",
            out_path,
        ], capture_output=True, check=False)
    return out_path


def loop_to_duration(bgm_path: str, target_duration: float, out_path: str) -> str:
    """Loop BGM to match the voiceover duration."""
    ensure_dir(os.path.dirname(out_path) or ".")
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", bgm_path,
        "-t", str(target_duration),
        "-af", f"afade=t=in:st=0:d=2,afade=t=out:st={max(0, target_duration-2):.2f}:d=2,volume=0.15",
        "-ar", "44100",
        out_path,
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return out_path


if __name__ == "__main__":
    p = fetch_bgm("cinematic", "/tmp/test_bgm.mp3")
    print(f"Fetched BGM: {p}, size: {os.path.getsize(p)} bytes")
