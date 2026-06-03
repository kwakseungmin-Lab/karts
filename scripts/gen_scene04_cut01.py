"""Generate scene04_cut01 video via Sora sora-2 then upscale to 1920x1080."""
from __future__ import annotations

import base64
import io
import logging
import os
import subprocess
import time
from pathlib import Path

import requests
from PIL import Image, ImageOps

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

SORA_URL = "https://api.openai.com/v1/videos"
POLL_INTERVAL = 10
MAX_WAIT = 600

IMAGE_PATH = "/Users/ksm2761/karts/short-film-project/final/frames/scene04_cut01_hd.png"
SIZE = "1280x720"
SECONDS = "8"
OUTPUT_RAW = "/tmp/scene04_cut01_raw.mp4"
OUTPUT_FINAL = "/Users/ksm2761/karts/short-film-project/final/videos/scene04_cut01.mp4"

PROMPT = (
    "Cinematic wide establishing shot, ancient ruined stone arch bridge shrouded in dense morning fog, "
    "blue-grey monochrome tone, fog drifting slowly across the bridge surface, crumbling stone railings "
    "covered in moss, no figures present, telephoto lens compression making fog appear like a wall, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080, 16:9 composition. "
    "Static locked-off shot, fog drifts left to right, camera breathes slightly."
)


def build_data_url(image_path: str, size: str) -> str:
    w, h = map(int, size.split("x"))
    img = Image.open(image_path).convert("RGB")
    img = ImageOps.fit(img, (w, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def submit_job(data_url: str) -> str:
    headers = {
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sora-2",
        "prompt": PROMPT,
        "seconds": SECONDS,
        "size": SIZE,
        "input_reference": {"image_url": data_url},
    }
    resp = requests.post(SORA_URL, headers=headers, json=payload, timeout=60)
    if resp.status_code not in (200, 201, 202):
        raise RuntimeError(f"Submit failed {resp.status_code}: {resp.text}")
    data = resp.json()
    video_id = data.get("id")
    if not video_id:
        raise RuntimeError(f"No video id in response: {data}")
    log.info("Job submitted: %s (status=%s)", video_id, data.get("status"))
    return video_id


def poll_until_complete(video_id: str) -> None:
    headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        r = requests.get(f"{SORA_URL}/{video_id}", headers=headers, timeout=30)
        if r.status_code != 200:
            log.warning("Poll returned %s", r.status_code)
            continue
        d = r.json()
        s = d.get("status", "")
        log.info("[%s %s%%]", s, d.get("progress", 0))
        if s == "completed":
            return
        if s in ("failed", "cancelled"):
            err = (d.get("error") or {}).get("message", s)
            raise RuntimeError(f"Generation {s}: {err}")
    raise TimeoutError("Timed out waiting for Sora generation")


def download_video(video_id: str, output_path: str) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(
        f"{SORA_URL}/{video_id}/content/video",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
        timeout=120,
        stream=True,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Download failed {resp.status_code}: {resp.text[:200]}")
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    log.info("Raw video saved: %s", output_path)


def upscale_video(raw_path: str, final_path: str) -> None:
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
    log.info("Building data URL from %s", IMAGE_PATH)
    data_url = build_data_url(IMAGE_PATH, SIZE)

    video_id = submit_job(data_url)

    # 이미 완료된 경우도 있으므로 상태 재확인
    headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}
    r = requests.get(f"{SORA_URL}/{video_id}", headers=headers, timeout=30)
    if r.json().get("status") != "completed":
        poll_until_complete(video_id)

    download_video(video_id, OUTPUT_RAW)
    upscale_video(OUTPUT_RAW, OUTPUT_FINAL)
    log.info("scene04_cut01 complete: %s", OUTPUT_FINAL)


if __name__ == "__main__":
    main()
