"""Generate scene01_cut03 frame using gpt-image-1 generate endpoint."""
import base64
import os
import subprocess
import sys
from openai import OpenAI

client = OpenAI()

PROMPT = (
    "Cinematic slow tracking wide shot, detailed medieval battlefield ruins at ground level, "
    "broken swords, torn flags, collapsed armor, shattered shields, all half-buried in mud and fog, "
    "extremely desaturated grayscale with only faint red and gold tones on weathered banners, "
    "overcast diffused lighting with no directional shadows, atmosphere of melancholy desolation, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080, 16:9 composition"
)

OUT_RAW = "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene01_cut03.png"
OUT_HD = "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene01_cut03_hd.png"


def generate_frame(prompt: str, out_path: str) -> None:
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1536x1024",
        quality="high",
        n=1,
    )
    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Saved raw: {out_path}", flush=True)


def scale_to_hd(src: str, dst: str) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", src,
            "-vf", "scale=1920:1080:flags=lanczos,setsar=1",
            "-pix_fmt", "yuv420p",
            dst,
        ],
        check=True,
    )
    print(f"Saved HD: {dst}", flush=True)


if __name__ == "__main__":
    generate_frame(PROMPT, OUT_RAW)
    scale_to_hd(OUT_RAW, OUT_HD)
    print("DONE:scene01_cut03")
