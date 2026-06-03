"""Generate scene12_cut06 video using Sora sora-2."""
from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, "/Users/ksm2761/karts")

from tools.video.sora_video import SoraVideo

INPUT_IMAGE = "/Users/ksm2761/karts/short-film-project/final/frames/scene12_cut06_hd.png"
RAW_OUTPUT = "/tmp/scene12_cut06_raw.mp4"
FINAL_OUTPUT = "/Users/ksm2761/karts/short-film-project/final/videos/scene12_cut06.mp4"
SORA_SIZE = "1280x720"
SECONDS = 8

PROMPT = (
    "Cinematic title card, full black screen, centered title text '명예의 무게' with subtitle "
    "'The Weight of Honor' in elegant serif typography, subtle grey-white lettering on pure black, "
    "no decoration, minimal and dignified, final frame of film, 1920x1080 16:9. "
    "Slow fade to black over 3 seconds then title text fades in over 3 seconds, "
    "complete silence on last frame"
)


def main() -> None:
    tool = SoraVideo()
    ok, msg = tool.check_dependencies()
    if not ok:
        print(f"ERROR: {msg}", file=sys.stderr)
        sys.exit(1)

    print(f"Submitting Sora job — image: {INPUT_IMAGE}, size: {SORA_SIZE}, seconds: {SECONDS}")
    result = tool.execute(
        {
            "prompt": PROMPT,
            "image_path": INPUT_IMAGE,
            "duration": SECONDS,
            "size": SORA_SIZE,
            "output_path": RAW_OUTPUT,
        }
    )

    if not result.success:
        print(f"ERROR: Sora generation failed — {result.error}", file=sys.stderr)
        sys.exit(1)

    video_id = result.data.get("video_id", "unknown")
    duration = result.duration_seconds or 0
    print(f"Sora generation complete — video_id={video_id}, elapsed={duration:.1f}s")
    print(f"Raw output: {RAW_OUTPUT}")

    # FFmpeg upscale to 1920x1080
    print(f"Upscaling to 1920x1080 → {FINAL_OUTPUT}")
    Path(FINAL_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", RAW_OUTPUT,
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            FINAL_OUTPUT,
        ],
        check=True,
    )
    print(f"Done: {FINAL_OUTPUT}")


if __name__ == "__main__":
    main()
