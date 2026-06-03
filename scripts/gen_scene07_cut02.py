"""Generate scene07_cut02 — insert cut: Aiden's armor pauldron with defaced emblem."""
import base64
import os
import subprocess
from pathlib import Path

from openai import OpenAI

# Load API key from .env if not already set
_env_file = Path("/Users/ksm2761/karts/.env")
if _env_file.exists() and not os.environ.get("OPENAI_API_KEY"):
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

client = OpenAI()

PROMPT = (
    "Cinematic extreme close-up POV shot from Kagemasa's perspective, "
    "Aiden's left pauldron in dark steel partial plate armor, "
    "deep scratch marks carved into the metal surface where a Blackstone Legion emblem "
    "was deliberately defaced — gouged lines obliterating the crest, "
    "rust and battle damage around the scratches, morning light catching the grooves, "
    "symbolic detail, For Honor cinematic trailer style, photorealistic, 1920x1080 16:9. "
    "Reference the armor detail: dark steel pauldron with battle-worn surface texture."
)

INSERT_REF = Path(
    "/Users/ksm2761/karts/short-film-project/images/05_cuts/action_cuts/cut_06_scratch_mark_crest.png"
)
RAW_OUT = Path("/Users/ksm2761/karts/short-film-project/final/frames/scene07_cut02.png")
HD_OUT = Path("/Users/ksm2761/karts/short-film-project/final/frames/scene07_cut02_hd.png")


def generate_frame_with_ref(prompt: str, ref_path: Path, out_path: Path) -> None:
    with open(ref_path, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt,
            size="1536x1024",
        )
    data = base64.b64decode(response.data[0].b64_json)
    out_path.write_bytes(data)
    print(f"Raw image saved: {out_path} ({len(data)} bytes)")


def scale_to_hd(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            str(dst),
        ],
        check=True,
        capture_output=True,
    )
    print(f"HD image saved: {dst}")


if __name__ == "__main__":
    print(f"Generating scene07_cut02 using insert_ref: {INSERT_REF}")
    generate_frame_with_ref(PROMPT, INSERT_REF, RAW_OUT)
    scale_to_hd(RAW_OUT, HD_OUT)
    print("Done.")
