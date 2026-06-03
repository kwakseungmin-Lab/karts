"""Generate scene06_cut02 frame using GPT Image edit endpoint."""
import os
import base64
import subprocess
from openai import OpenAI

# Load API key from .env if not set
if not os.environ.get("OPENAI_API_KEY"):
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == "OPENAI_API_KEY":
                    os.environ["OPENAI_API_KEY"] = v.strip()
                    break

client = OpenAI()

INSERT_REF = "/Users/ksm2761/karts/short-film-project/images/05_cuts/action_cuts/cut_01_swords_x_sparks.png"
OUT_RAW = "/Users/ksm2761/karts/short-film-project/final/frames/scene06_cut02.png"
OUT_HD = "/Users/ksm2761/karts/short-film-project/final/frames/scene06_cut02_hd.png"

PROMPT = (
    "Cinematic extreme close-up slow motion insert, two sword blades clashing, "
    "longsword and nodachi crossed in impact, sparks and metal shards exploding outward, "
    "dramatic orange spark flash against cool blue-grey background, "
    "ultra sharp detail on blade edges, For Honor cinematic style, "
    "photorealistic, 1920x1080, 16:9 composition"
)


def generate_frame_with_ref(prompt: str, ref_path: str, out_path: str) -> None:
    with open(ref_path, "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt,
            size="1536x1024",
        )
    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)


def scale_to_hd(src: str, dst: str) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", src,
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            dst,
        ],
        check=True,
        capture_output=True,
    )


if __name__ == "__main__":
    print("Generating scene06_cut02 via GPT Image edit endpoint...")
    generate_frame_with_ref(PROMPT, INSERT_REF, OUT_RAW)
    print(f"Raw image saved: {OUT_RAW}")

    scale_to_hd(OUT_RAW, OUT_HD)
    print(f"HD image saved: {OUT_HD}")
