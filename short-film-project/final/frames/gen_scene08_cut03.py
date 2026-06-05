"""Generate scene08_cut03 frame using GPT Image generate endpoint (no refs available on disk)."""

import base64
import os
import subprocess

from openai import OpenAI

PROMPT = (
    "Cinematic slow-motion freeze frame then normal speed, Aiden — medieval knight in dark "
    "steel partial plate armor, scarred face, brown hair — drives shoulder into Kagemasa's "
    "guard break, then swings longsword crossguard directly into Kagemasa's menpou mask. "
    "Kagemasa — samurai in deep navy oyoroi armor, gold imperial crest, wide sode — staggers "
    "back, demon-face menpou mask visibly cracked from the impact. Extreme close-up insert of "
    "cracked menpou, then pull back to low-angle medium shot. Stone bridge ruins background, "
    "morning light, fog cleared. For Honor cinematic trailer style, photorealistic, 1920x1080, 16:9"
)

OUT_RAW = "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene08_cut03.png"
OUT_HD = "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene08_cut03_hd.png"


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
    print("DONE:scene08_cut03")
