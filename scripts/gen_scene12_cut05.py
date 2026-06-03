"""씬12 컷05 영상 생성 — Sora sora-2, 4초, 1280x720 → FFmpeg 1920x1080."""
from __future__ import annotations

import base64
import io
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from PIL import Image, ImageOps

# .env 로드
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

KEY = os.environ.get("OPENAI_API_KEY", "")
if not KEY:
    print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
    sys.exit(1)

URL = "https://api.openai.com/v1/videos"
HDRS = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

INPUT_IMAGE = Path(__file__).parent.parent / "short-film-project/final/frames/scene12_cut05_hd.png"
RAW_OUT = Path("/tmp/raw_scene12_cut05.mp4")
FINAL_OUT = Path(__file__).parent.parent / "short-film-project/final/videos/scene12_cut05.mp4"

PROMPT = (
    "Extreme close-up insert shot, crow perched on a rusted abandoned sword blade embedded in stone, "
    "single black feather detail, misty grey atmosphere, desaturated blue-grey, "
    "crow slowly spreads wings and takes flight, echoing the opening prologue scene, "
    "For Honor cinematic style, photorealistic, 1920x1080 16:9. "
    "Crow static then takes flight — single feather drops slowly, fade to black begins"
)

# API가 현재 지원하는 최대 landscape 해상도: 1280x720
SIZE = "1280x720"
SECONDS = "4"

# 1. 이미지 리사이즈 → base64 data URL
print(f"Loading image: {INPUT_IMAGE}")
img = Image.open(INPUT_IMAGE).convert("RGB")
img = ImageOps.fit(img, (1280, 720), Image.LANCZOS)
buf = io.BytesIO()
img.save(buf, format="PNG")
b64 = base64.b64encode(buf.getvalue()).decode()
data_url = f"data:image/png;base64,{b64}"
print(f"Image prepared: 1280x720, {len(b64)} chars base64")

# 2. Sora 제출
print("Submitting to Sora sora-2...")
payload = {
    "model": "sora-2",
    "prompt": PROMPT,
    "seconds": SECONDS,
    "size": SIZE,
    "input_reference": {"image_url": data_url},
}
resp = requests.post(URL, headers=HDRS, json=payload, timeout=60)
print(f"HTTP {resp.status_code}")
if resp.status_code not in (200, 201, 202):
    print(f"ERROR: {resp.text}", file=sys.stderr)
    sys.exit(1)

data = resp.json()
video_id = data.get("id")
status = data.get("status", "")
print(f"video_id={video_id}  status={status}")

# 3. 폴링
if status != "completed":
    deadline = time.time() + 900
    prev = ""
    while time.time() < deadline:
        time.sleep(10)
        r = requests.get(f"{URL}/{video_id}", headers=HDRS, timeout=30)
        if r.status_code != 200:
            continue
        d = r.json()
        status = d.get("status", "")
        prog = d.get("progress", 0)
        line = f"{status} {prog}%"
        if line != prev:
            print(f"  {line}", flush=True)
            prev = line
        if status == "completed":
            break
        if status in ("failed", "cancelled"):
            err = (d.get("error") or {}).get("message", status)
            print(f"ERROR: Generation {status}: {err}", file=sys.stderr)
            sys.exit(1)

if status != "completed":
    print("ERROR: Timed out", file=sys.stderr)
    sys.exit(1)

# 4. 다운로드 (raw) — /content/video 엔드포인트 우선, fallback /content
print("\nDownloading raw MP4...")
dl = None
for endpoint in (f"{URL}/{video_id}/content/video", f"{URL}/{video_id}/content"):
    dl = requests.get(
        endpoint,
        headers={"Authorization": f"Bearer {KEY}"},
        timeout=120,
        stream=True,
    )
    if dl.status_code == 200:
        break

if dl is None or dl.status_code != 200:
    print(f"ERROR: Download {dl.status_code if dl else 'None'}: {dl.text[:200] if dl else ''}", file=sys.stderr)
    sys.exit(1)

RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
with open(RAW_OUT, "wb") as f:
    for chunk in dl.iter_content(8192):
        f.write(chunk)
print(f"Raw video: {RAW_OUT}  ({RAW_OUT.stat().st_size / 1024 / 1024:.1f} MB)")

# 5. FFmpeg 업스케일: 1280x720 → 1920x1080
print("FFmpeg upscale to 1920x1080...")
FINAL_OUT.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(
    [
        "ffmpeg", "-y", "-i", str(RAW_OUT),
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264", "-crf", "18", "-preset", "slow",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(FINAL_OUT),
    ],
    check=True,
)
print(f"Final video: {FINAL_OUT}  ({FINAL_OUT.stat().st_size / 1024 / 1024:.1f} MB)")
print("Done.")
