#!/usr/bin/env python3
"""Generate scene10_cut06 frame image."""

import base64
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("/Users/ksm2761/karts/.env")

client = OpenAI()

PROMPT = (
    "Cinematic wide static shot, two warriors standing facing each other on ruined stone bridge, "
    "Aiden medieval knight in dark steel partial plate armor left side, "
    "Kagemasa samurai in deep navy oyoroi armor right side, "
    "swords sheathed, 5-meter space between them, "
    "bright warm morning sunlight bathing the bridge, fog fully cleared, "
    "distant landscape visible on both sides — gothic castle silhouette left, misty wetlands right, "
    "peaceful contemplative silence, For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)

PROJECT_ROOT = Path("/Users/ksm2761/karts/vimax/short-film-project")

CHARACTER_REFS = [
    PROJECT_ROOT / "images/01_character_sheets/aiden/aiden_01_front_view.png",
    PROJECT_ROOT / "images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
]

BACKGROUND_REF = PROJECT_ROOT / "images/03_background_art/borderlands_bridge/bg_02_bridge_both_ends.png"

OUT_RAW = PROJECT_ROOT / "final/frames/scene10_cut06.png"
OUT_HD = PROJECT_ROOT / "final/frames/scene10_cut06_hd.png"


def generate_frame_with_refs(prompt: str, ref_paths: list[Path], out_path: Path) -> None:
    """Generate frame using edit endpoint with reference images."""
    with open(ref_paths[0], "rb") as img_f:
        extra_desc = (
            " Reference images provided for character consistency."
            if len(ref_paths) > 1
            else ""
        )
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt + extra_desc,
            size="1536x1024",
        )
    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Saved raw: {out_path}")


def generate_frame(prompt: str, out_path: Path) -> None:
    """Generate frame using generate endpoint (no refs)."""
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1536x1024",
        quality="high",
        n=1,
    )
    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Saved raw: {out_path}")


def scale_to_hd(src: Path, dst: Path) -> None:
    """Scale 1536x1024 to 1920x1080 via FFmpeg."""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-vf",
            "scale=1920:1080:flags=lanczos,setsar=1",
            "-pix_fmt",
            "yuv420p",
            str(dst),
        ],
        check=True,
    )
    print(f"Saved HD: {dst}")


def main() -> None:
    available_char_refs = [p for p in CHARACTER_REFS if p.exists()]
    bg_available = BACKGROUND_REF.exists()

    print(f"Character refs available: {len(available_char_refs)}/{len(CHARACTER_REFS)}")
    print(f"Background ref available: {bg_available}")

    # Build ref list: character refs first, then background ref
    ref_list: list[Path] = list(available_char_refs)
    if bg_available:
        ref_list.append(BACKGROUND_REF)

    if ref_list:
        print(
            f"Using edit endpoint with {len(ref_list)} ref(s): {[str(p) for p in ref_list]}"
        )
        generate_frame_with_refs(PROMPT, ref_list, OUT_RAW)
    else:
        print("No refs available — using generate endpoint")
        generate_frame(PROMPT, OUT_RAW)

    scale_to_hd(OUT_RAW, OUT_HD)
    print("DONE:scene10_cut06")


if __name__ == "__main__":
    main()
