"""Utility helpers shared across the pipeline."""
import os
import json
import yaml
import time
import logging
import random
import string
from pathlib import Path
from typing import Any, Dict, Optional

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("freeflow")


def load_config(path: str = "pipeline/config.yaml") -> Dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def ensure_dir(path: str) -> str:
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def slugify(text: str, max_len: int = 50) -> str:
    """Make a filesystem-safe slug from any text."""
    import re
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text[:max_len] or "video"


def short_id(n: int = 6) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def safe_write(path: str, content: str, mode: str = "w") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode, encoding="utf-8") as f:
        f.write(content)


def safe_json(path: str) -> Optional[Dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def retry(fn, retries: int = 3, delay: float = 2.0, backoff: float = 2.0):
    """Retry with exponential backoff."""
    last_err = None
    for i in range(retries):
        try:
            return fn()
        except Exception as e:
            last_err = e
            if i < retries - 1:
                log.warning(f"Retry {i+1}/{retries} after error: {e}")
                time.sleep(delay * (backoff ** i))
    raise last_err
