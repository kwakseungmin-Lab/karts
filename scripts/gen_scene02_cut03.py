"""Generate scene02_cut03 video using Sora sora-2 (REST API, data URL approach)."""
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

# Load .env from project root
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

INPUT_IMAGE = Path("/Users/ksm2761/karts/short-film-project/final/frames/scene02_cut03_hd.png")
TMP_RAW = Path("/tmp/scene02_cut03_raw.mp4")
OUTPUT = Path("/Users/ksm2761/karts/short-film-project/final/videos/scene02_cut03.mp4")

SORA_URL = "https://api.openai.com/v1/videos"
SORA_SIZE = "1280x720"
SORA_SECONDS = "4"
POLL_INTERVAL = 10
MAX_WAIT = 600

PROMPT = (
    "Cinematic extreme close-up insert shot, left pauldron of dark steel armor with deep scratch marks "
    "gouged into metal surface where a crest emblem was deliberately scraped away, rain water running "
    "through the grooves of the scratches, torchlight catching the raw metal beneath, rust at edges. "
    "Identity rejection moment. Desaturated, only orange torchlight warmth on metal. "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9. "
    "Static extreme close-up, rain beads roll down armor surface into scratch grooves."
)


def _image_to_data_url(image_path: Path, size: str) -> str:
    w, h = map(int, size.split("x"))
    img = Image.open(image_path).convert("RGB")
    img = ImageOps.fit(img, (w, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def submit_job(key: str) -> str:
    log.info("Resizing input image to %s for Sora", SORA_SIZE)
    data_url = _image_to_data_url(INPUT_IMAGE, SORA_SIZE)

    payload = {
        "model": "sora-2",
        "prompt": PROMPT,
        "seconds": SORA_SECONDS,
        "size": SORA_SIZE,
        "input_reference": {"image_url": data_url},
    }

    log.info("Submitting Sora job...")
    resp = requests.post(
        SORA_URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    if resp.status_code not in (200, 201, 202):
        log.error("Submit failed %d: %s", resp.status_code, resp.text[:300])
        sys.exit(1)

    data = resp.json()
    video_id = data.get("id")
    log.info("Job submitted: id=%s status=%s", video_id, data.get("status"))
    return video_id


def poll_job(video_id: str, key: str) -> None:
    headers = {"Authorization": f"Bearer {key}"}
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        r = requests.get(f"{SORA_URL}/{video_id}", headers=headers, timeout=30)
        if r.status_code != 200:
            log.warning("Poll returned %d, retrying...", r.status_code)
            continue
        d = r.json()
        status = d.get("status", "")
        progress = d.get("progress", 0)
        log.info("  [%s %s%%]", status, progress)
        if status == "completed":
            return
        if status in ("failed", "cancelled"):
            err = (d.get("error") or {}).get("message", status)
            log.error("Generation %s: %s", status, err)
            sys.exit(1)
    log.error("Timed out waiting for Sora generation")
    sys.exit(1)


def download_video(video_id: str, key: str) -> None:
    log.info("Downloading raw video for id=%s", video_id)
    resp = requests.get(
        f"{SORA_URL}/{video_id}/content/video",
        headers={"Authorization": f"Bearer {key}"},
        timeout=120,
        stream=True,
    )
    if resp.status_code != 200:
        log.error("Download failed %d: %s", resp.status_code, resp.text[:200])
        sys.exit(1)
    TMP_RAW.parent.mkdir(parents=True, exist_ok=True)
    with open(TMP_RAW, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    log.info("Raw video saved to %s", TMP_RAW)


def upscale_video() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    log.info("Upscaling %s → %s (1920x1080 lanczos)", TMP_RAW, OUTPUT)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(TMP_RAW),
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(OUTPUT),
        ],
        check=True,
    )
    log.info("Final video saved to %s", OUTPUT)


def main() -> None:
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        log.error("OPENAI_API_KEY not set")
        sys.exit(1)

    video_id = submit_job(key)
    poll_job(video_id, key)
    download_video(video_id, key)
    upscale_video()
    log.info("Done: %s", OUTPUT)


if __name__ == "__main__":
    main()
