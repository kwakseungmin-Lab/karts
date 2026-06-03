#!/usr/bin/env python3
"""Generate scene03_cut05 frame using GPT Image edit endpoint with nodachi reference."""

import base64
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent.parent / ".env")
client = OpenAI()

REF_PATH = "/Users/ksm2761/karts/short-film-project/images/01_character_sheets/kagemasa/kagemasa_06_nodachi_detail.png"
OUT_PATH = "/Users/ksm2761/karts/short-film-project/final/frames/scene03_cut05.png"
OUT_HD_PATH = "/Users/ksm2761/karts/short-film-project/final/frames/scene03_cut05_hd.png"

PROMPT = (
    "Extreme close-up of nodachi sword blade planted in snow, cherry blossom tsuba guard visible, "
    "blood-stained blade against pure white snow with vivid crimson spreading around it, "
    "shallow depth of field, cold blue light, symbolic shot of fallen warriors and solitary survival, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9. "
    "Reference image provided for nodachi sword detail consistency."
)


def generate_frame_with_ref(prompt: str, ref_path: str, out_path: str) -> None:
    assert os.path.exists(ref_path), f"Reference not found: {ref_path}"
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
    print(f"Saved: {out_path} ({len(data):,} bytes)")


def scale_to_hd(src: str, dst: str) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", src,
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            dst,
        ],
        check=True,
    )
    print(f"HD saved: {dst}")


if __name__ == "__main__":
    print(f"Reference: {REF_PATH}")
    generate_frame_with_ref(PROMPT, REF_PATH, OUT_PATH)
    scale_to_hd(OUT_PATH, OUT_HD_PATH)
    print("Done.")
