"""트레일러 프레임을 레퍼런스로 gpt-image-2 캐릭터 시트 생성."""
import os, base64, subprocess
from pathlib import Path
from openai import OpenAI

for env in [Path.home()/"karts"/".env", Path(__file__).parent.parent/".env"]:
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())
        break

client = OpenAI()
CHAR_DIR = Path("/Users/ksm2761/karts-final/short-film-project/reference/characters")

CHARS = [
    {
        "name": "viking",
        "ref": str(CHAR_DIR / "viking_02.jpg"),
        "prompt": (
            "Character design reference sheet. Full body front view of this EXACT viking warrior character "
            "from the For Honor E3 2016 cinematic trailer. Reproduce his exact appearance: "
            "massive heavily muscled shirtless male warrior with dark tribal tattoos covering chest arms and face, "
            "worn brown fur cloak draped over shoulders, small bronze horned helmet with short horns, "
            "round wooden shield with metal rim studs held in left hand, single battle axe in right hand, "
            "dark leather hide pants, wrapped leather boots, battle-worn and dirty. "
            "Plain neutral grey studio background. Full body standing pose facing directly forward, "
            "photorealistic cinematic quality, For Honor game art style"
        ),
    },
    {
        "name": "samurai",
        "ref": str(CHAR_DIR / "samurai_79s.jpg"),
        "prompt": (
            "Character design reference sheet. Full body front view of this EXACT samurai warrior character "
            "from the For Honor E3 2016 cinematic trailer. Reproduce his exact appearance: "
            "lean male warrior wearing horizontal-banded lamellar armor in tan and khaki tones, "
            "conical kabuto helmet, dark cloth mask covering lower face, "
            "long naginata polearm held vertically, wrapped cloth bracers on forearms, "
            "worn and battle-damaged armor pieces. "
            "Plain neutral grey studio background. Full body standing pose facing directly forward, "
            "photorealistic cinematic quality, For Honor game art style"
        ),
    },
    {
        "name": "knight",
        "ref": str(CHAR_DIR / "knight_01.jpg"),
        "prompt": (
            "Character design reference sheet. Full body front view of this EXACT knight warrior character "
            "from the For Honor E3 2016 cinematic trailer. Reproduce his exact appearance: "
            "male knight in dark grey dented steel full plate armor, conical bascinet helmet with visor, "
            "chainmail visible at neck collar and gaps between plates, brown leather left pauldron, "
            "longsword with sun emblem crossguard held at side, dark tattered cloak, "
            "battle-worn scratched armor. "
            "Plain neutral grey studio background. Full body standing pose facing directly forward, "
            "photorealistic cinematic quality, For Honor game art style"
        ),
    },
]

for char in CHARS:
    print(f"[{char['name']}] 캐릭터 시트 생성 중...")
    out_raw = CHAR_DIR / f"sheet_{char['name']}_raw.png"
    out_hd  = CHAR_DIR / f"sheet_{char['name']}.png"

    with open(char["ref"], "rb") as f:
        resp = client.images.edit(
            model="gpt-image-2",
            image=f,
            prompt=char["prompt"],
            size="1536x1024",
        )

    out_raw.write_bytes(base64.b64decode(resp.data[0].b64_json))
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(out_raw),
         "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos", str(out_hd)],
        check=True, capture_output=True,
    )
    print(f"  완료: {out_hd.name} ({out_hd.stat().st_size//1024}KB)")

print("\n캐릭터 시트 3종 완성!")
