"""Generate scene06_cut03 frame using GPT Image edit endpoint with character refs."""

import base64
import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


PROJECT_ROOT = Path("/Users/ksm2761/karts/short-film-project")
FRAMES_DIR = PROJECT_ROOT / "final" / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

PROMPT = (
    "Cinematic medium handheld shot, Aiden medieval knight in dark steel partial plate armor "
    "with chain mail, scarred face, brown hair ducks under wide horizontal swing and drives "
    "shoulder into opponent, Kagemasa samurai in deep navy oyoroi armor stumbles back on ruined "
    "stone bridge, morning fog partially lifted, side light catching blade reflections, cool "
    "desaturated blue-grey tone with slight warmth entering from clearing fog, For Honor cinematic "
    "trailer style, photorealistic, 1920x1080, 16:9 composition. "
    "Maintain exact character appearances from reference images: Aiden (scarred face, brown hair, "
    "dark steel plate armor with chain mail) and Kagemasa (deep navy oyoroi samurai armor). "
    "Reference images provided for character consistency."
)

REF_PATHS = [
    PROJECT_ROOT / "images/01_character_sheets/aiden/aiden_01_front_view.png",
    PROJECT_ROOT / "images/01_character_sheets/aiden/aiden_04_face_closeup.png",
    PROJECT_ROOT / "images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
    PROJECT_ROOT / "images/03_background_art/borderlands_bridge/bg_02_bridge_both_ends.png",
]

OUT_RAW = FRAMES_DIR / "scene06_cut03.png"
OUT_HD = FRAMES_DIR / "scene06_cut03_hd.png"


def generate_frame_with_refs(prompt: str, ref_paths: list[Path], out_path: Path) -> None:
    from openai import OpenAI

    client = OpenAI()

    logger.info("Opening primary reference image: %s", ref_paths[0])
    with open(ref_paths[0], "rb") as img_f:
        logger.info("Calling GPT Image edit endpoint...")
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt,
            size="1536x1024",
        )

    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)
    logger.info("Saved raw frame: %s (%d bytes)", out_path, len(data))


def scale_to_hd(src: Path, dst: Path) -> None:
    logger.info("Scaling %s -> %s", src, dst)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            str(dst),
        ],
        check=True,
        capture_output=True,
    )
    logger.info("Saved HD frame: %s", dst)


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable is not set")
        sys.exit(1)

    for p in REF_PATHS:
        if not p.exists():
            logger.error("Reference image not found: %s", p)
            sys.exit(1)

    generate_frame_with_refs(PROMPT, REF_PATHS, OUT_RAW)
    scale_to_hd(OUT_RAW, OUT_HD)
    logger.info("Done. Output: %s", OUT_HD)


if __name__ == "__main__":
    main()
