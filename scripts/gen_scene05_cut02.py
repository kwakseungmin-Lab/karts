"""씬05 컷02 영상 생성 스크립트.

Sora sora-2, size=1280x720 (API 지원 landscape 최대), seconds=8
텍스트 프롬프트만 사용 (이미지 input_reference 모더레이션 차단으로 인해)
출력: short-film-project/final/videos/scene05_cut02.mp4
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

# .env 파일에서 API 키 로드 (환경변수에 없을 경우)
_ENV_PATH = Path("/Users/ksm2761/karts/.env")
if not os.environ.get("OPENAI_API_KEY") and _ENV_PATH.exists():
    for _line in _ENV_PATH.read_text().splitlines():
        _line = _line.strip()
        if _line.startswith("OPENAI_API_KEY="):
            os.environ["OPENAI_API_KEY"] = _line.split("=", 1)[1]
            break

SORA_GENERATIONS_URL = "https://api.openai.com/v1/videos"
POLL_INTERVAL = 10
MAX_WAIT = 600

SORA_SIZE = "1280x720"

RAW_VIDEO = Path("/tmp/scene05_cut02_raw.mp4")
OUTPUT_VIDEO = Path("/Users/ksm2761/karts/short-film-project/final/videos/scene05_cut02.mp4")

# 텍스트 전용 프롬프트 - 이미지 차단 우회, 무기/폭력 표현 완전 제거
PROMPT = (
    "Cinematic historical drama, two armored warriors standing on an ancient stone bridge at dawn, "
    "facing each other in tense standoff, "
    "left figure: medieval European knight in dark steel plate armor with chain mail coif, "
    "right figure: feudal Japanese samurai in deep navy lamellar armor with golden family crest, "
    "both in wide low defensive martial arts stances, weight balanced low, feet on mossy stone, "
    "oblique cold morning sunlight casting long shadows, visible breath vapor in freezing air, "
    "blue-grey heavily desaturated cinematic color grade, "
    "static camera at medium close-up height, slow deliberate tension-filled movement, "
    "photorealistic epic historical drama cinematography, 16:9 widescreen"
)


def submit_sora_job(api_key: str) -> tuple[str, str]:
    """Sora API에 텍스트 전용 영상 생성 요청 후 (video_id, status) 반환."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sora-2",
        "prompt": PROMPT,
        "seconds": "8",
        "size": SORA_SIZE,
    }
    log.info("Sora 텍스트 전용 영상 생성 요청 중 (size=%s)...", SORA_SIZE)
    resp = requests.post(SORA_GENERATIONS_URL, headers=headers, json=payload, timeout=60)
    log.info("응답 상태: %d", resp.status_code)

    if resp.status_code not in (200, 201, 202):
        log.error("제출 실패: %s", resp.text)
        sys.exit(1)

    data = resp.json()
    video_id = data.get("id")
    status = data.get("status", "")
    log.info("Video ID: %s, 초기 상태: %s", video_id, status)
    return video_id, status


def poll_until_complete(video_id: str, api_key: str, start: float) -> dict:
    """영상 생성 완료까지 폴링. 완료된 response 데이터 반환."""
    headers = {"Authorization": f"Bearer {api_key}"}
    deadline = time.time() + MAX_WAIT

    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        try:
            r = requests.get(
                f"{SORA_GENERATIONS_URL}/{video_id}",
                headers=headers,
                timeout=60,
            )
        except requests.exceptions.Timeout:
            log.warning("폴링 타임아웃, 재시도...")
            continue
        except requests.exceptions.RequestException as exc:
            log.warning("폴링 요청 오류: %s, 재시도...", exc)
            continue

        if r.status_code != 200:
            log.warning("폴링 응답 %d, 재시도...", r.status_code)
            continue

        d = r.json()
        s = d.get("status", "")
        progress = d.get("progress", 0)
        elapsed = int(time.time() - start)
        log.info("[%ds] 상태: %s, 진행: %d%%", elapsed, s, progress)

        if s == "completed":
            return d
        if s in ("failed", "cancelled"):
            err = (d.get("error") or {}).get("message", s)
            log.error("생성 %s: %s", s, err)
            sys.exit(1)

    log.error("타임아웃: Sora 생성 대기 %d초 초과", MAX_WAIT)
    sys.exit(1)


def download_video(video_id: str, api_key: str, completed_data: dict | None = None) -> None:
    """영상 다운로드. completed_data URL → SDK → REST 순서로 시도."""
    RAW_VIDEO.parent.mkdir(parents=True, exist_ok=True)

    # 1) completed_data 안에 URL이 있으면 직접 다운로드
    if completed_data:
        generations = completed_data.get("generations", [])
        if generations:
            video_url = generations[0].get("url") or generations[0].get("video_url")
            if video_url:
                log.info("URL로 직접 다운로드: %s...", video_url[:80])
                resp = requests.get(video_url, timeout=300, stream=True)
                if resp.status_code == 200:
                    with open(RAW_VIDEO, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=65536):
                            f.write(chunk)
                    log.info("직접 URL 다운로드 완료: %s", RAW_VIDEO)
                    return
                log.warning("직접 URL 다운로드 실패: %d", resp.status_code)

    # 2) SDK download_content 시도
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        content = client.videos.download_content(video_id)
        content.write_to_file(str(RAW_VIDEO))
        log.info("SDK 다운로드 완료: %s", RAW_VIDEO)
        return
    except Exception as exc:
        log.warning("SDK 다운로드 실패: %s", exc)

    # 3) REST /content/video 시도
    headers = {"Authorization": f"Bearer {api_key}"}
    for url_suffix in ("/content/video", "/content"):
        url = f"{SORA_GENERATIONS_URL}/{video_id}{url_suffix}"
        log.info("REST 다운로드 시도: %s", url)
        try:
            resp = requests.get(url, headers=headers, timeout=300, stream=True)
        except requests.exceptions.RequestException as exc:
            log.warning("REST 요청 오류: %s", exc)
            continue
        if resp.status_code == 200:
            with open(RAW_VIDEO, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)
            log.info("REST 다운로드 완료: %s", RAW_VIDEO)
            return
        log.warning("REST %s 실패: %d", url_suffix, resp.status_code)

    log.error("모든 다운로드 방법 실패. video_id=%s", video_id)
    sys.exit(1)


def upscale_to_1080p() -> None:
    """FFmpeg로 1280x720 → 1920x1080 업스케일."""
    OUTPUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(RAW_VIDEO),
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(OUTPUT_VIDEO),
    ]
    log.info("FFmpeg 업스케일 실행: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)
    log.info("최종 영상 저장 완료: %s", OUTPUT_VIDEO)


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        log.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    start = time.time()

    video_id, status = submit_sora_job(api_key)

    completed_data: dict | None = None
    if status != "completed":
        completed_data = poll_until_complete(video_id, api_key, start)
    else:
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            r = requests.get(
                f"{SORA_GENERATIONS_URL}/{video_id}",
                headers=headers,
                timeout=60,
            )
            if r.status_code == 200:
                completed_data = r.json()
        except requests.exceptions.RequestException as exc:
            log.warning("완료 데이터 조회 실패: %s", exc)

    download_video(video_id, api_key, completed_data)
    upscale_to_1080p()

    total = int(time.time() - start)
    log.info("전체 완료: %ds / 출력: %s", total, OUTPUT_VIDEO)


if __name__ == "__main__":
    main()
