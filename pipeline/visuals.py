"""Stock video fetcher using Pexels API.
FREE: 200 requests/hour, 20,000/month.
API key: https://www.pexels.com/api/
"""
import os
import requests
from typing import Dict, List
from .utils import log, env, retry, ensure_dir


PEXELS_API = "https://api.pexels.com/videos"


def search_videos(query: str, per_page: int = 3, orientation: str = "landscape") -> List[Dict]:
    """Search Pexels videos. Returns list of {id, url, duration, width, height}."""
    api_key = env("PEXELS_API_KEY")
    if not api_key:
        log.warning("PEXELS_API_KEY not set, will use image fallback only")
        return []

    def call():
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation,
            "size": "medium",
        }
        r = requests.get(
            PEXELS_API + "/search",
            headers={"Authorization": api_key},
            params=params,
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    try:
        data = retry(call, retries=2)
        videos = data.get("videos", [])
        # Pick the best quality file (HD if available)
        results = []
        for v in videos:
            files = v.get("video_files", [])
            # Prefer HD 1080p or 720p
            best = None
            for f in files:
                if orientation == "portrait" and f.get("width", 0) < f.get("height", 0):
                    if best is None or f.get("width", 0) > best.get("width", 0):
                        best = f
                elif orientation == "landscape" and f.get("width", 0) > f.get("height", 0):
                    if best is None or f.get("width", 0) > best.get("width", 0):
                        best = f
            if not best and files:
                best = files[0]
            if best:
                results.append({
                    "id": v["id"],
                    "url": best["link"],
                    "duration": v.get("duration", 10),
                    "width": best.get("width", 1920),
                    "height": best.get("height", 1080),
                })
        log.info(f"📹 Pexels: found {len(results)} videos for '{query}'")
        return results
    except Exception as e:
        log.warning(f"Pexels search failed for '{query}': {e}")
        return []


def download_video(url: str, out_path: str) -> str:
    """Download a stock video file."""
    ensure_dir(os.path.dirname(out_path) or ".")
    log.info(f"⬇️ Downloading {url[:60]}...")

    def call():
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)
        return out_path

    return retry(call, retries=2)


def fetch_visuals_for_scenes(scenes: List[Dict], out_dir: str, orientation: str = "landscape") -> List[Dict]:
    """For each scene, fetch a stock video. Returns list of {scene_id, path, query}."""
    ensure_dir(out_dir)
    results = []

    for scene in scenes:
        query = scene.get("visual_query") or scene.get("narration", "")[:50]
        scene_id = scene["id"]
        out_path = os.path.join(out_dir, f"scene_{scene_id:02d}.mp4")

        videos = search_videos(query, per_page=3, orientation=orientation)
        if videos:
            try:
                download_video(videos[0]["url"], out_path)
                results.append({
                    "scene_id": scene_id,
                    "path": out_path,
                    "query": query,
                    "source": "pexels",
                    "duration": videos[0]["duration"],
                })
                continue
            except Exception as e:
                log.warning(f"Download failed for scene {scene_id}: {e}")

        # No video found — image_gen will fill in
        results.append({"scene_id": scene_id, "query": query, "source": "none"})

    return results


if __name__ == "__main__":
    vids = search_videos("ocean waves aerial", per_page=2)
    print(f"Found {len(vids)} videos")
    for v in vids:
        print(f"  {v['width']}x{v['height']}, {v['duration']}s, {v['url'][:80]}")
