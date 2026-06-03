"""씬10 컷03 Sora 영상 생성 스크립트.

Sora REST API를 직접 호출 (data URL 방식).
sora-2, size=1792x1024, seconds=8
FFmpeg로 1920x1080 업스케일 후 저장.
"""
from __future__ import annotations

import base64
import io
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from PIL import Image

# .env 로드
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

SORA_URL = "https://api.openai.com/v1/videos"
API_KEY = os.environ["OPENAI_API_KEY"]
HEADERS_JSON = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

INPUT_PATH = "/Users/ksm2761/karts/short-film-project/final/frames/scene10_cut03_hd.png"
RAW_PATH = "/tmp/sora_scene10_cut03_raw.mp4"
FINAL_PATH = "/Users/ksm2761/karts/short-film-project/final/videos/scene10_cut03.mp4"
SIZE = "1280x720"

PROMPT = (
    "Cinematic medium close-up, Kagemasa samurai in deep navy oyoroi armor sheathing his nodachi sword "
    "with cherry blossom tsuba, deliberate slow motion of blade entering lacquered scabbard, "
    "gentle golden morning light catching the blade edge, Aiden medieval knight in dark steel partial plate armor "
    "watching in background, ruined stone bridge, warmest color temperature of entire film, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9. "
    "Focus pulls from blade to Kagemasa's face as sword is fully sheathed; "
    "slight slow motion on final insertion."
)


def image_to_data_url(path: str, size: str) -> str:
    w, h = map(int, size.split("x"))
    img = Image.open(path).convert("RGB").resize((w, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def main() -> None:
    print(f"Resizing input image to {SIZE}...", flush=True)
    data_url = image_to_data_url(INPUT_PATH, SIZE)
    print(f"Data URL length: {len(data_url)}", flush=True)

    payload = {
        "model": "sora-2",
        "prompt": PROMPT,
        "seconds": "8",
        "size": SIZE,
        "input_reference": {"image_url": data_url},
    }

    print("Submitting to Sora sora-2...", flush=True)
    resp = requests.post(SORA_URL, headers=HEADERS_JSON, json=payload, timeout=60)
    print(f"Submit status: {resp.status_code}", flush=True)
    if resp.status_code not in (200, 201, 202):
        print(f"Error: {resp.text}")
        sys.exit(1)

    data = resp.json()
    video_id = data.get("id")
    status = data.get("status", "")
    print(f"Video ID: {video_id}, Status: {status}", flush=True)

    if status != "completed":
        deadline = time.time() + 700
        while time.time() < deadline:
            time.sleep(10)
            r = requests.get(f"{SORA_URL}/{video_id}", headers=HEADERS_JSON, timeout=30)
            if r.status_code != 200:
                continue
            d = r.json()
            s = d.get("status", "")
            progress = d.get("progress", 0)
            print(f"  [{s} {progress}%]", flush=True)
            if s == "completed":
                status = "completed"
                break
            if s in ("failed", "cancelled"):
                err = (d.get("error") or {}).get("message", s)
                print(f"Generation {s}: {err}")
                sys.exit(1)

    if status != "completed":
        print("Timed out waiting for Sora generation")
        sys.exit(1)

    print(f"Downloading video {video_id}...", flush=True)
    dl_resp = requests.get(
        f"{SORA_URL}/{video_id}/content",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=120,
        stream=True,
    )
    if dl_resp.status_code != 200:
        print(f"Download failed {dl_resp.status_code}: {dl_resp.text[:200]}")
        sys.exit(1)

    with open(RAW_PATH, "wb") as f:
        for chunk in dl_resp.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Raw video saved: {RAW_PATH}", flush=True)

    print("Upscaling to 1920x1080 with FFmpeg...", flush=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", RAW_PATH,
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            FINAL_PATH,
        ],
        check=True,
    )
    print(f"Final video saved: {FINAL_PATH}", flush=True)
    print("DONE:scene10_cut03")


if __name__ == "__main__":
    main()
