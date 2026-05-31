"""Higgsfield video generation — DEPRECATED (Higgsfield Cloud API removed).

This tool previously called the Higgsfield Cloud API (paid, requires HIGGSFIELD_API_KEY).
All calls are now routed to LTXVideoLocal (open-source, runs locally).

Reason for replacement: Higgsfield Cloud API requires paid credentials and sends data
to an external cloud service. LTX-Video runs locally via diffusers/torch with no
ongoing cost and no data leaving the machine.
"""
# REPLACED: Higgsfield Cloud API removed — routing to ltx_video_local (open-source)

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


class HiggsFieldVideo(BaseTool):
    name = "higgsfield_video"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "higgsfield"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set HIGGSFIELD_API_KEY and HIGGSFIELD_API_SECRET for your Higgsfield Cloud credentials.\n"
        "  Get them at https://cloud.higgsfield.ai/api-keys\n"
        "  Alternatively, set HIGGSFIELD_KEY as a combined key:secret value."
    )
    agent_skills = ["seedance-2-0", "ai-video-gen"]

    capabilities = ["text_to_video", "image_to_video"]
    supports = {
        "text_to_video": True,
        "image_to_video": True,
        "character_consistency": True,
        "multi_model_routing": True,
        "native_audio": True,
        "cinematic_quality": True,
        "camera_direction": True,
        "lip_sync": True,
        "multi_shot": True,
    }
    best_for = [
        "preferred premium video gen on Higgsfield (Seedance 2.0 is the default model)",
        "cinematic trailers, teasers, and high-fidelity clips with native synchronized audio",
        "character-consistent video generation (Soul ID + Seedance 2.0 identity consistency)",
        "director-level camera control and multi-shot editing in a single generation",
        "lip-sync from quoted dialogue in prompts",
        "multi-model access through a single API (Seedance 2.0, Kling, Veo, Sora, WAN)",
    ]
    not_good_for = ["offline generation", "fine-grained model control", "budget projects without subscription"]
    fallback_tools = ["seedance_video", "seedance_replicate", "kling_video", "veo_video", "minimax_video"]
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
                "enum": [
                    "seedance_2.0",
                    "seedance_2.0_fast",
                    "kling_3.0",
                    "veo_3.1",
                    "sora_2",
                    "wan_2.5",
                    "soul_cinema",
                ],
                "default": "seedance_2.0",
                "description": "Underlying model. Defaults to Seedance 2.0 (preferred premium) — see .agents/skills/seedance-2-0/",
            },
            "duration": {
                "type": "string",
                "enum": ["5", "10", "15"],
                "default": "5",
                "description": "Duration in seconds (availability varies by model)",
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["16:9", "9:16", "1:1", "21:9"],
                "default": "16:9",
            },
            "image_url": {"type": "string", "description": "Reference image URL for image_to_video"},
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=500, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["prompt", "model", "operation", "duration"]
    side_effects = ["writes video file to output_path", "calls Higgsfield Cloud API"]
    user_visible_verification = ["Watch generated clip for motion coherence and visual quality"]

    def _get_credentials(self) -> tuple[str, str] | None:
        """Return (api_key, api_secret) or None if not configured."""
        combined = os.environ.get("HIGGSFIELD_KEY")
        if combined and ":" in combined:
            key, secret = combined.split(":", 1)
            return key, secret
        key = os.environ.get("HIGGSFIELD_API_KEY")
        secret = os.environ.get("HIGGSFIELD_API_SECRET")
        if key and secret:
            return key, secret
        return None

    def get_status(self) -> ToolStatus:
        if self._get_credentials():
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        model = inputs.get("model", "seedance_2.0")
        duration = int(inputs.get("duration", "5"))
        # Approximate per-clip costs based on Higgsfield credit pricing.
        # Seedance 2.0 on Higgsfield runs ~50-80 credits per 5s clip ≈ $0.50-$1.20.
        base_costs = {
            "seedance_2.0": 0.80,
            "seedance_2.0_fast": 0.50,
            "kling_3.0": 0.10,
            "wan_2.5": 0.10,
            "veo_3.1": 0.50,
            "sora_2": 0.50,
            "soul_cinema": 0.15,
        }
        base = base_costs.get(model, 0.15)
        return base * (duration / 5)

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        model = inputs.get("model", "seedance_2.0")
        if model in ("veo_3.1", "sora_2", "seedance_2.0"):
            return 120.0
        if model == "seedance_2.0_fast":
            return 60.0
        return 60.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        # REPLACED: Higgsfield Cloud API removed — routing to ltx_video_local (open-source)
        from tools.video.ltx_video_local import LTXVideoLocal
        return LTXVideoLocal().execute(inputs)
