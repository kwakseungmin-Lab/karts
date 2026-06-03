"""Generate scene10_cut01.mp4 using Sora sora-2, then upscale to 1920x1080."""
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SORA_URL = "https://api.openai.com/v1/videos"
POLL_INTERVAL = 10
MAX_WAIT = 600

INPUT_IMAGE = "/Users/ksm2761/karts/short-film-project/final/frames/scene10_cut01_hd.png"
RAW_OUTPUT = "/tmp/scene10_cut01_raw.mp4"
FINAL_OUTPUT = "/Users/ksm2761/karts/short-film-project/final/videos/scene10_cut01.mp4"
# Sora sora-2 currently supports 720x1280 and 1280x720 only
SORA_SIZE = "1280x720"
SECONDS = "8"

PROMPT = (
    "Cinematic medium shot slow tilt-up, Kagemasa samurai in deep navy oyoroi armor with gold imperial crest, "
    "wide shoulder sode, nodachi sword with cherry blossom tsuba, bare face revealed — 40s man with topknot "
    "black hair, deep calm eyes, rising from one knee using nodachi as support, Aiden medieval knight in dark "
    "steel partial plate armor with chain mail, scarred face brown hair, stepping back one pace to give space, "
    "ruined stone bridge background, soft warm morning sunlight, fog almost cleared, brightest moment of the film, "
    "natural color saturation, For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
    " Motion: Camera tilts up slowly as Kagemasa rises; Aiden steps backward into frame left"
)


def image_to_data_url(path: str, size: str) -> str:
    w, h = map(int, size.split("x"))
    img = Image.open(path).convert("RGB")
    img = ImageOps.fit(img, (w, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
        "Content-Type": "application/json",
    }


def submit_job(data_url: str) -> str:
    payload: dict = {
        "model": "sora-2",
        "prompt": PROMPT,
        "seconds": SECONDS,
        "size": SORA_SIZE,
        "input_reference": {"image_url": data_url},
    }
    log.info("Submitting Sora job (size=%s, seconds=%s)...", SORA_SIZE, SECONDS)
    resp = requests.post(SORA_URL, headers=_headers(), json=payload, timeout=60)
    if resp.status_code not in (200, 201, 202):
        log.error("Submit failed %d: %s", resp.status_code, resp.text)
        sys.exit(1)
    data = resp.json()
    video_id = data.get("id")
    status = data.get("status", "")
    log.info("Job submitted: id=%s status=%s", video_id, status)
    return video_id


def poll_job(video_id: str) -> None:
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        r = requests.get(f"{SORA_URL}/{video_id}", headers=_headers(), timeout=30)
        if r.status_code != 200:
            log.warning("Poll returned %d, retrying...", r.status_code)
            continue
        d = r.json()
        status = d.get("status", "")
        progress = d.get("progress", 0)
        log.info("  status=%s progress=%s%%", status, progress)
        if status == "completed":
            return
        if status in ("failed", "cancelled"):
            err = (d.get("error") or {}).get("message", status)
            log.error("Generation %s: %s", status, err)
            sys.exit(1)
    log.error("Timed out after %ds waiting for Sora generation", MAX_WAIT)
    sys.exit(1)


def download_video(video_id: str, output_path: str) -> None:
    log.info("Downloading video id=%s -> %s", video_id, output_path)
    resp = requests.get(
        f"{SORA_URL}/{video_id}/content",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
        timeout=120,
        stream=True,
    )
    if resp.status_code != 200:
        log.error("Download failed %d: %s", resp.status_code, resp.text[:200])
        sys.exit(1)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    log.info("Raw video saved: %s", output_path)


def upscale_to_1080p(raw_path: str, final_path: str) -> None:
    log.info("Upscaling %s -> %s (1920x1080, lanczos)", raw_path, final_path)
    Path(final_path).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", raw_path,
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            final_path,
        ],
        check=True,
    )
    log.info("Final video saved: %s", final_path)


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        log.error("OPENAI_API_KEY not set")
        sys.exit(1)

    log.info("Resizing input image %s to %s for Sora input...", INPUT_IMAGE, SORA_SIZE)
    data_url = image_to_data_url(INPUT_IMAGE, SORA_SIZE)

    video_id = submit_job(data_url)

    # Check if already completed immediately after submit
    r = requests.get(f"{SORA_URL}/{video_id}", headers=_headers(), timeout=30)
    if r.status_code == 200 and r.json().get("status") == "completed":
        log.info("Job already completed.")
    else:
        poll_job(video_id)

    download_video(video_id, RAW_OUTPUT)
    upscale_to_1080p(RAW_OUTPUT, FINAL_OUTPUT)
    log.info("Done: %s", FINAL_OUTPUT)
    print(FINAL_OUTPUT)


if __name__ == "__main__":
    main()
