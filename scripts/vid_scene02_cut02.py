#!/usr/bin/env python3
"""Generate scene02_cut02.mp4 via Sora sora-2 then upscale to 1920x1080."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/Users/ksm2761/karts")

from dotenv import load_dotenv
load_dotenv("/Users/ksm2761/karts/.env")

from tools.video.sora_video import SoraVideo

INPUT_IMAGE  = "/Users/ksm2761/karts/short-film-project/final/frames/scene02_cut02_hd.png"
RAW_OUTPUT   = "/tmp/scene02_cut02_raw.mp4"
FINAL_OUTPUT = "/Users/ksm2761/karts/short-film-project/final/videos/scene02_cut02.mp4"

PROMPT = (
    "Cinematic extreme close-up, Aiden's eyes inside barbeuta helmet visor, "
    "torchlight reflection dancing in pupils, eyes slowly closing in refusal — "
    "Aiden (medieval knight in dark steel partial plate armor with chain mail, "
    "scarred face, brown hair, left eye bears a vertical scar), "
    "rain droplets on helmet metal catching orange torchlight. "
    "Desaturated warm tone, deep shadows around eyes, emotional tension. "
    "For Honor cinematic trailer style, photorealistic, 1920x1080 16:9. "
    "Motion: Static close-up, eyes close slowly over 2 seconds, slight rain tremor on armor."
)

SIZE    = "1280x720"
SECONDS = 4


def main() -> None:
    print(f"Input  : {INPUT_IMAGE}")
    print(f"Raw    : {RAW_OUTPUT}")
    print(f"Final  : {FINAL_OUTPUT}")
    print(f"Size   : {SIZE}  |  Seconds: {SECONDS}")
    print()

    tool   = SoraVideo()
    result = tool.execute({
        "prompt":      PROMPT,
        "image_path":  INPUT_IMAGE,
        "duration":    SECONDS,
        "size":        SIZE,
        "output_path": RAW_OUTPUT,
    })

    if not result.success:
        print(f"ERROR: Sora failed — {result.error}", file=sys.stderr)
        sys.exit(1)

    print(f"\nSora OK  video_id={result.data['video_id']}  elapsed={result.duration_ms}ms")
    print("FFmpeg upscale 1920x1080 ...")

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

    print(f"\nDone: {FINAL_OUTPUT}")


if __name__ == "__main__":
    main()
