"""Generate scene04_cut06 frame image using GPT Image gpt-image-1."""
import base64
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Load .env — search upward from cwd
_env_path = Path("/Users/ksm2761/karts/.env")
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()

PROMPT = (
    "Cinematic medium close-up low angle, stone bridge surface level, "
    "two sets of armored boots stepping forward onto moss-covered ruined stone bridge, "
    "left: dark steel sabatons of Aiden, medieval knight, "
    "right: deep navy lacquered armored waraji sandals of Kagemasa, samurai kensei, "
    "each taking one deliberate step toward each other, "
    "fog-filled bridge gap between them, "
    "blue-grey desaturated, For Honor cinematic trailer style, photorealistic, "
    "1920x1080, 16:9 composition"
)

BASE_DIR = Path("/Users/ksm2761/karts/vimax/short-film-project")
FRAMES_DIR = BASE_DIR / "final" / "frames"
RAW_OUT = FRAMES_DIR / "scene04_cut06.png"
HD_OUT = FRAMES_DIR / "scene04_cut06_hd.png"

REF_PATHS = [
    BASE_DIR / "images/01_character_sheets/aiden/aiden_01_front_view.png",
    BASE_DIR / "images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
]
BG_REF = BASE_DIR / "images/03_background_art/borderlands_bridge/bg_03_bridge_detail_ruins.png"


def generate_with_ref(client: OpenAI, ref_path: Path) -> bytes:
    """Use edit endpoint with a single reference image."""
    with open(ref_path, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=PROMPT + " Reference image provided for character/environment consistency.",
            size="1536x1024",
        )
    return base64.b64decode(response.data[0].b64_json)


def generate_without_ref(client: OpenAI) -> bytes:
    """Use generate endpoint when no refs are available."""
    response = client.images.generate(
        model="gpt-image-1",
        prompt=PROMPT,
        size="1536x1024",
        quality="high",
        n=1,
    )
    return base64.b64decode(response.data[0].b64_json)


def scale_to_hd(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "scale=1920:1080:flags=lanczos,setsar=1",
            "-pix_fmt", "yuv420p",
            str(dst),
        ],
        check=True,
    )


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    # Determine which ref images are available
    available_refs = [p for p in REF_PATHS if p.exists()]
    bg_available = BG_REF.exists()

    if available_refs:
        print(f"Using edit endpoint with ref: {available_refs[0]}")
        data = generate_with_ref(client, available_refs[0])
    elif bg_available:
        print(f"Using edit endpoint with bg ref: {BG_REF}")
        data = generate_with_ref(client, BG_REF)
    else:
        print("No ref images found — using generate endpoint")
        data = generate_without_ref(client)

    RAW_OUT.write_bytes(data)
    print(f"Saved raw: {RAW_OUT}")

    scale_to_hd(RAW_OUT, HD_OUT)
    print(f"Saved HD: {HD_OUT}")
    print("DONE:scene04_cut06")


if __name__ == "__main__":
    main()
