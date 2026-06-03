"""Generate scene04_cut02 frame using GPT Image edit endpoint with character references."""

import base64
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

BASE_DIR = Path("/Users/ksm2761/karts/short-film-project")
OUT_DIR = BASE_DIR / "final/frames"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROMPT = (
    "Cinematic telephoto medium shot 200mm, Aiden, medieval knight in dark steel partial plate armor "
    "with chain mail, scarred face, brown hair, longsword with runic engravings, figure emerging from "
    "thick morning fog onto ruined stone bridge, slow deliberate walk coming to a stop at bridge entrance, "
    "blue-grey desaturated atmosphere, armor surface gleaming faintly through fog, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080, 16:9 composition. "
    "Reference images provided for character consistency."
)

CHARACTER_REFS = [
    BASE_DIR / "images/01_character_sheets/aiden/aiden_01_front_view.png",
    BASE_DIR / "images/01_character_sheets/aiden/aiden_02_three_quarter_view.png",
]

BACKGROUND_REF = BASE_DIR / "images/03_background_art/borderlands_bridge/bg_02_bridge_both_ends.png"

OUT_RAW = OUT_DIR / "scene04_cut02.png"
OUT_HD  = OUT_DIR / "scene04_cut02_hd.png"


def generate_frame_with_refs(prompt: str, ref_paths: list, out_path: Path) -> None:
    client = OpenAI()

    # Use the first character reference as the primary image for edit endpoint.
    # Additional references are described in the prompt for style/appearance consistency.
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
    print(f"Saved raw frame: {out_path}")


def scale_to_hd(src: Path, dst: Path) -> None:
    # 1536x1024 → crop to 16:9 (1536x864, centered) → scale to 1920x1080
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            str(dst),
        ],
        check=True,
    )
    print(f"Saved HD frame: {dst}")


def main() -> None:
    print("Generating scene04_cut02 with character references via GPT Image edit endpoint...")
    generate_frame_with_refs(PROMPT, CHARACTER_REFS, OUT_RAW)
    print("Scaling to 1920x1080...")
    scale_to_hd(OUT_RAW, OUT_HD)
    print("Done.")


if __name__ == "__main__":
    main()
