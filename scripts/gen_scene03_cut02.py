"""Generate scene03 cut02 frame using GPT Image edit endpoint."""
import base64
import subprocess
import sys
from pathlib import Path

from openai import OpenAI


def generate_frame_with_refs(prompt: str, ref_path: str, out_path: str) -> None:
    """Generate frame using GPT Image edit endpoint with reference image."""
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
    print(f"Saved raw frame: {out_path}")


def scale_to_hd(src: str, dst: str) -> None:
    """Scale 1536x1024 to 1920x1080 via 16:9 crop then upscale."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", src,
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            dst,
        ],
        check=True,
    )
    print(f"Saved HD frame: {dst}")


def main() -> None:
    project_root = Path("/Users/ksm2761/karts/short-film-project")
    frames_dir = project_root / "final" / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    # insert_ref is the primary reference image (refined from existing cut)
    insert_ref = str(
        project_root / "images" / "05_cuts" / "action_cuts" / "cut_07_imperial_crest_flaking.png"
    )
    character_ref_desc = (
        "kagemasa_05_armor_detail.png reference: deep navy lacquered oyoroi armor with gold imperial crest detail."
    )

    prompt = (
        "Extreme close-up of Kagemasa's chest armor, deep navy lacquered oyoroi with gold imperial crest — "
        "gold flaking and worn from battle damage, snow crystals settling on the surface, cold blue light, "
        "desaturated, symbolic detail shot emphasizing duty and sacrifice, For Honor cinematic trailer style, "
        "photorealistic, 1920x1080 16:9. "
        f"Character armor reference: {character_ref_desc} "
        "Reference images provided for character consistency."
    )

    raw_path = str(frames_dir / "scene03_cut02.png")
    hd_path = str(frames_dir / "scene03_cut02_hd.png")

    print("Generating scene03_cut02 with GPT Image edit endpoint...")
    print(f"  insert_ref: {insert_ref}")
    generate_frame_with_refs(prompt, insert_ref, raw_path)

    print("Scaling to 1920x1080...")
    scale_to_hd(raw_path, hd_path)

    print("Done.")
    print(f"  Raw: {raw_path}")
    print(f"  HD:  {hd_path}")


if __name__ == "__main__":
    main()
