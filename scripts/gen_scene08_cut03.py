"""Generate scene08_cut03.mp4 via Sora sora-2 (text-only) then upscale to 1920x1080.

Input image causes moderation block due to combat content.
Using text-only prompt per agent guidelines:
  "Veo 계열: 폭력적 이미지 NSFW 차단 → 텍스트 프롬프트로 대체"
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

SORA_GENERATIONS_URL = "https://api.openai.com/v1/videos"
RAW_OUTPUT = "/tmp/scene08_cut03_raw.mp4"
FINAL_OUTPUT = "/Users/ksm2761/karts/short-film-project/final/videos/scene08_cut03.mp4"
# sora-2 currently supports only 1280x720 or 720x1280
SIZE = "1280x720"
SECONDS = "8"

# Full cinematic prompt — text-only (no input_reference to avoid image moderation block)
PROMPT = (
    "Cinematic action sequence with slow-motion freeze frame technique on a ruined stone bridge. "
    "Two armored warriors: a medieval knight in dark steel partial plate armor with scarred face "
    "and brown hair, and a samurai in deep navy oyoroi armor with gold imperial crest, wide sode "
    "shoulder guards, and an ornate demon-face menpou mask. "
    "Shot begins handheld as the knight drives his armored shoulder into the samurai's guard, "
    "then swings his longsword's crossguard into the samurai's mask in a decisive blow. "
    "Time freezes on the moment of decisive contact — freeze-frame cinematography technique — "
    "then resumes at normal speed as the samurai in deep navy armor steps back, losing ground. "
    "Cut to extreme close-up of the ornate demon-face mask showing the force of the exchange, "
    "then pull back to low-angle medium shot revealing both warriors. "
    "Stone bridge ruins background, morning golden light, fog cleared. "
    "For Honor cinematic trailer style, photorealistic, dramatic lighting, 1920x1080, 16:9"
)


def load_api_key() -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
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
    return api_key


def submit_job(api_key: str) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    # Text-only: no input_reference (image caused moderation block)
    payload = {
        "model": "sora-2",
        "prompt": PROMPT,
        "seconds": SECONDS,
        "size": SIZE,
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
    if Path(FINAL_OUTPUT).exists():
        log.info("Already exists, skipping: %s", FINAL_OUTPUT)
        print("SKIP")
        return

    api_key = load_api_key()

    video_id = submit_job(api_key)

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
    print("DONE:scene08_cut03")


if __name__ == "__main__":
    main()
