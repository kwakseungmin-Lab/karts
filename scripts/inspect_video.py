"""완료된 Sora video job의 /content 엔드포인트를 GET으로 시도한다."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

VIDEO_ID = "video_6a1ff3606b44819092c04d697cc3648602131757ef66e1ae"
SORA_URL = "https://api.openai.com/v1/videos"
OUT_RAW = "/tmp/scene01_cut01_raw.mp4"

key = os.environ.get("OPENAI_API_KEY", "")
if not key:
    print("OPENAI_API_KEY 없음")
    sys.exit(1)

hdrs = {"Authorization": f"Bearer {key}"}

# /content 엔드포인트 GET 시도
url = f"{SORA_URL}/{VIDEO_ID}/content"
r = requests.get(url, headers=hdrs, timeout=120, stream=True, allow_redirects=True)
print(f"GET {url}")
print(f"  status: {r.status_code}")
print(f"  content-type: {r.headers.get('content-type', 'N/A')}")
print(f"  content-length: {r.headers.get('content-length', 'N/A')}")
if r.status_code == 200:
    with open(OUT_RAW, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    size_mb = Path(OUT_RAW).stat().st_size / 1024 / 1024
    print(f"  저장 완료: {OUT_RAW}  ({size_mb:.1f} MB)")
    sys.exit(0)
else:
    print(f"  응답: {r.text[:300]}")

# openai SDK 방식 시도
print("\nopenai SDK retrieve_content 시도...")
import openai
client = openai.OpenAI()
try:
    content = client.videos.retrieve_content(VIDEO_ID)
    print(f"  성공: {type(content)}")
    with open(OUT_RAW, "wb") as f:
        f.write(content.read())
    size_mb = Path(OUT_RAW).stat().st_size / 1024 / 1024
    print(f"  저장: {OUT_RAW}  ({size_mb:.1f} MB)")
    sys.exit(0)
except Exception as e:
    print(f"  오류: {e}")

# 목록 API로 generation URL 확인
print("\nGET /v1/videos 목록에서 URL 필드 확인...")
r2 = requests.get(f"{SORA_URL}?limit=5", headers=hdrs, timeout=30)
if r2.status_code == 200:
    import json
    data = r2.json()
    for item in data.get("data", []):
        if item.get("id") == VIDEO_ID:
            print(json.dumps(item, indent=2))
            break
