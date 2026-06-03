"""FFmpeg 기반 1920×1080 업스케일 유틸리티.

Sora 출력(1792×1024)과 GPT Image 출력(1536×1024)을
QuickTime 호환 Full HD로 변환한다.
"""

import logging
import os
import shutil
import subprocess
import tempfile


def upscale_to_1920x1080(input_path: str, output_path: str) -> None:
    """input_path 영상을 1920×1080으로 업스케일해 output_path에 저장.

    기존 파일이 이미 1920×1080이면 복사만 수행.
    """
    if not shutil.which("ffmpeg"):
        logging.warning("ffmpeg 실행 파일을 찾을 수 없습니다. 업스케일을 건너뜁니다.")
        shutil.copy2(input_path, output_path)
        return

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", "scale=1920:1080:flags=lanczos,setsar=1",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "copy",
        output_path,
    ]

    logging.info(f"FFmpeg 업스케일: {input_path} → {output_path} (1920×1080)")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"FFmpeg 오류:\n{result.stderr}")
        raise RuntimeError(f"FFmpeg 업스케일 실패: {result.stderr[-300:]}")

    logging.info(f"업스케일 완료: {output_path}")


def upscale_inplace(video_path: str) -> None:
    """video_path 영상을 1920×1080으로 업스케일해 제자리 교체."""
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
    os.close(tmp_fd)
    try:
        upscale_to_1920x1080(video_path, tmp_path)
        shutil.move(tmp_path, video_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
