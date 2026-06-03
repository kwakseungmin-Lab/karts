"""Download completed Sora video and upscale to 1920x1080."""
from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

VIDEO_ID = "video_6a1ff42247b88190906421cc3b7a1cfc0fbe9ee4bd51b6aa"
SORA_URL = "https://api.openai.com/v1/videos"
OUTPUT_RAW = "/tmp/scene04_cut01_raw.mp4"
OUTPUT_FINAL = "/Users/ksm2761/karts/short-film-project/final/videos/scene04_cut01.mp4"


def try_download(url: str, headers: dict) -> requests.Response:
    resp = requests.get(url, headers=headers, timeout=120, stream=True, allow_redirects=True)
    return resp


def main() -> None:
    headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}

    # Try different download endpoint variants
    candidates = [
        f"{SORA_URL}/{VIDEO_ID}/content/video",
        f"{SORA_URL}/{VIDEO_ID}/content",
        f"https://api.openai.com/v1/video/generations/{VIDEO_ID}/content/video",
    ]

    resp = None
    used_url = None
    for url in candidates:
        log.info("Trying: %s", url)
        r = try_download(url, headers)
        log.info("  -> %s, content-type: %s, len: %s", r.status_code, r.headers.get("content-type"), r.headers.get("content-length"))
        if r.status_code == 200 and "video" in r.headers.get("content-type", ""):
            resp = r
            used_url = url
            break
        if r.status_code == 200:
            # Log first 300 chars
            log.info("  body preview: %s", r.text[:300] if r.text else "(empty)")

    if resp is None:
        log.error("Could not find a working download URL")
        return

    log.info("Downloading from %s", used_url)
    Path(OUTPUT_RAW).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_RAW, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    size_mb = Path(OUTPUT_RAW).stat().st_size / 1024 / 1024
    log.info("Raw video saved: %s (%.1f MB)", OUTPUT_RAW, size_mb)

    # Upscale to 1920x1080
    Path(OUTPUT_FINAL).parent.mkdir(parents=True, exist_ok=True)
    log.info("Upscaling to 1920x1080...")
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", OUTPUT_RAW,
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            OUTPUT_FINAL,
        ],
        check=True,
    )
    size_mb_final = Path(OUTPUT_FINAL).stat().st_size / 1024 / 1024
    log.info("Final video saved: %s (%.1f MB)", OUTPUT_FINAL, size_mb_final)


if __name__ == "__main__":
    main()
