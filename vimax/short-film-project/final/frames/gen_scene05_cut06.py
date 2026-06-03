#!/usr/bin/env python3
"""Generate scene05 cut06 frame image using GPT Image."""

import base64
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("/Users/ksm2761/karts/.env")

PROMPT = (
    "Cinematic wide pull-back shot, two warriors stepping forward simultaneously on ancient ruined stone bridge, "
    "closing gap to 3 meters, left: Aiden, medieval knight in dark steel partial plate armor with chain mail, "
    "longsword with runic engravings catching oblique morning sunlight, right: Kagemasa, samurai in deep navy "
    "oyoroi armor with gold imperial crest, wide shoulder sode, nodachi sword with cherry blossom tsuba gleaming "
    "with first sunlight, fog partially cleared revealing moss-covered bridge details and misty abyss below, "
    "camera slowly pulling back to reveal full bridge and surrounding fog landscape, tension at peak before "
    "combat erupts, blue-grey desaturated with first warm sunlight glints on blades, For Honor cinematic trailer "
    "style, photorealistic, 1920x1080, 16:9 composition"
)

OUT_DIR = "/Users/ksm2761/karts/vimax/short-film-project/final/frames"
OUT_RAW = f"{OUT_DIR}/scene05_cut06.png"
OUT_HD = f"{OUT_DIR}/scene05_cut06_hd.png"


def generate_frame(prompt: str, out_path: str) -> None:
    client = OpenAI()
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
    print(f"Saved raw frame: {out_path}", file=sys.stderr)


def scale_to_hd(src: str, dst: str) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", src,
            "-vf", "scale=1920:1080:flags=lanczos,setsar=1",
            "-pix_fmt", "yuv420p",
            dst,
        ],
        check=True,
    )
    print(f"Saved HD frame: {dst}", file=sys.stderr)


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    generate_frame(PROMPT, OUT_RAW)
    scale_to_hd(OUT_RAW, OUT_HD)
    print("DONE:scene05_cut06")
