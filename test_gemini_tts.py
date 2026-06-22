#!/usr/bin/env python3
"""Quick test for Google Gemini TTS API.

Run this FIRST to verify your GEMINI_API_KEY works.
Saves a sample Hindi audio to /tmp/gemini_test.mp3

Usage:
    export GEMINI_API_KEY="AIza..."
    python test_gemini_tts.py
"""
import os
import sys
import subprocess

# Try to import
sys.path.insert(0, ".")

print("=" * 60)
print("🗣️  Google Gemini TTS — Quick Test")
print("=" * 60)

# Check API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("\n❌ GEMINI_API_KEY environment variable is NOT set!")
    print("\n📝 To set it:")
    print("   export GEMINI_API_KEY='AIzaSy...your_key_here...'")
    print("\n🌐 Get a free key at: https://aistudio.google.com")
    print("   → Sign in with Google account")
    print("   → Click 'Get API Key' → 'Create API Key'")
    print("   → Copy the key (starts with AIza...)")
    sys.exit(1)

print(f"\n✅ GEMINI_API_KEY found (length: {len(api_key)})")

# Test TTS
from pipeline.tts import synth_speech, GEMINI_VOICES, gemini_tts

# Test 1: Hindi (default)
print("\n" + "=" * 60)
print("🇮🇳 Test 1: Hindi Voice (hi-IN-Aoede)")
print("=" * 60)
hindi_text = "नमस्ते दोस्तों! यह Google Gemini TTS का टेस्ट है। अगर आप यह सुन रहे हैं, तो आपकी API key काम कर रही है!"
out1 = "/tmp/gemini_test_hindi.mp3"
try:
    synth_speech(
        hindi_text, out1,
        voice="hi-IN-Aoede",
        style_prompt="आप एक अनुभवी YouTube narrator हैं। स्क्रिप्ट को रोचक और स्पष्ट हिंदी में बोलें।"
    )
    print(f"\n✅ Hindi audio saved: {out1}")
    print(f"   Size: {os.path.getsize(out1) / 1024:.1f} KB")
except Exception as e:
    print(f"\n❌ Hindi TTS failed: {e}")
    sys.exit(1)

# Test 2: English
print("\n" + "=" * 60)
print("🇺🇸 Test 2: English Voice (en-US-Aoede)")
print("=" * 60)
english_text = "Hello friends! This is a Google Gemini TTS test. If you can hear this, your API key is working perfectly!"
out2 = "/tmp/gemini_test_english.mp3"
try:
    synth_speech(
        english_text, out2,
        voice="en-US-Aoede",
        style_prompt="Speak in a friendly, warm tone like a YouTube narrator."
    )
    print(f"\n✅ English audio saved: {out2}")
    print(f"   Size: {os.path.getsize(out2) / 1024:.1f} KB")
except Exception as e:
    print(f"\n❌ English TTS failed: {e}")
    sys.exit(1)

# Done
print("\n" + "=" * 60)
print("🎉 ALL TESTS PASSED!")
print("=" * 60)
print(f"\n📂 Generated files:")
print(f"   Hindi:   {out1}  ({os.path.getsize(out1) / 1024:.1f} KB)")
print(f"   English: {out2}  ({os.path.getsize(out2) / 1024:.1f} KB)")
print(f"\n🎧 Play them:")
print(f"   Linux:   xdg-open {out1}")
print(f"   macOS:   open {out1}")
print(f"   Windows: start {out1}")
print(f"\n🚀 Next steps:")
print(f"   1. If audio sounds good → Setup is ready!")
print(f"   2. Push to GitHub → Web app will trigger pipeline")
print(f"   3. Add topics to pipeline/topics.json for auto-mode")
print()
