"""Recraft image generation — DEPRECATED (fal.ai Recraft API removed).

This tool previously called Recraft V4 via the fal.ai API (paid, requires FAL_KEY).
All calls are now routed to LocalDiffusion (open-source Stable Diffusion, runs locally).

Reason for replacement: fal.ai Recraft requires a paid FAL_KEY and sends data to
external cloud services. Stable Diffusion via diffusers runs locally with no ongoing
cost and no data leaving the machine.
"""
# REPLACED: fal.ai Recraft API removed — routing to local_diffusion (open-source)

from __future__ import annotations

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


class RecraftImage(BaseTool):
    name = "recraft_image"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "image_generation"
    provider = "recraft"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set FAL_KEY to your fal.ai API key.\n"
        "  Get one at https://fal.ai/dashboard/keys"
    )
    agent_skills = []

    capabilities = [
        "generate_image",
        "generate_logo",
        "generate_vector",
        "text_to_image",
    ]
    supports = {
        "svg_output": True,
        "text_rendering": True,
        "color_palette": True,
        "custom_size": True,
    }
    best_for = [
        "logos and brand assets",
        "SVG vector output",
        "images with accurate text rendering",
        "clean professional graphics",
    ]
    not_good_for = ["photorealistic images", "offline generation"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "model": {
                "type": "string",
                "enum": ["v4", "v4-pro"],
                "default": "v4",
            },
            "image_size": {
                "type": "string",
                "enum": [
                    "square", "square_hd",
                    "landscape_4_3", "landscape_16_9",
                    "portrait_4_3", "portrait_16_9",
                ],
                "default": "square_hd",
            },
            "style": {
                "type": "string",
                "enum": [
                    "any", "realistic_image", "digital_illustration",
                    "vector_illustration", "icon",
                ],
                "default": "any",
            },
            "colors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Color palette as hex strings, e.g. ['#FF5733', '#2E86C1']",
            },
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=100, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["prompt", "model", "style", "image_size"]
    side_effects = ["writes image file to output_path", "calls fal.ai API"]
    user_visible_verification = ["Inspect generated image for brand accuracy and text readability"]

    def _get_api_key(self) -> str | None:
        return os.environ.get("FAL_KEY") or os.environ.get("FAL_AI_API_KEY")

    def get_status(self) -> ToolStatus:
        if self._get_api_key():
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        model = inputs.get("model", "v4")
        if model == "v4-pro":
            return 0.25
        return 0.04

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        # REPLACED: fal.ai Recraft API removed — routing to local_diffusion (open-source)
        from tools.graphics.local_diffusion import LocalDiffusion
        return LocalDiffusion().execute(inputs)
