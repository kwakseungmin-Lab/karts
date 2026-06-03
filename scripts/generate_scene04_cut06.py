"""씬04 컷06 이미지 생성 스크립트 — frame-artist 에이전트 지침 준수."""

import base64
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv("/Users/ksm2761/karts/.env")


def generate_frame_with_refs(
    prompt: str, ref_paths: list[str], out_path: str
) -> None:
    """GPT Image edit 엔드포인트로 참조 이미지 주입 후 프레임 생성.

    ref_paths: character_refs + background_ref 경로 목록 (첫 번째가 메인 참조)
    """
    from openai import OpenAI

    client = OpenAI()

    # 다수 참조 이미지를 프롬프트에 명시적으로 반영
    extra_desc = ""
    if len(ref_paths) > 1:
        extra_desc = (
            " Reference images provided for character and environment consistency."
        )

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
    print(f"생성 완료: {out_path}", file=sys.stderr)


def scale_to_hd(src: str, dst: str) -> None:
    """1536×1024 → 16:9 크롭(1536×864) → 1920×1080 (lanczos)."""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            src,
            "-vf",
            "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
            dst,
        ],
        check=True,
    )
    print(f"HD 변환 완료: {dst}", file=sys.stderr)


def main() -> None:
    project_root = Path("/Users/ksm2761/karts/short-film-project")

    prompt = (
        "Cinematic medium close-up low angle, stone bridge surface level, "
        "two sets of armored boots stepping forward onto moss-covered ruined stone bridge, "
        "left: dark steel sabatons of Aiden, medieval knight, "
        "right: deep navy lacquered armored waraji sandals of Kagemasa, samurai kensei, "
        "each taking one deliberate step toward each other, "
        "fog-filled bridge gap between them, "
        "blue-grey desaturated, For Honor cinematic trailer style, "
        "photorealistic, 1920x1080, 16:9 composition"
    )

    ref_paths = [
        str(project_root / "images/01_character_sheets/aiden/aiden_01_front_view.png"),
        str(project_root / "images/01_character_sheets/kagemasa/kagemasa_01_front_view.png"),
        str(project_root / "images/03_background_art/borderlands_bridge/bg_03_bridge_detail_ruins.png"),
    ]

    out_dir = project_root / "final/frames"
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_path = str(out_dir / "scene04_cut06.png")
    hd_path = str(out_dir / "scene04_cut06_hd.png")

    # 모든 참조 파일 존재 확인
    for p in ref_paths:
        if not Path(p).exists():
            print(f"참조 파일 없음: {p}", file=sys.stderr)
            sys.exit(1)

    print("GPT Image edit 엔드포인트로 씬04 컷06 생성 중...", file=sys.stderr)
    generate_frame_with_refs(prompt, ref_paths, raw_path)
    scale_to_hd(raw_path, hd_path)
    print(f"최종 출력: {hd_path}")


if __name__ == "__main__":
    main()
