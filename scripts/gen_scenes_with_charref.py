"""캐릭터 시트를 레퍼런스로 씬 이미지 생성.
- 배경 씬 (01-03, 08): images.generate
- 캐릭터 씬 (04-07): images.edit (캐릭터 시트 레퍼런스)
"""
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
CHAR_DIR  = Path("/Users/ksm2761/karts-final/short-film-project/reference/characters")
BOARD_DIR = Path("/Users/ksm2761/karts-final/short-film-project/reference/storyboard_v2")
BOARD_DIR.mkdir(exist_ok=True)

SCENES = [
    # ── 배경 씬 (characters.generate) ──
    {
        "id": "01", "mode": "generate", "char_ref": None,
        "prompt": (
            "Cinematic macro close-up of golden wheat stalks in a field at golden hour, "
            "warm amber backlight through the wheat creating soft bokeh glow, "
            "tiny light dust particles floating in the warm air, "
            "the camera is at ground level looking through the wheat, "
            "peaceful abundance before the war, deeply warm golden tones, "
            "photorealistic, For Honor E3 2016 cinematic style, 16:9"
        ),
    },
    {
        "id": "02", "mode": "generate", "char_ref": None,
        "prompt": (
            "Cinematic aerial wide shot of a lush green medieval landscape at golden hour, "
            "a grand stone castle with multiple towers perched dramatically on a rocky hilltop, "
            "dense green forested valleys below with a winding river catching the warm sunlight, "
            "morning mist clinging to the valleys, overcast warm sky, "
            "majestic and peaceful, the world before destruction, "
            "photorealistic, For Honor E3 2016 cinematic style, 16:9"
        ),
    },
    {
        "id": "03", "mode": "generate", "char_ref": None,
        "prompt": (
            "Cinematic wide shot of a medieval town completely engulfed in massive fires at night, "
            "countless buildings burning simultaneously with intense orange-red flames, "
            "thick black smoke rising against the pitch dark sky, "
            "collapsed structures and burning timber debris everywhere, "
            "extreme contrast between the raging orange fire and total darkness, "
            "apocalyptic total destruction of civilization, "
            "photorealistic, For Honor E3 2016 cinematic style, 16:9"
        ),
    },
    # ── 캐릭터 씬 (images.edit with character sheet ref) ──
    {
        "id": "04", "mode": "edit", "char_ref": "sheet_viking.png",
        "prompt": (
            "Place THIS EXACT viking warrior character into a new scene: "
            "seen from BEHIND walking away from the camera through a completely devastated post-war landscape, "
            "dead twisted bare trees scattered across rocky barren grey ground extending to the horizon, "
            "heavy overcast grey sky, ash and dust in the air, "
            "the warrior walks alone carrying his axe — the only living thing in this emptied world, "
            "deeply desaturated grey-brown tones, "
            "photorealistic, For Honor E3 2016 cinematic rear tracking shot style, 16:9"
        ),
    },
    {
        "id": "05", "mode": "edit", "char_ref": "sheet_viking.png",
        "prompt": (
            "Place THIS EXACT viking warrior character into a new scene, "
            "standing on the LEFT side of frame on rocky debris-covered ground facing right, "
            "on the RIGHT side at distance stands a samurai warrior in horizontal-banded lamellar armor with a long naginata, "
            "both warriors have just noticed each other and stopped walking, "
            "wide shot showing both warriors and the vast rocky wasteland between them, "
            "dead trees and cliff faces in background, grey overcast sky, "
            "tense moment of unexpected encounter between two lone survivors, "
            "desaturated warm-grey tones, "
            "photorealistic, For Honor E3 2016 cinematic style, 16:9"
        ),
    },
    {
        "id": "06", "mode": "edit", "char_ref": "sheet_knight.png",
        "prompt": (
            "Place THIS EXACT knight warrior character into a new scene, "
            "standing on the RIGHT side of frame on a rocky ridge, "
            "on the LEFT stands a massive viking warrior with axe and shield, "
            "in the CENTER BACKGROUND stands a samurai warrior with a long polearm, "
            "all three warriors are facing each other in a wide triangular standoff, "
            "dramatic aerial perspective looking slightly down at the three figures, "
            "rocky mountainous desolate landscape, heavy grey sky with mist, "
            "none of the three has an advantage — equal triangular formation, "
            "desaturated grey tones, "
            "photorealistic, For Honor E3 2016 cinematic style, 16:9"
        ),
    },
    {
        "id": "07", "mode": "edit", "char_ref": "sheet_viking.png",
        "prompt": (
            "Place THIS EXACT viking warrior character into a massive battle scene, "
            "he is in the foreground running forward as part of a huge army charge, "
            "hundreds of armored warriors behind him — knights in plate armor, samurai in lamellar armor, vikings with axes — "
            "all charging across an open rocky hillside battlefield in daylight, "
            "faction banners (a cross banner, a chrysanthemum banner, a skull banner) visible above the armies, "
            "dust clouds rising from hundreds of running feet, "
            "ruined stone walls on the hillside, natural hazy morning light, "
            "epic cinematic scale of a massive three-faction battle, "
            "photorealistic, For Honor E3 2016 large battle cinematic style, 16:9"
        ),
    },
    {
        "id": "08", "mode": "generate", "char_ref": None,
        "prompt": (
            "Cinematic very high altitude bird's eye aerial view looking straight down "
            "at an ancient deeply scarred battlefield landscape, "
            "the ground shows centuries of battle scars and partially recovered vegetation, "
            "THREE faction banners standing upright in the ruined earth — "
            "a white flag with black cross (knights), a dark flag with chrysanthemum (samurai), "
            "a black flag with skull (vikings), "
            "tiny warrior figures barely visible beginning to gather at the edges again, "
            "cold grey-green atmospheric aerial perspective, "
            "hopeless sense of eternal cyclical war, "
            "photorealistic, For Honor E3 2016 god's eye cinematic style, 16:9"
        ),
    },
]


def save_hd(raw: Path, hd: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw),
         "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos", str(hd)],
        check=True, capture_output=True,
    )


for scene in SCENES:
    sid   = scene["id"]
    raw   = BOARD_DIR / f"scene{sid}_raw.png"
    hd    = BOARD_DIR / f"scene{sid}_hd.png"

    if hd.exists():
        print(f"[씬{sid}] 존재, 스킵")
        continue

    print(f"[씬{sid}] {scene['mode']} 생성 중...")

    if scene["mode"] == "generate":
        resp = client.images.generate(
            model="gpt-image-2",
            prompt=scene["prompt"],
            size="1536x1024",
            quality="high",
            n=1,
        )
    else:  # edit
        ref_path = CHAR_DIR / scene["char_ref"]
        with open(ref_path, "rb") as f:
            resp = client.images.edit(
                model="gpt-image-2",
                image=f,
                prompt=scene["prompt"],
                size="1536x1024",
            )

    raw.write_bytes(base64.b64decode(resp.data[0].b64_json))
    save_hd(raw, hd)
    print(f"  완료: {hd.name} ({hd.stat().st_size//1024}KB)")

print("\n8씬 전체 완료!")
