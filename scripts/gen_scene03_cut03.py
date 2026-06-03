"""Generate scene03_cut03 video using Sora sora-2 then upscale to 1920x1080."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/Users/ksm2761/karts")

from tools.video.sora_video import SoraVideo

INPUT_IMAGE = "/Users/ksm2761/karts/short-film-project/final/frames/scene03_cut03_hd.png"
RAW_OUTPUT = "/tmp/scene03_cut03_raw.mp4"
FINAL_OUTPUT = "/Users/ksm2761/karts/short-film-project/final/videos/scene03_cut03.mp4"

PROMPT = (
    "Cinematic handheld chaos, sudden ambush in snow-covered mountain valley at dawn, "
    "Norse warriors in furs and horned helmets descending from rocky cliffs — dark silhouettes "
    "against overcast blizzard sky — Japanese samurai soldiers in the valley below, "
    "Kagemasa warrior in deep navy lamellar armor with gold crest standing alone amid the storm, "
    "crimson fabric banners torn by blizzard wind, white snow swirling, disorienting handheld angles, "
    "cinematic dramatic lighting, historical epic battle atmosphere, "
    "For Honor cinematic trailer aesthetic, photorealistic 16:9. "
    "Camera: fast shaky handheld during chaos then sudden eerie stillness — silence falls."
)

# sora-2 currently only supports 1280x720 or 720x1280
SORA_SIZE = "1280x720"


def main() -> None:
    tool = SoraVideo()
    ok, msg = tool.check_dependencies()
    if not ok:
        print(f"Dependency check failed: {msg}", file=sys.stderr)
        sys.exit(1)

    print("Submitting Sora job for scene03_cut03 (sora-2, 1280x720, 8s)...")
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

    print(f"Raw video saved: {RAW_OUTPUT}  (took {int(result.duration_seconds * 1000)}ms)")

    # FFmpeg upscale 1280x720 → 1920x1080
    Path(FINAL_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
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
    print("Upscaling to 1920x1080 with FFmpeg...")
    subprocess.run(cmd, check=True)
    print(f"Final video saved: {FINAL_OUTPUT}")


if __name__ == "__main__":
    main()
