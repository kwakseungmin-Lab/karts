"""Generate scene04_cut06 video using Sora sora-2."""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/Users/ksm2761/karts")

from tools.video.sora_video import SoraVideo

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INPUT_IMAGE = "/Users/ksm2761/karts/short-film-project/final/frames/scene04_cut06_hd.png"
RAW_OUTPUT = "/tmp/scene04_cut06_raw.mp4"
FINAL_OUTPUT = "/Users/ksm2761/karts/short-film-project/final/videos/scene04_cut06.mp4"
SIZE = "1280x720"
SECONDS = 4

PROMPT = (
    "Cinematic medium close-up low angle, stone bridge surface level, "
    "two sets of armored boots stepping forward onto moss-covered ruined stone bridge, "
    "left: dark steel sabatons of Aiden, medieval knight, "
    "right: deep navy lacquered armored waraji sandals of Kagemasa, samurai kensei, "
    "each taking one deliberate step toward each other, "
    "fog-filled bridge gap between them, "
    "blue-grey desaturated, For Honor cinematic trailer style, "
    "photorealistic, 1920x1080, 16:9 composition. "
    "Cross-cut between the two feet stepping forward, camera stays low near stone surface."
)


def upscale_to_1080p(raw_path: str, final_path: str) -> None:
    Path(final_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", raw_path,
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        final_path,
    ]
    logger.info("FFmpeg upscale: %s -> %s", raw_path, final_path)
    subprocess.run(cmd, check=True)
    logger.info("Upscale complete: %s", final_path)


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not set")
        sys.exit(1)

    if not Path(INPUT_IMAGE).exists():
        logger.error("Input image not found: %s", INPUT_IMAGE)
        sys.exit(1)

    tool = SoraVideo()
    logger.info("Submitting Sora job — model=sora-2, size=%s, seconds=%d", SIZE, SECONDS)
    result = tool.execute(
        {
            "prompt": PROMPT,
            "image_path": INPUT_IMAGE,
            "duration": SECONDS,
            "size": SIZE,
            "output_path": RAW_OUTPUT,
        }
    )

    if not result.success:
        logger.error("Sora generation failed: %s", result.error)
        sys.exit(1)

    logger.info("Sora generation succeeded: %s", result.data)

    upscale_to_1080p(RAW_OUTPUT, FINAL_OUTPUT)
    logger.info("Final video saved: %s", FINAL_OUTPUT)
    print(FINAL_OUTPUT)


if __name__ == "__main__":
    main()
