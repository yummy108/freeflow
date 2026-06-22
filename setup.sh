#!/bin/bash
# FreeFlow Quick Setup Script
# One-line setup for Linux/macOS

set -e
echo "🎬 FreeFlow Setup Starting..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ Python $PYTHON_VERSION found"

# Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️ FFmpeg not found. Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y ffmpeg
    elif command -v brew &> /dev/null; then
        brew install ffmpeg
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y ffmpeg
    else
        echo "❌ Could not install FFmpeg automatically. Please install it manually."
        echo "   Visit https://ffmpeg.org/download.html"
        exit 1
    fi
fi
echo "✅ FFmpeg found: $(ffmpeg -version | head -1)"

# Check ImageMagick (for text rendering)
if ! command -v convert &> /dev/null; then
    echo "⚠️ ImageMagick not found. Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y imagemagick
    elif command -v brew &> /dev/null; then
        brew install imagemagick
    fi
fi

# Install fonts
echo "📦 Installing fonts..."
if command -v apt-get &> /dev/null; then
    sudo apt-get install -y fonts-dejavu fonts-liberation fonts-noto-core 2>/dev/null || true
elif command -v brew &> /dev/null; then
    brew install --cask font-dejavu font-liberation 2>/dev/null || true
fi

# Create venv
if [ ! -d ".venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate

# Install Python packages
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt
pip install duckduckgo-search

# Create .env from template if not exists
if [ ! -f ".env" ]; then
    cat > .env << EOF
# FreeFlow Environment Variables
# Get free API keys and fill in:

# Gemini API (1,500 req/day free): https://aistudio.google.com
GEMINI_API_KEY=

# Groq API (1,000 req/day free): https://console.groq.com
GROQ_API_KEY=

# Pexels API (free stock video): https://www.pexels.com/api/
PEXELS_API_KEY=

# GitHub Token (auto-provided in Actions)
GITHUB_TOKEN=
EOF
    echo "📝 Created .env — fill in your free API keys!"
fi

# Create necessary dirs
mkdir -p pipeline/inputs/processed pipeline/work releases

# Done
echo ""
echo "============================================================"
echo "✅ Setup complete!"
echo "============================================================"
echo ""
echo "🚀 Quick test:"
echo "   source .venv/bin/activate"
echo "   python -m pipeline.md_to_video --md examples/sample-script.md --no-upload"
echo ""
echo "🎯 For auto-research mode:"
echo "   python -m pipeline.auto_research --no-upload"
echo ""
echo "📤 To enable publishing to GitHub Releases:"
echo "   Fill in GITHUB_TOKEN in .env (or use GitHub Actions)"
echo ""
echo "🌐 To deploy the web UI to GitHub Pages:"
echo "   git push to GitHub → enable Pages in repo settings"
echo ""
