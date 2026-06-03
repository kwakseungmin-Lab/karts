"""Generate scene03_cut03 frame image using GPT Image gpt-image-1."""

import base64
import os
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

client = OpenAI()

PROMPT = (
    "Cinematic sudden handheld chaotic shot, brutal ambush in snow-covered mountain valley, "
    "Viking berserkers leaping from rocks with double axes — silhouetted against overcast sky "
    "in backlight like monsters — samurai soldiers falling one by one in snow, Kagemasa samurai "
    "in deep navy oyoroi armor with gold imperial crest fighting desperately, last companion "
    "falling behind him, blood spreading vivid red on white snow, intense blizzard, disorienting "
    "angles, For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)

BASE_DIR = Path("/Users/ksm2761/karts/vimax/short-film-project")
RAW_OUT = BASE_DIR / "final/frames/scene03_cut03.png"
HD_OUT = BASE_DIR / "final/frames/scene03_cut03_hd.png"

# Character ref paths (may not exist)
REF_PATHS = [
    BASE_DIR / "images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
    BASE_DIR / "images/01_character_sheets/kagemasa/kagemasa_03_back_view.png",
]

EXISTING_REFS = [p for p in REF_PATHS if p.exists()]


def generate_frame_with_refs(prompt: str, ref_paths: list[Path], out_path: Path) -> None:
    """Use edit endpoint with first available character reference."""
    with open(ref_paths[0], "rb") as img_f:
        extra_desc = " Reference images provided for character consistency." if len(ref_paths) > 1 else ""
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt + extra_desc,
            size="1536x1024",
        )
    data = base64.b64decode(response.data[0].b64_json)
    out_path.write_bytes(data)
    print(f"Saved raw: {out_path}", flush=True)


def generate_frame(prompt: str, out_path: Path) -> None:
    """Use generate endpoint (no character refs available)."""
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1536x1024",
        quality="high",
        n=1,
    )
    data = base64.b64decode(response.data[0].b64_json)
    out_path.write_bytes(data)
    print(f"Saved raw: {out_path}", flush=True)


def scale_to_hd(src: Path, dst: Path) -> None:
    """Scale 1536x1024 → 1920x1080 via FFmpeg."""
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
    if EXISTING_REFS:
        print(f"Using {len(EXISTING_REFS)} character ref(s): {[str(p) for p in EXISTING_REFS]}", flush=True)
        generate_frame_with_refs(PROMPT, EXISTING_REFS, RAW_OUT)
    else:
        print("No character refs found — using generate endpoint.", flush=True)
        generate_frame(PROMPT, RAW_OUT)

    scale_to_hd(RAW_OUT, HD_OUT)
    print("DONE:scene03_cut03", flush=True)


if __name__ == "__main__":
    main()
