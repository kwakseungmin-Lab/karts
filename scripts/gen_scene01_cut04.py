"""Generate scene01_cut04 video using Sora sora-2."""

import logging
import subprocess
import sys
from pathlib import Path

import openai
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INPUT_IMAGE = Path("/Users/ksm2761/karts/short-film-project/final/frames/scene01_cut04_hd.png")
SORA_INPUT = Path("/tmp/sora_scene01_cut04.png")
RAW_VIDEO = Path("/tmp/sora_scene01_cut04_raw.mp4")
OUTPUT_VIDEO = Path("/Users/ksm2761/karts/short-film-project/final/videos/scene01_cut04.mp4")

# Sora sora-2 supports only 720x1280 or 1280x720 (landscape = 1280x720)
SORA_SIZE = "1280x720"
SORA_W, SORA_H = 1280, 720

PROMPT = (
    "Cinematic close-up of stone ground with dried blood pooling between cobblestones, "
    "fragments of three faction banners — knight heraldry, viking runes, samurai crest — "
    "lying in the blood, a single raindrop falls into the red pool creating ripples, "
    "extremely desaturated with only the blood retaining a faint red hue, "
    "For Honor cinematic style, photorealistic, 1920x1080, 16:9 composition"
)
MOTION = "Static, single raindrop falls into blood pool, ripple expands slowly"

FULL_PROMPT = f"{PROMPT} Motion: {MOTION}"


def resize_for_sora(src: Path, dst: Path) -> None:
    """Resize 1920x1080 image to 1280x720 for Sora input."""
    logger.info("Resizing %s → %dx%d → %s", src, SORA_W, SORA_H, dst)
    img = Image.open(src).resize((SORA_W, SORA_H), Image.LANCZOS)
    img.save(dst)
    logger.info("Saved resized image: %s", dst)


def submit_sora_job(client: openai.OpenAI, image_path: Path) -> str:
    """Submit image-to-video job to Sora and return job id."""
    logger.info("Submitting Sora job (model=sora-2, size=%s, seconds=4)", SORA_SIZE)
    with open(image_path, "rb") as f:
        job = client.videos.create(
            model="sora-2",
            prompt=FULL_PROMPT,
            input_reference=f,
            seconds=4,
            size=SORA_SIZE,
        )
    logger.info("Job submitted: id=%s", job.id)
    return job.id


def poll_and_download(client: openai.OpenAI, job_id: str, dst: Path) -> None:
    """Poll until job completes and download raw video."""
    logger.info("Polling job %s ...", job_id)
    video = client.videos.poll(job_id, poll_interval_ms=10000)
    logger.info("Job complete: id=%s status=%s", video.id, getattr(video, "status", "done"))
    logger.info("Downloading raw video → %s", dst)
    client.videos.download_content(video.id).write_to_file(str(dst))
    logger.info("Download complete: %s (%.1f MB)", dst, dst.stat().st_size / 1_048_576)


def upscale_to_1080p(src: Path, dst: Path) -> None:
    """FFmpeg upscale from 1280x720 to 1920x1080 (lanczos)."""
    logger.info("FFmpeg upscale %s → %s (1920x1080)", src, dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(dst),
        ],
        check=True,
    )
    logger.info("Saved final video: %s (%.1f MB)", dst, dst.stat().st_size / 1_048_576)


def main() -> None:
    if not INPUT_IMAGE.exists():
        logger.error("Input image not found: %s", INPUT_IMAGE)
        sys.exit(1)

    resize_for_sora(INPUT_IMAGE, SORA_INPUT)

    client = openai.OpenAI()
    job_id = submit_sora_job(client, SORA_INPUT)
    poll_and_download(client, job_id, RAW_VIDEO)
    upscale_to_1080p(RAW_VIDEO, OUTPUT_VIDEO)

    logger.info("Done. Output: %s", OUTPUT_VIDEO)


if __name__ == "__main__":
    main()
