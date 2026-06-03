"""Generate scene07_cut02 frame image using GPT Image generate endpoint.
Reference images not found on filesystem, falling back to generate endpoint.
"""
import base64
import subprocess
import sys
import os

from openai import OpenAI

PROMPT = (
    "Cinematic extreme close-up POV shot from Kagemasa's perspective, "
    "Aiden's left pauldron in dark steel partial plate armor, "
    "deep scratch marks carved into the metal surface where a Blackstone Legion emblem "
    "was deliberately defaced — gouged lines obliterating the crest, "
    "rust and battle damage around the scratches, morning light catching the grooves, "
    "symbolic detail, For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)

OUT_DIR = "/Users/ksm2761/karts/vimax/short-film-project/final/frames"
RAW_PATH = f"{OUT_DIR}/scene07_cut02.png"
HD_PATH = f"{OUT_DIR}/scene07_cut02_hd.png"


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
    print(f"Saved raw image: {out_path}", file=sys.stderr)


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
    print(f"Saved HD image: {dst}", file=sys.stderr)


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    generate_frame(PROMPT, RAW_PATH)
    scale_to_hd(RAW_PATH, HD_PATH)
    print("DONE:scene07_cut02")
