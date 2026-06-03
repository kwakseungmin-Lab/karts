"""Generate scene04_cut02 frame image using GPT Image API."""
import base64
import os
import subprocess
import sys

from openai import OpenAI

PROMPT = (
    "Cinematic telephoto medium shot 200mm, Aiden, medieval knight in dark steel partial plate armor "
    "with chain mail, scarred face, brown hair, longsword with runic engravings, figure emerging from "
    "thick morning fog onto ruined stone bridge, slow deliberate walk coming to a stop at bridge entrance, "
    "blue-grey desaturated atmosphere, armor surface gleaming faintly through fog, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080, 16:9 composition"
)

OUT_DIR = "/Users/ksm2761/karts/vimax/short-film-project/final/frames"
RAW_PATH = f"{OUT_DIR}/scene04_cut02.png"
HD_PATH = f"{OUT_DIR}/scene04_cut02_hd.png"


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
            "ffmpeg", "-y", "-i", src,
            "-vf", "scale=1920:1080:flags=lanczos,setsar=1",
            "-pix_fmt", "yuv420p",
            dst,
        ],
        check=True,
    )


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Generating frame: {RAW_PATH}", flush=True)
    generate_frame(PROMPT, RAW_PATH)
    print(f"Scaling to HD: {HD_PATH}", flush=True)
    scale_to_hd(RAW_PATH, HD_PATH)
    print("Done.", flush=True)
