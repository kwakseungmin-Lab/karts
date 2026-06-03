"""Generate scene12_cut01.mp4 using Sora sora-2.

sora-2 currently supports 1280x720 (landscape) only.
Input image is resized to 1280x720 for Sora, then upscaled to 1920x1080 via FFmpeg.
"""

import logging
import subprocess
from pathlib import Path

import openai
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INPUT_PATH = Path("/Users/ksm2761/karts/short-film-project/final/frames/scene12_cut01_hd.png")
OUTPUT_PATH = Path("/Users/ksm2761/karts/short-film-project/final/videos/scene12_cut01.mp4")
TMP_INPUT = Path("/tmp/scene12_cut01_sora_input.png")
TMP_RAW = Path("/tmp/scene12_cut01_raw.mp4")

PROMPT = (
    "Cinematic extreme wide static shot, locked off, both ends of a ruined stone bridge visible, "
    "Aiden (medieval knight in dark steel partial plate armor with chain mail, longsword sheathed on back) "
    "walking away left into fog, Kagemasa (samurai in deep navy oyoroi armor with gold imperial crest, "
    "nodachi sheathed) walking away right into fog, two silhouettes diverging symmetrically, "
    "heavy fog swallowing both figures, desaturated blue-grey tone, overcast sky, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)

# sora-2 supported landscape size
SORA_SIZE = "1280x720"
SORA_W, SORA_H = 1280, 720


def resize_for_sora(src: Path, dst: Path) -> None:
    """Resize source PNG to 1280x720 for Sora input."""
    img = Image.open(src).resize((SORA_W, SORA_H), Image.LANCZOS)
    img.save(dst)
    logger.info("Resized %s -> %s (%dx%d)", src, dst, SORA_W, SORA_H)


def generate_video(client: openai.OpenAI) -> None:
    """Submit Sora job and download raw video."""
    logger.info("Submitting Sora job (model=sora-2, size=%s, seconds=8)...", SORA_SIZE)
    with open(TMP_INPUT, "rb") as f:
        job = client.videos.create(
            model="sora-2",
            prompt=PROMPT,
            input_reference=f,
            seconds=8,
            size=SORA_SIZE,
        )
    logger.info("Job ID: %s -- polling...", job.id)
    video = client.videos.poll(job.id, poll_interval_ms=10000)
    logger.info("Job complete. Downloading video ID: %s", video.id)
    client.videos.download_content(video.id).write_to_file(str(TMP_RAW))
    logger.info("Raw video saved to %s", TMP_RAW)


def upscale_to_1080p(src: Path, dst: Path) -> None:
    """FFmpeg upscale 1280x720 -> 1920x1080 with QuickTime compatibility flags."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src),
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(dst),
    ]
    logger.info("Running FFmpeg upscale: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)
    logger.info("Final video saved to %s", dst)


def main() -> None:
    client = openai.OpenAI()

    resize_for_sora(INPUT_PATH, TMP_INPUT)
    generate_video(client)
    upscale_to_1080p(TMP_RAW, OUTPUT_PATH)

    logger.info("Done: %s", OUTPUT_PATH)


if __name__ == "__main__":
    main()
