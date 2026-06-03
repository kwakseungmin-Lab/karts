"""Generate scene07_cut05 frame using GPT Image edit endpoint with character refs."""

import base64
import os
import subprocess
from pathlib import Path

from openai import OpenAI

# Load API key from .env if not already set
_env_file = Path("/Users/ksm2761/karts/.env")
if _env_file.exists() and not os.environ.get("OPENAI_API_KEY"):
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

PROJECT_ROOT = Path("/Users/ksm2761/karts/short-film-project")
FRAMES_DIR = PROJECT_ROOT / "final" / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

client = OpenAI()

PROMPT = (
    "Cinematic wide static shot pulling back to reveal full ruined stone bridge, "
    "Aiden (medieval knight in dark steel partial plate armor with chain mail) and "
    "Kagemasa (samurai in deep navy oyoroi armor) standing 5 meters apart — "
    "neither sheathing their weapons but neither advancing, the vast silent bridge "
    "between them loaded with unspoken recognition, morning fog half-cleared "
    "revealing the bridge's damaged stonework, two civilizations' warrior traditions "
    "facing each other in suspended tension, contemplative and still, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)

CHARACTER_REFS = [
    PROJECT_ROOT / "images/01_character_sheets/aiden/aiden_01_front_view.png",
    PROJECT_ROOT / "images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
]

BACKGROUND_REF = PROJECT_ROOT / "images/03_background_art/borderlands_bridge/bg_02_bridge_both_ends.png"

OUT_PATH = FRAMES_DIR / "scene07_cut05.png"
OUT_HD_PATH = FRAMES_DIR / "scene07_cut05_hd.png"


def generate_frame_with_refs(
    prompt: str,
    ref_paths: list[Path],
    out_path: Path,
) -> None:
    """Generate frame using edit endpoint with reference images."""
    # Use background ref as primary image since this is a transition (wide landscape shot)
    # and inject character refs as additional context in the prompt
    primary_ref = BACKGROUND_REF

    extra_context = (
        " Character reference: Aiden wears dark steel partial plate armor with chain mail "
        "(medieval knight style). Kagemasa wears deep navy oyoroi samurai armor. "
        "Both characters are shown in wide shot, small figures on the bridge. "
        "Reference images provided for character consistency."
    )

    with open(primary_ref, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt + extra_context,
            size="1536x1024",
        )

    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Saved: {out_path}")


def scale_to_hd(src: Path, dst: Path) -> None:
    """Scale 1536x1024 to 1920x1080 via 16:9 crop."""
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
    )
    print(f"HD saved: {dst}")


def main() -> None:
    print("Generating scene07_cut05 with character + background refs...")
    generate_frame_with_refs(PROMPT, CHARACTER_REFS, OUT_PATH)

    print("Scaling to 1920x1080...")
    scale_to_hd(OUT_PATH, OUT_HD_PATH)

    print("Done.")
    print(f"  Original: {OUT_PATH}")
    print(f"  HD:       {OUT_HD_PATH}")


if __name__ == "__main__":
    main()
