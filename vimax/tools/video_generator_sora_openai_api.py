"""OpenAI Sora video generator implementing ViMax's VideoGenerator protocol.

Veo는 Google 전용이라 Sora(sora-2) REST API로 교체.
image_to_video(첫 프레임 레퍼런스)와 text_to_video 모두 지원.
"""

import asyncio
import base64
import io
import logging
import os
import time
from pathlib import Path
from typing import List, Optional

import requests
from PIL import Image, ImageOps

from interfaces.video_output import VideoOutput
from utils.rate_limiter import RateLimiter

SORA_GENERATIONS_URL = "https://api.openai.com/v1/videos"
POLL_INTERVAL = 10
MAX_WAIT = 600

_SORA_DURATION_SUPPORTED = (4, 8, 12)
_SORA_ASPECT_TO_SIZE = {
    "16:9": "1792x1024",
    "9:16": "1024x1792",
    "1:1": "1024x1024",
}


def _snap_duration(seconds: int) -> int:
    for s in _SORA_DURATION_SUPPORTED:
        if seconds <= s:
            return s
    return 12


def _image_to_data_url(image_path: str, width: int, height: int) -> str:
    img = Image.open(image_path).convert("RGB")
    img = ImageOps.fit(img, (width, height), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


class VideoGeneratorSoraOpenAIAPI:
    """Sora(sora-2) 기반 비디오 생성기 — ViMax VideoGenerator protocol 구현."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "sora-2",
        rate_limiter: Optional[RateLimiter] = None,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.")
        self.model = model
        self.rate_limiter = rate_limiter

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_single_video(
        self,
        prompt: str,
        reference_image_paths: List[str],
        aspect_ratio: str = "16:9",
        duration: int = 8,
        **kwargs,
    ) -> VideoOutput:
        """Sora로 단일 클립 생성.

        reference_image_paths:
          - 0개 → text-to-video
          - 1개 이상 → 첫 번째를 first-frame으로 사용 (Sora는 last-frame 미지원)
        """
        if self.rate_limiter:
            await self.rate_limiter.acquire()

        size = _SORA_ASPECT_TO_SIZE.get(aspect_ratio, "1792x1024")
        seconds = str(_snap_duration(duration))
        w, h = map(int, size.split("x"))

        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "seconds": seconds,
            "size": size,
        }

        if reference_image_paths:
            data_url = _image_to_data_url(reference_image_paths[0], w, h)
            payload["input_reference"] = {"image_url": data_url}
            if len(reference_image_paths) > 1:
                logging.warning(
                    "Sora는 last-frame을 지원하지 않습니다. "
                    "첫 번째 레퍼런스 이미지만 first-frame으로 사용합니다."
                )

        logging.info(f"Sora {self.model} 비디오 생성 요청 — size={size}, duration={seconds}s")

        resp = await asyncio.to_thread(
            requests.post,
            SORA_GENERATIONS_URL,
            headers=self._headers(),
            json=payload,
            timeout=60,
        )
        if resp.status_code not in (200, 201, 202):
            raise RuntimeError(f"Sora 제출 실패 {resp.status_code}: {resp.text}")

        data = resp.json()
        video_id = data.get("id")
        status = data.get("status", "")

        if status == "completed":
            return await self._download(video_id)

        if not video_id:
            raise RuntimeError(f"video_id 없음: {data}")

        deadline = time.time() + MAX_WAIT
        while time.time() < deadline:
            await asyncio.sleep(POLL_INTERVAL)
            r = await asyncio.to_thread(
                requests.get,
                f"{SORA_GENERATIONS_URL}/{video_id}",
                headers=self._headers(),
                timeout=30,
            )
            if r.status_code != 200:
                continue
            d = r.json()
            s = d.get("status", "")
            logging.info(f"  Sora 상태: {s} ({d.get('progress', 0)}%)")
            if s == "completed":
                return await self._download(video_id)
            if s in ("failed", "cancelled"):
                err = (d.get("error") or {}).get("message", s)
                raise RuntimeError(f"Sora 생성 {s}: {err}")

        raise RuntimeError("Sora 생성 타임아웃 (10분 초과)")

    async def _download(self, video_id: str) -> VideoOutput:
        resp = await asyncio.to_thread(
            requests.get,
            f"{SORA_GENERATIONS_URL}/{video_id}/content/video",
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=120,
            stream=True,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Sora 다운로드 실패 {resp.status_code}: {resp.text[:200]}")
        video_bytes = b"".join(resp.iter_content(chunk_size=8192))
        logging.info(f"  Sora 다운로드 완료 ({len(video_bytes)//1024}KB)")
        return VideoOutput(fmt="bytes", ext="mp4", data=video_bytes)
