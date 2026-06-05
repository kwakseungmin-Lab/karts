#!/usr/bin/env python3
"""Generate scene11_cut04 frame image using GPT Image generate endpoint."""

import base64
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("/Users/ksm2761/karts/.env")

PROMPT = (
    "Cinematic static wide shot of the empty ruined stone borderlands bridge, "
    "fog rolling in from both ends reclaiming the space, battle traces on the stone "
    "— smears of blood, a fallen fragment of metal from broken armor, scratches on the stone. "
    "The bridge is utterly empty, no human figures. "
    "Morning light completely overcast now, cold blue-grey desaturated tone matching the opening scene color, "
    "mist thickening, distant sound implied by the still and ominous atmosphere, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)

OUTPUT_DIR = Path("/Users/ksm2761/karts/vimax/short-film-project/final/frames")
SRC_PATH = OUTPUT_DIR / "scene11_cut04.png"
DST_PATH = OUTPUT_DIR / "scene11_cut04_hd.png"


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
    out_path.write_bytes(data)
    print(f"Generated: {out_path}", file=sys.stderr)


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
    print(f"Scaled: {dst}", file=sys.stderr)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generate_frame(PROMPT, SRC_PATH)
    scale_to_hd(SRC_PATH, DST_PATH)
    print("DONE:scene11_cut04")


if __name__ == "__main__":
    main()
