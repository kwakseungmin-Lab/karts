"""Generate scene10_cut03 frame using GPT Image generate endpoint."""

import base64
import os
import subprocess

from openai import OpenAI

client = OpenAI()

PROMPT = (
    "Cinematic medium close-up, Kagemasa samurai in deep navy oyoroi armor sheathing his nodachi sword "
    "with cherry blossom tsuba, deliberate slow motion of blade entering lacquered scabbard, "
    "gentle golden morning light catching the blade edge, Aiden medieval knight in dark steel partial "
    "plate armor watching in background, ruined stone bridge, warmest color temperature of entire film, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)

OUT_DIR = "/Users/ksm2761/karts/vimax/short-film-project/final/frames"
RAW_OUT = os.path.join(OUT_DIR, "scene10_cut03.png")
HD_OUT = os.path.join(OUT_DIR, "scene10_cut03_hd.png")


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


def scale_to_hd(src: str, dst: str) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            src,
            "-vf",
            "scale=1920:1080:flags=lanczos,setsar=1",
            "-pix_fmt",
            "yuv420p",
            dst,
        ],
        check=True,
    )


if __name__ == "__main__":
    print("Generating scene10_cut03 raw frame (1536x1024)...", flush=True)
    generate_frame(PROMPT, RAW_OUT)
    print(f"Raw frame saved: {RAW_OUT}", flush=True)

    print("Scaling to 1920x1080 HD...", flush=True)
    scale_to_hd(RAW_OUT, HD_OUT)
    print(f"HD frame saved: {HD_OUT}", flush=True)

    print("DONE:scene10_cut03", flush=True)
