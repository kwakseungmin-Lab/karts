"""씬11 컷01 영상 생성 스크립트 — Sora sora-2, 1280x720 → 1920x1080 업스케일."""
from __future__ import annotations

import base64
import io
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from PIL import Image, ImageOps

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

SORA_URL = "https://api.openai.com/v1/videos"
POLL_INTERVAL = 10
MAX_WAIT = 600

INPUT_IMAGE = "/Users/ksm2761/karts/short-film-project/final/frames/scene11_cut01_hd.png"
RAW_OUTPUT = "/tmp/scene11_cut01_raw.mp4"
FINAL_OUTPUT = "/Users/ksm2761/karts/short-film-project/final/videos/scene11_cut01.mp4"

SORA_SIZE = "1280x720"
SECONDS = "4"

PROMPT = (
    "Cinematic cross-cutting extreme close-up sequence, alternating between two warriors' faces. "
    "First: Aiden, medieval knight in dark steel partial plate armor with chain mail, scarred face with vertical scar above left eye, "
    "brown hair, eyes slowly closing in exhaustion then tightening jaw in resignation then opening with quiet resolve. "
    "Second: Kagemasa, samurai in deep navy oyoroi armor with gold imperial crest (partially worn), 40s, black hair in topknot, "
    "deep calm eyes reacting identically — sorrow to resignation to resolve. "
    "Desaturating color grade returning, cold blue-grey tone, clouds beginning to obscure the morning sun, "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9"
)


def image_to_data_url(image_path: str, size: str) -> str:
    w, h = map(int, size.split("x"))
    img = Image.open(image_path).convert("RGB")
    img = ImageOps.fit(img, (w, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def submit_job(api_key: str) -> tuple[str, str, dict]:
    print(f"이미지 리사이즈 중 (1920x1080 → {SORA_SIZE})...")
    data_url = image_to_data_url(INPUT_IMAGE, SORA_SIZE)

    payload = {
        "model": "sora-2",
        "prompt": PROMPT,
        "seconds": SECONDS,
        "size": SORA_SIZE,
        "input_reference": {"image_url": data_url},
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    print("Sora 제출 중...")
    resp = requests.post(SORA_URL, headers=headers, json=payload, timeout=60)
    if resp.status_code not in (200, 201, 202):
        print(f"제출 실패 {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    video_id = data.get("id")
    status = data.get("status", "")
    print(f"Job ID: {video_id}, 크기: {data.get('size')}, 초기 상태: {status}")
    return video_id, status, headers


def poll_until_done(video_id: str, headers: dict) -> None:
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        r = requests.get(f"{SORA_URL}/{video_id}", headers=headers, timeout=30)
        if r.status_code != 200:
            print(f"폴링 오류 {r.status_code}", file=sys.stderr)
            continue
        d = r.json()
        s = d.get("status", "")
        progress = d.get("progress", 0)
        print(f"    [{s} {progress}%]", end="\r", flush=True)
        if s == "completed":
            print()
            return
        if s in ("failed", "cancelled"):
            err = (d.get("error") or {}).get("message", s)
            print(f"\n생성 실패: {err}", file=sys.stderr)
            sys.exit(1)
    print("\n타임아웃", file=sys.stderr)
    sys.exit(1)


def download_video(video_id: str, api_key: str) -> None:
    print(f"영상 다운로드 중 → {RAW_OUTPUT}")
    resp = requests.get(
        f"{SORA_URL}/{video_id}/content",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=180,
        stream=True,
    )
    if resp.status_code != 200:
        print(f"다운로드 실패 {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
        sys.exit(1)
    Path(RAW_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_OUTPUT, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    size_mb = Path(RAW_OUTPUT).stat().st_size / 1024 / 1024
    print(f"다운로드 완료.  ({size_mb:.1f} MB)")


def upscale_to_1080p() -> None:
    print(f"FFmpeg 업스케일 {SORA_SIZE} → 1920x1080 → {FINAL_OUTPUT}")
    Path(FINAL_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", RAW_OUTPUT,
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            FINAL_OUTPUT,
        ],
        check=True,
    )
    size_mb = Path(FINAL_OUTPUT).stat().st_size / 1024 / 1024
    print(f"저장 완료: {FINAL_OUTPUT}  ({size_mb:.1f} MB)")


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY 환경변수 없음", file=sys.stderr)
        sys.exit(1)

    video_id, status, headers = submit_job(api_key)

    if status != "completed":
        poll_until_done(video_id, headers)

    download_video(video_id, api_key)
    upscale_to_1080p()
    print(f"\n완료: {FINAL_OUTPUT}")


if __name__ == "__main__":
    main()
