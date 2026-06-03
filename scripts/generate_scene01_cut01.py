"""Generate scene01_cut01 frame using GPT Image edit endpoint with background reference."""

import base64
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path("/Users/ksm2761/karts/.env"))

PROJECT_ROOT = Path("/Users/ksm2761/karts/short-film-project")
FRAMES_DIR = PROJECT_ROOT / "final" / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

BACKGROUND_REF = (
    PROJECT_ROOT
    / "images"
    / "03_background_art"
    / "battlefield_ruins"
    / "bg_10_battlefield_crows_aerial.png"
)

PROMPT = (
    "Cinematic extreme wide aerial shot, fog-covered medieval battlefield at dawn, "
    "desaturated near-grayscale, broken swords and fallen armor scattered across muddy ruins, "
    "three faction banners — knight cross, viking raven, samurai chrysanthemum — half-buried in mud, "
    "crows circling overhead, dramatic overcast sky with no sun, eerie silence conveyed through stillness, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080, 16:9 composition"
)

OUT_RAW = FRAMES_DIR / "scene01_cut01.png"
OUT_HD = FRAMES_DIR / "scene01_cut01_hd.png"


def generate_frame_with_ref(prompt: str, ref_path: Path, out_path: Path) -> None:
    client = OpenAI()
    with ref_path.open("rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt,
            size="1536x1024",
        )
    data = base64.b64decode(response.data[0].b64_json)
    with out_path.open("wb") as f:
        f.write(data)
    print(f"Saved raw: {out_path}", file=sys.stderr)


def scale_to_hd(src: Path, dst: Path) -> None:
    # 1536×1024 → 16:9 crop (1536×864, centred) → 1920×1080
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
    print(f"Saved HD: {dst}", file=sys.stderr)


if __name__ == "__main__":
    print("Generating scene01_cut01 via GPT Image edit endpoint...", file=sys.stderr)
    generate_frame_with_ref(PROMPT, BACKGROUND_REF, OUT_RAW)
    scale_to_hd(OUT_RAW, OUT_HD)
    print(str(OUT_HD))
