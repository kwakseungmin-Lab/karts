#!/usr/bin/env python3
"""Generate scene01_cut02 frame image using GPT Image edit endpoint."""
import base64
import os
import subprocess
from pathlib import Path
from openai import OpenAI


def _load_env(env_path: str) -> None:
    """Load KEY=VALUE pairs from an env file into os.environ."""
    for line in Path(env_path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    _load_env("/Users/ksm2761/karts/.env")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    client = OpenAI(api_key=api_key)

    base_dir = "/Users/ksm2761/karts"
    insert_ref = f"{base_dir}/short-film-project/images/05_cuts/action_cuts/cut_10_crow_blade.png"
    out_path = f"{base_dir}/short-film-project/final/frames/scene01_cut02.png"
    hd_path = f"{base_dir}/short-film-project/final/frames/scene01_cut02_hd.png"

    prompt = (
        "Cinematic extreme close-up macro shot, a single crow perched on a rusted medieval sword blade "
        "half-buried in mud, desaturated near-grayscale, single black feather trembling in slight wind, "
        "rust and old blood on blade surface, shallow depth of field, For Honor cinematic style, "
        "photorealistic, 1920x1080, 16:9 composition"
    )

    print(f"Generating image with insert ref: {insert_ref}")
    with open(insert_ref, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt,
            size="1536x1024",
        )

    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Saved original: {out_path} ({len(data)} bytes)")

    # Scale 1536x1024 -> 16:9 crop (1536x864) -> 1920x1080
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", out_path,
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            hd_path,
        ],
        check=True,
    )
    print(f"Saved HD: {hd_path}")


if __name__ == "__main__":
    main()
