"""씬09 컷01 영상 생성 스크립트.

입력: short-film-project/final/frames/scene09_cut01_hd.png (1920x1080)
처리: Sora sora-2 텍스트 전용 -> FFmpeg 1920x1080 업스케일
출력: short-film-project/final/videos/scene09_cut01.mp4

주의: Sora API 현재 지원 크기는 1280x720만 허용.
      MAX_WAIT 1800초(30분)로 연장.
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

SORA_URL = "https://api.openai.com/v1/videos"
FRAME_PATH = "/Users/ksm2761/karts/short-film-project/final/frames/scene09_cut01_hd.png"
RAW_OUTPUT = "/tmp/scene09_cut01_raw.mp4"
FINAL_OUTPUT = "/Users/ksm2761/karts/short-film-project/final/videos/scene09_cut01.mp4"

POLL_INTERVAL = 15
MAX_WAIT = 1800  # 30분

PROMPT = (
    "Cinematic slow motion, camera tilts upward following a gleaming sword blade rising toward clear morning sky. "
    "Low angle wide shot, ancient stone bridge at dawn over a misty valley, "
    "two armored warriors in ceremonial confrontation, "
    "one standing knight in dark steel medieval plate armor holds a longsword upright overhead, "
    "backlit by brilliant cold morning sunlight, dramatic golden rim light silhouette, "
    "second warrior in ornate navy and gold ceremonial eastern armor, "
    "seated respectfully in formal bow on stone bridge, decorative mask on face, "
    "fog gently lifting from valley below, crisp bright cold morning atmosphere, "
    "vivid saturated cinematic color grading, amber and blue tones, "
    "epic historical fantasy, photorealistic cinematic quality, 16:9 wide composition"
)


def headers() -> dict:
    return {
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
        "Content-Type": "application/json",
    }


def submit_job() -> str:
    payload = {
        "model": "sora-2",
        "prompt": PROMPT,
        "seconds": "8",
        "size": "1280x720",
    }
    resp = requests.post(SORA_URL, headers=headers(), json=payload, timeout=60)
    if resp.status_code not in (200, 201, 202):
        raise RuntimeError(f"Submit failed {resp.status_code}: {resp.text}")
    data = resp.json()
    video_id = data.get("id")
    if not video_id:
        raise RuntimeError(f"No video id in response: {data}")
    log.info("Job 제출 완료 — video_id=%s", video_id)
    return video_id


def poll_until_done(video_id: str) -> None:
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        r = requests.get(f"{SORA_URL}/{video_id}", headers=headers(), timeout=30)
        if r.status_code != 200:
            log.warning("폴링 응답 오류: %s", r.status_code)
            continue
        d = r.json()
        status = d.get("status", "")
        progress = d.get("progress", 0)
        log.info("상태: %s %s%%", status, progress)
        if status == "completed":
            return
        if status in ("failed", "cancelled"):
            err = (d.get("error") or {}).get("message", status)
            raise RuntimeError(f"Generation {status}: {err}")
    raise TimeoutError(f"Sora 타임아웃 ({MAX_WAIT}초 초과)")


def download(video_id: str, output_path: str) -> None:
    resp = requests.get(
        f"{SORA_URL}/{video_id}/content",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
        timeout=120,
        stream=True,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Download failed {resp.status_code}: {resp.text[:200]}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    log.info("Raw 영상 저장: %s", output_path)


def upscale_to_1080p(raw_path: str, final_path: str) -> None:
    Path(final_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", raw_path,
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        final_path,
    ]
    log.info("FFmpeg 업스케일: %s -> %s", raw_path, final_path)
    subprocess.run(cmd, check=True)
    log.info("최종 저장: %s", final_path)


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        log.error("OPENAI_API_KEY 미설정")
        sys.exit(1)

    video_id = submit_job()
    poll_until_done(video_id)
    download(video_id, RAW_OUTPUT)
    upscale_to_1080p(RAW_OUTPUT, FINAL_OUTPUT)
    log.info("완료: %s", FINAL_OUTPUT)


if __name__ == "__main__":
    main()
