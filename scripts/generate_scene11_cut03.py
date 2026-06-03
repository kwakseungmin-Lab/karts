"""Generate scene11_cut03 frame using GPT Image edit endpoint with character references."""

import base64
import subprocess
from pathlib import Path

from openai import OpenAI

BASE = Path("/Users/ksm2761/karts/short-film-project")
FRAMES_DIR = BASE / "final/frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

client = OpenAI()

PROMPT = (
    "Cinematic over-the-shoulder shot transitioning into cross-cut close-ups. "
    "First frame: over Aiden's shoulder — dark steel partial plate armor with chain mail, "
    "looking back across the empty ruined stone bridge at the small distant silhouette of "
    "Kagemasa in deep navy oyoroi armor also turned back. Cross-cut close-up: Kagemasa's face, "
    "40s samurai with black topknot, deep calm eyes locking gaze across the distance. "
    "Then Aiden's face extreme close-up, scarred knight, vertical scar above left eye, "
    "brown hair, eyes meeting in silent recognition. Final wide: both figures frozen mid-turn "
    "on opposite ends of bridge, fog between them, cold desaturated blue-grey, morning overcast light, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9. "
    "Reference images provided for character consistency."
)

CHARACTER_REFS = [
    BASE / "images/01_character_sheets/aiden/aiden_02_three_quarter_view.png",
    BASE / "images/01_character_sheets/aiden/aiden_04_face_closeup.png",
    BASE / "images/01_character_sheets/kagemasa/kagemasa_02_three_quarter_view.png",
    BASE / "images/01_character_sheets/kagemasa/kagemasa_04_face_without_mask.png",
]

BACKGROUND_REF = BASE / "images/03_background_art/borderlands_bridge/bg_02_bridge_both_ends.png"

OUT_RAW = FRAMES_DIR / "scene11_cut03.png"
OUT_HD = FRAMES_DIR / "scene11_cut03_hd.png"


def generate_frame_with_refs(prompt: str, ref_paths: list[Path], out_path: Path) -> None:
    """Generate frame using GPT Image edit endpoint with character reference as primary image."""
    primary_ref = ref_paths[0]
    print(f"Using primary reference: {primary_ref.name}")
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
    """Scale 1536x1024 to 1920x1080 via 16:9 crop then lanczos upscale."""
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
    print("Generating scene11_cut03 with character references...")
    generate_frame_with_refs(PROMPT, CHARACTER_REFS, OUT_RAW)
    print("Scaling to 1920x1080...")
    scale_to_hd(OUT_RAW, OUT_HD)
    print("Done.")


if __name__ == "__main__":
    main()
