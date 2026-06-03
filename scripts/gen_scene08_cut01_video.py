"""Generate scene08_cut01 video with Sora sora-2 (text-to-video).

Input image triggers Sora moderation (combat scene with weapons).
Generating text-only with full character and scene description instead.
Sora sora-2 API only supports 1280x720 or 720x1280.
FFmpeg upscales output to 1920x1080.
"""

import logging
import os
import subprocess
import time
import requests
from pathlib import Path

import openai

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Load .env from project root
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

VIDEOS_DIR = Path("/Users/ksm2761/karts/short-film-project/final/videos")
OUTPUT_PATH = VIDEOS_DIR / "scene08_cut01.mp4"
TMP_RAW_VIDEO = Path("/tmp/scene08_cut01_raw.mp4")
SORA_SIZE = "1280x720"
SORA_URL = "https://api.openai.com/v1/videos"

VIDEO_PROMPT = (
    "Cinematic orbiting camera shot sweeping a 180-degree arc around two legendary armored warriors "
    "facing each other on a ruined stone bridge at bright morning. "
    "Left figure: medieval knight in dark steel partial plate armor with chain mail, scarred face, "
    "brown hair, holding a longsword engraved with runes. "
    "Right figure: Japanese samurai in deep navy oyoroi lamellar armor with gold imperial crest, "
    "wide shoulder sode, holding a nodachi blade with cherry blossom tsuba. "
    "Both warriors in dynamic opposing stances, blades engaged mid-parry. "
    "Fog cleared, bright morning side-light, dust rising from ancient stone, "
    "morning light glinting off polished armor, deep emotional tension between the two. "
    "Recovered warm saturation. For Honor cinematic trailer style, photorealistic, "
    "epic historical fantasy, 16:9 composition. Camera arcs smoothly from behind knight "
    "to behind samurai, both fully visible throughout."
)


def generate_video(client: openai.OpenAI) -> None:
    key = os.environ["OPENAI_API_KEY"]
    hdrs = {"Authorization": f"Bearer {key}"}

    log.info("Submitting Sora text-only job (sora-2, %s, 8s)...", SORA_SIZE)
    job = client.videos.create(
        model="sora-2",
        prompt=VIDEO_PROMPT,
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
            log.info("Sora job complete. Downloading...")
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
    log.info("FFmpeg upscale -> 1920x1080...")
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
        print("SKIP")
        return

    client = openai.OpenAI()
    generate_video(client)
    upscale_video()
    print("DONE:scene08_cut01")


if __name__ == "__main__":
    main()
