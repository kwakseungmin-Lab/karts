"""씬03 컷06 — 완료된 Sora job 다운로드 + FFmpeg 1920x1080 업스케일."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

import requests  # noqa: E402

KEY = os.environ["OPENAI_API_KEY"]
URL = "https://api.openai.com/v1/videos"

VIDEO_ID = "video_6a1ff4a2dd388191ab7f98854374b2aa01b698260891a443"
RAW_OUT = Path("/tmp/sora_scene03_cut06_raw.mp4")
FINAL_OUT = Path(__file__).parent.parent / "short-film-project" / "final" / "videos" / "scene03_cut06.mp4"

print(f"Downloading {VIDEO_ID}...")
dl = requests.get(
    f"{URL}/{VIDEO_ID}/content",
    headers={"Authorization": f"Bearer {KEY}"},
    timeout=180,
    stream=True,
)
print(f"Status: {dl.status_code}  Content-Type: {dl.headers.get('content-type')}")
if dl.status_code != 200:
    print("Error:", dl.text[:300])
    sys.exit(1)

RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
with open(RAW_OUT, "wb") as f:
    for chunk in dl.iter_content(chunk_size=8192):
        f.write(chunk)
size_mb = RAW_OUT.stat().st_size / 1024 / 1024
print(f"Raw saved: {RAW_OUT}  ({size_mb:.1f} MB)")

# FFmpeg 1920x1080 업스케일
FINAL_OUT.parent.mkdir(parents=True, exist_ok=True)
result = subprocess.run(
    [
        "ffmpeg", "-y", "-i", str(RAW_OUT),
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(FINAL_OUT),
    ],
    capture_output=True,
    text=True,
)
if result.returncode != 0:
    print("FFmpeg error:", result.stderr[-500:])
    sys.exit(1)

size_mb = FINAL_OUT.stat().st_size / 1024 / 1024
print(f"Final saved: {FINAL_OUT}  ({size_mb:.2f} MB)")
print("Done.")
