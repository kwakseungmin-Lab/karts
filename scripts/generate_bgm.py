#!/usr/bin/env python3
"""Generate background music for short film using ElevenLabs Music API."""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

api_key = os.environ.get("ELEVENLABS_API_KEY")
if not api_key:
    print("ERROR: ELEVENLABS_API_KEY not found in environment")
    sys.exit(1)

print(f"API key loaded: {api_key[:8]}...")

# First do a quick test to understand the API response format
url = "https://api.elevenlabs.io/v1/music"
headers = {
    "xi-api-key": api_key,
    "Content-Type": "application/json",
}

# Test with short duration first
test_payload = {
    "prompt": "dark medieval orchestral, epic cinematic, somber and brooding",
    "music_length_ms": 10000,
}

print("\n--- Testing API with 10s clip ---")
response = requests.post(url, headers=headers, json=test_payload, timeout=60)
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
if response.status_code != 200:
    print(f"Error response: {response.text[:3000]}")
    # Try to understand the correct endpoint
    print("\n--- Checking available endpoints ---")
    r2 = requests.get(
        "https://api.elevenlabs.io/v1/user",
        headers={"xi-api-key": api_key},
        timeout=10,
    )
    print(f"User endpoint status: {r2.status_code}")
    if r2.status_code == 200:
        print(f"User info: {r2.text[:500]}")
    sys.exit(1)
else:
    print(f"Response size: {len(response.content)} bytes")
    print(f"First 4 bytes hex: {response.content[:4].hex()}")
    ct = response.headers.get("Content-Type", "")
    if "json" in ct:
        data = response.json()
        print(f"JSON keys: {list(data.keys())}")
        print(f"JSON preview: {json.dumps(data, indent=2)[:1000]}")
    else:
        print("Binary response (likely audio)")
        # Save test file
        test_path = Path("/tmp/bgm_test.mp3")
        test_path.write_bytes(response.content)
        print(f"Test file saved: {test_path} ({len(response.content)} bytes)")
