"""Generate scene05_cut03 frame using gpt-image-1 generate endpoint."""

import base64
import os
import subprocess

from openai import OpenAI

client = OpenAI()

PROMPT = (
    "Cinematic extreme close-up macro detail, gauntleted fingers gripping longsword hilt "
    "with runic engraving, dark steel armor joint at knuckle, a single water droplet from "
    "morning fog rolling slowly down the blade toward the crossguard, cold blue-grey light, "
    "metallic surface texture, ASMR-level detail, breath tension visible in moisture, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080, 16:9 composition"
)

OUT_DIR = "/Users/ksm2761/karts/vimax/short-film-project/final/frames"
RAW_PATH = os.path.join(OUT_DIR, "scene05_cut03.png")
HD_PATH = os.path.join(OUT_DIR, "scene05_cut03_hd.png")


def generate_frame(prompt: str, out_path: str) -> None:
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


if __name__ == "__main__":
    print("Generating frame via gpt-image-1 generate endpoint...")
    generate_frame(PROMPT, RAW_PATH)
    print(f"Raw frame saved: {RAW_PATH}")

    print("Scaling to 1920x1080...")
    scale_to_hd(RAW_PATH, HD_PATH)
    print(f"HD frame saved: {HD_PATH}")
    print("DONE:scene05_cut03")
