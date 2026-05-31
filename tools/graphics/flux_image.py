"""FLUX image generation — DEPRECATED (fal.ai FLUX API removed).

This tool previously called FLUX via the fal.ai API (paid, requires FAL_KEY).
All calls are now routed to LocalDiffusion (open-source Stable Diffusion/FLUX.1,
runs locally — FLUX.1 weights are freely available on HuggingFace).

Reason for replacement: fal.ai FLUX requires a paid FAL_KEY. FLUX.1-dev and
FLUX.1-schnell can be run locally via diffusers with no ongoing cost and no data
leaving the machine.
"""
# REPLACED: fal.ai FLUX API removed — routing to local_diffusion (open-source, supports FLUX.1 locally)

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


class FluxImage(BaseTool):
    name = "flux_image"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "image_generation"
    provider = "flux"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.SEEDED
    runtime = ToolRuntime.API

    dependencies = []  # checked dynamically via env var
    install_instructions = (
        "Set FAL_KEY to your fal.ai API key.\n"
        "  Get one at https://fal.ai/dashboard/keys"
    )
    agent_skills = ["flux-best-practices", "bfl-api"]

    capabilities = ["generate_image", "generate_illustration", "text_to_image"]
    supports = {
        "negative_prompt": True,
        "seed": True,
        "custom_size": True,
    }
    best_for = [
        "photorealistic images",
        "general-purpose image generation",
        "high quality at low cost (~$0.03/image)",
    ]
    not_good_for = ["text rendering in images", "offline generation"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "negative_prompt": {"type": "string", "default": ""},
            "width": {"type": "integer", "default": 1024},
            "height": {"type": "integer", "default": 1024},
            "model": {
                "type": "string",
                "enum": ["flux-pro/v1.1", "flux/dev", "flux-pro"],
                "default": "flux-pro/v1.1",
            },
            "seed": {"type": "integer"},
            "num_inference_steps": {"type": "integer"},
            "guidance_scale": {"type": "number"},
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=100, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["prompt", "width", "height", "seed", "model"]
    side_effects = ["writes image file to output_path", "calls fal.ai API"]
    user_visible_verification = ["Inspect generated image for relevance and quality"]

    def _get_api_key(self) -> str | None:
        return os.environ.get("FAL_KEY") or os.environ.get("FAL_AI_API_KEY")

    def get_status(self) -> ToolStatus:
        if self._get_api_key():
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        model = inputs.get("model", "flux-pro/v1.1")
        if "pro" in model:
            return 0.05
        return 0.03  # dev tier

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        # REPLACED: fal.ai FLUX API removed — routing to local_diffusion (open-source, supports FLUX.1 locally)
        from tools.graphics.local_diffusion import LocalDiffusion
        return LocalDiffusion().execute(inputs)
