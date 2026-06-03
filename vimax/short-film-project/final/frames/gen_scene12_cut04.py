"""Generate scene12_cut04 frame using GPT Image generate endpoint."""
import base64
import subprocess
import sys
from pathlib import Path

from openai import OpenAI


PROMPT = (
    "Cinematic ultra-wide aerial bird's eye view, extreme pull-back reveal, "
    "Heathmoor landscape, ancient stone bridge tiny in center frame, "
    "left hill silhouettes of knight army marching (Iron Legion banners), "
    "right hill silhouettes of samurai army advancing (Dawn Empire banners), "
    "fog filling the valley between, overcast grey sky, crows circling above, "
    "two armies converging toward the same bridge, desaturated blue-grey, "
    "epic and tragic, For Honor cinematic trailer style, photorealistic, "
    "1920x1080 16:9"
)

OUT_DIR = Path("/Users/ksm2761/karts/vimax/short-film-project/final/frames")
RAW_PATH = OUT_DIR / "scene12_cut04.png"
HD_PATH = OUT_DIR / "scene12_cut04_hd.png"


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
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Raw image saved: {out_path}", file=sys.stderr)


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
    print(f"HD image saved: {dst}", file=sys.stderr)


def main() -> None:
    generate_frame(PROMPT, RAW_PATH)
    scale_to_hd(RAW_PATH, HD_PATH)
    print("DONE:scene12_cut04")


if __name__ == "__main__":
    main()
