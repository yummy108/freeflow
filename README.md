# 🎬 FreeFlow — 100% Free AI Video Pipeline

> Upload a `.md` file OR auto-research trending topics → AI script → neural voice → stock video → AI images → subtitles → final MP4. **All free, all open source, runs on GitHub Actions.**

## 🌟 Two Modes

### Mode 1 — **MD → Video** (On-Demand)
You push/upload a `.md` file → GitHub Action triggers → MP4 video gets generated and uploaded to GitHub Releases.

### Mode 2 — **Auto-Research Channel** (Hourly Cron)
Add topics to `topics.json` → Every hour, GitHub Action picks a topic → Deep research via Gemini → Script → Voice → Video → auto-publish.

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Frontend (GitHub Pages — Free)                          │
│  ├── Upload .md → triggers GitHub Action via API         │
│  ├── Add/manage auto-research topics                     │
│  ├── View & download generated videos                    │
│  └── Topic picker, status dashboard                      │
└──────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  GitHub Actions Runner (FREE for public repos)           │
│                                                          │
│  Pipeline:                                               │
│  1. research.py    → Gemini search grounding (real data) │
│  2. script_gen.py  → Groq Llama 3.3 70B (free, fast)    │
│  3. tts.py         → edge-tts (MS neural, no key)        │
│  4. visuals.py     → Pexels API (free stock video)       │
│  5. image_gen.py   → Pollinations (Flux, no key)         │
│  6. music.py       → Pixabay / Suno (free)               │
│  7. assemble.py    → MoviePy + FFmpeg                   │
│  8. subtitles.py   → auto word-level captions            │
│  9. publish.py     → GitHub Releases (free CDN)          │
└──────────────────────────────────────────────────────────┘
                       │
                       ▼
            GitHub Releases (Free CDN/Storage)
```

## 💰 Cost Breakdown

| Item | Cost |
|------|------|
| Gemini API (research + script) | **$0** (1,500 RPD free) |
| Groq Llama 3.3 70B | **$0** (1,000 RPD free) |
| Edge TTS | **$0** (unlimited, no key) |
| Pexels stock video | **$0** (free API) |
| Pollinations image gen | **$0** (unlimited, no key) |
| Pixabay music | **$0** (free) |
| MoviePy / FFmpeg | **$0** (open source) |
| GitHub Actions (public repo) | **$0** (unlimited minutes) |
| GitHub Pages hosting | **$0** (free subdomain) |
| GitHub Releases storage | **$0** (free CDN) |

**Total: $0/month** 🎉

## 🚀 Quick Start

1. **Fork this repo** (make it PUBLIC for free Actions)
2. **Get free API keys** (optional but recommended):
   - `GEMINI_API_KEY` — https://aistudio.google.com (1,500 req/day free)
   - `GROQ_API_KEY` — https://console.groq.com (1,000 req/day free)
   - `PEXELS_API_KEY` — https://www.pexels.com/api/ (free)
3. **Add secrets** in repo Settings → Secrets → Actions
4. **Edit `pipeline/topics.json`** to add your niche topics (for auto mode)
5. **Enable GitHub Pages** in Settings → Pages → branch `main` / `/docs`
6. **Visit your site** at `https://<user>.github.io/<repo>`

## 📁 Project Structure

```
.
├── index.html                  # Web app (MD upload, topic mgmt)
├── assets/
│   ├── style.css
│   └── app.js
├── pipeline/
│   ├── __init__.py
│   ├── config.yaml             # All settings (voices, fonts, etc.)
│   ├── topics.json             # Auto-research topics list
│   ├── research.py             # Deep research with Gemini
│   ├── script_gen.py           # LLM script generation
│   ├── tts.py                  # Edge TTS (Microsoft neural)
│   ├── visuals.py              # Pexels stock video fetcher
│   ├── image_gen.py            # Pollinations image generator
│   ├── music.py                # Background music
│   ├── subtitles.py            # Word-level subtitle generator
│   ├── assemble.py             # MoviePy + FFmpeg composer
│   └── publish.py              # GitHub Releases uploader
├── .github/
│   └── workflows/
│       ├── on-demand.yml       # Triggered by MD upload / manual
│       └── auto-hourly.yml     # Runs every hour
├── examples/
│   └── sample-script.md        # Example input
├── requirements.txt
└── README.md
```

## 🎬 Pipeline Stages

| # | Stage | Free Tool | Output |
|---|-------|-----------|--------|
| 1 | Research | Gemini 2.5 Flash + Google Search Grounding | `research.json` |
| 2 | Script | Groq Llama 3.3 70B (or Gemini) | `script.json` w/ scenes |
| 3 | Voice | Microsoft Edge TTS | `voice.mp3` |
| 4 | Visuals | Pexels API + Pollinations | `scene_*.mp4` + `scene_*.jpg` |
| 5 | Music | Pixabay free library | `bgm.mp3` |
| 6 | Subtitles | word-level timing | `subs.ass` |
| 7 | Assemble | FFmpeg + MoviePy | `final.mp4` |
| 8 | Publish | GitHub Releases API | Direct CDN URL |

## 🛠️ Local Run

```bash
git clone https://github.com/youruser/freeflow
cd freeflow
pip install -r requirements.txt
python pipeline/md_to_video.py --md examples/sample-script.md
```

## 🌐 API Endpoints (free backend)

If you want to add a free backend later:
- **HuggingFace Spaces** — free Gradio/Streamlit hosting
- **Render** — 750 hrs/month free
- **Fly.io** — free tier

## 📜 License
MIT — free for commercial & personal use.
