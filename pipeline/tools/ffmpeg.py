"""FFmpeg wrapper for color grading and video editing."""

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent.parent
VIDEOS_DIR = REPO_ROOT / "short-film-project/final/videos"
FINAL_DIR = REPO_ROOT / "short-film-project/final"
CONFIG_PATH = Path(__file__).parent.parent / "config/color_grades.json"


def load_color_grades() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def color_grade(
    scene_num: str,
    src: Path,
    dst: Path,
    grades: dict | None = None,
) -> Path:
    """씬에 색보정 필터를 적용한다."""
    if grades is None:
        grades = load_color_grades()

    g = grades[scene_num]
    vf = (
        f"eq=brightness={g['bright']}:contrast={g['contrast']}:saturation={g['sat']},"
        f"colorbalance="
        f"rs={g['red']:.3f}:gs=0:bs={g['blue']:.3f}:"
        f"rm={g['red']*0.5:.3f}:gm=0:bm={g['blue']*0.5:.3f}:"
        f"rh={g['red']*0.3:.3f}:gh=0:bh={g['blue']*0.3:.3f}"
    )

    dst.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-vf", vf,
         "-c:v", "libx264", "-crf", "18", "-preset", "fast",
         "-pix_fmt", "yuv420p", "-c:a", "copy", str(dst)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg 색보정 실패: {result.stderr[-300:]}")
    return dst


def grade_all(
    src_dir: Path | None = None,
    dst_dir: Path | None = None,
    scenes: list[str] | None = None,
) -> list[Path]:
    """전체 씬에 색보정을 적용하고 결과 경로 목록을 반환."""
    src_dir = src_dir or VIDEOS_DIR
    dst_dir = dst_dir or Path("/tmp/karts_output/graded")
    dst_dir.mkdir(parents=True, exist_ok=True)

    grades = load_color_grades()
    targets = scenes or sorted(grades.keys())
    results = []

    for n in targets:
        src = src_dir / f"scene{n}_veo3.mp4"
        dst = dst_dir / f"scene{n}_graded.mp4"
        if not src.exists():
            print(f"씬{n}: 파일 없음 ({src})")
            continue
        try:
            color_grade(n, src, dst, grades)
            print(f"씬{n}: 색보정 ✓")
            results.append(dst)
        except Exception as e:
            print(f"씬{n}: ✗ {e}")

    return results


def get_duration(path: Path) -> float:
    """영상 길이(초) 반환."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(path)],
        capture_output=True, text=True,
    )
    data = json.loads(result.stdout)
    return float(next(
        s["duration"] for s in data["streams"] if s["codec_type"] == "video"
    ))


def concat_with_xfade(
    videos: list[Path],
    output: Path,
    fade_duration: float = 0.8,
) -> Path:
    """씬 영상들을 xfade 크로스페이드로 이어붙인다."""
    n = len(videos)
    durations = [get_duration(v) for v in videos]

    inputs = []
    for v in videos:
        inputs += ["-i", str(v)]

    filters = []
    current = "0:v"
    offset = 0.0
    for i in range(1, n):
        offset += durations[i - 1] - fade_duration
        out_lbl = f"v{i}"
        filters.append(
            f"[{current}][{i}:v]xfade=transition=fade"
            f":duration={fade_duration}:offset={offset:.3f}[{out_lbl}]"
        )
        current = out_lbl

    output.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["ffmpeg", "-y"] + inputs +
        ["-filter_complex", ";".join(filters),
         "-map", f"[{current}]",
         "-c:v", "libx264", "-crf", "18", "-preset", "fast",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart",
         "-c:a", "aac", "-b:a", "128k",
         str(output)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg concat 실패: {result.stderr[-300:]}")

    total = sum(durations) - fade_duration * (n - 1)
    size_mb = output.stat().st_size / (1024 * 1024)
    print(f"✓ {output.name} — {total:.1f}초, {size_mb:.1f}MB")
    return output


def make_final(
    graded_dir: Path | None = None,
    output: Path | None = None,
    fade_duration: float = 0.8,
) -> Path:
    """색보정 영상들을 이어붙여 최종 완성본을 만든다."""
    graded_dir = graded_dir or Path("/tmp/karts_output/graded")
    output = output or FINAL_DIR / "the_weight_of_honor.mp4"

    videos = sorted(graded_dir.glob("scene*_graded.mp4"))
    if not videos:
        raise FileNotFoundError(f"색보정 영상 없음: {graded_dir}")

    print(f"{len(videos)}개 씬 이어붙이기 중...")
    return concat_with_xfade(videos, output, fade_duration)
