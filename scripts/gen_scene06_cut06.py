"""씬06 컷06 Sora 영상 생성 + FFmpeg 1920×1080 업스케일.

입력 이미지가 NSFW 필터 트리거 → image_reference 없이 텍스트 프롬프트만으로 생성.
생성된 raw 영상을 FFmpeg으로 1920x1080 업스케일.
"""
from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.video.sora_video import SoraVideo

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

RAW_VIDEO = "/tmp/scene06_cut06_raw.mp4"
FINAL_VIDEO = "/Users/ksm2761/karts/short-film-project/final/videos/scene06_cut06.mp4"

# 이미지 참조 없이 텍스트 전용 — cinematic insert shot 묘사
PROMPT = (
    "Cinematic extreme close-up of a weathered dark stone bridge surface at dawn, "
    "a single drop of deep crimson liquid falls in slow motion, "
    "spreading in a thin rivulet across cold grey stone texture, "
    "nearly monochromatic scene with one vivid red accent color, "
    "shallow depth of field, cool early morning light raking across surface, "
    "For Honor medieval cinematic style, photorealistic, 16:9"
)


def generate_raw() -> None:
    tool = SoraVideo()
    log.info("Sora 텍스트 전용 생성 시작")
    # image_path 생략 → 텍스트 only
    result = tool.execute(
        {
            "prompt": PROMPT,
            "duration": 4,
            "size": "1280x720",
            "output_path": RAW_VIDEO,
        }
    )
    if not result.success:
        raise RuntimeError(f"Sora 생성 실패: {result.error}")
    log.info("Sora 생성 완료: %s (%.1fs)", result.data["output"], result.duration_seconds)


def upscale_to_1080p() -> None:
    Path(FINAL_VIDEO).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", RAW_VIDEO,
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        FINAL_VIDEO,
    ]
    log.info("FFmpeg 업스케일: %s → %s", RAW_VIDEO, FINAL_VIDEO)
    subprocess.run(cmd, check=True)
    log.info("저장 완료: %s", FINAL_VIDEO)


def main() -> None:
    generate_raw()
    upscale_to_1080p()
    size_mb = Path(FINAL_VIDEO).stat().st_size / 1024 / 1024
    log.info("최종 파일: %s (%.2f MB)", FINAL_VIDEO, size_mb)


if __name__ == "__main__":
    main()
