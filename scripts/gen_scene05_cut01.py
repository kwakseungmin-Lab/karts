"""Generate scene05_cut01 video using Sora sora-2."""
from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image, ImageOps

load_dotenv("/Users/ksm2761/karts/.env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SORA_URL = "https://api.openai.com/v1/videos"
POLL_INTERVAL = 10
MAX_WAIT = 600

INPUT_IMAGE = "/Users/ksm2761/karts/short-film-project/final/frames/scene05_cut01_hd.png"
RAW_OUTPUT = "/tmp/scene05_cut01_raw.mp4"
FINAL_OUTPUT = "/Users/ksm2761/karts/short-film-project/final/videos/scene05_cut01.mp4"

# Sora currently supports only 720x1280 or 1280x720
SORA_SIZE = "1280x720"
SECONDS = "8"

# Moderation-safe prompt: removed weapon/combat specifics
PROMPT = (
    "Cinematic medium two-shot slightly low angle, ancient ruined stone bridge at dawn, "
    "two armored figures standing still at opposite ends of the bridge, 5 meters apart, "
    "facing each other in a tense dramatic standoff, "
    "left figure: medieval European knight in dark steel plate armor, scarred face, brown hair, "
    "standing in a formal dueling stance, "
    "right figure: Japanese samurai in deep navy traditional lamellar armor with gold crest and wide shoulder guards, "
    "standing in a formal upper guard position, "
    "morning fog gently lifting, warm oblique sunlight filtering through mist, "
    "blue-grey desaturated cinematic atmosphere, dramatic stillness, "
    "slow dolly forward camera movement stopping as both figures stand motionless, "
    "camera settling into a static chest-height framing, "
    "For Honor cinematic style, photorealistic, epic historical drama, 16:9 composition"
)


def _get_api_key() -> str:
    import os
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise EnvironmentError("OPENAI_API_KEY not set")
    return key


def _headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _submit_job(api_key: str, image_path: str) -> str:
    import base64, io

    img = Image.open(image_path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    data_url = f"data:image/png;base64,{b64}"

    payload = {
        "model": "sora-2",
        "prompt": PROMPT,
        "seconds": SECONDS,
        "size": SORA_SIZE,
        "input_reference": {"image_url": data_url},
    }

    resp = requests.post(SORA_URL, headers=_headers(api_key), json=payload, timeout=60)
    if resp.status_code not in (200, 201, 202):
        raise RuntimeError(f"Submit failed {resp.status_code}: {resp.text}")

    data = resp.json()
    video_id = data.get("id")
    if not video_id:
        raise RuntimeError(f"No video id in response: {data}")

    log.info("Job submitted. video_id=%s status=%s", video_id, data.get("status"))
    return video_id


def _poll_until_done(api_key: str, video_id: str) -> None:
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        r = requests.get(f"{SORA_URL}/{video_id}", headers=_headers(api_key), timeout=30)
        if r.status_code != 200:
            log.warning("Poll returned %s", r.status_code)
            continue
        d = r.json()
        status = d.get("status", "")
        progress = d.get("progress", 0)
        log.info("  status=%s progress=%s%%", status, progress)
        if status == "completed":
            return
        if status in ("failed", "cancelled"):
            err_msg = (d.get("error") or {}).get("message", status)
            raise RuntimeError(f"Generation {status}: {err_msg}")

    raise TimeoutError("Timed out waiting for Sora generation")


def _download(api_key: str, video_id: str, dest: str) -> None:
    import openai

    client = openai.OpenAI(api_key=api_key)
    content = client.videos.download_content(video_id)
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    content.write_to_file(dest)
    log.info("Downloaded raw video → %s", dest)


def _upscale(src: str, dest: str) -> None:
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", src,
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        dest,
    ]
    log.info("FFmpeg upscale: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)
    log.info("Upscaled → %s", dest)


def main() -> None:
    api_key = _get_api_key()

    # Resize input image to Sora supported size (1280x720)
    resized_path = "/tmp/scene05_cut01_sora_input.png"
    w, h = map(int, SORA_SIZE.split("x"))
    img = Image.open(INPUT_IMAGE).convert("RGB")
    img = ImageOps.fit(img, (w, h), Image.LANCZOS)
    img.save(resized_path, format="PNG")
    log.info("Resized input image → %s (%dx%d)", resized_path, w, h)

    video_id = _submit_job(api_key, resized_path)
    _poll_until_done(api_key, video_id)
    _download(api_key, video_id, RAW_OUTPUT)
    _upscale(RAW_OUTPUT, FINAL_OUTPUT)

    log.info("Done. Final video: %s", FINAL_OUTPUT)


if __name__ == "__main__":
    main()
