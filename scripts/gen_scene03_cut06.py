"""씬03 컷06 영상 생성 — Sora sora-2 image-to-video + FFmpeg 1920x1080 업스케일.

API 실제 지원 사이즈: 720x1280, 1280x720 → 1280x720으로 생성 후 1920x1080 업스케일.
다운로드 엔드포인트: /videos/{id}/content  (not /content/video)
"""
from __future__ import annotations

import base64
import io
import os
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageOps

# --- .env 로드 ---
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

import requests  # noqa: E402 (after env load)

KEY = os.environ["OPENAI_API_KEY"]
HEADERS_JSON = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
HEADERS_AUTH = {"Authorization": f"Bearer {KEY}"}
URL = "https://api.openai.com/v1/videos"

SRC = Path(__file__).parent.parent / "short-film-project" / "final" / "frames" / "scene03_cut06_hd.png"
RAW_OUT = Path("/tmp/sora_scene03_cut06_raw.mp4")
FINAL_OUT = Path(__file__).parent.parent / "short-film-project" / "final" / "videos" / "scene03_cut06.mp4"

# API가 실제로 지원하는 landscape 최대 사이즈
SIZE = "1280x720"
SECONDS = "4"
PROMPT = (
    "Cinematic wide static shot, Kagemasa — samurai in deep navy oyoroi armor, "
    "lone survivor — slowly rising to stand with nodachi sword, silhouette walking "
    "away into intensifying blizzard, figure gradually consumed by white snowstorm, "
    "fade to white transition, cold desaturated tone, atmosphere of grief and resolve, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)


def image_to_data_url(src: Path, size: str) -> str:
    w, h = map(int, size.split("x"))
    img = Image.open(src).convert("RGB")
    img = ImageOps.fit(img, (w, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def submit_job() -> str:
    data_url = image_to_data_url(SRC, SIZE)
    print(f"Input image encoded ({len(data_url):,} chars) at {SIZE}")

    payload = {
        "model": "sora-2",
        "prompt": PROMPT,
        "seconds": SECONDS,
        "size": SIZE,
        "input_reference": {"image_url": data_url},
    }

    print("Submitting to Sora sora-2...")
    resp = requests.post(URL, headers=HEADERS_JSON, json=payload, timeout=60)
    print(f"Submit response: {resp.status_code}")
    if resp.status_code not in (200, 201, 202):
        print("Error:", resp.text)
        sys.exit(1)

    data = resp.json()
    video_id = data.get("id")
    status = data.get("status", "")
    print(f"Job ID: {video_id}  Status: {status}")

    if not video_id:
        print("No video id:", data)
        sys.exit(1)

    return video_id


def poll_until_done(video_id: str) -> None:
    print("Polling...")
    deadline = time.time() + 900  # 15분 타임아웃
    while time.time() < deadline:
        time.sleep(15)
        r = requests.get(f"{URL}/{video_id}", headers=HEADERS_AUTH, timeout=30)
        if r.status_code != 200:
            print(f"  poll error {r.status_code}")
            continue
        d = r.json()
        status = d.get("status", "")
        prog = d.get("progress", 0)
        print(f"  {status} {prog}%", flush=True)
        if status == "completed":
            return
        if status in ("failed", "cancelled"):
            err = (d.get("error") or {}).get("message", status)
            print(f"Generation {status}: {err}")
            sys.exit(1)
    print("Timed out (15 min)")
    sys.exit(1)


def download_video(video_id: str) -> None:
    print(f"Downloading video {video_id}...")
    # 올바른 엔드포인트: /content (not /content/video)
    dl = requests.get(
        f"{URL}/{video_id}/content",
        headers=HEADERS_AUTH,
        timeout=180,
        stream=True,
    )
    if dl.status_code != 200:
        print(f"Download failed {dl.status_code}: {dl.text[:200]}")
        sys.exit(1)
    RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_OUT, "wb") as f:
        for chunk in dl.iter_content(chunk_size=8192):
            f.write(chunk)
    size_mb = RAW_OUT.stat().st_size / 1024 / 1024
    print(f"Raw video saved: {RAW_OUT}  ({size_mb:.1f} MB)")


def ffmpeg_upscale() -> None:
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
        print("FFmpeg stderr:", result.stderr)
        sys.exit(1)
    size_mb = FINAL_OUT.stat().st_size / 1024 / 1024
    print(f"Final video saved: {FINAL_OUT}  ({size_mb:.2f} MB)")


if __name__ == "__main__":
    video_id = submit_job()
    poll_until_done(video_id)
    download_video(video_id)
    ffmpeg_upscale()
    print("Done.")
