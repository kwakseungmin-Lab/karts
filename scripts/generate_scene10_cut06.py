"""
씬10 컷06 이미지 생성 스크립트
타입: transition (캐릭터 참조 있음 → edit 엔드포인트 사용)
"""

import base64
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

PROJECT_ROOT = Path("/Users/ksm2761/karts/short-film-project")
OUTPUT_DIR = PROJECT_ROOT / "final" / "frames"

PROMPT = (
    "Cinematic wide static shot, two warriors standing facing each other on ruined stone bridge, "
    "Aiden medieval knight in dark steel partial plate armor left side, "
    "Kagemasa samurai in deep navy oyoroi armor right side, "
    "swords sheathed, 5-meter space between them, "
    "bright warm morning sunlight bathing the bridge, fog fully cleared, "
    "distant landscape visible on both sides — gothic castle silhouette left, misty wetlands right, "
    "peaceful contemplative silence, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)

CHARACTER_REFS = [
    PROJECT_ROOT / "images/01_character_sheets/aiden/aiden_01_front_view.png",
    PROJECT_ROOT / "images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
]

BACKGROUND_REF = PROJECT_ROOT / "images/03_background_art/borderlands_bridge/bg_02_bridge_both_ends.png"

OUT_RAW = OUTPUT_DIR / "scene10_cut06.png"
OUT_HD = OUTPUT_DIR / "scene10_cut06_hd.png"


def generate_frame_with_refs(
    prompt: str,
    ref_paths: list[Path],
    out_path: Path,
) -> None:
    """
    GPT Image edit 엔드포인트로 캐릭터 참조 이미지를 주입하여 프레임 생성.
    첫 번째 참조 이미지를 메인으로 사용하고, 나머지는 프롬프트에 명시.
    """
    client = OpenAI()

    extra_desc = ""
    if len(ref_paths) > 1:
        extra_desc = " Reference images provided for character consistency."

    with open(ref_paths[0], "rb") as img_f:
        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt + extra_desc,
            size="1536x1024",
        )

    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)

    print(f"생성 완료: {out_path}", flush=True)


def scale_to_hd(src: Path, dst: Path) -> None:
    """1536×1024 → 16:9 크롭(1536×864) → 1920×1080"""
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            str(dst),
        ],
        check=True,
    )
    print(f"HD 변환 완료: {dst}", flush=True)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 참조 이미지 순서: 두 캐릭터 + 배경
    ref_paths = CHARACTER_REFS + [BACKGROUND_REF]

    # 존재 여부 확인
    for p in ref_paths:
        if not p.exists():
            print(f"참조 파일 없음: {p}", file=sys.stderr)
            return 1

    print("GPT Image edit 엔드포인트로 씬10 컷06 생성 중...", flush=True)
    generate_frame_with_refs(PROMPT, ref_paths, OUT_RAW)

    print("FFmpeg HD 변환 중...", flush=True)
    scale_to_hd(OUT_RAW, OUT_HD)

    print(f"\n완료:")
    print(f"  원본: {OUT_RAW}")
    print(f"  HD:   {OUT_HD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
