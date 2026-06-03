#!/usr/bin/env python3
"""Generate scene10_cut04 frame image."""

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
    "Extreme close-up insert shot, cherry blossom tsuba (handguard) of nodachi sword clicking into scabbard mouth, "
    "warm golden morning light reflecting off polished steel and lacquered scabbard, "
    "cherry blossom engraving detail visible, soft bokeh background, "
    "symbol of peace and honor restored, For Honor cinematic style, photorealistic, 1920x1080 16:9"
)

PROJECT_ROOT = Path("/Users/ksm2761/karts/vimax/short-film-project")

CHARACTER_REFS = [
    PROJECT_ROOT / "images/01_character_sheets/kagemasa/kagemasa_06_nodachi_detail.png",
]

INSERT_REF = PROJECT_ROOT / "images/05_cuts/action_cuts/cut_08_cherry_blossom_tsuba.png"

OUT_RAW = PROJECT_ROOT / "final/frames/scene10_cut04.png"
OUT_HD = PROJECT_ROOT / "final/frames/scene10_cut04_hd.png"


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
    available_refs = [p for p in CHARACTER_REFS if p.exists()]
    insert_available = INSERT_REF.exists()

    print(f"Character refs available: {len(available_refs)}/{len(CHARACTER_REFS)}")
    print(f"Insert ref available: {insert_available}")

    # Priority: insert_ref > character_refs > generate
    ref_list: list[Path] = []
    if insert_available:
        ref_list.append(INSERT_REF)
    ref_list.extend(available_refs)

    if ref_list:
        print(
            f"Using edit endpoint with {len(ref_list)} ref(s): {[str(p) for p in ref_list]}"
        )
        generate_frame_with_refs(PROMPT, ref_list, OUT_RAW)
    else:
        print("No refs available — using generate endpoint")
        generate_frame(PROMPT, OUT_RAW)

    scale_to_hd(OUT_RAW, OUT_HD)
    print("DONE:scene10_cut04")


if __name__ == "__main__":
    main()
