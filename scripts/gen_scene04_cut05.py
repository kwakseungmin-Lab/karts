"""Generate scene04_cut05 frame using GPT Image edit endpoint with character refs."""

import base64
import subprocess
from pathlib import Path

from openai import OpenAI

PROJECT_ROOT = Path("/Users/ksm2761/karts/short-film-project")
FRAMES_DIR = PROJECT_ROOT / "final" / "frames"

PROMPT = (
    "Cinematic extreme close-up split insert, left frame: gauntleted hand resting on nodachi "
    "scabbard with cherry blossom tsuba detail, deep navy lacquered sheath, right frame: "
    "longsword blade slowly drawing from scabbard, faint runic engraving catching diffuse fog "
    "light, blue-grey desaturated, metallic gleam, tense stillness before combat, For Honor "
    "cinematic trailer style, photorealistic, 1920x1080, 16:9 composition"
)

REF_PATHS = [
    PROJECT_ROOT / "images/01_character_sheets/aiden/aiden_06_sword_detail.png",
    PROJECT_ROOT / "images/01_character_sheets/kagemasa/kagemasa_06_nodachi_detail.png",
    PROJECT_ROOT / "images/03_background_art/borderlands_bridge/bg_03_bridge_detail_ruins.png",
]

OUT_RAW = FRAMES_DIR / "scene04_cut05.png"
OUT_HD = FRAMES_DIR / "scene04_cut05_hd.png"


def generate_frame_with_refs(prompt: str, ref_paths: list[Path], out_path: Path) -> None:
    client = OpenAI()
    extra_desc = " Reference images provided for character consistency." if len(ref_paths) > 1 else ""

    with open(ref_paths[0], "rb") as img_f:
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
    print(f"Saved raw frame: {out_path}")


def scale_to_hd(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            str(dst),
        ],
        check=True,
    )
    print(f"Saved HD frame: {dst}")


if __name__ == "__main__":
    for ref in REF_PATHS:
        if not ref.exists():
            raise FileNotFoundError(f"Reference image not found: {ref}")

    generate_frame_with_refs(PROMPT, REF_PATHS, OUT_RAW)
    scale_to_hd(OUT_RAW, OUT_HD)
    print("Done.")
