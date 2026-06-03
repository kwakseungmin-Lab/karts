"""Generate scene12_cut04.mp4 using Sora sora-2."""
from __future__ import annotations

import base64
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from PIL import Image, ImageOps

# .env 로드
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SORA_URL = "https://api.openai.com/v1/videos"
POLL_INTERVAL = 10
MAX_WAIT = 600

INPUT_IMAGE = "/Users/ksm2761/karts/short-film-project/final/frames/scene12_cut04_hd.png"
TMP_INPUT = "/tmp/scene12_cut04_sora_input.png"
TMP_RAW = "/tmp/scene12_cut04_raw.mp4"
OUTPUT = "/Users/ksm2761/karts/short-film-project/final/videos/scene12_cut04.mp4"

SORA_SIZE = "1280x720"
SECONDS = "8"
PROMPT = (
    "Cinematic ultra-wide aerial bird's eye view, extreme pull-back reveal, "
    "Heathmoor landscape, ancient stone bridge tiny in center frame, "
    "left hill silhouettes of knight army marching (Iron Legion banners), "
    "right hill silhouettes of samurai army advancing (Dawn Empire banners), "
    "fog filling the valley between, overcast grey sky, crows circling above, "
    "two armies converging toward the same bridge, desaturated blue-grey, "
    "epic and tragic, For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)
MOTION = (
    "Slow camera pull-back revealing full scale of landscape and converging armies on both sides"
)
FULL_PROMPT = f"{PROMPT} Motion: {MOTION}"


def prepare_input_image() -> str:
    w, h = map(int, SORA_SIZE.split("x"))
    img = Image.open(INPUT_IMAGE).convert("RGB")
    img = ImageOps.fit(img, (w, h), Image.LANCZOS)
    img.save(TMP_INPUT)
    logger.info("Input image resized to %dx%d -> %s", w, h, TMP_INPUT)
    return TMP_INPUT


def image_to_data_url(image_path: str) -> str:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{b64}"


def submit_job(data_url: str) -> str:
    api_key = os.environ["OPENAI_API_KEY"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sora-2",
        "prompt": FULL_PROMPT,
        "seconds": SECONDS,
        "size": SORA_SIZE,
        "input_reference": {"image_url": data_url},
    }
    logger.info("Submitting Sora job (size=%s, seconds=%s)...", SORA_SIZE, SECONDS)
    resp = requests.post(SORA_URL, headers=headers, json=payload, timeout=60)
    if resp.status_code not in (200, 201, 202):
        logger.error("Submit failed %d: %s", resp.status_code, resp.text)
        sys.exit(1)
    data = resp.json()
    video_id = data.get("id")
    logger.info("Job submitted. video_id=%s status=%s", video_id, data.get("status"))
    return video_id


def poll_job(video_id: str) -> None:
    api_key = os.environ["OPENAI_API_KEY"]
    headers = {"Authorization": f"Bearer {api_key}"}
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        r = requests.get(f"{SORA_URL}/{video_id}", headers=headers, timeout=30)
        if r.status_code != 200:
            logger.warning("Poll returned %d, retrying...", r.status_code)
            continue
        d = r.json()
        status = d.get("status", "")
        progress = d.get("progress", 0)
        logger.info("Status: %s %s%%", status, progress)
        if status == "completed":
            return
        if status in ("failed", "cancelled"):
            err = (d.get("error") or {}).get("message", status)
            logger.error("Generation %s: %s", status, err)
            sys.exit(1)
    logger.error("Timed out after %ds", MAX_WAIT)
    sys.exit(1)


def download_video(video_id: str) -> None:
    api_key = os.environ["OPENAI_API_KEY"]
    headers = {"Authorization": f"Bearer {api_key}"}
    logger.info("Downloading video %s -> %s", video_id, TMP_RAW)
    resp = requests.get(
        f"{SORA_URL}/{video_id}/content",
        headers=headers,
        timeout=120,
        stream=True,
    )
    if resp.status_code != 200:
        logger.error("Download failed %d: %s", resp.status_code, resp.text[:200])
        sys.exit(1)
    Path(TMP_RAW).parent.mkdir(parents=True, exist_ok=True)
    with open(TMP_RAW, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    logger.info("Raw video saved: %s", TMP_RAW)


def upscale_to_1080p() -> None:
    Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", TMP_RAW,
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        OUTPUT,
    ]
    logger.info("Upscaling to 1920x1080: %s", OUTPUT)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("FFmpeg failed:\n%s", result.stderr)
        sys.exit(1)
    logger.info("Output saved: %s", OUTPUT)


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not set")
        sys.exit(1)

    prepare_input_image()
    data_url = image_to_data_url(TMP_INPUT)
    video_id = submit_job(data_url)

    # 제출 직후 상태 확인 — 아직 완료되지 않으면 폴링
    api_key = os.environ["OPENAI_API_KEY"]
    headers = {"Authorization": f"Bearer {api_key}"}
    r = requests.get(f"{SORA_URL}/{video_id}", headers=headers, timeout=30)
    if r.status_code != 200 or r.json().get("status") != "completed":
        poll_job(video_id)

    download_video(video_id)
    upscale_to_1080p()
    logger.info("Done: %s", OUTPUT)


if __name__ == "__main__":
    main()
