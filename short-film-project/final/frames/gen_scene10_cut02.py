"""Generate scene10_cut02 frame using GPT Image generate endpoint (no refs available)."""

import base64
import os
import subprocess
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("/Users/ksm2761/karts/.env")

client = OpenAI()

PROMPT = (
    "Cinematic cross-cutting extreme close-up, first Kagemasa bare face — "
    "40s samurai, topknot black hair, deep calm exhausted eyes, no mask, steady gaze, "
    "then Aiden medieval knight face — 30s man, short brown hair, vertical scar above left eye, "
    "tired yet resolute eyes, soft warm golden morning light on both faces, no shadows, "
    "serene expression after battle, For Honor cinematic trailer style, photorealistic, "
    "1920x1080 16:9"
)

OUT_DIR = "/Users/ksm2761/karts/vimax/short-film-project/final/frames"
RAW_OUT = os.path.join(OUT_DIR, "scene10_cut02.png")
HD_OUT = os.path.join(OUT_DIR, "scene10_cut02_hd.png")


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
    print("Generating scene10_cut02 raw frame (1536x1024)...", flush=True)
    generate_frame(PROMPT, RAW_OUT)
    print(f"Raw frame saved: {RAW_OUT}", flush=True)

    print("Scaling to 1920x1080 HD...", flush=True)
    scale_to_hd(RAW_OUT, HD_OUT)
    print(f"HD frame saved: {HD_OUT}", flush=True)

    print("DONE:scene10_cut02", flush=True)
