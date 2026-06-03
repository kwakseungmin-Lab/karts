#!/usr/bin/env python3
"""Generate scene02_cut02 image using GPT Image edit endpoint with character reference."""

import base64
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("/Users/ksm2761/karts/.env")

PROJECT_ROOT = Path("/Users/ksm2761/karts/short-film-project")
OUTPUT_DIR = PROJECT_ROOT / "final" / "frames"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_PATH = str(OUTPUT_DIR / "scene02_cut02.png")
OUT_HD_PATH = str(OUTPUT_DIR / "scene02_cut02_hd.png")

CHARACTER_REF = str(
    PROJECT_ROOT / "images" / "01_character_sheets" / "aiden" / "aiden_04_face_closeup.png"
)

PROMPT = (
    "Cinematic extreme close-up, Aiden's eyes inside barbeuta helmet visor, "
    "torchlight reflection dancing in pupils, eyes slowly closing in refusal — "
    "Aiden (medieval knight in dark steel partial plate armor with chain mail, "
    "scarred face, brown hair, left eye bears a vertical scar), "
    "rain droplets on helmet metal catching orange torchlight. "
    "Desaturated warm tone, deep shadows around eyes, emotional tension. "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)


def generate_frame_with_refs(prompt: str, ref_path: str, out_path: str) -> None:
    client = OpenAI()
    with open(ref_path, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt + " Reference image provided for character face consistency.",
            size="1536x1024",
        )
    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Saved: {out_path}", file=sys.stderr)


def scale_to_hd(src: str, dst: str) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", src,
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            dst,
        ],
        check=True,
    )
    print(f"Saved HD: {dst}", file=sys.stderr)


if __name__ == "__main__":
    print("Generating scene02_cut02 with character reference...", file=sys.stderr)
    generate_frame_with_refs(PROMPT, CHARACTER_REF, OUT_PATH)
    scale_to_hd(OUT_PATH, OUT_HD_PATH)
    print(OUT_HD_PATH)
