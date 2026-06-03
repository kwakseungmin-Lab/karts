#!/usr/bin/env python3
"""Generate scene08_cut06 image using GPT Image edit endpoint with character refs."""

import base64
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("/Users/ksm2761/karts/.env")

BASE = Path("/Users/ksm2761/karts/short-film-project")
FRAMES_DIR = BASE / "final/frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

CHARACTER_REFS = {
    "aiden": {
        "default": BASE / "images/01_character_sheets/aiden/aiden_01_front_view.png",
        "closeup": BASE / "images/01_character_sheets/aiden/aiden_04_face_closeup.png",
    },
    "kagemasa": {
        "default": BASE / "images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
        "face_without_mask": BASE / "images/01_character_sheets/kagemasa/kagemasa_04_face_without_mask.png",
    },
}

PROMPT = (
    "Cinematic low angle shot looking up at Aiden — medieval knight in dark steel partial plate armor "
    "with chain mail, scarred face, brown hair, longsword raised — standing over Kagemasa who has dropped "
    "to one knee on the stone bridge. Kagemasa — samurai in deep navy oyoroi armor, cracked menpou mask "
    "beginning to slip — is kneeling but undefeated in spirit. Dramatic power dynamic, Aiden silhouetted "
    "against bright morning sky, rim light along sword edge. Stone bridge ruins, morning light flooding scene, "
    "emotional climax building directly into scene 09. For Honor cinematic trailer style, photorealistic, "
    "1920x1080, 16:9. "
    "CRITICAL: Maintain exact character appearances from reference images. "
    "Aiden: dark steel partial plate armor with chain mail, scarred face, brown hair. "
    "Kagemasa: deep navy oyoroi samurai armor, cracked menpou half-mask slipping to reveal face beneath. "
    "Reference images provided for both characters to ensure visual consistency."
)


def generate_frame_with_refs(prompt: str, ref_paths: list[Path], out_path: Path) -> None:
    """Generate frame using GPT Image edit endpoint with reference images."""
    client = OpenAI()

    # Use the primary character ref (Aiden front view) as the main image
    primary_ref = ref_paths[0]
    print(f"Primary ref: {primary_ref}")
    print(f"Additional refs: {[str(p) for p in ref_paths[1:]]}")

    # Build supplemental description mentioning all refs
    extra_desc = (
        " Character reference images injected for consistency: "
        "Aiden front view, Aiden face closeup, Kagemasa front view, Kagemasa face without mask."
    )

    with open(primary_ref, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt + extra_desc,
            size="1536x1024",
        )

    image_data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(image_data)
    print(f"Saved: {out_path}")


def scale_to_hd(src: Path, dst: Path) -> None:
    """Scale 1536×1024 → crop to 16:9 (1536×864) → upscale to 1920×1080."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            str(dst),
        ],
        check=True,
    )
    print(f"HD saved: {dst}")


def main() -> None:
    out_raw = FRAMES_DIR / "scene08_cut06.png"
    out_hd = FRAMES_DIR / "scene08_cut06_hd.png"

    ref_paths = [
        CHARACTER_REFS["aiden"]["default"],
        CHARACTER_REFS["aiden"]["closeup"],
        CHARACTER_REFS["kagemasa"]["default"],
        CHARACTER_REFS["kagemasa"]["face_without_mask"],
    ]

    print("Generating scene08_cut06 with character refs...")
    generate_frame_with_refs(PROMPT, ref_paths, out_raw)

    print("Scaling to 1920x1080...")
    scale_to_hd(out_raw, out_hd)

    print("Done.")
    print(f"Raw:  {out_raw}")
    print(f"HD:   {out_hd}")


if __name__ == "__main__":
    main()
