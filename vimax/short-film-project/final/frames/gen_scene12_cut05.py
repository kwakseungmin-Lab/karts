"""Generate scene12_cut05 frame image using GPT Image generate endpoint."""
import base64
import os
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

PROMPT = (
    "Extreme close-up insert shot, crow perched on a rusted abandoned sword blade embedded in stone, "
    "single black feather detail, misty grey atmosphere, desaturated blue-grey, crow slowly spreads "
    "wings and takes flight, echoing the opening scene, For Honor cinematic style, photorealistic, "
    "1920x1080 16:9"
)

OUTPUT_DIR = Path("/Users/ksm2761/karts/vimax/short-film-project/final/frames")
RAW_OUT = OUTPUT_DIR / "scene12_cut05.png"
HD_OUT = OUTPUT_DIR / "scene12_cut05_hd.png"


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
    print(f"Saved raw frame: {out_path}")


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
    print(f"Saved HD frame: {dst}")


def main() -> None:
    generate_frame(PROMPT, RAW_OUT)
    scale_to_hd(RAW_OUT, HD_OUT)
    print("DONE:scene12_cut05")


if __name__ == "__main__":
    main()
