"""Generate scene10_cut01 using GPT Image edit endpoint with character references."""

import base64
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

BASE = Path("/Users/ksm2761/karts/short-film-project")

CHARACTER_REFS = {
    "kagemasa_front": BASE / "images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
    "kagemasa_face": BASE / "images/01_character_sheets/kagemasa/kagemasa_04_face_without_mask.png",
    "aiden_front": BASE / "images/01_character_sheets/aiden/aiden_01_front_view.png",
}

BACKGROUND_REF = BASE / "images/03_background_art/borderlands_bridge/bg_02_bridge_both_ends.png"

OUT_RAW = BASE / "final/frames/scene10_cut01.png"
OUT_HD = BASE / "final/frames/scene10_cut01_hd.png"

PROMPT = (
    "Cinematic medium shot slow tilt-up, Kagemasa samurai in deep navy oyoroi armor with gold "
    "imperial crest, wide shoulder sode, nodachi sword with cherry blossom tsuba, bare face "
    "revealed — 40s man with topknot black hair, deep calm eyes, rising from one knee using "
    "nodachi as support, Aiden medieval knight in dark steel partial plate armor with chain mail, "
    "scarred face brown hair, stepping back one pace to give space, ruined stone bridge "
    "background, soft warm morning sunlight, fog almost cleared, brightest moment of the film, "
    "natural color saturation, For Honor cinematic trailer style, photorealistic, 1920x1080 16:9. "
    "Character reference images provided: maintain exact facial features, armor design, and "
    "proportions for both Kagemasa (Japanese samurai) and Aiden (medieval knight)."
)


def generate_frame_with_refs(
    prompt: str,
    ref_paths: list[Path],
    out_path: Path,
) -> None:
    """Generate frame using GPT Image edit endpoint with reference images."""
    client = OpenAI()

    # Use kagemasa_face as the primary reference (bare face revealed is key to this cut)
    primary_ref = ref_paths[0]
    print(f"Primary reference: {primary_ref}")
    print(f"Additional refs: {[str(p) for p in ref_paths[1:]]}")

    extra_refs_desc = (
        " Additional character references: "
        "kagemasa_04_face_without_mask.png (bare face, 40s Japanese man, topknot black hair, "
        "deep calm eyes), "
        "kagemasa_01_front_view.png (deep navy oyoroi armor, gold crest, wide sode pauldrons), "
        "aiden_01_front_view.png (dark steel partial plate, chain mail, scarred face, brown hair). "
        "Maintain strict visual consistency with these character sheets."
    )

    with open(primary_ref, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt + extra_refs_desc,
            size="1536x1024",
        )

    data = base64.b64decode(response.data[0].b64_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Saved raw: {out_path}")


def scale_to_hd(src: Path, dst: Path) -> None:
    """Scale 1536x1024 -> 16:9 crop (1536x864) -> 1920x1080."""
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
    print(f"Saved HD: {dst}")


def main() -> None:
    ref_paths = [
        CHARACTER_REFS["kagemasa_face"],   # primary: bare face close match
        CHARACTER_REFS["kagemasa_front"],  # secondary: full armor reference
        CHARACTER_REFS["aiden_front"],     # tertiary: Aiden armor reference
        BACKGROUND_REF,                   # background reference
    ]

    # Verify all refs exist
    for p in ref_paths:
        if not p.exists():
            print(f"ERROR: Reference not found: {p}", file=sys.stderr)
            sys.exit(1)

    print("Generating scene10_cut01 with GPT Image edit endpoint...")
    generate_frame_with_refs(PROMPT, ref_paths, OUT_RAW)

    print("Scaling to 1920x1080 HD...")
    scale_to_hd(OUT_RAW, OUT_HD)

    print(f"Done. Output: {OUT_HD}")


if __name__ == "__main__":
    main()
