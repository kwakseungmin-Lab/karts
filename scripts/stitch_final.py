"""렌더링된 씬별 클립을 FFmpeg으로 이어붙여 최종 영상 완성.

사용법:
  python3 scripts/stitch_final.py
  python3 scripts/stitch_final.py --output final_cut.mp4
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


OUTPUT_DIR = Path(__file__).parent.parent / "short-film-project" / "output"
FINAL_DIR = Path(__file__).parent.parent / "short-film-project" / "final"


def get_clips() -> list[Path]:
    clips = []
    for scene_dir in sorted(OUTPUT_DIR.glob("scene_*")):
        for clip in sorted(scene_dir.glob("clip_*.mp4")):
            clips.append(clip)
    return clips


def stitch(clips: list[Path], output: Path) -> None:
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    concat_list = OUTPUT_DIR / "_concat.txt"
    concat_list.write_text("\n".join(f"file '{c.resolve()}'" for c in clips))

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output),
    ]
    print("FFmpeg 합성 중…")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg 오류:\n{result.stderr}")
        sys.exit(1)
    concat_list.unlink(missing_ok=True)
    print(f"완성: {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="weight_of_honor_cut.mp4")
    args = parser.parse_args()

    clips = get_clips()
    if not clips:
        print("렌더링된 클립이 없습니다. 먼저 render_scenes.py를 실행하세요.")
        sys.exit(1)

    print(f"클립 {len(clips)}개 발견:")
    for c in clips:
        print(f"  {c.relative_to(OUTPUT_DIR.parent.parent)}")

    output = FINAL_DIR / args.output
    stitch(clips, output)


if __name__ == "__main__":
    main()
