"""Generate scene07_cut01_hd.png with GPT Image, then create video with Sora."""

import base64
import logging
import os
import subprocess
from pathlib import Path

import openai
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
HD_PATH = FRAMES_DIR / "scene07_cut01_hd.png"
OUTPUT_PATH = VIDEOS_DIR / "scene07_cut01.mp4"
# Sora 현재 landscape 지원: 1280x720 (API 실제 제한)
# 목표: 지시사항 1792x1024이나 API가 1280x720만 지원 → 생성 후 1920x1080 업스케일
TMP_SORA_INPUT = Path("/tmp/scene07_cut01_sora_input.png")
TMP_RAW_VIDEO = Path("/tmp/scene07_cut01_raw.mp4")
SORA_SIZE = "1280x720"
SORA_W, SORA_H = 1280, 720

FRAME_PROMPT = (
    "Cinematic medium two-shot, static camera, Aiden and Kagemasa standing 5 meters apart "
    "on a ruined stone bridge after first clash, both showing combat damage — "
    "Aiden (medieval knight in dark steel partial plate armor with chain mail, scarred face, "
    "brown hair, longsword lowered but not sheathed, left arm with fresh graze wound) and "
    "Kagemasa (samurai in deep navy oyoroi armor with gold imperial crest, wide shoulder sode, "
    "nodachi sword held cautiously, right thigh with shallow cut), heavy breathing visible, "
    "morning fog halfway cleared, soft lateral light on armor, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)

VIDEO_PROMPT = FRAME_PROMPT

MOTION_DESC = "Static shot, slight camera breathing, both warriors heaving with effort"


def generate_frame(client: openai.OpenAI) -> None:
    log.info("Generating scene07_cut01_hd.png via GPT Image...")
    result = client.images.generate(
        model="gpt-image-1",
        prompt=FRAME_PROMPT,
        size="1536x1024",
        n=1,
    )
    img_data = base64.b64decode(result.data[0].b64_json)
    HD_PATH.write_bytes(img_data)
    log.info("Saved %s (%d bytes)", HD_PATH, len(img_data))


def resize_for_sora() -> None:
    log.info("Resizing to %dx%d for Sora input...", SORA_W, SORA_H)
    img = Image.open(HD_PATH).resize((SORA_W, SORA_H), Image.LANCZOS)
    img.save(TMP_SORA_INPUT)
    log.info("Sora input saved: %s", TMP_SORA_INPUT)


def generate_video(client: openai.OpenAI) -> None:
    log.info("Submitting Sora job (sora-2, %s, 8s)...", SORA_SIZE)
    with open(TMP_SORA_INPUT, "rb") as f:
        job = client.videos.create(
            model="sora-2",
            prompt=f"{VIDEO_PROMPT} Motion: {MOTION_DESC}",
            input_reference=f,
            seconds=8,
            size=SORA_SIZE,
        )
    log.info("Job ID: %s -- polling...", job.id)
    video = client.videos.poll(job.id, poll_interval_ms=10000)
    log.info("Sora job complete. Downloading...")
    client.videos.download_content(video.id).write_to_file(str(TMP_RAW_VIDEO))
    log.info("Raw video saved: %s", TMP_RAW_VIDEO)


def upscale_video() -> None:
    log.info("FFmpeg upscale 1280x720 -> 1920x1080...")
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
    client = openai.OpenAI()

    if not HD_PATH.exists():
        generate_frame(client)
    else:
        log.info("HD frame already exists, skipping GPT Image generation.")

    resize_for_sora()
    generate_video(client)
    upscale_video()
    print("DONE:scene07_cut01")


if __name__ == "__main__":
    main()
