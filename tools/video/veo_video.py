"""Google Veo video generation — DEPRECATED (Google Veo fal.ai API removed).

This tool previously called Google Veo 3.1 via the fal.ai API (paid, requires FAL_KEY).
All calls are now routed to CogVideoX (open-source, runs locally).

Reason for replacement: fal.ai Veo requires a paid FAL_KEY and sends data to
Google/fal.ai cloud services. CogVideoX runs locally via diffusers/torch with
no ongoing cost and no data leaving the machine.
"""
# REPLACED: Google Veo fal.ai API removed — routing to cogvideo_video (open-source)

from __future__ import annotations

import os
import mimetypes
import base64
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


class VeoVideo(BaseTool):
    name = "veo_video"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "veo"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set FAL_KEY or FAL_AI_API_KEY to your fal.ai API key.\n"
        "  Get one at https://fal.ai/dashboard/keys"
    )
    agent_skills = ["ai-video-gen"]

    capabilities = ["text_to_video", "image_to_video", "reference_to_video", "first_last_frame_to_video"]
    supports = {
        "text_to_video": True,
        "image_to_video": True,
        "reference_to_video": True,
        "first_last_frame_to_video": True,
        "native_audio": True,
        "dialogue_generation": True,
        "ambient_sound": True,
    }
    best_for = [
        "videos with synchronized dialogue and audio",
        "cutting-edge quality from Google DeepMind",
        "ambient sound and music generation built in",
    ]
    not_good_for = ["budget projects", "offline generation", "quick iteration"]
    fallback_tools = ["kling_video", "minimax_video", "wan_video"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "operation": {
                "type": "string",
                "enum": ["text_to_video", "image_to_video", "reference_to_video", "first_last_frame_to_video"],
                "default": "text_to_video",
            },
            "model_variant": {
                "type": "string",
                "enum": ["veo3", "veo3/fast", "veo3.1", "veo3.1/fast"],
                "default": "veo3.1",
            },
            "duration": {
                "type": "string",
                "enum": ["4s", "6s", "8s"],
                "default": "8s",
                "description": "Duration in seconds",
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["16:9", "9:16"],
                "default": "16:9",
            },
            "generate_audio": {
                "type": "boolean",
                "default": True,
                "description": "Whether to generate synchronized audio",
            },
            "resolution": {
                "type": "string",
                "enum": ["720p", "1080p", "4k"],
                "default": "1080p",
            },
            "negative_prompt": {"type": "string"},
            "seed": {"type": "integer"},
            "auto_fix": {"type": "boolean", "default": True},
            "safety_tolerance": {
                "type": "string",
                "enum": ["1", "2", "3", "4", "5", "6"],
                "default": "4",
            },
            "image_url": {"type": "string", "description": "Reference image URL for image_to_video"},
            "image_path": {"type": "string", "description": "Local reference image path for image_to_video"},
            "reference_image_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Reference image URLs for reference_to_video",
            },
            "reference_image_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Local reference image paths for reference_to_video",
            },
            "first_frame_url": {"type": "string"},
            "first_frame_path": {"type": "string"},
            "last_frame_url": {"type": "string"},
            "last_frame_path": {"type": "string"},
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=500, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["prompt", "model_variant", "operation", "duration"]
    side_effects = ["writes video file to output_path", "calls fal.ai API"]
    user_visible_verification = [
        "Watch generated clip for visual quality and motion",
        "Listen for audio synchronization and quality",
    ]

    def _get_api_key(self) -> str | None:
        return os.environ.get("FAL_KEY") or os.environ.get("FAL_AI_API_KEY")

    def get_status(self) -> ToolStatus:
        if self._get_api_key():
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        variant = inputs.get("model_variant", "veo3.1")
        duration_text = str(inputs.get("duration", "8s")).replace("s", "")
        duration = int(duration_text)
        resolution = inputs.get("resolution", "1080p")
        generate_audio = bool(inputs.get("generate_audio", True))

        if "fast" in variant:
            base_per_second = 0.10
            audio_per_second = 0.20
        else:
            if resolution == "4k":
                base_per_second = 0.40
                audio_per_second = 0.60
            else:
                base_per_second = 0.20
                audio_per_second = 0.40

        return (audio_per_second if generate_audio else base_per_second) * duration

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        variant = inputs.get("model_variant", "veo3.1")
        if "fast" in variant:
            return 45.0
        return 120.0

    @staticmethod
    def _file_to_data_uri(path_str: str) -> str:
        path = Path(path_str)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
        mime_type, _ = mimetypes.guess_type(path.name)
        if not mime_type:
            mime_type = "application/octet-stream"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _normalize_file_input(self, url_value: str | None, path_value: str | None) -> str | None:
        if url_value:
            return url_value
        if path_value:
            return self._file_to_data_uri(path_value)
        return None

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        # REPLACED: Google Veo fal.ai API removed — routing to cogvideo_video (open-source)
        from tools.video.cogvideo_video import CogVideoVideo
        return CogVideoVideo().execute(inputs)
