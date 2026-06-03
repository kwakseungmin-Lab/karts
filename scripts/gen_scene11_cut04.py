#!/usr/bin/env python3
"""씬11 컷04 영상 생성 스크립트.

Sora sora-2, 1280x720, 8초 → FFmpeg 1920x1080 업스케일.
(API가 현재 720x1280, 1280x720만 지원)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv("/Users/ksm2761/karts/.env")

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, "/Users/ksm2761/karts")

from tools.video.sora_video import SoraVideo  # noqa: E402

INPUT_IMAGE = "/Users/ksm2761/karts/short-film-project/final/frames/scene11_cut04_hd.png"
RAW_OUTPUT = "/tmp/scene11_cut04_raw.mp4"
FINAL_OUTPUT = "/Users/ksm2761/karts/short-film-project/final/videos/scene11_cut04.mp4"

PROMPT = (
    "Cinematic static wide shot of the empty ruined stone borderlands bridge, "
    "fog rolling in from both ends reclaiming the space, battle traces on the stone "
    "— smears of blood, a fallen fragment of metal armor, deep scratch marks on the stone pavement. "
    "The bridge is utterly empty, no human figures. "
    "Morning light completely overcast, cold blue-grey desaturated tone echoing the opening prologue, "
    "mist thickening across the full width, ominous stillness, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9. "
    "Camera holds static for 4 seconds on empty bridge; "
    "slow gentle push-in toward bridge center over remaining 4 seconds; "
    "fog drifts slowly across frame."
)


def main() -> None:
    tool = SoraVideo()
    ok, msg = tool.check_dependencies()
    if not ok:
        print(f"ERROR: {msg}", file=sys.stderr)
        sys.exit(1)

    print("Submitting to Sora sora-2 (1280x720, 8s)...")
    result = tool.execute(
        {
            "prompt": PROMPT,
            "image_path": INPUT_IMAGE,
            "duration": 8,
            "size": "1280x720",
            "output_path": RAW_OUTPUT,
        }
    )

    if not result.success:
        print(f"ERROR: Sora generation failed: {result.error}", file=sys.stderr)
        sys.exit(1)

    video_id = result.data.get("video_id", "")
    elapsed = result.duration_seconds or 0.0
    print(f"Sora complete: video_id={video_id}, elapsed={elapsed:.1f}s")
    print(f"Raw output: {RAW_OUTPUT}")

    # FFmpeg 1920x1080 업스케일
    print("Upscaling to 1920x1080 via FFmpeg (lanczos)...")
    Path(FINAL_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            RAW_OUTPUT,
            "-vf",
            "scale=1920:1080:flags=lanczos",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            FINAL_OUTPUT,
        ],
        check=True,
    )
    print(f"Final output saved: {FINAL_OUTPUT}")


if __name__ == "__main__":
    main()
