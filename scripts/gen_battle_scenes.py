"""씬07 전투 씬 재생성 — 세 진영이 서로 싸우는 구체적 장면."""
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

SCENES = [
    {
        "id": "07a",
        "title": "바이킹 vs 사무라이 — 첫 교전",
        "mode": "edit",
        "char_ref": "sheet_viking.png",
        "prompt": (
            "Place THIS EXACT viking warrior character in an intense one-on-one duel, "
            "the viking is on the LEFT swinging his axe TOWARD the opponent on the RIGHT, "
            "the opponent on the RIGHT is a samurai in horizontal-banded lamellar armor "
            "deflecting with his naginata polearm, "
            "the two warriors are FIGHTING EACH OTHER — they are ENEMIES, not allies, "
            "rocky wasteland ground, dead trees, grey overcast sky, "
            "dramatic side lighting, dust kicked up from their feet, "
            "cinematic medium shot capturing the clash, "
            "desaturated tones with motion blur on the weapons, "
            "photorealistic, For Honor E3 2016 combat cinematic style, 16:9"
        ),
    },
    {
        "id": "07b",
        "title": "기사 vs 바이킹 — 근접 충돌",
        "mode": "edit",
        "char_ref": "sheet_knight.png",
        "prompt": (
            "Place THIS EXACT knight warrior character in an intense one-on-one combat, "
            "the knight is on the RIGHT raising his longsword to strike DOWNWARD at the opponent, "
            "the opponent on the LEFT is a massive shirtless tattooed viking warrior "
            "blocking with his round wooden shield while counter-attacking with his axe, "
            "the two warriors are FIGHTING EACH OTHER as mortal enemies, "
            "rocky battlefield ground with ruins in background, dramatic low angle shot, "
            "the knight's dark steel armor vs the viking's raw fur and muscle, "
            "desaturated grey tones, cinematic impact moment, "
            "photorealistic, For Honor E3 2016 combat cinematic style, 16:9"
        ),
    },
    {
        "id": "07c",
        "title": "세 진영 혼전 — 카오스",
        "mode": "edit",
        "char_ref": "sheet_viking.png",
        "prompt": (
            "Place THIS EXACT viking warrior character in the CENTER of a chaotic three-way battle, "
            "the viking is fighting SIMULTANEOUSLY against enemies on BOTH SIDES — "
            "a knight in dark plate armor attacks him from the LEFT, "
            "a samurai in lamellar armor attacks him from the RIGHT, "
            "in the BACKGROUND hundreds of warriors from all three factions are fighting EACH OTHER "
            "in total chaotic melee — knights vs samurai, vikings vs knights, samurai vs vikings, "
            "faction banners of all three sides visible among the chaos, "
            "smoke and dust, fire in distant background, dramatic battle lighting, "
            "ALL THREE FACTIONS ARE ENEMIES fighting each other, not allies, "
            "photorealistic, For Honor E3 2016 large battle cinematic style, 16:9"
        ),
    },
    {
        "id": "07d",
        "title": "전장 와이드 — 세 진영 난전",
        "mode": "generate",
        "char_ref": None,
        "prompt": (
            "Cinematic wide battle shot, a chaotic three-way medieval battle where "
            "THREE FACTIONS ARE FIGHTING EACH OTHER simultaneously — "
            "LEFT side: dark steel armored knights clashing AGAINST samurai warriors, "
            "RIGHT side: fur-clad viking warriors fighting AGAINST knights, "
            "CENTER: samurai warriors battling AGAINST vikings, "
            "each faction fights the other two — total three-way war, "
            "faction banners visible: cross banner (knights), chrysanthemum banner (samurai), "
            "skull banner (vikings) — all on OPPOSING sides, "
            "dramatic battlefield chaos, dust and fire, rocky hillside terrain, "
            "cinematic wide shot showing the full scale of mutual combat, "
            "photorealistic, For Honor E3 2016 battle cinematic style, 16:9"
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
    sid  = scene["id"]
    raw  = BOARD_DIR / f"scene{sid}_raw.png"
    hd   = BOARD_DIR / f"scene{sid}_hd.png"

    print(f"[씬{sid}] {scene['title']} 생성 중...")

    if scene["mode"] == "generate":
        resp = client.images.generate(
            model="gpt-image-2",
            prompt=scene["prompt"],
            size="1536x1024",
            quality="high",
            n=1,
        )
    else:
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

print("\n전투 씬 4종 완성!")
