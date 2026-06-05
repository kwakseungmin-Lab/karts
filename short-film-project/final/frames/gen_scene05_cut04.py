"""Generate scene05_cut04 frame image using GPT Image API."""

import base64
import os
import subprocess
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("/Users/ksm2761/karts/.env")

client = OpenAI()

PROMPT = (
    "Cinematic extreme close-up macro detail, deep navy lacquered samurai waraji foot armor "
    "scraping one deliberate step on moss-covered ancient stone bridge, intricate lacquerwork "
    "and leather armor strap pulled taut at the waist joint, stone surface texture and "
    "green-grey moss under armored foot, oblique cold morning light catching lacquer sheen, "
    "blue-grey desaturated with subtle gold glint from lacquer, For Honor cinematic trailer "
    "style, photorealistic, 1920x1080, 16:9 composition"
)

BASE_DIR = "/Users/ksm2761/karts/vimax/short-film-project"
FRAMES_DIR = f"{BASE_DIR}/final/frames"

RAW_PATH = f"{FRAMES_DIR}/scene05_cut04.png"
HD_PATH = f"{FRAMES_DIR}/scene05_cut04_hd.png"

CHARACTER_REFS = [
    f"{BASE_DIR}/images/01_character_sheets/kagemasa/kagemasa_05_armor_detail.png",
    f"{BASE_DIR}/images/01_character_sheets/kagemasa/kagemasa_06_nodachi_detail.png",
]
BACKGROUND_REF = f"{BASE_DIR}/images/03_background_art/borderlands_bridge/bg_03_bridge_detail_ruins.png"


def refs_exist(paths: list[str]) -> list[str]:
    return [p for p in paths if os.path.exists(p)]


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


def generate_frame_with_refs(prompt: str, ref_paths: list[str], out_path: str) -> None:
    with open(ref_paths[0], "rb") as img_f:
        extra_desc = ""
        if len(ref_paths) > 1:
            extra_desc = " Reference images provided for character consistency."
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt + extra_desc,
            size="1536x1024",
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


def main() -> None:
    os.makedirs(FRAMES_DIR, exist_ok=True)

    available_refs = refs_exist(CHARACTER_REFS)
    if available_refs:
        print(f"Using edit endpoint with {len(available_refs)} character ref(s): {available_refs}")
        generate_frame_with_refs(PROMPT, available_refs, RAW_PATH)
    else:
        print("No character refs found — using generate endpoint.")
        generate_frame(PROMPT, RAW_PATH)

    print(f"Raw frame saved: {RAW_PATH}")
    scale_to_hd(RAW_PATH, HD_PATH)
    print(f"HD frame saved: {HD_PATH}")


if __name__ == "__main__":
    main()
