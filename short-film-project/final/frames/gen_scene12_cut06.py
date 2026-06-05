#!/usr/bin/env python3
"""Generate scene12_cut06 frame image using GPT Image generate endpoint."""

import base64
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Load .env from karts directory
load_dotenv("/Users/ksm2761/karts/.env")

PROMPT = (
    "Cinematic title card, full black screen fade-in, centered title text '명예의 무게' "
    "with subtitle 'The Weight of Honor' in elegant serif typography, "
    "subtle grey-white lettering on pure black, no decoration, minimal, "
    "final frame of film, 1920x1080 16:9"
)

FRAMES_DIR = Path("/Users/ksm2761/karts/vimax/short-film-project/final/frames")
RAW_PATH = FRAMES_DIR / "scene12_cut06.png"
HD_PATH = FRAMES_DIR / "scene12_cut06_hd.png"


def generate_frame(prompt: str, out_path: Path) -> None:
    client = OpenAI()
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1536x1024",
        quality="high",
        n=1,
    )
    data = base64.b64decode(response.data[0].b64_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Raw image saved: {out_path}", file=sys.stderr)


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
    print(f"HD image saved: {dst}", file=sys.stderr)


def main() -> None:
    print("Generating scene12_cut06 frame...", file=sys.stderr)
    generate_frame(PROMPT, RAW_PATH)
    print("Scaling to 1920x1080 HD...", file=sys.stderr)
    scale_to_hd(RAW_PATH, HD_PATH)
    print("DONE:scene12_cut06")


if __name__ == "__main__":
    main()
