"""OpenAI Sora image-to-video tool.

SDK의 create()는 input_reference를 항상 multipart file로 처리하므로
image_url 방식(ImageInputReferenceParam)을 JSON body로 전달할 수 없다.
requests로 직접 REST 호출해서 우회한다.

다운로드는 /videos/{id}/content REST 엔드포인트를 사용한다.
"""
from __future__ import annotations

import base64
import io
import os
import time
from pathlib import Path

import requests

from tools.base_tool import BaseTool, ToolResult, ToolTier, ToolRuntime, ToolStability, ResourceProfile

SORA_GENERATIONS_URL = "https://api.openai.com/v1/videos"
POLL_INTERVAL = 10
MAX_WAIT = 600


def _nearest_seconds(n: int) -> str:
    for s in (4, 8, 12):
        if n <= s:
            return str(s)
    return "12"


def _image_to_data_url(image_path: str, size: str) -> str:
    from PIL import Image, ImageOps

    w, h = map(int, size.split("x"))
    img = Image.open(image_path).convert("RGB")
    img = ImageOps.fit(img, (w, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


class SoraVideo(BaseTool):
    name = "sora_video"
    version = "0.5.1"
    description = "Image-to-video via OpenAI Sora API (sora-2)"
    tier = ToolTier.GENERATE
    runtime = ToolRuntime.API
    stability = ToolStability.PRODUCTION
    capabilities = ["image_to_video", "text_to_video"]
    providers = ["openai"]
    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=1024, network_required=True)

    MODEL = "sora-2"

    def check_dependencies(self) -> tuple[bool, str]:
        if not os.environ.get("OPENAI_API_KEY"):
            return False, "OPENAI_API_KEY not set"
        return True, ""

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "Content-Type": "application/json",
        }

    def execute(self, inputs: dict) -> ToolResult:
        start = time.time()
        ok, msg = self.check_dependencies()
        if not ok:
            return ToolResult(success=False, error=msg)

        prompt = inputs.get("prompt", "")
        image_path = inputs.get("image_path")
        duration = int(inputs.get("duration", 5))
        size = inputs.get("size", "1280x720")
        output_path = inputs.get("output_path", "output.mp4")
        seconds = _nearest_seconds(duration)

        payload: dict = {
            "model": self.MODEL,
            "prompt": prompt,
            "seconds": seconds,
            "size": size,
        }

        if image_path:
            data_url = _image_to_data_url(image_path, size)
            payload["input_reference"] = {"image_url": data_url}

        # 제출
        resp = requests.post(SORA_GENERATIONS_URL, headers=self._headers(), json=payload, timeout=60)
        if resp.status_code not in (200, 201, 202):
            return ToolResult(success=False, error=f"Submit failed {resp.status_code}: {resp.text}")

        data = resp.json()
        video_id = data.get("id")
        status = data.get("status", "")

        # 이미 완료된 경우
        if status == "completed":
            return self._download_and_return(video_id, output_path, start)

        if not video_id:
            return ToolResult(success=False, error=f"No video id in response: {data}")

        # 폴링
        deadline = time.time() + MAX_WAIT
        while time.time() < deadline:
            time.sleep(POLL_INTERVAL)
            r = requests.get(f"{SORA_GENERATIONS_URL}/{video_id}", headers=self._headers(), timeout=30)
            if r.status_code != 200:
                continue
            d = r.json()
            s = d.get("status", "")
            print(f"    [{s} {d.get('progress', 0)}%]", end="\r", flush=True)
            if s == "completed":
                return self._download_and_return(video_id, output_path, start)
            if s in ("failed", "cancelled"):
                err = (d.get("error") or {}).get("message", s)
                return ToolResult(success=False, error=f"Generation {s}: {err}")

        return ToolResult(success=False, error="Timed out waiting for Sora generation")

    def _download_and_return(self, video_id: str, output_path: str, start: float) -> ToolResult:
        """REST /videos/{id}/content 엔드포인트로 mp4 저장."""
        resp = requests.get(
            f"{SORA_GENERATIONS_URL}/{video_id}/content",
            headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
            timeout=120,
            stream=True,
        )
        if resp.status_code != 200:
            return ToolResult(success=False, error=f"Download failed {resp.status_code}: {resp.text[:200]}")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        print()
        return ToolResult(
            success=True,
            data={"output": output_path, "video_id": video_id},
            duration_seconds=time.time() - start,
        )
