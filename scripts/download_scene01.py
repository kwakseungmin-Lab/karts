"""완료된 Sora 영상 다운로드 및 업스케일."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

import requests

api_key = os.environ["OPENAI_API_KEY"]
video_id = "video_6a1ff35c0da88191a7b1e698bc775cb40c9c70d7264cda86"
RAW_OUTPUT = "/tmp/scene01_cut01_raw.mp4"
FINAL_OUTPUT = "/Users/ksm2761/karts/short-film-project/final/videos/scene01_cut01.mp4"

headers_auth = {"Authorization": f"Bearer {api_key}"}

# openai SDK 방식으로 다운로드 시도
try:
    import openai

    client = openai.OpenAI(api_key=api_key)
    print("openai SDK로 다운로드 시도...")
    content = client.videos.download_content(video_id)
    Path(RAW_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    content.write_to_file(RAW_OUTPUT)
    print(f"SDK 다운로드 완료: {RAW_OUTPUT}")
except Exception as e:
    print(f"SDK 실패: {e}")
    # REST API 대안: /content/download
    endpoints_to_try = [
        f"https://api.openai.com/v1/videos/{video_id}/content/download",
        f"https://api.openai.com/v1/videos/{video_id}/download",
        f"https://api.openai.com/v1/video/generations/{video_id}/content/video",
    ]
    downloaded = False
    for url in endpoints_to_try:
        print(f"시도: {url}")
        r = requests.get(url, headers=headers_auth, timeout=120, stream=True, allow_redirects=True)
        print(f"  → {r.status_code}")
        if r.status_code == 200:
            Path(RAW_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
            with open(RAW_OUTPUT, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            size = Path(RAW_OUTPUT).stat().st_size
            print(f"다운로드 완료: {RAW_OUTPUT} ({size} bytes)")
            downloaded = True
            break
        else:
            print(f"  실패: {r.text[:200]}")

    if not downloaded:
        print("모든 다운로드 시도 실패", file=sys.stderr)
        sys.exit(1)

# FFmpeg 업스케일
print(f"FFmpeg 업스케일 1280x720 → 1920x1080...")
Path(FINAL_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
subprocess.run(
    [
        "ffmpeg", "-y", "-i", RAW_OUTPUT,
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        FINAL_OUTPUT,
    ],
    check=True,
)
size = Path(FINAL_OUTPUT).stat().st_size
print(f"완료: {FINAL_OUTPUT} ({size:,} bytes)")
