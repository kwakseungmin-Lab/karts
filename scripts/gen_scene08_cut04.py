"""Generate scene08_cut04 using GPT Image edit endpoint with character references."""

import base64
import os
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

client = OpenAI()

BASE = Path("/Users/ksm2761/karts/short-film-project")
OUT_DIR = BASE / "final" / "frames"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROMPT = (
    "Cinematic POV handheld shaky shot, Kagemasa — samurai in deep navy oyoroi armor "
    "with gold imperial crest, cracked menpou mask, wide shoulder sode — unleashes "
    "furious wide nodachi swings with raw anger and grief. Aiden — medieval knight in "
    "dark steel partial plate armor — parries desperately, retreating step by step "
    "toward the crumbling stone bridge railing. Aiden's back presses against the ruined "
    "parapet. Morning light, fog cleared, emotional intensity visible in both warriors' "
    "postures. Kinetic, dynamic, close-quarters combat. For Honor cinematic trailer "
    "style, photorealistic, 1920x1080, 16:9. "
    "Character reference images provided for visual consistency: "
    "Kagemasa wears deep navy oyoroi armor with gold crest and cracked menpou mask; "
    "Aiden wears dark steel partial plate armor with red crusader cross motif."
)

REF_PATHS = [
    BASE / "images/01_character_sheets/aiden/aiden_01_front_view.png",
    BASE / "images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
    BASE / "images/01_character_sheets/kagemasa/kagemasa_02_three_quarter_view.png",
]

OUT_RAW = OUT_DIR / "scene08_cut04.png"
OUT_HD = OUT_DIR / "scene08_cut04_hd.png"


def generate_frame_with_refs(prompt: str, ref_paths: list[Path], out_path: Path) -> None:
    """Generate frame using edit endpoint with first ref image as base."""
    primary_ref = ref_paths[0]
    extra_note = (
        " Multiple character reference images provided for consistency: "
        "Aiden (medieval knight, dark steel plate armor with red cross motif) "
        "and Kagemasa (samurai, deep navy oyoroi armor, gold imperial crest, cracked menpou mask)."
    )

    print(f"Calling GPT Image edit endpoint with primary ref: {primary_ref.name}")
    with open(primary_ref, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt + extra_note,
            size="1536x1024",
        )

    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Saved raw image: {out_path}")


def scale_to_hd(src: Path, dst: Path) -> None:
    """Scale 1536x1024 to 1920x1080 via 16:9 crop then upscale."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            str(dst),
        ],
        check=True,
    )
    print(f"Saved HD image: {dst}")


def main() -> None:
    generate_frame_with_refs(PROMPT, REF_PATHS, OUT_RAW)
    scale_to_hd(OUT_RAW, OUT_HD)
    print(f"Done. Output: {OUT_HD}")


if __name__ == "__main__":
    main()
