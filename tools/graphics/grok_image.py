"""xAI Grok image generation — DEPRECATED (xAI Grok image API removed).

This tool previously called the xAI Grok Imagine Image API (paid, requires XAI_API_KEY).
All calls are now routed to LocalDiffusion (open-source Stable Diffusion, runs locally).

Reason for replacement: xAI Grok image API requires a paid API key and sends data
to xAI cloud services. Stable Diffusion via diffusers runs locally with no ongoing
cost and no data leaving the machine.
"""
# REPLACED: xAI Grok image API removed — routing to local_diffusion (open-source)

from __future__ import annotations

import base64
import mimetypes
import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)


def _file_to_data_uri(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    mime_type, _ = mimetypes.guess_type(path.name)
    if not mime_type:
        mime_type = "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _normalize_image_input(url_value: str | None, path_value: str | None) -> dict[str, str] | None:
    if url_value:
        return {"url": url_value, "type": "image_url"}
    if path_value:
        return {"url": _file_to_data_uri(path_value), "type": "image_url"}
    return None


class GrokImage(BaseTool):
    name = "grok_image"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "image_generation"
    provider = "grok"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set XAI_API_KEY to your xAI API key.\n"
        "  Get one from the xAI developer console"
    )
    agent_skills = ["grok-media"]

    capabilities = [
        "generate_image",
        "edit_image",
        "text_to_image",
        "image_to_image",
        "style_transfer",
    ]
    supports = {
        "image_edit": True,
        "multiple_outputs": True,
        "aspect_ratio": True,
        "resolution": True,
        "reference_image": True,
        "multiple_reference_images": True,
    }
    best_for = [
        "single-image edits and style transfers",
        "multi-image compositing into one generated frame",
        "general-purpose image generation with aspect ratio control",
    ]
    not_good_for = ["offline generation", "strict seeded reproducibility"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "generation_mode": {
                "type": "string",
                "enum": ["generate", "edit"],
                "default": "generate",
                "description": "Use 'edit' when providing one or more source images.",
            },
            "model": {
                "type": "string",
                "enum": ["grok-imagine-image"],
                "default": "grok-imagine-image",
            },
            "aspect_ratio": {"type": "string", "description": "Examples: 1:1, 3:2, 16:9, 9:16"},
            "resolution": {
                "type": "string",
                "enum": ["1k", "2k"],
                "description": "xAI image output resolution tier",
            },
            "n": {
                "type": "integer",
                "minimum": 1,
                "maximum": 10,
                "default": 1,
            },
            "image_url": {"type": "string", "description": "Single source image URL for edit mode"},
            "image_path": {"type": "string", "description": "Single local source image path for edit mode"},
            "image_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Multiple source image URLs for compositing edits",
            },
            "image_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Multiple local source image paths for compositing edits",
            },
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=100, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["prompt", "generation_mode", "model", "aspect_ratio", "resolution", "n"]
    side_effects = ["writes image file(s) to output_path", "calls xAI image API"]
    user_visible_verification = ["Inspect generated image(s) for composition quality and edit fidelity"]

    def get_status(self) -> ToolStatus:
        if os.environ.get("XAI_API_KEY"):
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    @staticmethod
    def _input_image_count(inputs: dict[str, Any]) -> int:
        count = 0
        if inputs.get("image_url") or inputs.get("image_path"):
            count += 1
        count += len(inputs.get("image_urls") or [])
        count += len(inputs.get("image_paths") or [])
        return count

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        output_count = int(inputs.get("n", 1))
        input_count = self._input_image_count(inputs)
        # xAI currently publishes Grok Imagine Image at $0.02 per generated
        # image plus $0.002 per input image for edits or composites.
        return output_count * 0.02 + input_count * 0.002

    def _build_payload(self, inputs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        mode = inputs.get("generation_mode", "generate")
        payload: dict[str, Any] = {
            "model": inputs.get("model", "grok-imagine-image"),
            "prompt": inputs["prompt"],
        }
        if inputs.get("aspect_ratio"):
            payload["aspect_ratio"] = inputs["aspect_ratio"]
        if inputs.get("resolution"):
            payload["resolution"] = inputs["resolution"]
        if inputs.get("n"):
            payload["n"] = inputs["n"]

        primary_image = _normalize_image_input(inputs.get("image_url"), inputs.get("image_path"))
        extra_images = [
            {"url": url, "type": "image_url"}
            for url in (inputs.get("image_urls") or [])
        ]
        extra_images.extend(
            {"url": _file_to_data_uri(path), "type": "image_url"}
            for path in (inputs.get("image_paths") or [])
        )

        if primary_image or extra_images:
            mode = "edit"

        if mode == "edit":
            endpoint = "https://api.x.ai/v1/images/edits"
            if primary_image and not extra_images:
                payload["image"] = primary_image
            else:
                images = []
                if primary_image:
                    images.append(primary_image)
                images.extend(extra_images)
                if not images:
                    raise ValueError(
                        "Edit mode requires image_url/image_path or image_urls/image_paths"
                    )
                payload["images"] = images
        else:
            endpoint = "https://api.x.ai/v1/images/generations"

        return endpoint, payload

    @staticmethod
    def _infer_extension(url: str) -> str:
        suffix = Path(urlparse(url).path).suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
            return suffix
        return ".png"

    @staticmethod
    def _output_paths(output_path: str | None, count: int, extension: str) -> list[Path]:
        if not output_path:
            stem = "grok_image"
            return [Path(f"{stem}_{idx + 1}{extension}") for idx in range(count)]

        path = Path(output_path)
        suffix = path.suffix or extension
        if count == 1:
            return [path if path.suffix else path.with_suffix(suffix)]

        base = path.with_suffix("") if path.suffix else path
        return [base.parent / f"{base.name}_{idx + 1}{suffix}" for idx in range(count)]

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        # REPLACED: xAI Grok image API removed — routing to local_diffusion (open-source)
        from tools.graphics.local_diffusion import LocalDiffusion
        return LocalDiffusion().execute(inputs)
