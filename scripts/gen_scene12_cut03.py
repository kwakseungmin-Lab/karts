#!/usr/bin/env python3
"""Generate scene12 cut03 using GPT Image edit endpoint with insert reference."""

import base64
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("/Users/ksm2761/karts/.env")


def generate_frame_with_ref(prompt: str, ref_path: str, out_path: str) -> None:
    client = OpenAI()
    with open(ref_path, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt,
            size="1536x1024",
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
            "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            dst,
        ],
        check=True,
    )


def main() -> None:
    insert_ref = "/Users/ksm2761/karts/short-film-project/images/05_cuts/action_cuts/cut_02_menpou_floor.png"
    out_path = "/Users/ksm2761/karts/short-film-project/final/frames/scene12_cut03.png"
    out_hd = "/Users/ksm2761/karts/short-film-project/final/frames/scene12_cut03_hd.png"

    prompt = (
        "Extreme close-up insert shot, broken cracked menpo (samurai demon face mask) lying on ancient stone floor, "
        "blood spreading on stone, sword scratch marks on cobblestone, metal fragments, shallow depth of field, "
        "desaturated blue-grey, single dust particle drifting in ambient light, "
        "For Honor cinematic style, photorealistic, 1920x1080 16:9"
    )

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    print("Generating with edit endpoint using insert reference...")
    generate_frame_with_ref(prompt, insert_ref, out_path)
    print(f"Saved: {out_path}")

    print("Scaling to 1920x1080...")
    scale_to_hd(out_path, out_hd)
    print(f"Saved HD: {out_hd}")
    print("Done.")


if __name__ == "__main__":
    main()
