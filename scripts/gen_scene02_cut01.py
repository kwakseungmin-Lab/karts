#!/usr/bin/env python3
"""Generate scene02_cut01 frame using GPT Image edit endpoint with character references."""

import base64
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("/Users/ksm2761/karts/.env")

PROJECT_ROOT = Path("/Users/ksm2761/karts/short-film-project")
OUTPUT_DIR = PROJECT_ROOT / "final/frames"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_OUT = OUTPUT_DIR / "scene02_cut01.png"
HD_OUT = OUTPUT_DIR / "scene02_cut01_hd.png"

PROMPT = (
    "Cinematic low angle wide shot, Blackstone Legion camp at night in rain, "
    "Gothic castle wall looming behind, torches and campfire flickering in downpour, "
    "Black commander in dark full plate armor with wolf-crest helmet stands at map table, "
    "flanked by 5 armored soldiers, chiaroscuro torchlight against blue-cold rain. "
    "Aiden (medieval knight in dark steel partial plate armor with chain mail, "
    "scarred face, brown hair, longsword with runic engravings) stands as dark silhouette "
    "at frame edge, back to torchlight. Highly desaturated — warm orange torchlight only color, "
    "rain steam rising from fires. For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)

CHARACTER_REFS = [
    PROJECT_ROOT / "images/01_character_sheets/aiden/aiden_01_front_view.png",
    PROJECT_ROOT / "images/01_character_sheets/aiden/aiden_02_three_quarter_view.png",
]

BACKGROUND_REF = PROJECT_ROOT / "images/03_background_art/ashfeld/bg_04_ashfeld_night_camp.png"


def generate_frame_with_refs(prompt: str, ref_paths: list[Path], out_path: Path) -> None:
    client = OpenAI()

    # Use the first character reference as the primary image input
    primary_ref = ref_paths[0]
    extra_desc = (
        " Reference images provided for character consistency. "
        "Maintain exact character appearance from reference sheets."
    )

    with open(primary_ref, "rb") as img_f:
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
    # Verify all reference files exist
    all_refs = CHARACTER_REFS + [BACKGROUND_REF]
    for ref in all_refs:
        if not ref.exists():
            print(f"WARNING: Reference not found: {ref}", file=sys.stderr)

    # Generate using character refs (edit endpoint)
    generate_frame_with_refs(PROMPT, CHARACTER_REFS, RAW_OUT)

    # Scale to HD
    scale_to_hd(RAW_OUT, HD_OUT)

    print(str(HD_OUT))


if __name__ == "__main__":
    main()
