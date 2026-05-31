"""MiniMax (Hailuo AI) video generation — DEPRECATED (fal.ai MiniMax API removed).

This tool previously called MiniMax (Hailuo AI) via the fal.ai API (paid, requires FAL_KEY).
All calls are now routed to LTXVideoLocal (open-source, runs locally).

Reason for replacement: fal.ai MiniMax requires a paid FAL_KEY and sends data to
external cloud services. LTX-Video runs locally via diffusers/torch with no ongoing
cost and no data leaving the machine.
"""
# REPLACED: fal.ai MiniMax API removed — routing to ltx_video_local (open-source)

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


class MiniMaxVideo(BaseTool):
    name = "minimax_video"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "minimax"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set FAL_KEY to your fal.ai API key.\n"
        "  Get one at https://fal.ai/dashboard/keys"
    )
    agent_skills = ["ai-video-gen"]

    capabilities = ["text_to_video", "image_to_video"]
    supports = {
        "text_to_video": True,
        "image_to_video": True,
        "camera_direction": True,
    }
    best_for = [
        "prompt-following with camera directions (framing, motion, composition)",
        "high-texture footage with minimal hallucination",
        "cost-effective video generation",
    ]
    not_good_for = ["offline generation", "very long clips"]
    fallback_tools = ["kling_video", "veo_video", "wan_video"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "operation": {
                "type": "string",
                "enum": ["text_to_video", "image_to_video"],
                "default": "text_to_video",
            },
            "model_variant": {
                "type": "string",
                "enum": [
                    "video-01", "hailuo-02/pro", "hailuo-02/standard",
                    "hailuo-2.3-fast/pro", "hailuo-2.3-fast/standard",
                ],
                "default": "hailuo-02/pro",
            },
            "image_url": {"type": "string", "description": "Reference image URL for image_to_video"},
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=500, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["prompt", "model_variant", "operation"]
    side_effects = ["writes video file to output_path", "calls fal.ai API"]
    user_visible_verification = ["Watch generated clip for motion coherence and prompt adherence"]

    def _get_api_key(self) -> str | None:
        return os.environ.get("FAL_KEY") or os.environ.get("FAL_AI_API_KEY")

    def get_status(self) -> ToolStatus:
        if self._get_api_key():
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        variant = inputs.get("model_variant", "hailuo-02/pro")
        if "pro" in variant:
            return 0.15
        if "fast" in variant:
            return 0.08
        return 0.10  # standard

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        variant = inputs.get("model_variant", "hailuo-02/pro")
        if "fast" in variant:
            return 30.0
        return 60.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        # REPLACED: fal.ai MiniMax API removed — routing to ltx_video_local (open-source)
        from tools.video.ltx_video_local import LTXVideoLocal
        return LTXVideoLocal().execute(inputs)
