"""Generate scene02_cut04.mp4 using Sora sora-2, then upscale to 1920x1080.

Note: sora-2 only supports 1280x720 and 720x1280.
Using 1280x720 (landscape) then FFmpeg upscale to 1920x1080.
"""
import logging
import subprocess
from pathlib import Path

import openai
from dotenv import load_dotenv
from PIL import Image

load_dotenv(Path("/Users/ksm2761/karts/.env"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INPUT_IMAGE = Path("/Users/ksm2761/karts/short-film-project/final/frames/scene02_cut04_hd.png")
TMP_INPUT = Path("/tmp/scene02_cut04_sora_input.png")
TMP_RAW = Path("/tmp/scene02_cut04_raw.mp4")
OUTPUT = Path("/Users/ksm2761/karts/short-film-project/final/videos/scene02_cut04.mp4")

PROMPT = (
    "Cinematic over-the-shoulder medium pull-back shot, Aiden (medieval knight in dark steel "
    "partial plate armor with chain mail, brown hair, longsword sheathed on back) turns away "
    "from the Blackstone commander and walks toward darkness beyond the camp. Camera slowly "
    "pulls back as Aiden recedes into shadow. Behind him the commander raises a flamberge sword "
    "in threat. Rain soaking everything, torchlight falls off as Aiden moves into darkness. "
    "Desaturated, chiaroscuro, dramatic. For Honor cinematic trailer style, photorealistic, "
    "1920x1080 16:9"
)

# sora-2 supported landscape size
SORA_SIZE = "1280x720"
SORA_W, SORA_H = 1280, 720


def resize_for_sora(src: Path, dst: Path) -> None:
    img = Image.open(src).resize((SORA_W, SORA_H), Image.LANCZOS)
    img.save(dst)
    logger.info("Resized %s -> %s (%dx%d)", src, dst, SORA_W, SORA_H)


def generate_video(input_path: Path, raw_out: Path) -> None:
    client = openai.OpenAI()
    with open(input_path, "rb") as f:
        logger.info("Submitting Sora sora-2 job (8s, %s) ...", SORA_SIZE)
        job = client.videos.create(
            model="sora-2",
            prompt=PROMPT,
            input_reference=f,
            seconds=8,
            size=SORA_SIZE,
        )
    logger.info("Job id: %s -- polling ...", job.id)
    video = client.videos.poll(job.id, poll_interval_ms=10000)
    logger.info("Job complete, downloading ...")
    client.videos.download_content(video.id).write_to_file(str(raw_out))
    logger.info("Raw video saved: %s", raw_out)


def upscale(raw: Path, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(raw),
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(out),
    ]
    logger.info("FFmpeg upscale: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)
    logger.info("Final video: %s", out)


def main() -> None:
    resize_for_sora(INPUT_IMAGE, TMP_INPUT)
    generate_video(TMP_INPUT, TMP_RAW)
    upscale(TMP_RAW, OUTPUT)
    logger.info("Done: %s", OUTPUT)


if __name__ == "__main__":
    main()
