"""Runway video generation — DEPRECATED (Runway paid API removed).

This tool previously called the Runway ML API (paid, requires RUNWAY_API_KEY).
All calls are now routed to WanVideo (open-source, runs locally).

Reason for replacement: Runway API requires a paid subscription and sends data
to an external cloud service. Wan2.1 runs locally via diffusers/torch with no
ongoing cost and no data leaving the machine.
"""
# REPLACED: Runway API removed — routing to wan_video (open-source)

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

_RATIO_MAP = {
    "16:9": "1280:720",
    "9:16": "720:1280",
    "1:1": "720:720",
}

_COST_PER_SECOND = {
    "gen3a_turbo": 0.05,
    "gen4_turbo": 0.05,
    "gen4_aleph": 0.15,
    # Third-party Seedance 2.0 inside Runway (Enterprise/Unlimited, non-US).
    "seedance_2.0": 0.30,
    "seedance_2.0_fast": 0.24,
}

_RUNTIME_SECONDS = {
    "gen3a_turbo": 25.0,
    "gen4_turbo": 30.0,
    "gen4_aleph": 60.0,
    "seedance_2.0": 120.0,
    "seedance_2.0_fast": 60.0,
}


class RunwayVideo(BaseTool):
    name = "runway_video"
    version = "0.2.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "runway"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set RUNWAY_API_KEY to your Runway API secret.\n"
        "  Get one at https://dev.runwayml.com/"
    )
    agent_skills = ["seedance-2-0", "ai-video-gen"]

    capabilities = ["text_to_video", "image_to_video"]
    supports = {
        "text_to_video": True,
        "image_to_video": True,
        "professional_control": True,
        "native_audio": True,
        "cinematic_quality": True,
        "camera_direction": True,
        "lip_sync": True,
        "multi_shot": True,
    }
    best_for = [
        "preferred premium video gen on Runway when Seedance 2.0 model is selected",
        "cinematic trailers, teasers, and high-fidelity clips with native synchronized audio (Seedance 2.0 path)",
        "director-level camera control and multi-shot editing (Seedance 2.0) or Runway Gen-4 professional control",
        "lip-sync from quoted dialogue in prompts (Seedance 2.0)",
        "professional video production",
    ]
    not_good_for = ["budget projects", "offline generation", "very long clips"]
    fallback_tools = ["seedance_video", "seedance_replicate", "kling_video", "veo_video", "minimax_video", "wan_video"]
    quality_score = 0.9

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
            "model": {
                "type": "string",
                "enum": ["seedance_2.0", "seedance_2.0_fast", "gen4_turbo", "gen4_aleph", "gen3a_turbo"],
                "default": "seedance_2.0",
                "description": (
                    "seedance_2.0 = preferred premium default (single-pass synced audio, multi-shot, lip-sync — "
                    "Runway Unlimited/Enterprise plan, non-US only). "
                    "seedance_2.0_fast = lower-cost Seedance variant. "
                    "gen4_aleph = Runway's highest-fidelity native model. "
                    "gen4_turbo = balanced Runway native. "
                    "gen3a_turbo = cheapest Runway native."
                ),
            },
            "duration": {
                "type": "integer",
                "enum": [5, 10],
                "default": 5,
                "description": "Duration in seconds",
            },
            "ratio": {
                "type": "string",
                "enum": ["16:9", "9:16", "1:1"],
                "default": "16:9",
            },
            "watermark": {
                "type": "boolean",
                "default": False,
                "description": "Include Runway watermark on output",
            },
            "image_url": {"type": "string", "description": "Reference image URL for image_to_video"},
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=500, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout", "THROTTLED"])
    idempotency_key_fields = ["prompt", "model", "operation", "duration"]
    side_effects = ["writes video file to output_path", "calls Runway API"]
    user_visible_verification = ["Watch generated clip for visual quality and motion coherence"]

    def get_status(self) -> ToolStatus:
        if os.environ.get("RUNWAY_API_KEY") or os.environ.get("RUNWAYML_API_SECRET"):
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def _get_api_key(self) -> str | None:
        return os.environ.get("RUNWAY_API_KEY") or os.environ.get("RUNWAYML_API_SECRET")

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        model = inputs.get("model", "gen4_turbo")
        duration = inputs.get("duration", 5)
        return _COST_PER_SECOND.get(model, 0.05) * duration

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        model = inputs.get("model", "gen4_turbo")
        return _RUNTIME_SECONDS.get(model, 30.0)

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        # REPLACED: Runway API removed — routing to wan_video (open-source)
        from tools.video.wan_video import WanVideo
        return WanVideo().execute(inputs)
