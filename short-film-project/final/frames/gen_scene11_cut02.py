#!/usr/bin/env python3
"""Generate scene11_cut02 frame using GPT Image edit endpoint with character refs."""

import base64
import os
import subprocess
import sys
from pathlib import Path

from openai import OpenAI


def _load_env(path: Path) -> None:
    """Load key=value pairs from a .env file into os.environ."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


_load_env(Path("/Users/ksm2761/karts/.env"))

BASE = Path("/Users/ksm2761/karts/short-film-project")
OUT_DIR = Path("/Users/ksm2761/karts/vimax/short-film-project/final/frames")

PROMPT = (
    "Cinematic static wide shot, locked-off camera, full ruined stone bridge visible from center, "
    "two warriors separating in opposite directions. Left side: Aiden, medieval knight in dark steel "
    "partial plate armor with chain mail, back to camera, longsword at side, walking toward the Ashfeld "
    "gothic ruin end of the bridge. Right side: Kagemasa, samurai in deep navy oyoroi armor with gold "
    "imperial crest, back to camera, nodachi sheathed, walking toward the Myre mist end. Symmetrical "
    "composition, bridge centre empty, fog rolling back in from both sides, morning light dimming as "
    "clouds gather, cold desaturating blue-grey tone, For Honor cinematic trailer style, photorealistic, "
    "1920x1080 16:9. Reference images provided for character consistency."
)

REF_PATHS = [
    BASE / "images/01_character_sheets/aiden/aiden_01_front_view.png",
    BASE / "images/01_character_sheets/aiden/aiden_03_back_view.png",
    BASE / "images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
    BASE / "images/01_character_sheets/kagemasa/kagemasa_03_back_view.png",
    BASE / "images/03_background_art/borderlands_bridge/bg_02_bridge_both_ends.png",
]

RAW_OUT = OUT_DIR / "scene11_cut02.png"
HD_OUT = OUT_DIR / "scene11_cut02_hd.png"


def generate_frame_with_refs(prompt: str, ref_paths: list[Path], out_path: Path) -> None:
    client = OpenAI()
    # Use the first reference image (background/bridge) as the main edit base
    # Additional refs described in prompt
    with open(ref_paths[0], "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt,
            size="1536x1024",
        )
    data = base64.b64decode(response.data[0].b64_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Saved raw: {out_path}", flush=True)


def scale_to_hd(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "scale=1920:1080:flags=lanczos,setsar=1",
            "-pix_fmt", "yuv420p",
            str(dst),
        ],
        check=True,
    )
    print(f"Saved HD: {dst}", flush=True)


def main() -> None:
    # Verify refs exist
    for p in REF_PATHS:
        if not p.exists():
            print(f"ERROR: ref not found: {p}", file=sys.stderr)
            sys.exit(1)

    generate_frame_with_refs(PROMPT, REF_PATHS, RAW_OUT)
    scale_to_hd(RAW_OUT, HD_OUT)
    print("DONE:scene11_cut02")


if __name__ == "__main__":
    main()
