"""AI Image generation using Pollinations.ai — FREE, NO API KEY, NO LIMITS.
Uses Flux, GPT-Image, Kontext, and many other open models.
Just hit a URL: https://image.pollinations.ai/prompt/<prompt>
"""
import os
import time
import random
import urllib.parse
import requests
from typing import Dict, Optional
from .utils import log, ensure_dir


def generate_image(
    prompt: str,
    out_path: str,
    width: int = 1920,
    height: int = 1080,
    model: str = "flux",
    enhance: bool = True,
    seed: Optional[int] = None,
) -> str:
    """Generate an image via Pollinations.ai. Free, no key, no limits."""
    ensure_dir(os.path.dirname(out_path) or ".")
    if seed is None:
        seed = random.randint(1, 999999999)

    params = {
        "width": width,
        "height": height,
        "seed": seed,
        "nologo": "true",
        "private": "true",
        "model": model,
        "enhance": str(enhance).lower(),
    }
    encoded_prompt = urllib.parse.quote(prompt)
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?{qs}"

    log.info(f"🎨 Generating image: '{prompt[:60]}...' [{model}]")
    try:
        r = requests.get(url, timeout=180)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(r.content)
        return out_path
    except Exception as e:
        log.error(f"Pollinations failed for '{prompt[:40]}': {e}")
        return _placeholder_image(out_path, prompt, width, height)


def _placeholder_image(out_path: str, prompt: str, width: int, height: int) -> str:
    """Solid-color fallback image so the pipeline doesn't break."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        # Gradient based on prompt hash
        import hashlib
        h = int(hashlib.md5(prompt.encode()).hexdigest()[:6], 16)
        r1, g1, b1 = (h >> 16) & 0xFF, (h >> 8) & 0xFF, h & 0xFF
        r2, g2, b2 = (h >> 16) & 0xFF, (h >> 8) & 0xFF, h & 0xFF
        img = Image.new("RGB", (width, height), (r1, g1, b1))
        draw = ImageDraw.Draw(img)
        # Draw diagonal gradient
        for y in range(height):
            ratio = y / height
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        # Title text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except OSError:
            font = ImageFont.load_default()
        text = prompt[:50]
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        draw.text(((width - w) / 2, height / 2 - 30), text, fill="white", font=font)
        img.save(out_path, "JPEG", quality=85)
    except ImportError:
        # No PIL — write a 1x1 black JPEG
        with open(out_path, "wb") as f:
            f.write(bytes.fromhex(
                "ffd8ffe000104a46494600010101006000600000ffdb004300080606070605080707070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432ffc0000b08000100010101110000ffc4001f0000010501010101010100000000000000000102030405060708090a0bffc400b5100002010303020403050504040000017d01020300041105122131410613516107227114328191a1082342b1c11552d1f02433627282090a161718191a25262728292a3435363738393a434445464748494a535455565758595a636465666768696a737475767778797a838485868788898a92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9cad2d3d4d5d6d7d8d9dae1e2e3e4e5e6e7e8e9eaf1f2f3f4f5f6f7f8f9faffda0008010100003f00fb0affd9"
            ))
    return out_path


def generate_for_scenes(scenes: list, out_dir: str, width: int = 1920, height: int = 1080, model: str = "flux") -> list:
    """Generate one image per scene."""
    ensure_dir(out_dir)
    results = []
    for scene in scenes:
        prompt = scene.get("image_prompt") or scene.get("visual_query") or scene.get("narration", "")[:100]
        out_path = os.path.join(out_dir, f"scene_{scene['id']:02d}.jpg")
        try:
            generate_image(prompt, out_path, width=width, height=height, model=model)
            results.append({"scene_id": scene["id"], "path": out_path, "prompt": prompt, "source": "pollinations"})
        except Exception as e:
            log.warning(f"Image gen failed for scene {scene['id']}: {e}")
            _placeholder_image(out_path, prompt, width, height)
            results.append({"scene_id": scene["id"], "path": out_path, "prompt": prompt, "source": "placeholder"})
    return results


if __name__ == "__main__":
    out = generate_image(
        "a serene mountain lake at sunset, cinematic, 4K, dramatic lighting",
        "/tmp/test_pollinations.jpg",
        width=1280, height=720, model="flux"
    )
    print(f"Generated: {out}, size: {os.path.getsize(out)} bytes")
