"""Generate scene02_cut02 frame using gpt-image-1."""
import base64
import os
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

PROMPT = (
    "Cinematic extreme close-up, Aiden's eyes inside barbeuta helmet visor, "
    "torchlight reflection dancing in pupils, eyes slowly closing in refusal — "
    "Aiden (medieval knight in dark steel partial plate armor with chain mail, "
    "scarred face, brown hair, left eye bears a vertical scar), "
    "rain droplets on helmet metal catching orange torchlight. "
    "Desaturated warm tone, deep shadows around eyes, emotional tension. "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)

CHARACTER_REF = Path(
    "/Users/ksm2761/karts/vimax/short-film-project/images/01_character_sheets"
    "/aiden/aiden_04_face_closeup.png"
)

RAW_OUT = Path("/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene02_cut02.png")
HD_OUT = Path("/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene02_cut02_hd.png")


def generate_with_ref(prompt: str, ref_path: Path, out_path: Path) -> None:
    client = OpenAI()
    with open(ref_path, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt + " Reference image provided for character consistency.",
            size="1536x1024",
        )
    data = base64.b64decode(response.data[0].b64_json)
    out_path.write_bytes(data)
    print(f"Saved raw: {out_path}")


def generate_without_ref(prompt: str, out_path: Path) -> None:
    client = OpenAI()
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1536x1024",
        quality="high",
        n=1,
    )
    data = base64.b64decode(response.data[0].b64_json)
    out_path.write_bytes(data)
    print(f"Saved raw: {out_path}")


def scale_to_hd(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "scale=1920:1080:flags=lanczos,setsar=1",
            "-pix_fmt", "yuv420p",
            str(dst),
        ],
        check=True,
    )
    print(f"Saved HD: {dst}")


def main() -> None:
    if CHARACTER_REF.exists():
        print(f"Using character ref: {CHARACTER_REF}")
        generate_with_ref(PROMPT, CHARACTER_REF, RAW_OUT)
    else:
        print("Character ref not found, using generate endpoint.")
        generate_without_ref(PROMPT, RAW_OUT)

    scale_to_hd(RAW_OUT, HD_OUT)
    print("DONE:scene02_cut02")


if __name__ == "__main__":
    main()
