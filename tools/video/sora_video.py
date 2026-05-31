"""OpenAI Sora image-to-video tool."""
from __future__ import annotations

import base64
import os
import time
from pathlib import Path

import requests

from tools.base_tool import BaseTool, ToolResult, ToolTier, ToolRuntime, ToolStability, ResourceProfile


class SoraVideo(BaseTool):
    name = "sora_video"
    version = "0.1.0"
    description = "Image-to-video via OpenAI Sora API"
    tier = ToolTier.GENERATE
    runtime = ToolRuntime.API
    stability = ToolStability.PRODUCTION
    capabilities = ["image_to_video", "text_to_video"]
    providers = ["openai"]
    resource_profile = ResourceProfile(cpu_cores=1, ram_gb=1, vram_gb=0, disk_gb=1, network_required=True)

    MODEL = "sora-1.5"
    GENERATIONS_URL = "https://api.openai.com/v1/video/generations"
    POLL_INTERVAL = 10
    MAX_WAIT = 600

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
        resolution = inputs.get("resolution", "1080p")
        quality = inputs.get("quality", "medium")
        output_path = inputs.get("output_path", "output.mp4")

        payload: dict = {
            "model": self.MODEL,
            "prompt": prompt,
            "n": 1,
            "duration": duration,
            "resolution": resolution,
            "quality": quality,
        }

        # image-to-video: base64 encode the reference image
        if image_path:
            image_bytes = Path(image_path).read_bytes()
            b64 = base64.b64encode(image_bytes).decode()
            ext = Path(image_path).suffix.lstrip(".")
            payload["first_frame"] = f"data:image/{ext};base64,{b64}"

        # submit
        resp = requests.post(self.GENERATIONS_URL, headers=self._headers(), json=payload, timeout=60)
        if resp.status_code != 200:
            return ToolResult(success=False, error=f"Sora submit failed {resp.status_code}: {resp.text}")

        data = resp.json()
        gen_id = data.get("id") or (data.get("data", [{}])[0].get("id"))

        if not gen_id:
            # synchronous response — video URL already present
            video_url = (data.get("data") or [{}])[0].get("url")
            if video_url:
                self._download(video_url, output_path)
                return ToolResult(success=True, data={"output": output_path}, duration_ms=int((time.time()-start)*1000))
            return ToolResult(success=False, error=f"No generation id or url in response: {data}")

        # poll
        poll_url = f"{self.GENERATIONS_URL}/{gen_id}"
        deadline = time.time() + self.MAX_WAIT
        while time.time() < deadline:
            time.sleep(self.POLL_INTERVAL)
            r = requests.get(poll_url, headers=self._headers(), timeout=30)
            if r.status_code != 200:
                continue
            d = r.json()
            status = d.get("status", "")
            if status == "completed":
                video_url = (d.get("data") or [{}])[0].get("url") or d.get("url")
                if video_url:
                    self._download(video_url, output_path)
                    return ToolResult(success=True, data={"output": output_path}, duration_ms=int((time.time()-start)*1000))
                return ToolResult(success=False, error="Completed but no video URL")
            if status in ("failed", "cancelled"):
                return ToolResult(success=False, error=f"Generation {status}: {d}")

        return ToolResult(success=False, error="Timed out waiting for Sora generation")

    def _download(self, url: str, dest: str) -> None:
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, timeout=120, stream=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
