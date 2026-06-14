import os, base64, subprocess
from pathlib import Path
from openai import OpenAI

for env in [Path.home()/"karts"/".env"]:
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k,_,v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())
        break

client = OpenAI()
BOARD = Path("/Users/ksm2761/karts-final/short-film-project/reference/storyboard_v2")

resp = client.images.generate(
    model="gpt-image-2",
    prompt=(
        "Cinematic wide aerial shot, two opposing lines of medieval warriors facing each other "
        "across a rocky battlefield — LEFT side: armored knights army with cross banners, "
        "RIGHT side: fur-clad viking warriors with skull banners, "
        "dramatic wide gap between the two opposing armies in tense standoff, "
        "grey overcast sky, dust rising, epic cinematic scale, "
        "For Honor cinematic style, photorealistic, 16:9"
    ),
    size="1536x1024", quality="high", n=1,
)
raw = BOARD / "scene07b_raw.png"
hd  = BOARD / "scene07b_hd.png"
raw.write_bytes(base64.b64decode(resp.data[0].b64_json))
subprocess.run(["ffmpeg","-y","-i",str(raw),
                "-vf","crop=1536:864:0:80,scale=1920:1080:flags=lanczos",str(hd)],
               check=True, capture_output=True)
print(f"완료: {hd.stat().st_size//1024}KB")
