"""Generate scene08_cut02 frame using GPT Image generate endpoint (no refs available)."""

import base64
import os
import subprocess
from pathlib import Path

from openai import OpenAI

# Load API key from .env if not already set
_env_file = Path("/Users/ksm2761/karts/.env")
if not os.environ.get("OPENAI_API_KEY") and _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        if _line.startswith("OPENAI_API_KEY="):
            os.environ["OPENAI_API_KEY"] = _line.split("=", 1)[1].strip()
            break

PROMPT = (
    "Extreme close-up slow motion insert, blade deflection impact, nodachi edge scraping "
    "against chain mail rings, sparks and metal fragments scatter in slow motion, morning "
    "light catches each spark, chain mail ring flying off frame, rusted stone surface beneath, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080"
)

OUT_RAW = "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene08_cut02.png"
OUT_HD = "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene08_cut02_hd.png"


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
    print(f"Saved raw frame: {out_path}")


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
    print(f"Saved HD frame: {dst}")


if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY environment variable not set")

    generate_frame(PROMPT, OUT_RAW)
    scale_to_hd(OUT_RAW, OUT_HD)
    print("DONE:scene08_cut02")
