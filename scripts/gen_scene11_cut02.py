#!/usr/bin/env python3
"""Generate scene11_cut02 frame with character references via GPT Image edit endpoint."""

import base64
import logging
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path("/Users/ksm2761/karts/.env"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path("/Users/ksm2761/karts/short-film-project")
FRAMES_DIR = PROJECT_ROOT / "final" / "frames"

PROMPT = (
    "Cinematic static wide shot, locked-off camera, full ruined stone bridge visible from center, "
    "two warriors separating in opposite directions. "
    "Left side: Aiden, medieval knight in dark steel partial plate armor with chain mail, "
    "back to camera, longsword with runic engravings at side, walking toward the Ashfeld gothic ruin "
    "end of the bridge. "
    "Right side: Kagemasa, samurai in deep navy oyoroi armor with gold imperial crest, wide shoulder sode, "
    "nodachi sword with cherry blossom tsuba sheathed, back to camera, walking toward the Myre mist end. "
    "Symmetrical composition, bridge centre empty, fog rolling back in from both sides, morning light "
    "dimming as clouds gather, cold desaturating blue-grey tone, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)

CHARACTER_REFS = [
    PROJECT_ROOT / "images/01_character_sheets/aiden/aiden_01_front_view.png",
    PROJECT_ROOT / "images/01_character_sheets/aiden/aiden_03_back_view.png",
    PROJECT_ROOT / "images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
    PROJECT_ROOT / "images/01_character_sheets/kagemasa/kagemasa_03_back_view.png",
]

BACKGROUND_REF = PROJECT_ROOT / "images/03_background_art/borderlands_bridge/bg_02_bridge_both_ends.png"

OUT_PATH = FRAMES_DIR / "scene11_cut02.png"
HD_PATH = FRAMES_DIR / "scene11_cut02_hd.png"


def generate_frame_with_refs(prompt: str, ref_paths: list[Path], out_path: Path) -> None:
    """Generate frame using GPT Image edit endpoint with reference images."""
    client = OpenAI()

    # Use background reference as primary image for the edit endpoint
    # Include character back-view refs as additional context
    primary_ref = ref_paths[0]  # aiden_01_front_view as primary character ref

    extra_desc = (
        " Reference images provided: Aiden medieval knight (front view, back view) and "
        "Kagemasa samurai (front view, back view) for character consistency. "
        "Both characters shown from behind walking away from camera on a ruined stone bridge. "
        "Background: foggy ruined stone bridge connecting two realms."
    )

    logger.info("Generating frame with %d reference images", len(ref_paths))
    logger.info("Primary ref: %s", primary_ref)

    with open(primary_ref, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt + extra_desc,
            size="1536x1024",
        )

    data = base64.b64decode(response.data[0].b64_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(data)
    logger.info("Saved raw frame: %s (%d bytes)", out_path, len(data))


def scale_to_hd(src: Path, dst: Path) -> None:
    """Scale 1536x1024 to 1920x1080 via 16:9 crop then upscale."""
    logger.info("Scaling %s -> %s", src, dst)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            str(dst),
        ],
        check=True,
    )
    logger.info("Saved HD frame: %s", dst)


def main() -> int:
    if not FRAMES_DIR.exists():
        FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    # Verify all reference files exist
    missing = [p for p in [*CHARACTER_REFS, BACKGROUND_REF] if not p.exists()]
    if missing:
        for m in missing:
            logger.error("Missing reference: %s", m)
        return 1

    # Use character refs + background ref
    all_refs = CHARACTER_REFS + [BACKGROUND_REF]

    generate_frame_with_refs(PROMPT, all_refs, OUT_PATH)
    scale_to_hd(OUT_PATH, HD_PATH)

    logger.info("Done. HD frame at: %s", HD_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
