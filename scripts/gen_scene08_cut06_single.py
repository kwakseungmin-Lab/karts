#!/usr/bin/env python3
"""Single-cut Sora video generation: scene08 cut06."""

import os
import base64
import io
import time
import subprocess
import logging
from typing import Optional

import requests
from PIL import Image, ImageOps

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------
ENV_PATH = "/Users/ksm2761/karts/.env"
for line in open(ENV_PATH):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip()

API_KEY = os.environ["OPENAI_API_KEY"]
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

FRAME_PATH = "/Users/ksm2761/karts/short-film-project/final/frames/scene08_cut06_hd.png"
OUTPUT_PATH = "/Users/ksm2761/karts/short-film-project/final/videos/scene08_cut06.mp4"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

PROMPT = (
    "Cinematic low angle shot looking up at medieval knight in dark steel partial plate "
    "armor standing victorious on ruined stone bridge, sword at rest, dramatic morning "
    "light breaking through overcast sky, blue-grey desaturated cinematic color, "
    "For Honor trailer style, photorealistic"
)
SECONDS = "8"
SIZE = "1280x720"


def image_to_data_url(path: str) -> str:
    img = Image.open(path).convert("RGB")
    img = ImageOps.fit(img, (1280, 720), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def submit_video(use_image: bool) -> str:
    payload: dict = {
        "model": "sora-2",
        "prompt": PROMPT,
        "seconds": SECONDS,
        "size": SIZE,
    }
    if use_image:
        payload["input_reference"] = {"image_url": image_to_data_url(FRAME_PATH)}
    mode = "img2vid" if use_image else "txt2vid"
    resp = requests.post(
        "https://api.openai.com/v1/videos",
        headers=HEADERS,
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    video_id = resp.json()["id"]
    log.info("Submitted %s job: %s", mode, video_id)
    return video_id


def poll_video(video_id: str, max_minutes: int = 15) -> tuple[bool, bool]:
    """Returns (success, was_moderation_blocked)."""
    deadline = time.time() + max_minutes * 60
    consecutive_errors = 0
    while time.time() < deadline:
        time.sleep(15)
        try:
            r = requests.get(
                f"https://api.openai.com/v1/videos/{video_id}",
                headers=HEADERS,
                timeout=45,
            )
            r.raise_for_status()
            consecutive_errors = 0
        except requests.exceptions.RequestException as exc:
            consecutive_errors += 1
            log.warning("Poll network error (%d/5): %s", consecutive_errors, exc)
            if consecutive_errors >= 5:
                return False, False
            continue
        data = r.json()
        status = data.get("status")
        progress = data.get("progress", 0)
        log.info("  Job %s status: %s (%s%%)", video_id, status, progress)
        if status == "completed":
            return True, False
        if status in ("failed", "cancelled"):
            err_obj = data.get("error") or {}
            code = err_obj.get("code", "")
            msg = err_obj.get("message", status)
            log.error("Job %s ended: %s — %s", video_id, status, msg)
            return False, code in ("moderation_blocked", "content_policy_violation")
    log.error("Timeout waiting for job %s", video_id)
    return False, False


def download_and_upscale(video_id: str) -> None:
    resp = requests.get(
        f"https://api.openai.com/v1/videos/{video_id}/content",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=120,
        stream=True,
    )
    resp.raise_for_status()
    tmp_path = f"/tmp/raw_{video_id}.mp4"
    with open(tmp_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    raw_size = os.path.getsize(tmp_path)
    log.info("Downloaded raw video: %d bytes → %s", raw_size, tmp_path)

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", tmp_path,
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            OUTPUT_PATH,
        ],
        check=True,
        capture_output=True,
    )
    os.remove(tmp_path)
    final_size = os.path.getsize(OUTPUT_PATH)
    log.info("Upscaled → %s  (%d bytes / %.1f MB)", OUTPUT_PATH, final_size, final_size / 1_048_576)


def main() -> None:
    log.info("=== scene08_cut06: img2vid attempt ===")
    video_id = submit_video(use_image=True)
    success, moderated = poll_video(video_id)

    if success:
        download_and_upscale(video_id)
    elif moderated:
        log.warning("Moderation blocked — retrying text-only")
        video_id2 = submit_video(use_image=False)
        success2, _ = poll_video(video_id2)
        if success2:
            download_and_upscale(video_id2)
        else:
            log.error("Text-only attempt also failed.")
            raise RuntimeError("Both img2vid and txt2vid failed for scene08_cut06")
    else:
        log.error("Generation failed (non-moderation error).")
        raise RuntimeError("Video generation failed for scene08_cut06")

    size = os.path.getsize(OUTPUT_PATH)
    print(f"\nDONE: {OUTPUT_PATH}")
    print(f"Size: {size} bytes ({size / 1_048_576:.1f} MB)")


if __name__ == "__main__":
    main()
