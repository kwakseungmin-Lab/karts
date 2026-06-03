"""Generate scene08_cut05 frame using GPT Image generate endpoint (no character refs, insert ref not found)."""

import base64
import os
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

PROMPT = (
    "Extreme close-up insert, fresh blood droplets spreading on ancient rough stone bridge "
    "surface, red blood contrasting with gray weathered stone, morning light reveals texture "
    "of each stone, visceral detail, For Honor cinematic style, photorealistic, 1920x1080"
)

OUT_DIR = Path("/Users/ksm2761/karts/vimax/short-film-project/final/frames")
RAW_PATH = OUT_DIR / "scene08_cut05.png"
HD_PATH = OUT_DIR / "scene08_cut05_hd.png"


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
    print(f"Saved raw image: {out_path}", file=sys.stderr)


def scale_to_hd(src: Path, dst: Path) -> None:
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
    print(f"Saved HD image: {dst}", file=sys.stderr)


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    generate_frame(PROMPT, RAW_PATH)
    scale_to_hd(RAW_PATH, HD_PATH)
    print("DONE:scene08_cut05")


if __name__ == "__main__":
    main()
