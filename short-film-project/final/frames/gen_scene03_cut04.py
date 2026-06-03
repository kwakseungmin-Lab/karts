"""Generate scene03_cut04 frame using GPT Image edit endpoint with character refs."""
import base64
import os
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

client = OpenAI()

PROMPT = (
    "Cinematic low angle medium shot tilting up slowly, Kagemasa — samurai in battered deep navy "
    "oyoroi armor with gold imperial crest, kabuto helmet, menpou demon face mask — kneeling alone "
    "in snow, nodachi sword planted blade-down into snow with both hands resting on the hilt in "
    "silent prayer, motionless armored warriors lying in the snow around him, dark red scattered "
    "across white snow, blizzard winding down to silence, grey overcast sky, solitary and "
    "grief-stricken, solemn battlefield aftermath, For Honor cinematic trailer style, "
    "photorealistic, 1920x1080 16:9"
)

REF_PATHS = [
    "/Users/ksm2761/karts/short-film-project/images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
    "/Users/ksm2761/karts/short-film-project/images/01_character_sheets/kagemasa/kagemasa_04_face_without_mask.png",
    "/Users/ksm2761/karts/short-film-project/images/01_character_sheets/kagemasa/kagemasa_06_nodachi_detail.png",
]

BG_REF = "/Users/ksm2761/karts/short-film-project/images/03_background_art/myre/bg_06_myre_wetlands.png"

OUT_RAW = "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene03_cut04.png"
OUT_HD = "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene03_cut04_hd.png"


def generate_frame_with_refs(prompt: str, ref_paths: list[str], out_path: str) -> None:
    """Generate frame using edit endpoint with character reference images."""
    extra_desc = " Reference images provided for character consistency." if len(ref_paths) > 1 else ""

    with open(ref_paths[0], "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt + extra_desc,
            size="1536x1024",
        )

    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Saved raw frame: {out_path}", file=sys.stderr)


def scale_to_hd(src: str, dst: str) -> None:
    """Scale 1536x1024 to 1920x1080."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", src,
            "-vf", "scale=1920:1080:flags=lanczos,setsar=1",
            "-pix_fmt", "yuv420p",
            dst,
        ],
        check=True,
    )
    print(f"Saved HD frame: {dst}", file=sys.stderr)


if __name__ == "__main__":
    generate_frame_with_refs(PROMPT, REF_PATHS, OUT_RAW)
    scale_to_hd(OUT_RAW, OUT_HD)
    print("DONE:scene03_cut04")
