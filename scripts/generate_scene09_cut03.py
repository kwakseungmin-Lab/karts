#!/usr/local/bin/python3
"""Generate scene09_cut03 image using GPT Image edit endpoint.

Uses insert_ref (cut_04_kagemasa_eyes_fearless.png) as the base image
and character refs for consistency, then scales to 1920x1080.
"""

import base64
import os
import subprocess
import sys
from pathlib import Path

# Load API key from .env if not already set
env_file = Path("/Users/ksm2761/karts/.env")
if env_file.exists() and not os.environ.get("OPENAI_API_KEY"):
    for line in env_file.read_text().splitlines():
        if line.startswith("OPENAI_API_KEY="):
            os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()
            break

from openai import OpenAI

PROJECT_ROOT = Path("/Users/ksm2761/karts/short-film-project")
OUT_DIR = PROJECT_ROOT / "final" / "frames"

INSERT_REF = PROJECT_ROOT / "images/05_cuts/action_cuts/cut_04_kagemasa_eyes_fearless.png"
CHAR_REF_PRIMARY = PROJECT_ROOT / "images/01_character_sheets/kagemasa/kagemasa_04_face_without_mask.png"
CHAR_REF_SECONDARY = PROJECT_ROOT / "images/01_character_sheets/kagemasa/kagemasa_01_front_view.png"

OUT_RAW = OUT_DIR / "scene09_cut03.png"
OUT_HD = OUT_DIR / "scene09_cut03_hd.png"

PROMPT = (
    "Cinematic extreme close-up, Kagemasa, samurai in deep navy oyoroi armor with gold imperial crest, "
    "bare face revealed without menpou mask, early 40s weathered face, long black hair tied in topknot, "
    "deep calm fearless eyes looking upward, exhausted but resolute, no fear in expression, "
    "cold morning light illuminating face, subtle moisture in eyes, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080, 16:9 composition. "
    "Reference images provided for character consistency."
)


def generate_frame_with_refs(prompt: str, ref_paths: list[Path], out_path: Path) -> None:
    client = OpenAI()
    with open(ref_paths[0], "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt,
            size="1536x1024",
        )
    data = base64.b64decode(response.data[0].b64_json)
    out_path.write_bytes(data)
    print(f"Saved raw: {out_path}")


def scale_to_hd(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            str(dst),
        ],
        check=True,
    )
    print(f"Saved HD: {dst}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Use insert_ref as primary base, character refs for consistency context
    ref_paths = [INSERT_REF, CHAR_REF_PRIMARY, CHAR_REF_SECONDARY]

    # Verify all refs exist
    for ref in ref_paths:
        if not ref.exists():
            print(f"ERROR: ref not found: {ref}", file=sys.stderr)
            sys.exit(1)

    print("Generating scene09_cut03 via GPT Image edit endpoint...")
    generate_frame_with_refs(PROMPT, ref_paths, OUT_RAW)

    print("Scaling to 1920x1080...")
    scale_to_hd(OUT_RAW, OUT_HD)

    print("Done.")


if __name__ == "__main__":
    main()
