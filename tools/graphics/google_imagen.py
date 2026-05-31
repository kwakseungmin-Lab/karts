"""Google Imagen image generation — DEPRECATED (Google Imagen API removed).

This tool previously called Google Imagen via the Gemini API (paid, requires GOOGLE_API_KEY).
All calls are now routed to LocalDiffusion (open-source Stable Diffusion, runs locally).

Reason for replacement: Google Imagen API requires a paid API key and sends data
to Google cloud. Stable Diffusion via diffusers runs locally with no ongoing cost
and no data leaving the machine.
"""
# REPLACED: Google Imagen API removed — routing to local_diffusion (open-source)

from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from typing import Any

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

# Aspect ratio to approximate pixel dimensions (for cost/reporting only)
ASPECT_RATIOS = {
    "1:1": (1024, 1024),
    "3:4": (896, 1152),
    "4:3": (1152, 896),
    "9:16": (768, 1344),
    "16:9": (1344, 768),
}


def _dims_to_aspect_ratio(width: int, height: int) -> str:
    """Convert width/height to the nearest supported aspect ratio."""
    target = width / height
    best = "1:1"
    best_diff = float("inf")
    for ratio, (w, h) in ASPECT_RATIOS.items():
        diff = abs(target - w / h)
        if diff < best_diff:
            best_diff = diff
            best = ratio
    return best


class GoogleImagen(BaseTool):
    name = "google_imagen"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "image_generation"
    provider = "google_imagen"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []  # checked dynamically via env var
    install_instructions = (
        "Set GOOGLE_API_KEY (or GEMINI_API_KEY) to your Google AI API key.\n"
        "  Get one at https://aistudio.google.com/apikey"
    )
    agent_skills = []

    capabilities = ["generate_image", "generate_illustration", "text_to_image"]
    supports = {
        "negative_prompt": False,
        "seed": False,
        "custom_size": False,
        "aspect_ratio": True,
    }
    best_for = [
        "high-quality photorealistic images",
        "Google ecosystem integration",
        "fast generation with multiple aspect ratios",
    ]
    not_good_for = [
        "negative prompt control (not supported)",
        "exact pixel dimensions (uses aspect ratios)",
        "offline generation",
    ]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string", "description": "Image description (max 480 tokens)"},
            "aspect_ratio": {
                "type": "string",
                "enum": ["1:1", "3:4", "4:3", "9:16", "16:9"],
                "default": "1:1",
                "description": "Aspect ratio of generated image",
            },
            "width": {
                "type": "integer",
                "description": "Desired width in pixels — mapped to nearest aspect ratio",
            },
            "height": {
                "type": "integer",
                "description": "Desired height in pixels — mapped to nearest aspect ratio",
            },
            "model": {
                "type": "string",
                "enum": [
                    "imagen-4.0-generate-001",
                    "imagen-4.0-fast-generate-001",
                    "imagen-4.0-ultra-generate-001",
                ],
                "default": "imagen-4.0-generate-001",
                "description": "Imagen model variant",
            },
            "number_of_images": {
                "type": "integer",
                "default": 1,
                "minimum": 1,
                "maximum": 4,
            },
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=100, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["prompt", "aspect_ratio", "model"]
    side_effects = ["writes image file to output_path", "calls Google Generative AI API"]
    user_visible_verification = ["Inspect generated image for relevance and quality"]

    def _get_api_key(self) -> str | None:
        return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

    def get_status(self) -> ToolStatus:
        if self._get_api_key():
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        model = inputs.get("model", "imagen-4.0-generate-001")
        n = inputs.get("number_of_images", 1)
        if "ultra" in model:
            return 0.06 * n
        if "fast" in model:
            return 0.02 * n
        return 0.04 * n

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        # REPLACED: Google Imagen API removed — routing to local_diffusion (open-source)
        from tools.graphics.local_diffusion import LocalDiffusion
        return LocalDiffusion().execute(inputs)
