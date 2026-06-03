#!/usr/bin/env python3
"""Generate scene05_cut05 frame image using GPT Image generate endpoint."""

import base64
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

    raw_path = str(frames_dir / "scene05_cut05.png")
    hd_path = str(frames_dir / "scene05_cut05_hd.png")

    prompt = (
        "Cinematic tight close-up alternating over-the-shoulder, eyes only visible beneath battle helmets, "
        "left: Aiden's scarred face visible under open-faced bascinet helmet, brown hair, "
        "narrow intense eyes reading opponent's sword angle, "
        "right: Kagemasa's eyes above menpou demon-face half-mask, "
        "deep focused gaze tracking enemy shoulder movement, "
        "both faces framed by cold blue-grey fog behind, "
        "oblique morning light on face edges, extreme psychological intensity, "
        "no dialogue, story told through eyes alone, "
        "For Honor cinematic trailer style, photorealistic, 1920x1080, 16:9 composition"
    )

    print("Generating scene05_cut05 frame...")
    generate_frame(prompt, raw_path)
    print(f"Raw image saved: {raw_path}")

    print("Scaling to 1920x1080 HD...")
    scale_to_hd(raw_path, hd_path)
    print(f"HD image saved: {hd_path}")


if __name__ == "__main__":
    main()
