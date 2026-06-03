"""Generate scene09 cut02 frame using GPT Image edit endpoint."""

import base64
import os
import subprocess
from pathlib import Path

from openai import OpenAI


def _load_env(env_path: str = "/Users/ksm2761/karts/.env") -> None:
    """Load key=value pairs from .env file into os.environ if not already set."""
    p = Path(env_path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value

INSERT_REF = "short-film-project/images/05_cuts/action_cuts/cut_02_menpou_floor.png"
OUT_RAW = "short-film-project/final/frames/scene09_cut02.png"
OUT_HD = "short-film-project/final/frames/scene09_cut02_hd.png"

PROMPT = (
    "Cinematic extreme close-up insert shot, cracked oni-face menpou mask falling and sliding "
    "across stone bridge floor, metal and ceramic hitting stone, hairline cracks spreading across "
    "the iron face of the mask, settling on ancient worn stone surface, cold morning light casting "
    "sharp shadows, For Honor cinematic trailer style, photorealistic, 1920x1080, 16:9 composition. "
    "Reference image provided for mask design and stone floor detail consistency."
)


def main() -> None:
    _load_env()
    client = OpenAI()

    print("Calling GPT Image edit endpoint...")
    with open(INSERT_REF, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=PROMPT,
            size="1536x1024",
        )

    data = base64.b64decode(response.data[0].b64_json)
    with open(OUT_RAW, "wb") as f:
        f.write(data)
    print(f"Saved raw: {OUT_RAW}  ({len(data)} bytes)")

    print("Scaling to HD...")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            OUT_RAW,
            "-vf",
            "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            OUT_HD,
        ],
        check=True,
    )
    print(f"Saved HD:  {OUT_HD}")


if __name__ == "__main__":
    main()
