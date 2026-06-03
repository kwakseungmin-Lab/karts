"""Generate scene11_cut03 frame using GPT Image generate endpoint (refs not available on disk)."""

import base64
import os
import subprocess

from openai import OpenAI

PROMPT = (
    "Cinematic over-the-shoulder shot transitioning into cross-cut close-ups. "
    "First frame: over Aiden's shoulder — dark steel partial plate armor with chain mail, "
    "looking back across the empty ruined stone bridge at the small distant silhouette of "
    "Kagemasa in deep navy oyoroi armor also turned back. "
    "Second frame cross-cut: Kagemasa's face extreme close-up, 40s samurai, black topknot, "
    "deep calm eyes locking gaze across the distance. "
    "Third frame: Aiden's face extreme close-up, scarred knight face, brown hair, "
    "eyes meeting in silent recognition. "
    "Final wide: both figures frozen mid-turn on opposite ends of bridge, fog between them, "
    "cold desaturated blue-grey, morning overcast light, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)

OUT_RAW = "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene11_cut03.png"
OUT_HD = "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene11_cut03_hd.png"


def generate_frame(prompt: str, out_path: str) -> None:
    client = OpenAI()
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
    print(f"Saved raw frame: {out_path}")


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
    print(f"Saved HD frame: {dst}")


if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY environment variable not set")

    generate_frame(PROMPT, OUT_RAW)
    scale_to_hd(OUT_RAW, OUT_HD)
    print("DONE:scene11_cut03")
