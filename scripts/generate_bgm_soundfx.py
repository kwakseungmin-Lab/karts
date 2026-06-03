#!/usr/bin/env python3
"""
Generate background music for "명예의 무게" (The Weight of Honor)
using ElevenLabs Sound Generation API.

Strategy: Generate multiple overlapping musical segments and
concatenate/crossfade them to reach 423 seconds total.

Film arc: dark/desaturated -> slightly brighter -> dark again (U-curve)
- Segment A (prologue, dark):     somber medieval orchestral
- Segment B (encounter, tense):   tension building, battle prep
- Segment C (first fight, action): intense battle
- Segment D (calm moment):        brief reprieve
- Segment E (second fight):       intense climax
- Segment F (resolution):         honor/sacrifice, warm then dark
- Segment G (epilogue):           dark, somber fade
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

api_key = os.environ.get("ELEVENLABS_API_KEY")
if not api_key:
    print("ERROR: ELEVENLABS_API_KEY not found")
    sys.exit(1)

print(f"API key loaded: {api_key[:8]}...")

OUTPUT_DIR = Path("/Users/ksm2761/karts/short-film-project/final")
SEGMENTS_DIR = OUTPUT_DIR / "bgm_segments"
SEGMENTS_DIR.mkdir(parents=True, exist_ok=True)

FINAL_BGM = OUTPUT_DIR / "bgm_ai.mp3"

URL = "https://api.elevenlabs.io/v1/sound-generation"
HEADERS = {
    "xi-api-key": api_key,
    "Content-Type": "application/json",
}

# Max duration per API call is 22 seconds per ElevenLabs docs
# We'll generate 22s segments and loop/chain them
# Total film: 423 seconds

SEGMENTS = [
    {
        "name": "01_prologue_dark",
        "prompt": "dark medieval orchestral music, somber and brooding, minor key strings ensemble, slow tempo, desolate atmosphere, cinematic score, no drums, melancholic",
        "duration": 22.0,
        "loops": 5,  # ~110s: covers scenes 01-03
    },
    {
        "name": "02_encounter_tension",
        "prompt": "tense orchestral music, medieval fantasy cinematic, brass staccato, low strings tremolo, building suspense, battle anticipation, dark atmospheric",
        "duration": 22.0,
        "loops": 4,  # ~88s: covers scenes 04-05
    },
    {
        "name": "03_first_battle",
        "prompt": "intense epic battle orchestral, medieval fantasy action, fast tempo, powerful drums, brass fanfare, strings driving rhythm, cinematic combat music",
        "duration": 22.0,
        "loops": 3,  # ~66s: covers scene 06
    },
    {
        "name": "04_calm_interlude",
        "prompt": "gentle orchestral interlude, medieval fantasy, soft strings melody, contemplative mood, gradual color returning, hopeful undertones, cinematic score",
        "duration": 22.0,
        "loops": 2,  # ~44s: covers scene 07
    },
    {
        "name": "05_second_battle",
        "prompt": "epic climactic orchestral battle music, medieval fantasy, full orchestra, powerful and intense, heroic brass, driving strings, percussive impact",
        "duration": 22.0,
        "loops": 3,  # ~66s: covers scene 08
    },
    {
        "name": "06_honor_resolution",
        "prompt": "warm orchestral resolution, medieval fantasy, bright strings, noble melody, honor and sacrifice theme, bittersweet cinematic score, emotional crescendo",
        "duration": 22.0,
        "loops": 2,  # ~44s: covers scenes 09-10
    },
    {
        "name": "07_epilogue_dark",
        "prompt": "dark somber orchestral fade, medieval cinematic, return to minor key, strings fading, desolate atmosphere, end credits mood, quiet and brooding",
        "duration": 22.0,
        "loops": 2,  # ~44s: covers scenes 11-12
    },
]
# Total: ~462s > 423s (we'll trim to 423s at the end)


def generate_segment(name: str, prompt: str, duration: float) -> Path:
    """Generate a single audio segment."""
    out_path = SEGMENTS_DIR / f"{name}.mp3"
    if out_path.exists():
        print(f"  [SKIP] {name} already exists ({out_path.stat().st_size} bytes)")
        return out_path

    print(f"  Generating {name} ({duration}s)...")
    payload = {
        "text": prompt,
        "duration_seconds": duration,
        "prompt_influence": 0.5,
    }

    for attempt in range(3):
        try:
            response = requests.post(
                URL, headers=HEADERS, json=payload, timeout=120
            )
            if response.status_code == 200:
                ct = response.headers.get("Content-Type", "")
                if "audio" in ct or len(response.content) > 1000:
                    out_path.write_bytes(response.content)
                    print(f"  [OK] {name}: {len(response.content)} bytes")
                    return out_path
                else:
                    print(f"  [WARN] Unexpected response: {response.text[:200]}")
            elif response.status_code == 429:
                print(f"  [RATE LIMIT] Waiting 30s...")
                time.sleep(30)
            else:
                print(f"  [ERROR] Status {response.status_code}: {response.text[:200]}")
        except requests.exceptions.Timeout:
            print(f"  [TIMEOUT] Attempt {attempt + 1}/3")
        except Exception as e:
            print(f"  [EXCEPTION] {e}")

        if attempt < 2:
            time.sleep(5)

    raise RuntimeError(f"Failed to generate segment: {name}")


def loop_segment(src: Path, out: Path, loops: int) -> Path:
    """Loop a segment N times using ffmpeg."""
    if out.exists():
        print(f"  [SKIP] {out.name} already exists")
        return out

    print(f"  Looping {src.name} x{loops} -> {out.name}")
    # Create a concat file
    concat_file = SEGMENTS_DIR / f"{src.stem}_concat.txt"
    with open(concat_file, "w") as f:
        for _ in range(loops):
            f.write(f"file '{src.absolute()}'\n")

    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-c:a", "libmp3lame", "-b:a", "128k",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    concat_file.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"  [FFMPEG ERROR] {result.stderr[-500:]}")
        raise RuntimeError(f"FFmpeg loop failed for {src.name}")

    print(f"  [OK] {out.name}")
    return out


def crossfade_merge(segments: list[Path], output: Path, fade_duration: float = 2.0) -> Path:
    """Merge segments with crossfade using ffmpeg filter_complex."""
    if output.exists():
        print(f"  [SKIP] {output.name} already exists")
        return output

    print(f"\nMerging {len(segments)} segments with {fade_duration}s crossfade...")

    if len(segments) == 1:
        import shutil
        shutil.copy(segments[0], output)
        return output

    # Build ffmpeg filter_complex for sequential crossfade
    inputs = []
    for s in segments:
        inputs.extend(["-i", str(s)])

    # Get durations first
    durations = []
    for s in segments:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", str(s)],
            capture_output=True, text=True,
        )
        import json
        d = json.loads(r.stdout)
        durations.append(float(d["format"]["duration"]))
        print(f"  {s.name}: {durations[-1]:.1f}s")

    # Build filter: adelay + amix
    # For crossfade: each segment starts (cumulative_duration - fade_duration * i) later
    filter_parts = []
    offset_ms = 0
    for i, (s, dur) in enumerate(zip(segments, durations)):
        if i == 0:
            filter_parts.append(f"[{i}:a]acopy[a{i}]")
            offset_ms = int(dur * 1000 - fade_duration * 1000)
        else:
            filter_parts.append(
                f"[{i}:a]adelay={offset_ms}|{offset_ms}[a{i}]"
            )
            offset_ms += int(dur * 1000 - fade_duration * 1000)

    all_a = "".join(f"[a{i}]" for i in range(len(segments)))
    filter_parts.append(
        f"{all_a}amix=inputs={len(segments)}:normalize=0[out]"
    )
    filter_str = ";".join(filter_parts)

    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex", filter_str,
            "-map", "[out]",
            "-c:a", "libmp3lame", "-b:a", "192k",
            str(output),
        ]
    )

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [FFMPEG ERROR] {result.stderr[-1000:]}")
        raise RuntimeError("FFmpeg merge failed")

    print(f"  [OK] Merged: {output}")
    return output


def trim_to_duration(src: Path, out: Path, duration: float) -> Path:
    """Trim audio to exact duration."""
    print(f"\nTrimming to {duration}s...")
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(src),
            "-t", str(duration),
            "-af", f"afade=t=out:st={duration - 3}:d=3",
            "-c:a", "libmp3lame", "-b:a", "192k",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  [FFMPEG ERROR] {result.stderr[-500:]}")
        raise RuntimeError("Trim failed")
    return out


def main() -> None:
    print("\n=== Generating BGM for '명예의 무게' ===")
    print(f"Target duration: 423s")
    print(f"Output: {FINAL_BGM}\n")

    # Step 1: Generate base segments
    looped_segments = []
    for seg in SEGMENTS:
        print(f"\n[Segment: {seg['name']}]")
        base = generate_segment(seg["name"], seg["prompt"], seg["duration"])
        time.sleep(1)  # Avoid rate limiting

        looped = SEGMENTS_DIR / f"{seg['name']}_looped.mp3"
        loop_segment(base, looped, seg["loops"])
        looped_segments.append(looped)

    # Step 2: Merge all looped segments
    merged = SEGMENTS_DIR / "bgm_merged.mp3"
    crossfade_merge(looped_segments, merged, fade_duration=3.0)

    # Step 3: Trim to exact 423s with fade-out
    trim_to_duration(merged, FINAL_BGM, 423.0)

    # Verify output
    print("\n=== Verification ===")
    if FINAL_BGM.exists():
        size_mb = FINAL_BGM.stat().st_size / (1024 * 1024)
        # Get duration via ffprobe
        import json
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", str(FINAL_BGM)],
            capture_output=True, text=True,
        )
        d = json.loads(r.stdout)
        actual_duration = float(d["format"]["duration"])
        print(f"File: {FINAL_BGM}")
        print(f"Size: {size_mb:.2f} MB")
        print(f"Duration: {actual_duration:.1f}s (target: 423s)")
    else:
        print("ERROR: Output file not found!")
        sys.exit(1)


if __name__ == "__main__":
    main()
