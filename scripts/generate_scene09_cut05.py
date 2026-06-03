"""
Generate scene09_cut05 using GPT Image edit endpoint with character references.
"""
import base64
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

BASE = Path("/Users/ksm2761/karts/short-film-project")
FRAMES_DIR = BASE / "final" / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

client = OpenAI()

PROMPT = (
    "Cinematic medium over-the-shoulder shot from behind Aiden, medieval knight in dark steel "
    "partial plate armor with chain mail, scarred face, brown hair, longsword with runic "
    "engravings frozen motionless overhead at peak of execution arc, looking down at kneeling "
    "Kagemasa, samurai in deep navy oyoroi armor with gold imperial crest, bare unmasked face "
    "looking up without fear, bright clean morning light flooding stone bridge, long frozen "
    "moment of suspended time, emotional climax of film, For Honor cinematic trailer style, "
    "photorealistic, 1920x1080, 16:9 composition"
)

CHARACTER_REFS = [
    BASE / "images/01_character_sheets/aiden/aiden_01_front_view.png",
    BASE / "images/01_character_sheets/aiden/aiden_04_face_closeup.png",
    BASE / "images/01_character_sheets/kagemasa/kagemasa_04_face_without_mask.png",
    BASE / "images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
]

BACKGROUND_REF = BASE / "images/03_background_art/borderlands_bridge/bg_02_bridge_both_ends.png"


def generate_frame_with_refs(
    prompt: str,
    ref_paths: list[Path],
    out_path: Path,
) -> None:
    """
    Use GPT Image edit endpoint with first reference image and
    mention additional references in the prompt.
    """
    extra_desc = ""
    if len(ref_paths) > 1:
        extra_desc = " Reference images provided for character consistency: Aiden (medieval knight, scarred face, brown hair, dark steel armor) and Kagemasa (samurai, deep navy oyoroi armor, bare unmasked face with honorable expression)."

    full_prompt = prompt + extra_desc

    print(f"Generating with {len(ref_paths)} reference images...")
    print(f"Primary ref: {ref_paths[0].name}")
    print(f"Prompt length: {len(full_prompt)} chars")

    with open(ref_paths[0], "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=full_prompt,
            size="1536x1024",
        )

    image_data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(image_data)
    print(f"Saved raw frame: {out_path}")


def scale_to_hd(src: Path, dst: Path) -> None:
    """Scale 1536x1024 -> 16:9 crop (1536x864) -> 1920x1080."""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-vf",
            "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            str(dst),
        ],
        check=True,
        capture_output=True,
    )
    print(f"Saved HD frame: {dst}")


def main() -> None:
    raw_out = FRAMES_DIR / "scene09_cut05.png"
    hd_out = FRAMES_DIR / "scene09_cut05_hd.png"

    # Use background ref as primary if character sheets aren't available,
    # but character refs are available so use first character ref as primary
    all_refs = CHARACTER_REFS + [BACKGROUND_REF]

    # Verify all ref files exist
    for ref in all_refs:
        if not ref.exists():
            print(f"WARNING: Reference file not found: {ref}", file=sys.stderr)

    generate_frame_with_refs(PROMPT, CHARACTER_REFS, raw_out)
    scale_to_hd(raw_out, hd_out)

    print(f"\nDone.")
    print(f"Raw: {raw_out}")
    print(f"HD:  {hd_out}")


if __name__ == "__main__":
    main()
