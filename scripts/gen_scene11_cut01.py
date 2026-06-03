"""씬11 컷01 영상 생성 스크립트.

Sora sora-2, 1280x720 (현재 지원 최대 landscape) → FFmpeg 1920x1080 업스케일
"""
from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/Users/ksm2761/karts")

from tools.video.sora_video import SoraVideo

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

INPUT_IMAGE = "/Users/ksm2761/karts/short-film-project/final/frames/scene11_cut01_hd.png"
RAW_OUTPUT = "/tmp/scene11_cut01_raw.mp4"
FINAL_OUTPUT = "/Users/ksm2761/karts/short-film-project/final/videos/scene11_cut01.mp4"

PROMPT = (
    "Cinematic cross-cutting extreme close-up sequence, alternating between two warriors' faces. "
    "First: Aiden, medieval knight in dark steel partial plate armor with chain mail, scarred face "
    "with vertical scar above left eye, brown hair, eyes slowly closing in exhaustion then tightening "
    "jaw in resignation then opening with quiet resolve. "
    "Second: Kagemasa, samurai in deep navy oyoroi armor with gold imperial crest (partially worn), "
    "40s, black hair in topknot, deep calm eyes reacting identically — sorrow to resignation to resolve. "
    "Rapid cross-cut between Aiden face and Kagemasa face, each held 1.5-2 seconds; subtle facial muscle "
    "micro-movements convey the emotional shift. "
    "Desaturating color grade returning, cold blue-grey tone, clouds beginning to obscure the morning sun, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)

# sora-2가 현재 지원하는 최대 landscape 해상도
SORA_SIZE = "1280x720"


def upscale_to_1080p(src: str, dst: str) -> None:
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", src,
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        dst,
    ]
    log.info("FFmpeg 업스케일: %s → %s", src, dst)
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg 실패:\n{result.stderr}")
    log.info("업스케일 완료: %s", dst)


def main() -> None:
    log.info("씬11 컷01 영상 생성 시작")
    log.info("입력 이미지: %s", INPUT_IMAGE)

    if not Path(INPUT_IMAGE).exists():
        log.error("입력 이미지 없음: %s", INPUT_IMAGE)
        sys.exit(1)

    tool = SoraVideo()
    ok, msg = tool.check_dependencies()
    if not ok:
        log.error("의존성 오류: %s", msg)
        sys.exit(1)

    log.info("Sora sora-2 제출 중 (%s, 4초)...", SORA_SIZE)
    result = tool.execute(
        {
            "prompt": PROMPT,
            "image_path": INPUT_IMAGE,
            "duration": 4,
            "size": SORA_SIZE,
            "output_path": RAW_OUTPUT,
        }
    )

    if not result.success:
        log.error("Sora 생성 실패: %s", result.error)
        sys.exit(1)

    log.info(
        "Sora 생성 성공 (video_id=%s, %.1fs)",
        result.data.get("video_id"),
        result.duration_seconds or 0,
    )

    upscale_to_1080p(RAW_OUTPUT, FINAL_OUTPUT)
    log.info("최종 저장: %s", FINAL_OUTPUT)
    print(FINAL_OUTPUT)


if __name__ == "__main__":
    main()
