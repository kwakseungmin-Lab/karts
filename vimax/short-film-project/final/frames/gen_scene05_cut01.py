#!/usr/bin/env python3
"""Generate scene05_cut01 frame image using GPT Image generate endpoint."""

import base64
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Load .env from karts directory
load_dotenv("/Users/ksm2761/karts/.env")


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


def scale_to_hd(src: str, dst: str) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            src,
            "-vf",
            "scale=1920:1080:flags=lanczos,setsar=1",
            "-pix_fmt",
            "yuv420p",
            dst,
        ],
        check=True,
    )


def main() -> None:
    frames_dir = Path("/Users/ksm2761/karts/vimax/short-film-project/final/frames")
    frames_dir.mkdir(parents=True, exist_ok=True)

    raw_path = str(frames_dir / "scene05_cut01.png")
    hd_path = str(frames_dir / "scene05_cut01_hd.png")

    prompt = (
        "Cinematic medium two-shot slightly low angle, on ancient ruined stone bridge at dawn, "
        "two warriors approaching center from opposite ends and halting simultaneously 5 meters apart, "
        "left: Aiden, medieval knight in dark steel partial plate armor with chain mail, scarred face, "
        "brown hair, longsword with runic engravings raised into guard position, "
        "right: Kagemasa, samurai in deep navy oyoroi armor with gold imperial crest, "
        "wide shoulder sode, nodachi sword with cherry blossom tsuba held high in jodan upper stance, "
        "morning fog partially lifting, faint oblique sunlight beginning to filter through mist, "
        "blue-grey desaturated atmosphere, both warriors locked in tense stillness, "
        "For Honor cinematic trailer style, photorealistic, 1920x1080, 16:9 composition"
    )

    print("Generating scene05_cut01 frame...")
    generate_frame(prompt, raw_path)
    print(f"Raw image saved: {raw_path}")

    print("Scaling to 1920x1080 HD...")
    scale_to_hd(raw_path, hd_path)
    print(f"HD image saved: {hd_path}")


if __name__ == "__main__":
    main()
