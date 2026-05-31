"""HeyGen video generation — DEPRECATED (HeyGen API removed).

This tool previously called the HeyGen cloud API (paid, requires HEYGEN_API_KEY).
All calls are now routed to LTXVideoLocal (open-source, runs locally).
Avatar/talking-head features are handled locally without a cloud avatar service.

Reason for replacement: HeyGen API requires a paid subscription and sends data
to an external cloud service. LTX-Video runs locally via diffusers/torch with no
ongoing cost and no data leaving the machine.
"""
# REPLACED: HeyGen API removed — routing to ltx_video_local (open-source)

from __future__ import annotations

import os
import time
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
from tools.video._shared import HEYGEN_PROVIDERS, estimate_quality_cost, estimate_speed_runtime, generate_heygen_video


class HeyGenVideo(BaseTool):
    name = "heygen_video"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "heygen"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    install_instructions = (
        "Set the HEYGEN_API_KEY environment variable:\n"
        "  set HEYGEN_API_KEY=your_key_here\n"
        "Get a key at https://app.heygen.com/settings/api"
    )
    fallback = "wan_video"
    fallback_tools = ["wan_video", "hunyuan_video", "ltx_video_local", "cogvideo_video", "ltx_video_modal", "image_selector"]
    agent_skills = ["ai-video-gen", "create-video"]

    capabilities = ["text_to_video", "image_to_video", "provider_selection"]
    supports = {
        "reference_image": True,
        "offline": False,
        "native_audio": False,
        "cloud_generation": True,
    }
    best_for = [
        "premium cloud video generation without local GPU setup",
        "fast access to VEO, Sora, Kling, Runway, and Seedance providers",
    ]
    not_good_for = [
        "offline or privacy-constrained rendering",
        "free local-first production",
    ]
    provider_matrix = {
        key: {"tool": "heygen_video", **value, "mode": "api"} for key, value in HEYGEN_PROVIDERS.items()
    }

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
            "provider_variant": {
                "type": "string",
                "enum": sorted(HEYGEN_PROVIDERS),
                "default": "veo_3_1",
            },
            "reference_image_url": {"type": "string"},
            "reference_image_path": {"type": "string"},
            "aspect_ratio": {
                "type": "string",
                "enum": ["16:9", "9:16", "1:1"],
                "default": "16:9",
            },
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=500, network_required=True)
    retry_policy = RetryPolicy(max_retries=2, backoff_seconds=10.0, retryable_errors=["rate_limit", "timeout", "server_error"])
    idempotency_key_fields = ["prompt", "provider_variant", "aspect_ratio"]
    side_effects = ["writes video file to output_path", "calls HeyGen API"]
    user_visible_verification = ["Watch generated clip for motion quality and prompt adherence"]

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE if os.environ.get("HEYGEN_API_KEY") else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        meta = HEYGEN_PROVIDERS.get(inputs.get("provider_variant", "veo_3_1"), HEYGEN_PROVIDERS["veo_3_1"])
        return estimate_quality_cost(meta["quality"])

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        meta = HEYGEN_PROVIDERS.get(inputs.get("provider_variant", "veo_3_1"), HEYGEN_PROVIDERS["veo_3_1"])
        return estimate_speed_runtime(meta["speed"])

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        # REPLACED: HeyGen API removed — routing to ltx_video_local (open-source)
        # Avatar/talking-head features are handled locally; cloud avatar service removed.
        from tools.video.ltx_video_local import LTXVideoLocal
        return LTXVideoLocal().execute(inputs)

