"""Generate scene03_cut01 video using Sora sora-2."""

import logging
import subprocess
from pathlib import Path

import openai
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INPUT_IMAGE = Path("/Users/ksm2761/karts/short-film-project/final/frames/scene03_cut01_hd.png")
# sora-2 landscape 지원 크기: 1280x720
SORA_INPUT = Path("/tmp/sora_scene03_cut01_input.png")
RAW_VIDEO = Path("/tmp/sora_scene03_cut01_raw.mp4")
OUTPUT_VIDEO = Path(
    "/Users/ksm2761/karts/short-film-project/final/videos/scene03_cut01.mp4"
)

PROMPT = (
    "Cinematic smooth side tracking shot, samurai patrol marching through "
    "snow-covered mountain valley in blizzard, Kagemasa leading — samurai in "
    "deep navy oyoroi armor with gold imperial crest, wide shoulder sode, kabuto "
    "helmet with menpou demon face mask, nodachi sword at side — followed by 4 "
    "samurai soldiers in formation, footsteps crunching in deep snow, overcast "
    "grey sky, cold desaturated tone, snow particles drifting, For Honor cinematic "
    "trailer style, photorealistic, 1920x1080 16:9"
)

MOTION_NOTE = (
    "Steadicam lateral track following the patrol at mid distance, "
    "slight shaky quality to suggest cold and tension"
)

FULL_PROMPT = f"{PROMPT}. Camera motion: {MOTION_NOTE}."

# sora-2 현재 지원 크기 (landscape)
SORA_WIDTH = 1280
SORA_HEIGHT = 720
SORA_SIZE = f"{SORA_WIDTH}x{SORA_HEIGHT}"


def resize_for_sora(src: Path, dst: Path) -> None:
    logger.info("Resizing %s → %s for Sora", src, SORA_SIZE)
    img = Image.open(src).resize((SORA_WIDTH, SORA_HEIGHT), Image.LANCZOS)
    img.save(dst)
    logger.info("Saved Sora input to %s", dst)


def generate_with_sora(image_path: Path, output_path: Path) -> None:
    client = openai.OpenAI()

    logger.info("Submitting Sora job (sora-2, %s, 8s)...", SORA_SIZE)
    with open(image_path, "rb") as f:
        job = client.videos.create(
            model="sora-2",
            prompt=FULL_PROMPT,
            input_reference=f,
            seconds=8,
            size=SORA_SIZE,
        )

    logger.info("Job created: %s — polling...", job.id)
    video = client.videos.poll(job.id, poll_interval_ms=10000)
    logger.info("Job complete: %s", video.id)

    client.videos.download_content(video.id).write_to_file(str(output_path))
    logger.info("Raw video saved to %s", output_path)


def upscale_to_1080p(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Upscaling %s → 1920x1080 → %s", src, dst)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(dst),
        ],
        check=True,
    )
    logger.info("Final video saved to %s", dst)


def main() -> None:
    resize_for_sora(INPUT_IMAGE, SORA_INPUT)
    generate_with_sora(SORA_INPUT, RAW_VIDEO)
    upscale_to_1080p(RAW_VIDEO, OUTPUT_VIDEO)
    logger.info("Done. Output: %s", OUTPUT_VIDEO)


if __name__ == "__main__":
    main()
