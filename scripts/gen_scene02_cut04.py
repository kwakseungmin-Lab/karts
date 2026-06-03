#!/usr/bin/env python3
"""Generate scene02_cut04 frame using GPT Image edit endpoint with character references."""

import base64
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Load .env from project root
load_dotenv(Path("/Users/ksm2761/karts/.env"))

PROJECT_ROOT = Path("/Users/ksm2761/karts/short-film-project")
OUTPUT_DIR = PROJECT_ROOT / "final/frames"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_OUT = OUTPUT_DIR / "scene02_cut04.png"
HD_OUT = OUTPUT_DIR / "scene02_cut04_hd.png"

PROMPT = (
    "Cinematic over-the-shoulder medium pull-back shot, Aiden (medieval knight in dark steel "
    "partial plate armor with chain mail, brown hair, longsword sheathed on back) turns away "
    "from the Blackstone commander and walks toward darkness beyond the camp. "
    "Camera slowly pulls back as Aiden recedes into shadow. Behind him the commander raises "
    "a flamberge sword in threat. Rain soaking everything, torchlight falls off as Aiden moves "
    "into darkness. Desaturated, chiaroscuro, dramatic. "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9. "
    "Reference images provided for character consistency. "
    "Maintain exact character appearance from reference sheets."
)

CHARACTER_REFS = [
    PROJECT_ROOT / "images/01_character_sheets/aiden/aiden_01_front_view.png",
    PROJECT_ROOT / "images/01_character_sheets/aiden/aiden_03_back_view.png",
]

BACKGROUND_REF = PROJECT_ROOT / "images/03_background_art/ashfeld/bg_04_ashfeld_night_camp.png"


def generate_frame_with_refs(prompt: str, ref_paths: list[Path], out_path: Path) -> None:
    client = OpenAI()

    primary_ref = ref_paths[0]

    with open(primary_ref, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt,
            size="1536x1024",
        )

    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Saved raw frame: {out_path}", file=sys.stderr)


def scale_to_hd(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            str(dst),
        ],
        check=True,
    )
    print(f"Saved HD frame: {dst}", file=sys.stderr)


def main() -> None:
    all_refs = CHARACTER_REFS + [BACKGROUND_REF]
    for ref in all_refs:
        if not ref.exists():
            print(f"WARNING: Reference not found: {ref}", file=sys.stderr)

    generate_frame_with_refs(PROMPT, CHARACTER_REFS, RAW_OUT)
    scale_to_hd(RAW_OUT, HD_OUT)

    print(str(HD_OUT))


if __name__ == "__main__":
    main()
