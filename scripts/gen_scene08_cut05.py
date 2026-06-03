#!/usr/bin/env python3
"""Generate scene08_cut05 — blood on stone insert, refined from cut_09 reference."""

import base64
import subprocess
from pathlib import Path

from openai import OpenAI

INSERT_REF = Path(
    "/Users/ksm2761/karts/short-film-project/images/05_cuts/action_cuts/cut_09_blood_on_stone.png"
)
OUT_BASE = Path("/Users/ksm2761/karts/short-film-project/final/frames/scene08_cut05.png")
OUT_HD = Path("/Users/ksm2761/karts/short-film-project/final/frames/scene08_cut05_hd.png")

PROMPT = (
    "Extreme close-up insert, fresh blood droplets spreading on ancient rough stone bridge surface, "
    "red blood contrasting with gray weathered stone, morning light reveals texture of each stone, "
    "visceral detail, For Honor cinematic style, photorealistic, 1920x1080"
)


def generate_frame_with_insert_ref(prompt: str, ref_path: Path, out_path: Path) -> None:
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
    print(f"Saved base image: {out_path}")


def scale_to_hd(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            str(dst),
        ],
        check=True,
    )
    print(f"Saved HD image: {dst}")


if __name__ == "__main__":
    OUT_BASE.parent.mkdir(parents=True, exist_ok=True)
    generate_frame_with_insert_ref(PROMPT, INSERT_REF, OUT_BASE)
    scale_to_hd(OUT_BASE, OUT_HD)
    print("Done.")
