"""Generate scene05_cut06 video using Sora sora-2 via direct REST API."""

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
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

SORA_URL = "https://api.openai.com/v1/videos"
INPUT_IMAGE = Path("/Users/ksm2761/karts/short-film-project/final/frames/scene05_cut06_hd.png")
RAW_VIDEO_TMP = Path("/tmp/sora_scene05_cut06_raw.mp4")
OUTPUT_VIDEO = Path("/Users/ksm2761/karts/short-film-project/final/videos/scene05_cut06.mp4")

SORA_SIZE = "1280x720"
SECONDS = 8
POLL_INTERVAL = 15
MAX_WAIT = 600

PROMPT = (
    "Cinematic wide pull-back shot, two warriors stepping forward simultaneously on ancient ruined "
    "stone bridge, closing gap to 3 meters, left: Aiden, medieval knight in dark steel partial "
    "plate armor with chain mail, longsword with runic engravings catching oblique morning sunlight, "
    "right: Kagemasa, samurai in deep navy oyoroi armor with gold imperial crest, wide shoulder "
    "sode, nodachi sword with cherry blossom tsuba gleaming with first sunlight, fog partially "
    "cleared revealing moss-covered bridge details and misty abyss below, camera slowly pulling "
    "back to reveal full bridge and surrounding fog landscape, tension at peak before combat erupts, "
    "blue-grey desaturated with first warm sunlight glints on blades, For Honor cinematic trailer "
    "style, photorealistic, 1920x1080, 16:9 composition. "
    "Slow pull-back dolly as both warriors step forward simultaneously, revealing full bridge "
    "tableau, ends on wide locked frame with both warriors facing off in center."
)


def _image_to_data_url(src: Path, size: str) -> str:
    w, h = map(int, size.split("x"))
    img = Image.open(src).convert("RGB").resize((w, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    log.info("Image resized to %dx%d and encoded as data URL", w, h)
    return f"data:image/png;base64,{b64}"


def _headers_json() -> dict[str, str]:
    api_key = os.environ["OPENAI_API_KEY"]
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def submit_job(data_url: str) -> str:
    payload = {
        "model": "sora-2",
        "prompt": PROMPT,
        "seconds": str(SECONDS),
        "size": SORA_SIZE,
        "input_reference": {"image_url": data_url},
    }
    log.info("Submitting Sora job (model=sora-2, seconds=%d, size=%s)", SECONDS, SORA_SIZE)
    resp = requests.post(SORA_URL, headers=_headers_json(), json=payload, timeout=60)
    if resp.status_code not in (200, 201, 202):
        raise RuntimeError(f"Submit failed {resp.status_code}: {resp.text}")
    data = resp.json()
    video_id = data.get("id")
    if not video_id:
        raise RuntimeError(f"No video id in response: {data}")
    log.info("Job submitted: video_id=%s status=%s", video_id, data.get("status"))
    return video_id


def poll_until_complete(video_id: str) -> None:
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        r = requests.get(f"{SORA_URL}/{video_id}", headers=_headers_json(), timeout=30)
        if r.status_code != 200:
            log.warning("Poll returned %d, retrying", r.status_code)
            continue
        d = r.json()
        status = d.get("status", "")
        progress = d.get("progress", 0)
        log.info("Status: %s  Progress: %s%%", status, progress)
        if status == "completed":
            return
        if status in ("failed", "cancelled"):
            err = (d.get("error") or {}).get("message", status)
            raise RuntimeError(f"Generation {status}: {err}")
    raise TimeoutError(f"Timed out after {MAX_WAIT}s waiting for video_id={video_id}")


def download_video(video_id: str, dest: Path) -> None:
    log.info("Downloading video %s → %s", video_id, dest)
    resp = requests.get(
        f"{SORA_URL}/{video_id}/content",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
        timeout=120,
        stream=True,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Download failed {resp.status_code}: {resp.text[:200]}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    log.info("Raw video saved: %s (%.1f MB)", dest, dest.stat().st_size / 1_048_576)


def upscale_to_1080p(src: Path, dst: Path) -> None:
    log.info("Upscaling %s → 1920x1080 → %s", src, dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(src),
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(dst),
        ],
        check=True,
    )
    log.info("Final video: %s (%.1f MB)", dst, dst.stat().st_size / 1_048_576)


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is not set")

    data_url = _image_to_data_url(INPUT_IMAGE, SORA_SIZE)
    video_id = submit_job(data_url)

    # Sora sometimes completes immediately; check status first
    r = requests.get(f"{SORA_URL}/{video_id}", headers=_headers_json(), timeout=30)
    if r.status_code == 200 and r.json().get("status") != "completed":
        poll_until_complete(video_id)

    download_video(video_id, RAW_VIDEO_TMP)
    upscale_to_1080p(RAW_VIDEO_TMP, OUTPUT_VIDEO)

    log.info("Done: %s", OUTPUT_VIDEO)
    print(str(OUTPUT_VIDEO))


if __name__ == "__main__":
    sys.exit(main())
