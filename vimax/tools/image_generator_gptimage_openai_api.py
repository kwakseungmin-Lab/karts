"""OpenAI GPT Image (gpt-image-1) 이미지 생성기 — ViMax ImageGenerator protocol 구현.

Nanobanana(Gemini) 대신 OpenAI의 gpt-image-1을 사용.
레퍼런스 이미지가 있으면 edit 엔드포인트, 없으면 generate 엔드포인트를 사용.
"""

import asyncio
import base64
import io
import logging
import os
from typing import List, Optional

import requests
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential

from interfaces.image_output import ImageOutput
from utils.rate_limiter import RateLimiter

OPENAI_IMAGES_URL = "https://api.openai.com/v1/images"

_ASPECT_TO_SIZE = {
    "16:9": "1536x1024",
    "9:16": "1024x1536",
    "1:1": "1024x1024",
}


def _pil_to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.convert("RGBA").save(buf, format="PNG")
    return buf.getvalue()


class ImageGeneratorGptImageOpenAIAPI:
    """gpt-image-1 기반 이미지 생성기 — ViMax ImageGenerator protocol 구현."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-image-1",
        rate_limiter: Optional[RateLimiter] = None,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.")
        self.model = model
        self.rate_limiter = rate_limiter

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=5, max=30))
    async def generate_single_image(
        self,
        prompt: str,
        reference_image_paths: List[str] = [],
        aspect_ratio: Optional[str] = "16:9",
        **kwargs,
    ) -> ImageOutput:
        """gpt-image-1로 단일 이미지 생성.

        reference_image_paths:
          - 0개 → /generations 엔드포인트 (텍스트→이미지)
          - 1개 이상 → /edits 엔드포인트 (이미지+텍스트→이미지)
        """
        if self.rate_limiter:
            await self.rate_limiter.acquire()

        size = _ASPECT_TO_SIZE.get(aspect_ratio or "16:9", "1536x1024")
        logging.info(f"GPT Image {self.model} 이미지 생성 — size={size}, refs={len(reference_image_paths)}")

        if reference_image_paths:
            return await self._edit(prompt, reference_image_paths, size)
        return await self._generate(prompt, size)

    async def _generate(self, prompt: str, size: str) -> ImageOutput:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "output_format": "png",
            "n": 1,
        }
        resp = await asyncio.to_thread(
            requests.post,
            f"{OPENAI_IMAGES_URL}/generations",
            headers=self._headers(),
            json=payload,
            timeout=120,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"GPT Image generate 실패 {resp.status_code}: {resp.text[:300]}")
        b64_data = resp.json()["data"][0]["b64_json"]
        img = Image.open(io.BytesIO(base64.b64decode(b64_data))).convert("RGB")
        return ImageOutput(fmt="pil", ext="png", data=img)

    async def _edit(self, prompt: str, reference_image_paths: List[str], size: str) -> ImageOutput:
        files = []
        try:
            for path in reference_image_paths:
                img = Image.open(path)
                png_bytes = _pil_to_png_bytes(img)
                files.append(("image[]", (os.path.basename(path), png_bytes, "image/png")))

            data = {
                "model": self.model,
                "prompt": prompt,
                "size": size,
                "n": "1",
            }
            resp = await asyncio.to_thread(
                requests.post,
                f"{OPENAI_IMAGES_URL}/edits",
                headers=self._headers(),
                data=data,
                files=files,
                timeout=120,
            )
        finally:
            pass

        if resp.status_code != 200:
            raise RuntimeError(f"GPT Image edit 실패 {resp.status_code}: {resp.text[:300]}")
        b64_data = resp.json()["data"][0]["b64_json"]
        img = Image.open(io.BytesIO(base64.b64decode(b64_data))).convert("RGB")
        return ImageOutput(fmt="pil", ext="png", data=img)
