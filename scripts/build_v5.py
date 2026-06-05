#!/usr/bin/env python3
"""
Build the_weight_of_honor_v5_video.mp4

Strategy:
  - Within a scene: concat all cuts directly (no transition)
  - Between scenes: xfade crossfade 0.8s

We build scene-level segments first, then xfade them together.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from collections import defaultdict

GRADED = Path("/Users/ksm2761/karts/short-film-project/final/graded")
OUTPUT = Path("/Users/ksm2761/karts/short-film-project/final/the_weight_of_honor_v5_video.mp4")
XFADE_DUR = 0.8
TMP_DIR = Path("/Users/ksm2761/karts/short-film-project/final/tmp_v5")
TMP_DIR.mkdir(exist_ok=True)


def get_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def concat_cuts(cuts: list[Path], out: Path) -> None:
    """Concat cuts within a scene using concat demuxer (lossless-ish)."""
    if len(cuts) == 1:
        # Re-encode to ensure uniform stream parameters
        subprocess.run([
            "ffmpeg", "-y", "-i", str(cuts[0]),
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-r", "24",
            str(out)
        ], check=True, capture_output=True)
        return

    # Write concat list
    list_file = TMP_DIR / f"{out.stem}_list.txt"
    with open(list_file, "w") as f:
        for c in cuts:
            f.write(f"file '{c}'\n")

    # Concat then re-encode for uniform params
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-r", "24",
        str(out)
    ], check=True, capture_output=True)


def xfade_two(a: Path, b: Path, out: Path, dur_a: float) -> None:
    """Apply xfade crossfade between two segments."""
    offset = max(dur_a - XFADE_DUR, 0.01)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(a),
        "-i", str(b),
        "-filter_complex",
        f"[0:v][1:v]xfade=transition=fade:duration={XFADE_DUR}:offset={offset}[v];"
        f"[0:a][1:a]acrossfade=d={XFADE_DUR}[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-r", "24",
        str(out)
    ], check=True, capture_output=True)


def main():
    # Gather files grouped by scene
    files = sorted(f for f in GRADED.iterdir() if f.suffix == ".mp4")
    scenes: dict[int, list[tuple[int, Path]]] = defaultdict(list)
    for f in files:
        stem = f.stem  # scene01_cut01
        parts = stem.split("_")
        scene_num = int(parts[0].replace("scene", ""))
        cut_num   = int(parts[1].replace("cut", ""))
        scenes[scene_num].append((cut_num, f))

    scene_nums = sorted(scenes.keys())

    # Step 1: Build per-scene segments
    print("=== Step 1: Building scene segments ===")
    scene_segs: list[Path] = []
    for sn in scene_nums:
        cuts = [p for _, p in sorted(scenes[sn])]
        seg_path = TMP_DIR / f"scene{sn:02d}_seg.mp4"
        if seg_path.exists():
            print(f"  scene{sn:02d}: cached {seg_path.name}")
        else:
            print(f"  scene{sn:02d}: concatenating {len(cuts)} cuts -> {seg_path.name}")
            concat_cuts(cuts, seg_path)
        scene_segs.append(seg_path)

    # Step 2: Chain xfades between scene segments
    print("\n=== Step 2: Applying xfade transitions between scenes ===")
    current = scene_segs[0]
    for i in range(1, len(scene_segs)):
        nxt = scene_segs[i]
        merged = TMP_DIR / f"merged_{i:02d}.mp4"
        if merged.exists():
            print(f"  xfade {i:02d}/{len(scene_segs)-1}: cached {merged.name}")
        else:
            dur_current = get_duration(current)
            print(f"  xfade scene{scene_nums[i-1]:02d} -> scene{scene_nums[i]:02d} "
                  f"(offset={dur_current - XFADE_DUR:.3f}s) -> {merged.name}")
            xfade_two(current, nxt, merged, dur_current)
        current = merged

    # Step 3: Final encode with movflags+faststart
    print(f"\n=== Step 3: Final encode -> {OUTPUT.name} ===")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(current),
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(OUTPUT)
    ], check=True)

    dur = get_duration(OUTPUT)
    size = OUTPUT.stat().st_size
    print(f"\n완료!")
    print(f"  총 길이: {dur:.3f}초 ({dur/60:.1f}분)")
    print(f"  파일 크기: {size:,} bytes ({size/1024/1024:.1f} MB)")


if __name__ == "__main__":
    main()
