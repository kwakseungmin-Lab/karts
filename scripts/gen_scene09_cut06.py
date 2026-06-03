"""Generate scene09_cut06 video with Sora sora-2 (image-to-video).

Sora sora-2 API only supports 1280x720 or 720x1280.
We resize input to 1280x720, generate, then upscale to 1920x1080 with FFmpeg.
"""

import logging
import os
import subprocess
import time
from pathlib import Path

import openai
import requests
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Load .env from project root
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

FRAMES_DIR = Path("/Users/ksm2761/karts/short-film-project/final/frames")
VIDEOS_DIR = Path("/Users/ksm2761/karts/short-film-project/final/videos")
HD_PATH = FRAMES_DIR / "scene09_cut06_hd.png"
OUTPUT_PATH = VIDEOS_DIR / "scene09_cut06.mp4"
TMP_SORA_INPUT = Path("/tmp/scene09_cut06_sora_input.png")
TMP_RAW_VIDEO = Path("/tmp/scene09_cut06_raw.mp4")
# sora-2 only supports 1280x720 or 720x1280
SORA_SIZE = "1280x720"
SORA_W, SORA_H = 1280, 720
SORA_URL = "https://api.openai.com/v1/videos"

VIDEO_PROMPT = (
    "Ultra slow motion sword lowering arc, final moment when tip touches stone in real time with metallic ring. "
    "Cinematic medium side profile shot, Aiden, medieval knight in dark steel partial plate armor with chain mail, "
    "scarred face, brown hair, longsword with runic engravings slowly lowering from overhead execution position "
    "down to stone bridge floor, sword tip touching ancient stone, Kagemasa, samurai in deep navy oyoroi armor, "
    "still kneeling watching, bright clean morning light on stone bridge, slow deliberate movement of mercy, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080, 16:9 composition"
)


def resize_for_sora() -> None:
    log.info("Resizing %s to %dx%d for Sora input...", HD_PATH, SORA_W, SORA_H)
    img = Image.open(HD_PATH).resize((SORA_W, SORA_H), Image.LANCZOS)
    img.save(TMP_SORA_INPUT)
    log.info("Sora input saved: %s", TMP_SORA_INPUT)


def generate_video(client: openai.OpenAI) -> None:
    key = os.environ["OPENAI_API_KEY"]
    hdrs = {"Authorization": f"Bearer {key}"}

    log.info("Submitting Sora job (sora-2, %s, 8s)...", SORA_SIZE)
    with open(TMP_SORA_INPUT, "rb") as f:
        job = client.videos.create(
            model="sora-2",
            prompt=VIDEO_PROMPT,
            input_reference=f,
            seconds=8,
            size=SORA_SIZE,
        )
    video_id = job.id
    log.info("Job ID: %s -- polling...", video_id)

    deadline = time.time() + 1200
    prev = ""
    while time.time() < deadline:
        time.sleep(10)
        r = requests.get(f"{SORA_URL}/{video_id}", headers=hdrs, timeout=30)
        if r.status_code != 200:
            log.warning("poll error %s", r.status_code)
            continue
        d = r.json()
        status = d.get("status", "")
        progress = d.get("progress", 0)
        line = f"{status} {progress}%"
        if line != prev:
            log.info("  %s", line)
            prev = line
        if status == "completed":
            log.info("Sora job complete. Downloading via /content/video...")
            dl = requests.get(
                f"{SORA_URL}/{video_id}/content/video",
                headers=hdrs,
                timeout=120,
                stream=True,
            )
            if dl.status_code != 200:
                log.warning("/content/video returned %s, trying /content...", dl.status_code)
                dl = requests.get(
                    f"{SORA_URL}/{video_id}/content",
                    headers=hdrs,
                    timeout=120,
                    stream=True,
                )
            if dl.status_code != 200:
                raise RuntimeError(f"Download failed {dl.status_code}: {dl.text[:200]}")
            with open(TMP_RAW_VIDEO, "wb") as f:
                for chunk in dl.iter_content(8192):
                    f.write(chunk)
            size_mb = TMP_RAW_VIDEO.stat().st_size / 1024 / 1024
            log.info("Raw video saved: %s (%.1f MB)", TMP_RAW_VIDEO, size_mb)
            return
        if status in ("failed", "cancelled"):
            err = (d.get("error") or {}).get("message", status)
            raise RuntimeError(f"Generation {status}: {err}")

    raise RuntimeError("Timed out waiting for Sora generation")


def upscale_video() -> None:
    log.info("FFmpeg upscale %s -> 1920x1080...", SORA_SIZE)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(TMP_RAW_VIDEO),
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(OUTPUT_PATH),
        ],
        check=True,
    )
    log.info("Final video saved: %s", OUTPUT_PATH)


def main() -> None:
    if OUTPUT_PATH.exists():
        print("SKIP: already exists")
        return

    client = openai.OpenAI()
    resize_for_sora()
    generate_video(client)
    upscale_video()
    print("DONE:scene09_cut06")


if __name__ == "__main__":
    main()
