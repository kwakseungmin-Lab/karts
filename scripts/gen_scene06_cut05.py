"""Generate scene06_cut05 frame using GPT Image edit endpoint with character references."""

import base64
import os
import subprocess

from dotenv import load_dotenv

load_dotenv("/Users/ksm2761/karts/.env")

from openai import OpenAI  # noqa: E402

client = OpenAI()

BASE = "/Users/ksm2761/karts/short-film-project"

REF_PATHS = [
    f"{BASE}/images/01_character_sheets/aiden/aiden_01_front_view.png",
    f"{BASE}/images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
    f"{BASE}/images/01_character_sheets/kagemasa/kagemasa_05_armor_detail.png",
    f"{BASE}/images/03_background_art/borderlands_bridge/bg_01_bridge_foggy_morning.png",
]

PROMPT = (
    "Cinematic medium close-up POV feint shot on a stone bridge in fog, "
    "Aiden — a medieval knight in dark steel partial plate armor — feints high "
    "with a longsword bearing runic engravings then drops low to slash; "
    "Kagemasa — a samurai in deep navy oyoroi armor — reacts too late, "
    "sword blade grazes his thigh armor plate causing first blood — "
    "a vivid red streak on the deep navy armor is the ONLY saturated color; "
    "Kagemasa steps back to regroup. "
    "Cool blue-grey desaturated cinematic tone, blood red accent only. "
    "For Honor cinematic trailer style, photorealistic, 16:9 composition."
    " [Character reference images supplied for consistency: Aiden knight, "
    "Kagemasa samurai front view, Kagemasa armor detail.]"
)

OUT_RAW = f"{BASE}/final/frames/scene06_cut05.png"
OUT_HD = f"{BASE}/final/frames/scene06_cut05_hd.png"


def generate_frame_with_refs(prompt: str, ref_paths: list[str], out_path: str) -> None:
    """Generate frame via GPT Image edit endpoint using first ref as primary input."""
    primary_ref = ref_paths[0]
    print(f"[generate] primary_ref={primary_ref}")
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
    print(f"[generate] saved raw: {out_path} ({len(data):,} bytes)")


def scale_to_hd(src: str, dst: str) -> None:
    """Scale 1536x1024 -> crop 1536x864 (16:9) -> 1920x1080 via lanczos."""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            src,
            "-vf",
            "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            dst,
        ],
        check=True,
    )
    print(f"[scale] saved HD: {dst}")


if __name__ == "__main__":
    generate_frame_with_refs(PROMPT, REF_PATHS, OUT_RAW)
    scale_to_hd(OUT_RAW, OUT_HD)
    print("Done.")
