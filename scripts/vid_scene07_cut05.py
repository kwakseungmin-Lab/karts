"""Generate scene07_cut05.mp4 via Sora sora-2 then upscale to 1920x1080."""
from __future__ import annotations

import base64
import io
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from PIL import Image, ImageOps

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

SORA_GENERATIONS_URL = "https://api.openai.com/v1/videos"
INPUT_IMAGE = "/Users/ksm2761/karts/short-film-project/final/frames/scene07_cut05_hd.png"
RAW_OUTPUT = "/tmp/scene07_cut05_raw.mp4"
FINAL_OUTPUT = "/Users/ksm2761/karts/short-film-project/final/videos/scene07_cut05.mp4"
SIZE = "1280x720"
SECONDS = "8"
PROMPT = (
    "Cinematic wide static shot pulling back to reveal full ruined stone bridge, "
    "Aiden (medieval knight in dark steel partial plate armor with chain mail) and "
    "Kagemasa (samurai in deep navy oyoroi armor) standing 5 meters apart — neither "
    "sheathing their weapons but neither advancing, the vast silent bridge between them "
    "loaded with unspoken recognition, morning fog half-cleared revealing the bridge's "
    "damaged stonework, two civilizations' warrior traditions facing each other in "
    "suspended tension, contemplative and still, For Honor cinematic trailer style, "
    "photorealistic, 1920x1080 16:9. "
    "Camera motion: Slow camera pull-back revealing the full bridge, gradual hold on wide composition"
)


def build_data_url(image_path: str, width: int, height: int) -> str:
    img = Image.open(image_path).convert("RGB")
    img = ImageOps.fit(img, (width, height), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def submit_job(api_key: str, data_url: str) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sora-2",
        "prompt": PROMPT,
        "seconds": SECONDS,
        "size": SIZE,
        "input_reference": {"image_url": data_url},
    }
    resp = requests.post(SORA_GENERATIONS_URL, headers=headers, json=payload, timeout=60)
    if resp.status_code not in (200, 201, 202):
        log.error("Submit failed %d: %s", resp.status_code, resp.text)
        sys.exit(1)
    data = resp.json()
    video_id = data["id"]
    log.info("Submitted. video_id=%s status=%s", video_id, data.get("status"))
    return video_id


def poll_until_done(api_key: str, video_id: str, timeout: int = 600) -> None:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(10)
        r = requests.get(f"{SORA_GENERATIONS_URL}/{video_id}", headers=headers, timeout=30)
        if r.status_code != 200:
            log.warning("Poll HTTP %d", r.status_code)
            continue
        d = r.json()
        s = d.get("status", "")
        log.info("  status=%s progress=%s%%", s, d.get("progress", 0))
        if s == "completed":
            return
        if s in ("failed", "cancelled"):
            err = (d.get("error") or {}).get("message", s)
            log.error("Generation %s: %s", s, err)
            sys.exit(1)
    log.error("Timed out waiting for Sora generation")
    sys.exit(1)


def download_video(api_key: str, video_id: str, dest: str) -> None:
    resp = requests.get(
        f"{SORA_GENERATIONS_URL}/{video_id}/content",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=120,
        stream=True,
    )
    if resp.status_code != 200:
        log.error("Download failed %d: %s", resp.status_code, resp.text[:200])
        sys.exit(1)
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    log.info("Raw video saved: %s", dest)


def upscale(raw_path: str, final_path: str) -> None:
    Path(final_path).parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-i", raw_path,
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            final_path,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error("FFmpeg error:\n%s", result.stderr)
        sys.exit(1)
    size_mb = Path(final_path).stat().st_size / 1024 / 1024
    log.info("Final video saved: %s (%.1f MB)", final_path, size_mb)


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        # .env 폴백
        env_file = Path("/Users/ksm2761/karts/.env")
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())
        api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        log.error("OPENAI_API_KEY not set")
        sys.exit(1)

    log.info("Resizing input image 1920x1080 -> 1280x720")
    data_url = build_data_url(INPUT_IMAGE, 1280, 720)
    log.info("data_url length: %d", len(data_url))

    video_id = submit_job(api_key, data_url)

    resp = requests.get(
        f"{SORA_GENERATIONS_URL}/{video_id}",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    if resp.json().get("status") != "completed":
        poll_until_done(api_key, video_id)

    download_video(api_key, video_id, RAW_OUTPUT)
    upscale(RAW_OUTPUT, FINAL_OUTPUT)
    log.info("Done.")


if __name__ == "__main__":
    main()
