"""Generate scene10_cut04 — insert shot with insert_ref + character_ref (nodachi detail)."""

import base64
import os
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

# Load API key from .env if not already set
_env_file = Path("/Users/ksm2761/karts/.env")
if _env_file.exists() and not os.environ.get("OPENAI_API_KEY"):
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _val = _line.partition("=")
            os.environ.setdefault(_key.strip(), _val.strip())

PROMPT = (
    "Extreme close-up insert shot, cherry blossom tsuba (handguard) of nodachi sword clicking "
    "into scabbard mouth, warm golden morning light reflecting off polished steel and lacquered "
    "scabbard, cherry blossom engraving detail visible, soft bokeh background, symbol of peace "
    "and honor restored, For Honor cinematic style, photorealistic, 1920x1080 16:9"
)

BASE = "/Users/ksm2761/karts/short-film-project"
INSERT_REF = f"{BASE}/images/05_cuts/action_cuts/cut_08_cherry_blossom_tsuba.png"
CHAR_REF = f"{BASE}/images/01_character_sheets/kagemasa/kagemasa_06_nodachi_detail.png"
OUT_RAW = f"{BASE}/final/frames/scene10_cut04.png"
OUT_HD = f"{BASE}/final/frames/scene10_cut04_hd.png"


def generate_frame_with_refs(prompt: str, ref_path: str, out_path: str) -> None:
    client = OpenAI()
    with open(ref_path, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt,
            size="1536x1024",
        )
    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Saved raw: {out_path}")


def scale_to_hd(src: str, dst: str) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", src,
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            dst,
        ],
        check=True,
    )
    print(f"Saved HD: {dst}")


if __name__ == "__main__":
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    # insert_ref exists → use it as the primary reference image for the edit endpoint.
    # The character_ref (nodachi detail) is folded into the prompt as textual guidance.
    augmented_prompt = (
        PROMPT
        + " Reference: kagemasa nodachi sword — long curved blade with cherry blossom engraving "
          "on tsuba, black lacquered scabbard (saya) with gold cherry blossom motif."
    )

    generate_frame_with_refs(augmented_prompt, INSERT_REF, OUT_RAW)
    scale_to_hd(OUT_RAW, OUT_HD)
    print("Done.")
