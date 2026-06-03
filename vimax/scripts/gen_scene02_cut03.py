"""Generate scene02_cut03 video via Sora.

Sora-2 currently only supports 720x1280 and 1280x720.
We use 1280x720 (landscape) and upscale to 1920x1080 via FFmpeg.
If input frame exists, resize to 1280x720 for input_reference.
"""
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import dotenv
import openai

dotenv.load_dotenv("/Users/ksm2761/karts/.env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

INPUT_FRAME = Path(
    "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene02_cut03_hd.png"
)
OUTPUT_PATH = Path(
    "/Users/ksm2761/karts/vimax/short-film-project/final/videos/scene02_cut03.mp4"
)
SORA_SIZE = "1280x720"  # sora-2 supported landscape size
SECONDS = 4
PROMPT = (
    "Cinematic extreme close-up insert shot, left pauldron of dark steel armor with deep scratch marks "
    "gouged into metal surface where a crest emblem was deliberately scraped away, rain water running "
    "through the grooves of the scratches, torchlight catching the raw metal beneath, rust at edges. "
    "This is the moment of identity rejection. Desaturated, only orange torchlight warmth on metal. "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9. "
    "Static extreme close-up, rain beads roll down armor surface into scratch grooves."
)


def run_ffmpeg_upscale(raw_path: str, out_path: str) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        raw_path,
        "-vf",
        "scale=1920:1080:flags=lanczos",
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        out_path,
    ]
    log.info("FFmpeg upscale: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


def generate_with_input_reference(client: openai.OpenAI, tmp_dir: str) -> str:
    from PIL import Image

    log.info("Resizing input frame 1920x1080 -> 1280x720 for Sora input_reference")
    img = Image.open(str(INPUT_FRAME)).resize((1280, 720), Image.LANCZOS)
    resized_path = Path(tmp_dir) / "sora_input.png"
    img.save(str(resized_path))

    log.info("Submitting Sora job with input_reference ...")
    with open(str(resized_path), "rb") as f:
        job = client.videos.create(
            model="sora-2",
            prompt=PROMPT,
            input_reference=f,
            seconds=SECONDS,
            size=SORA_SIZE,
        )

    log.info("Polling Sora job %s ...", job.id)
    video = client.videos.poll(job.id, poll_interval_ms=10000)
    raw_path = Path(tmp_dir) / "raw.mp4"
    client.videos.download_content(video.id).write_to_file(str(raw_path))
    log.info("Downloaded raw video: %s", raw_path)
    return str(raw_path)


def generate_text_only(client: openai.OpenAI, tmp_dir: str) -> str:
    log.info("Submitting Sora job (text prompt only, no input_reference) ...")
    job = client.videos.create(
        model="sora-2",
        prompt=PROMPT,
        seconds=SECONDS,
        size=SORA_SIZE,
    )

    log.info("Polling Sora job %s ...", job.id)
    video = client.videos.poll(job.id, poll_interval_ms=10000)
    raw_path = Path(tmp_dir) / "raw.mp4"
    client.videos.download_content(video.id).write_to_file(str(raw_path))
    log.info("Downloaded raw video: %s", raw_path)
    return str(raw_path)


def main() -> int:
    if OUTPUT_PATH.exists():
        print("SKIP")
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    client = openai.OpenAI()

    with tempfile.TemporaryDirectory() as tmp_dir:
        if INPUT_FRAME.exists():
            raw_path = generate_with_input_reference(client, tmp_dir)
        else:
            log.warning(
                "Input frame not found: %s — falling back to text-prompt only", INPUT_FRAME
            )
            raw_path = generate_text_only(client, tmp_dir)

        run_ffmpeg_upscale(raw_path, str(OUTPUT_PATH))

    log.info("Saved: %s", OUTPUT_PATH)
    print("DONE:scene02_cut03")
    return 0


if __name__ == "__main__":
    sys.exit(main())
