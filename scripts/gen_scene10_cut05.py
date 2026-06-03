import os
import base64
import subprocess
from openai import OpenAI

import dotenv; dotenv.load_dotenv()

client = OpenAI()

project_root = "/Users/ksm2761/karts/short-film-project"

ref_paths = [
    f"{project_root}/images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
    f"{project_root}/images/01_character_sheets/kagemasa/kagemasa_04_face_without_mask.png",
    f"{project_root}/images/01_character_sheets/aiden/aiden_01_front_view.png",
    f"{project_root}/images/01_character_sheets/aiden/aiden_04_face_closeup.png",
]

prompt = (
    "Cinematic medium two-shot, equal framing, Kagemasa samurai in deep navy oyoroi armor "
    "with gold imperial crest bare-faced giving a respectful bow, and Aiden medieval knight "
    "in dark steel partial plate armor with chain mail giving a knight's salute — right fist "
    "to left chest, both warriors equal size in frame, swords sheathed, battle damage visible "
    "on armor, soft warm golden morning light, fog cleared, ruined stone bridge background, "
    "serene and dignified, For Honor cinematic trailer style, photorealistic, 1920x1080 16:9. "
    "Reference images provided for character consistency."
)

out_path = f"{project_root}/final/frames/scene10_cut05.png"
hd_path = f"{project_root}/final/frames/scene10_cut05_hd.png"

print("Generating image via GPT Image edit endpoint...")
with open(ref_paths[0], "rb") as img_f:
    response = client.images.edit(
        model="gpt-image-1",
        image=img_f,
        prompt=prompt,
        size="1536x1024",
    )

data = base64.b64decode(response.data[0].b64_json)
with open(out_path, "wb") as f:
    f.write(data)

print(f"Generated: {out_path} ({os.path.getsize(out_path)} bytes)")

# Scale to 1920x1080 via FFmpeg
print("Scaling to 1920x1080...")
subprocess.run([
    "ffmpeg", "-y", "-i", out_path,
    "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
    hd_path
], check=True)

print(f"HD output: {hd_path} ({os.path.getsize(hd_path)} bytes)")
