"""Generate scene12_cut01 frame image using GPT Image generate endpoint."""
import base64
import os
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

PROMPT = (
    "Cinematic extreme wide static shot, locked off, both ends of a ruined stone bridge visible, "
    "Aiden (medieval knight in dark steel partial plate armor with chain mail, longsword sheathed on back) "
    "walking away left into fog, Kagemasa (samurai in deep navy oyoroi armor with gold imperial crest, "
    "nodachi sheathed) walking away right into fog, two silhouettes diverging symmetrically, "
    "heavy fog swallowing both figures, desaturated blue-grey tone, overcast sky, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)

OUTPUT_BASE = Path("/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene12_cut01.png")
OUTPUT_HD = Path("/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene12_cut01_hd.png")


def generate_frame(prompt: str, out_path: Path) -> None:
    client = OpenAI()
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1536x1024",
        quality="high",
        n=1,
    )
    data = base64.b64decode(response.data[0].b64_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Saved: {out_path}", file=sys.stderr)


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
    print(f"HD saved: {dst}", file=sys.stderr)


def main() -> None:
    generate_frame(PROMPT, OUTPUT_BASE)
    scale_to_hd(OUTPUT_BASE, OUTPUT_HD)
    print("DONE:scene12_cut01")


if __name__ == "__main__":
    main()
