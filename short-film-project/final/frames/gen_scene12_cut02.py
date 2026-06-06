"""Generate scene12_cut02 frame image using GPT Image generate endpoint."""

import base64
import os
import subprocess
import sys

from openai import OpenAI

PROMPT = (
    "Cinematic slow crane-up aerial ascent, bird's eye view descending on ruined stone bridge, "
    "empty bridge with battle traces — blood stains, metal fragments, broken mask pieces on stone floor, "
    "fog on both sides of bridge, left side shows gothic Ashfeld castle silhouette and green forest, "
    "right side shows Myre misty wetlands and bamboo silhouette, "
    "two worlds divided by one bridge, extreme desaturation blue-grey, overcast, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)

RAW_OUT = "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene12_cut02.png"
HD_OUT = "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene12_cut02_hd.png"


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
    print(f"Raw frame saved: {out_path}", file=sys.stderr)


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
    print(f"HD frame saved: {dst}", file=sys.stderr)


if __name__ == "__main__":
    generate_frame(PROMPT, RAW_OUT)
    scale_to_hd(RAW_OUT, HD_OUT)
    print("DONE:scene12_cut02")
