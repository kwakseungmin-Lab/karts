"""Generate scene02_cut05 frame using GPT Image edit endpoint with character reference."""

import base64
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("/Users/ksm2761/karts/.env")

client = OpenAI()

PROJECT_ROOT = Path("/Users/ksm2761/karts/short-film-project")
FRAMES_DIR = PROJECT_ROOT / "final" / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

PROMPT = (
    "Cinematic symmetrical medium wide shot, Aiden (medieval knight in dark steel partial plate armor "
    "with chain mail, scarred face, brown hair, longsword with runic engravings) walks through massive "
    "Gothic stone archway gate of Ashfeld castle into rain-soaked darkness beyond. Gothic arch frames "
    "shot perfectly. Behind Aiden the heavy wooden gate slowly swings closed. Rain pouring down stone "
    "walls, torchlight from inside fading as gate closes. Figure walking toward camera into the unknown. "
    "Flashback ends — cold blue rain outside vs warm orange torchlight inside. Desaturated, atmospheric. "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9. "
    "Reference image provided for character consistency."
)

CHARACTER_REF = PROJECT_ROOT / "images" / "01_character_sheets" / "aiden" / "aiden_01_front_view.png"
OUT_RAW = FRAMES_DIR / "scene02_cut05.png"
OUT_HD = FRAMES_DIR / "scene02_cut05_hd.png"


def generate_frame_with_refs(prompt: str, ref_path: Path, out_path: Path) -> None:
    """Generate frame using GPT Image edit endpoint with character reference image."""
    print(f"Generating with reference: {ref_path}")
    with open(ref_path, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt,
            size="1536x1024",
        )
    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Saved raw image: {out_path}")


def scale_to_hd(src: Path, dst: Path) -> None:
    """Scale 1536x1024 to 1920x1080 via 16:9 crop then upscale."""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-vf",
            "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            str(dst),
        ],
        check=True,
    )
    print(f"Saved HD image: {dst}")


def main() -> None:
    generate_frame_with_refs(PROMPT, CHARACTER_REF, OUT_RAW)
    scale_to_hd(OUT_RAW, OUT_HD)
    print(f"Done: {OUT_HD}")


if __name__ == "__main__":
    main()
