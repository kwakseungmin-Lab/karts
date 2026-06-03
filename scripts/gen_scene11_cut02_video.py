"""Generate scene11_cut02 video using Sora sora-2, then upscale to 1920x1080.

Sora sora-2 currently supports only 720x1280 and 1280x720.
We generate at 1280x720 (landscape) and upscale to 1920x1080 via FFmpeg lanczos.
"""
from __future__ import annotations

import subprocess
import sys

sys.path.insert(0, "/Users/ksm2761/karts")

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path("/Users/ksm2761/karts/.env"))

from tools.video.sora_video import SoraVideo

INPUT_IMAGE = "/Users/ksm2761/karts/short-film-project/final/frames/scene11_cut02_hd.png"
RAW_OUTPUT = "/tmp/scene11_cut02_raw.mp4"
FINAL_OUTPUT = "/Users/ksm2761/karts/short-film-project/final/videos/scene11_cut02.mp4"

# Sora sora-2 currently only accepts 1280x720 or 720x1280
SORA_SIZE = "1280x720"

PROMPT = (
    "Cinematic static wide shot, locked-off camera, full ruined stone bridge visible from center, "
    "two warriors separating in opposite directions. "
    "Left side: Aiden, medieval knight in dark steel partial plate armor with chain mail, "
    "back to camera, longsword with runic engravings at side, walking toward the Ashfeld gothic ruin end of the bridge. "
    "Right side: Kagemasa, samurai in deep navy oyoroi armor with gold imperial crest, wide shoulder sode, "
    "nodachi sword with cherry blossom tsuba sheathed, back to camera, walking toward the Myre mist end. "
    "Symmetrical composition, bridge centre empty, fog rolling back in from both sides, "
    "morning light dimming as clouds gather, cold desaturating blue-grey tone, "
    "For Honor cinematic trailer style, photorealistic. "
    "Motion: Static locked camera; Aiden turns and walks left — 3 seconds; "
    "brief pause; Kagemasa turns and walks right — 3 seconds; "
    "both figures recede toward opposite fog banks."
)


def main() -> None:
    tool = SoraVideo()
    ok, msg = tool.check_dependencies()
    if not ok:
        print(f"Dependency check failed: {msg}", file=sys.stderr)
        sys.exit(1)

    print(f"Submitting to Sora sora-2 (size={SORA_SIZE}, seconds=8)...")
    result = tool.execute(
        {
            "prompt": PROMPT,
            "image_path": INPUT_IMAGE,
            "duration": 8,
            "size": SORA_SIZE,
            "output_path": RAW_OUTPUT,
        }
    )

    if not result.success:
        print(f"Sora generation failed: {result.error}", file=sys.stderr)
        sys.exit(1)

    print(f"Raw video saved: {RAW_OUTPUT}  (took {result.duration_seconds:.1f}s)")

    # FFmpeg upscale 1280x720 -> 1920x1080
    print("Upscaling to 1920x1080 with FFmpeg (lanczos)...")
    cmd = [
        "ffmpeg", "-y",
        "-i", RAW_OUTPUT,
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        FINAL_OUTPUT,
    ]
    subprocess.run(cmd, check=True)
    print(f"Final video saved: {FINAL_OUTPUT}")


if __name__ == "__main__":
    main()
