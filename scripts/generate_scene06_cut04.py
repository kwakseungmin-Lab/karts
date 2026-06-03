"""Generate scene06_cut04 frame using GPT Image edit endpoint with character refs."""
import base64
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

BASE = Path("/Users/ksm2761/karts/short-film-project")
OUT_DIR = BASE / "final" / "frames"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROMPT = (
    "Cinematic medium 360-degree tracking shot, Kagemasa samurai in deep navy oyoroi armor "
    "with wide shoulder sode presses forward with long nodachi sweeping strikes, "
    "Aiden medieval knight in dark steel partial plate armor retreats parrying desperately, "
    "stone bridge railing visible behind Aiden, morning light glinting on blades, "
    "slightly warmer tone with residual fog wisps on bridge, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080, 16:9 composition. "
    "Reference images provided for character consistency: "
    "Kagemasa wears deep navy oyoroi Japanese armor with wide shoulder sode plates and carries a long nodachi; "
    "Aiden wears dark steel medieval partial plate armor."
)

CHARACTER_REFS = [
    BASE / "images/01_character_sheets/aiden/aiden_01_front_view.png",
    BASE / "images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
    BASE / "images/01_character_sheets/kagemasa/kagemasa_06_nodachi_detail.png",
]
BACKGROUND_REF = BASE / "images/03_background_art/borderlands_bridge/bg_03_bridge_detail_ruins.png"

RAW_OUT = OUT_DIR / "scene06_cut04.png"
HD_OUT = OUT_DIR / "scene06_cut04_hd.png"


def generate_frame_with_refs(
    prompt: str,
    ref_paths: list[Path],
    out_path: Path,
) -> None:
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
    out_path.write_bytes(data)
    print(f"Saved raw frame: {out_path}", flush=True)


def scale_to_hd(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            str(dst),
        ],
        check=True,
    )
    print(f"Saved HD frame: {dst}", flush=True)


def main() -> None:
    all_refs = CHARACTER_REFS + [BACKGROUND_REF]
    generate_frame_with_refs(PROMPT, all_refs, RAW_OUT)
    scale_to_hd(RAW_OUT, HD_OUT)


if __name__ == "__main__":
    main()
