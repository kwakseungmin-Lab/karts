"""Generate scene07_cut05 frame using GPT Image edit endpoint with character refs."""
import base64
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("/Users/ksm2761/karts/.env")

PROMPT = (
    "Cinematic wide static shot pulling back to reveal full ruined stone bridge, "
    "Aiden (medieval knight in dark steel partial plate armor with chain mail) and "
    "Kagemasa (samurai in deep navy oyoroi armor) standing 5 meters apart — neither "
    "sheathing their weapons but neither advancing, the vast silent bridge between them "
    "loaded with unspoken recognition, morning fog half-cleared revealing the bridge's "
    "damaged stonework, two civilizations' warrior traditions facing each other in "
    "suspended tension, contemplative and still, For Honor cinematic trailer style, "
    "photorealistic, 1920x1080 16:9"
)

AIDEN_REF = Path(
    "/Users/ksm2761/karts/short-film-project/images/01_character_sheets/aiden/aiden_01_front_view.png"
)
KAGEMASA_REF = Path(
    "/Users/ksm2761/karts/short-film-project/images/01_character_sheets/kagemasa/kagemasa_01_front_view.png"
)
BG_REF = Path(
    "/Users/ksm2761/karts/short-film-project/images/03_background_art/borderlands_bridge/bg_02_bridge_both_ends.png"
)

OUT_RAW = Path("/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene07_cut05.png")
OUT_HD = Path(
    "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene07_cut05_hd.png"
)


def generate_frame_with_refs(
    prompt: str,
    ref_paths: list[Path],
    out_path: Path,
) -> None:
    client = OpenAI()

    extra_desc = (
        " Maintain exact character appearances from reference images. "
        "Aiden wears dark steel partial plate armor with chain mail. "
        "Kagemasa wears deep navy oyoroi samurai armor with face mask. "
        "Background: ruined stone bridge with morning fog. Reference images provided for character consistency."
    )

    # Use the first ref as primary image; additional refs described in prompt
    with open(ref_paths[0], "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt + extra_desc,
            size="1536x1024",
        )

    data = base64.b64decode(response.data[0].b64_json)
    out_path.write_bytes(data)
    print(f"Saved raw frame: {out_path}", flush=True)


def scale_to_hd(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-vf",
            "scale=1920:1080:flags=lanczos,setsar=1",
            "-pix_fmt",
            "yuv420p",
            str(dst),
        ],
        check=True,
    )
    print(f"Saved HD frame: {dst}", flush=True)


def main() -> None:
    ref_paths = [AIDEN_REF, KAGEMASA_REF, BG_REF]
    for p in ref_paths:
        if not p.exists():
            print(f"ERROR: ref not found: {p}", file=sys.stderr)
            sys.exit(1)

    generate_frame_with_refs(PROMPT, ref_paths, OUT_RAW)
    scale_to_hd(OUT_RAW, OUT_HD)
    print("DONE:scene07_cut05")


if __name__ == "__main__":
    main()
