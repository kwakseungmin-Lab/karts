#!/usr/bin/env python3
"""Check ElevenLabs account and explore available endpoints."""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

api_key = os.environ.get("ELEVENLABS_API_KEY")
print(f"API key: {api_key[:8]}...")

headers_key = {"xi-api-key": api_key}
headers_bearer = {"Authorization": f"Bearer {api_key}"}

# Check subscription
print("\n--- Subscription ---")
r = requests.get(
    "https://api.elevenlabs.io/v1/user/subscription",
    headers=headers_key,
    timeout=15,
)
print(f"Status: {r.status_code}")
print(r.text[:1000])

# Check user info
print("\n--- User ---")
r2 = requests.get(
    "https://api.elevenlabs.io/v1/user",
    headers=headers_key,
    timeout=15,
)
print(f"Status: {r2.status_code}")
print(r2.text[:500])

# Check sound generation (different from music)
print("\n--- Sound Generation (Sound Effects) ---")
r3 = requests.post(
    "https://api.elevenlabs.io/v1/sound-generation",
    headers={**headers_key, "Content-Type": "application/json"},
    json={
        "text": "dark orchestral ambience, medieval battle atmosphere",
        "duration_seconds": 5.0,
        "prompt_influence": 0.3,
    },
    timeout=60,
)
print(f"Status: {r3.status_code}")
ct = r3.headers.get("Content-Type", "")
print(f"Content-Type: {ct}")
if r3.status_code == 200:
    print(f"Response size: {len(r3.content)} bytes")
    Path("/tmp/bgm_sound_effect.mp3").write_bytes(r3.content)
    print("Saved to /tmp/bgm_sound_effect.mp3")
else:
    print(r3.text[:1000])
