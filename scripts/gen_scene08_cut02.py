"""Generate scene08_cut02 frame using GPT Image edit endpoint with insert_ref."""

import base64
import subprocess
from pathlib import Path

from openai import OpenAI

client = OpenAI()

INSERT_REF = (
    "/Users/ksm2761/karts/short-film-project/images/05_cuts/action_cuts/cut_01_swords_x_sparks.png"
)
OUT_PATH = "/Users/ksm2761/karts/short-film-project/final/frames/scene08_cut02.png"
HD_PATH = "/Users/ksm2761/karts/short-film-project/final/frames/scene08_cut02_hd.png"

PROMPT = (
    "Extreme close-up slow motion insert, blade deflection impact, nodachi edge scraping against "
    "chain mail rings, sparks and metal fragments scatter in slow motion, morning light catches each spark, "
    "chain mail ring flying off frame, rusted stone surface beneath, For Honor cinematic trailer style, "
    "photorealistic, 1920x1080"
)


def generate() -> None:
    print("Generating scene08_cut02 via edit endpoint...")
    with open(INSERT_REF, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=PROMPT,
            size="1536x1024",
        )

    data = base64.b64decode(response.data[0].b64_json)
    with open(OUT_PATH, "wb") as f:
        f.write(data)
    print(f"Saved: {OUT_PATH}")


def scale_to_hd() -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            OUT_PATH,
            "-vf",
            "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            HD_PATH,
        ],
        check=True,
        capture_output=True,
    )
    print(f"Scaled HD: {HD_PATH}")


if __name__ == "__main__":
    generate()
    scale_to_hd()
    print("Done.")
