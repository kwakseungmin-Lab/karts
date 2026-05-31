"""Seedance video generation — DEPRECATED (fal.ai Seedance API removed).

This tool previously called ByteDance Seedance 2.0 via the fal.ai API (paid, requires FAL_KEY).
All calls are now routed to WanVideo (open-source, runs locally).

Reason for replacement: fal.ai Seedance requires a paid FAL_KEY and sends data to
external cloud services. Wan2.1 runs locally via diffusers/torch with no ongoing
cost and no data leaving the machine.
"""
# REPLACED: fal.ai Seedance API removed — routing to wan_video (open-source)

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


class SeedanceVideo(BaseTool):
    name = "seedance_video"
    version = "0.2.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "seedance"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set FAL_KEY to your fal.ai API key.\n"
        "  Get one at https://fal.ai/dashboard/keys"
    )
    agent_skills = ["seedance-2-0", "ai-video-gen"]

    capabilities = ["text_to_video", "image_to_video", "reference_to_video"]
    supports = {
        "text_to_video": True,
        "image_to_video": True,
        "reference_to_video": True,
        "multiple_reference_images": True,
        "reference_image": True,
        "native_audio": True,
        "cinematic_quality": True,
        "camera_direction": True,
        "lip_sync": True,
        "multi_shot": True,
        "aspect_ratio": True,
        "seed": True,
    }
    best_for = [
        "preferred premium video gen when FAL_KEY is available",
        "cinematic trailers, teasers, and high-fidelity clips with native synchronized audio",
        "director-level camera control and multi-shot editing in a single generation",
        "lip-sync from quoted dialogue in prompts",
        "reference-conditioned generation (up to 9 images + 3 video clips + 3 audio clips)",
        "consistent character identity across shots",
    ]
    not_good_for = ["offline generation", "budget-constrained projects"]
    fallback_tools = ["veo_video", "kling_video", "minimax_video"]
    # Premium model — beat out "experimental stability" baseline. The scoring
    # engine reads quality_score directly when present (see lib/scoring.py).
    quality_score = 0.95

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "operation": {
                "type": "string",
                "enum": ["text_to_video", "image_to_video", "reference_to_video"],
                "default": "text_to_video",
            },
            "model_variant": {
                "type": "string",
                "enum": ["standard", "fast"],
                "default": "standard",
                "description": "standard = highest quality, fast = lower latency and cost",
            },
            "duration": {
                "type": "string",
                "enum": ["auto", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"],
                "default": "5",
                "description": "Duration in seconds. 'auto' lets the model decide.",
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["auto", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"],
                "default": "16:9",
            },
            "resolution": {
                "type": "string",
                "enum": ["480p", "720p"],
                "default": "720p",
            },
            "generate_audio": {
                "type": "boolean",
                "default": True,
                "description": "Generate synchronized audio (speech, SFX, ambient)",
            },
            "image_url": {
                "type": "string",
                "description": "Start frame image URL for image_to_video (jpg, png, webp)",
            },
            "image_path": {
                "type": "string",
                "description": "Local start-frame path for image_to_video. Auto-uploaded to fal.ai storage.",
            },
            "end_image_url": {
                "type": "string",
                "description": "Optional end frame URL for image_to_video",
            },
            "reference_image_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Up to 9 reference image URLs for reference_to_video (identity / wardrobe / setting / style anchors).",
            },
            "reference_image_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Local reference image paths for reference_to_video. Auto-uploaded to fal.ai storage.",
            },
            "reference_video_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Up to 3 reference video clip URLs for reference_to_video (motion / camera / pacing anchors).",
            },
            "reference_audio_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Up to 3 reference audio clip URLs for reference_to_video (voice / music / ambience anchors).",
            },
            "seed": {
                "type": "integer",
                "description": "Optional seed for reproducibility",
            },
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=500, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["prompt", "model_variant", "operation", "duration", "seed"]
    side_effects = ["writes video file to output_path", "calls fal.ai API"]
    user_visible_verification = [
        "Watch generated clip for motion coherence, audio sync, and visual quality"
    ]

    def _get_api_key(self) -> str | None:
        return os.environ.get("FAL_KEY") or os.environ.get("FAL_AI_API_KEY")

    def get_status(self) -> ToolStatus:
        if self._get_api_key():
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        variant = inputs.get("model_variant", "standard")
        duration = inputs.get("duration", "5")
        secs = 5 if duration == "auto" else int(duration)
        rate = 0.2419 if variant == "fast" else 0.3034
        return round(rate * secs, 2)

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        variant = inputs.get("model_variant", "standard")
        return 60.0 if variant == "fast" else 120.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        # REPLACED: fal.ai Seedance API removed — routing to wan_video (open-source)
        from tools.video.wan_video import WanVideo
        return WanVideo().execute(inputs)
