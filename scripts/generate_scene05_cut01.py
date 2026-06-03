"""
Generate scene05_cut01 frame using GPT Image edit endpoint with character references.
Characters: Aiden (left) + Kagemasa (right) on ruined bridge at dawn.
"""

import base64
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

PROJECT_ROOT = Path("/Users/ksm2761/karts/short-film-project")

AIDEN_REF = PROJECT_ROOT / "images/01_character_sheets/aiden/aiden_01_front_view.png"
KAGEMASA_REF = PROJECT_ROOT / "images/01_character_sheets/kagemasa/kagemasa_01_front_view.png"
BG_REF = PROJECT_ROOT / "images/03_background_art/borderlands_bridge/bg_01_bridge_foggy_morning.png"

OUT_RAW = PROJECT_ROOT / "final/frames/scene05_cut01.png"
OUT_HD = PROJECT_ROOT / "final/frames/scene05_cut01_hd.png"

PROMPT = (
    "Cinematic medium two-shot slightly low angle, on ancient ruined stone bridge at dawn, "
    "two warriors approaching center from opposite ends and halting simultaneously 5 meters apart. "
    "LEFT WARRIOR - Aiden: medieval knight in dark steel partial plate armor with chain mail, "
    "scarred face, brown hair, longsword with runic engravings raised into guard position. "
    "RIGHT WARRIOR - Kagemasa: samurai in deep navy oyoroi armor with gold imperial crest, "
    "wide shoulder sode, nodachi sword with cherry blossom tsuba held high in jodan upper stance. "
    "Morning fog partially lifting, faint oblique sunlight beginning to filter through mist, "
    "blue-grey desaturated atmosphere, both warriors locked in tense stillness, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080, 16:9 composition. "
    "Character reference images provided for consistency."
)


def generate_frame_with_refs(
    prompt: str,
    ref_paths: list[Path],
    out_path: Path,
) -> None:
    client = OpenAI()

    # Use the background reference as the primary edit base
    # and mention character references in the prompt
    primary_ref = ref_paths[0]
    print(f"Using primary reference: {primary_ref}")
    print(f"Additional references: {[str(p) for p in ref_paths[1:]]}")

    with open(primary_ref, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt,
            size="1536x1024",
        )

    raw_data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(raw_data)
    print(f"Saved raw image: {out_path} ({len(raw_data):,} bytes)")


def scale_to_hd(src: Path, dst: Path) -> None:
    # 1536×1024 → crop to 16:9 (1536×864, centered) → scale to 1920×1080
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
    print(f"Saved HD image: {dst}")


def main() -> int:
    ref_paths = [BG_REF, AIDEN_REF, KAGEMASA_REF]

    for ref in ref_paths:
        if not ref.exists():
            print(f"ERROR: reference file not found: {ref}", file=sys.stderr)
            return 1

    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)

    print("Generating scene05_cut01 via GPT Image edit endpoint...")
    generate_frame_with_refs(PROMPT, ref_paths, OUT_RAW)

    print("Scaling to 1920×1080...")
    scale_to_hd(OUT_RAW, OUT_HD)

    print(f"Done. Output: {OUT_HD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
