"""Generate scene01_cut02 frame using GPT Image generate endpoint."""

import base64
import os
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

PROMPT = (
    "Cinematic extreme close-up macro shot, a single crow perched on a rusted medieval "
    "sword blade half-buried in mud, desaturated near-grayscale, single black feather "
    "trembling in slight wind, rust and old blood on blade surface, shallow depth of field, "
    "For Honor cinematic style, photorealistic, 1920x1080, 16:9 composition"
)

OUT_DIR = Path("/Users/ksm2761/karts/vimax/short-film-project/final/frames")
RAW_PATH = OUT_DIR / "scene01_cut02.png"
HD_PATH = OUT_DIR / "scene01_cut02_hd.png"


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
    print("DONE:scene01_cut02")


if __name__ == "__main__":
    main()
