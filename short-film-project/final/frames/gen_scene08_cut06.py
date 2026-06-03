"""Generate scene08_cut06 frame using GPT Image generate endpoint."""

import base64
import logging
import os
import subprocess

from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROMPT = (
    "Cinematic low angle shot looking up at Aiden — medieval knight in dark steel partial plate "
    "armor with chain mail, scarred face, brown hair, longsword raised — standing over Kagemasa "
    "who has dropped to one knee on the stone bridge. Kagemasa — samurai in deep navy oyoroi "
    "armor, cracked menpou mask beginning to slip — is kneeling but undefeated in spirit. "
    "Dramatic power dynamic, Aiden silhouetted against bright morning sky, rim light along sword "
    "edge. Stone bridge ruins, morning light flooding scene, emotional climax building directly "
    "into scene 09. For Honor cinematic trailer style, photorealistic, 1920x1080, 16:9"
)

OUT_RAW = "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene08_cut06.png"
OUT_HD = "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene08_cut06_hd.png"


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
    logger.info("Saved raw frame: %s", out_path)


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
    logger.info("Saved HD frame: %s", dst)


if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY environment variable not set")

    generate_frame(PROMPT, OUT_RAW)
    scale_to_hd(OUT_RAW, OUT_HD)
    print("DONE:scene08_cut06")
