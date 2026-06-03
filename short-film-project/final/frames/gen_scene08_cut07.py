"""Generate scene08_cut07 frame using GPT Image generate endpoint (no refs available)."""

import base64
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("/Users/ksm2761/karts/.env")

PROMPT = (
    "For Honor cinematic trailer style, whip-pan tracking shot of intense breathtaking sword "
    "exchange between two warriors on a ruined stone bridge. Aiden — medieval knight in battered "
    "dark steel partial plate armor with chain mail, scarred face, brown hair, longsword with "
    "runic engravings — and Kagemasa — samurai in deep navy oyoroi armor with cracked gold "
    "imperial crest menpou mask, wide shoulder sode, nodachi with cherry blossom tsuba — locked "
    "in a rapid flurry of parry-riposte-parry chain. Both warriors bloodied but unyielding, eyes "
    "locked with fierce intensity. Dynamic blade clashes send sparks arcing through morning light, "
    "steel ringing off steel in rapid succession. Recovering saturation, warm morning side-light "
    "glinting off steel, dust and debris scattered by the force of their strikes. Camera whips "
    "and cuts between tight angles capturing the blur of motion. Photorealistic, 1920x1080, "
    "16:9 composition"
)

OUT_RAW = "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene08_cut07.png"
OUT_HD = "/Users/ksm2761/karts/vimax/short-film-project/final/frames/scene08_cut07_hd.png"


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
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    generate_frame(PROMPT, OUT_RAW)
    scale_to_hd(OUT_RAW, OUT_HD)
    print("DONE:scene08_cut07")
