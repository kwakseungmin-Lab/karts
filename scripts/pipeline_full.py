#!/usr/bin/env python3
"""명예의 무게 — 전체 파이프라인
1. cut_reference_map.md 파싱 → 75컷 프롬프트 추출
2. Seedance 1.5 영상 생성 (배치 8개, Ultra 플랜 제한)
3. FFmpeg 색보정 (씬별 파라미터)
4. xfade 크로스페이드로 최종 편집
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

# ─────────────────────────────────────────────
# 경로
# ─────────────────────────────────────────────
ROOT = Path("/Users/ksm2761/karts-final/short-film-project")
FRAMES_DIR = ROOT / "final" / "frames"
VIDEOS_DIR = ROOT / "final" / "videos"
GRADED_DIR = ROOT / "final" / "graded"
FINAL_DIR  = ROOT / "final"
REF_MAP    = Path("/tmp/cut_reference_map.md")
COLOR_JSON = ROOT / "plan" / "color_grades.json"

VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
GRADED_DIR.mkdir(parents=True, exist_ok=True)

BATCH_SIZE = 8          # Ultra 플랜 동시 job 한도
POLL_INTERVAL = 15      # 초
XFADE_DURATION = 0.8    # 크로스페이드 초
CLIP_DURATION = 8.0     # 컷당 초

# ─────────────────────────────────────────────
# 색보정 (씬별) — scene00은 scene01 그레이드 사용
# ─────────────────────────────────────────────
with open(COLOR_JSON) as f:
    GRADES: dict = json.load(f)
GRADES["scene00"] = GRADES["scene01"]  # 프롤로그 프리퀄

# ─────────────────────────────────────────────
# 1. reference map 파싱
# ─────────────────────────────────────────────
def parse_cuts(md_path: Path) -> list[dict]:
    text = md_path.read_text(encoding="utf-8")
    cuts: list[dict] = []

    scene_blocks = re.split(r"^---\n## 씬 ", text, flags=re.MULTILINE)
    for block in scene_blocks[1:]:
        scene_header = block.split("\n", 1)[0]
        scene_num_match = re.match(r"(\d+)", scene_header)
        if not scene_num_match:
            continue
        scene_num = int(scene_num_match.group(1))
        scene_id = f"scene{scene_num:02d}"

        cut_blocks = re.split(r"^### 컷 ", block, flags=re.MULTILINE)
        for cb in cut_blocks[1:]:
            cut_header = cb.split("\n", 1)[0]
            cut_num_match = re.match(r"(\d+)", cut_header)
            if not cut_num_match:
                continue
            cut_num = int(cut_num_match.group(1))
            cut_id = f"cut{cut_num:02d}"

            # 프롬프트 (첫 번째 blockquote)
            prompt_match = re.search(r"\*\*프롬프트\*\*\s*\n+> (.+?)(?:\n\n|\Z)", cb, re.DOTALL)
            prompt = ""
            if prompt_match:
                prompt = re.sub(r"\n> ?", " ", prompt_match.group(1)).strip()

            # 카메라/모션
            camera_match = re.search(r"\*\*카메라/모션\*\*: (.+?)(?:\n|$)", cb)
            camera = camera_match.group(1).strip() if camera_match else ""

            frame_path = FRAMES_DIR / f"{scene_id}_{cut_id}_hd.png"
            out_path   = VIDEOS_DIR / f"{scene_id}_{cut_id}.mp4"

            cuts.append({
                "scene_id": scene_id,
                "cut_id": cut_id,
                "label": f"{scene_id}_{cut_id}",
                "prompt": prompt,
                "camera": camera,
                "frame_path": frame_path,
                "out_path": out_path,
            })

    return cuts


# ─────────────────────────────────────────────
# 2. 영상 생성
# ─────────────────────────────────────────────
def submit_job(cut: dict) -> str | None:
    full_prompt = cut["prompt"]
    if cut["camera"]:
        full_prompt += f". Camera: {cut['camera']}"

    if not cut["frame_path"].exists():
        print(f"  [WARN] 프레임 없음: {cut['frame_path']} — 스킵")
        return None

    result = subprocess.run(
        [
            "higgsfield", "generate", "create", "seedance1_5",
            "--prompt", full_prompt,
            "--image", str(cut["frame_path"]),
            "--duration", "8",
            "--resolution", "1080p",
            "--aspect_ratio", "16:9",
            "--json",
        ],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        print(f"  [ERR] {cut['label']} 제출 실패: {result.stderr.strip()}")
        return None

    try:
        job_ids = json.loads(result.stdout)
        return job_ids[0] if job_ids else None
    except Exception as e:
        print(f"  [ERR] {cut['label']} JSON 파싱 실패: {e}")
        return None


def poll_jobs(job_map: dict[str, dict]) -> dict[str, str]:
    """job_id → result_url 반환. 완료된 job만 포함."""
    completed: dict[str, str] = {}
    pending = dict(job_map)

    while pending:
        still_pending: dict[str, dict] = {}
        for job_id, cut in pending.items():
            r = subprocess.run(
                ["higgsfield", "generate", "get", job_id, "--json"],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode != 0:
                still_pending[job_id] = cut
                continue
            try:
                info = json.loads(r.stdout)
            except Exception:
                still_pending[job_id] = cut
                continue

            status = info.get("status", "")
            if status == "completed":
                url = info.get("result_url", "")
                if url:
                    completed[job_id] = url
                    print(f"  ✓ {cut['label']} 완료")
                else:
                    print(f"  [WARN] {cut['label']} result_url 없음")
            elif status in ("failed", "error"):
                print(f"  [ERR] {cut['label']} 실패 (status={status})")
            else:
                still_pending[job_id] = cut

        pending = still_pending
        if pending:
            print(f"  대기 중: {len(pending)}개 — {POLL_INTERVAL}초 후 재확인...")
            time.sleep(POLL_INTERVAL)

    return completed


def download_video(url: str, out_path: Path) -> bool:
    r = subprocess.run(
        ["curl", "-L", "-o", str(out_path), url],
        capture_output=True, timeout=300,
    )
    return r.returncode == 0


# ─────────────────────────────────────────────
# 3. 색보정
# ─────────────────────────────────────────────
def color_grade(in_path: Path, out_path: Path, scene_id: str) -> bool:
    g = GRADES.get(scene_id, GRADES["scene01"])
    sat = g["saturation"]
    bri = g["brightness"]
    con = g["contrast"]
    red = g.get("red", 0.0)
    blue = g.get("blue", 0.0)

    # hue/saturation 조정 (eq 필터) + colorbalance
    # eq: contrast, brightness(-1~1), saturation
    # colorbalance: shadows/midtones/highlights RGB 조정
    vf = (
        f"eq=contrast={con}:brightness={bri}:saturation={sat},"
        f"colorbalance=rm={red}:gm={red}:bm={red}:rs={blue}:gs={blue}:bs={blue}"
    )

    r = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(in_path),
            "-vf", vf,
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            str(out_path),
        ],
        capture_output=True, timeout=120,
    )
    return r.returncode == 0


# ─────────────────────────────────────────────
# 4. 최종 편집 (xfade)
# ─────────────────────────────────────────────
def stitch_final(graded_clips: list[Path], out_path: Path) -> bool:
    if not graded_clips:
        print("[ERR] 편집할 클립 없음")
        return False

    # xfade chain 빌드
    n = len(graded_clips)
    inputs = []
    for clip in graded_clips:
        inputs += ["-i", str(clip)]

    if n == 1:
        subprocess.run(
            ["cp", str(graded_clips[0]), str(out_path)], check=True
        )
        return True

    # filter_complex 생성
    filter_parts: list[str] = []
    prev_v = "[0:v]"
    prev_a = "[0:a]"

    for i in range(1, n):
        offset = round((CLIP_DURATION - XFADE_DURATION) * i, 3)
        out_v = f"[v{i}]"
        out_a = f"[a{i}]"
        filter_parts.append(
            f"{prev_v}[{i}:v]xfade=transition=fade:duration={XFADE_DURATION}:offset={offset}{out_v};"
            f"{prev_a}[{i}:a]acrossfade=d={XFADE_DURATION}{out_a}"
        )
        prev_v = out_v
        prev_a = out_a

    filter_complex = ";".join(filter_parts)
    final_v = prev_v
    final_a = prev_a

    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex", filter_complex,
            "-map", final_v,
            "-map", final_a,
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(out_path),
        ]
    )
    r = subprocess.run(cmd, capture_output=True, timeout=600)
    if r.returncode != 0:
        print(f"[ERR] stitch 실패:\n{r.stderr.decode()[-500:]}")
    return r.returncode == 0


# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("명예의 무게 — 전체 파이프라인")
    print("=" * 60)

    # ── 파싱
    cuts = parse_cuts(REF_MAP)
    print(f"\n[1/4] 컷 파싱 완료: {len(cuts)}개")
    for c in cuts:
        frame_ok = "✓" if c["frame_path"].exists() else "✗"
        video_ok = "✓" if c["out_path"].exists() else " "
        print(f"  {c['label']}  프레임{frame_ok}  영상{video_ok}")

    # 이미 영상 있는 컷 제외
    todo = [c for c in cuts if not c["out_path"].exists()]
    print(f"\n  → 생성 필요: {len(todo)}컷 (이미 있음: {len(cuts)-len(todo)}컷)")

    # ── 영상 생성 (배치 8)
    print(f"\n[2/4] 영상 생성 시작 (배치={BATCH_SIZE})")
    job_results: dict[str, str] = {}  # label → result_url

    for batch_start in range(0, len(todo), BATCH_SIZE):
        batch = todo[batch_start: batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (len(todo) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"\n  배치 {batch_num}/{total_batches}: {[c['label'] for c in batch]}")

        job_map: dict[str, dict] = {}
        for cut in batch:
            print(f"  제출 중: {cut['label']} ...", end=" ", flush=True)
            job_id = submit_job(cut)
            if job_id:
                job_map[job_id] = cut
                print(f"→ {job_id}")
            else:
                print("실패")

        if not job_map:
            continue

        print(f"  폴링 시작 ({len(job_map)}개)...")
        completed = poll_jobs(job_map)

        # 다운로드
        for job_id, url in completed.items():
            cut = job_map[job_id]
            print(f"  다운로드: {cut['label']} ...", end=" ", flush=True)
            ok = download_video(url, cut["out_path"])
            if ok:
                sz = cut["out_path"].stat().st_size // 1024 // 1024
                print(f"✓ ({sz}MB)")
                job_results[cut["label"]] = url
            else:
                print("실패")

    # ── 색보정
    print(f"\n[3/4] 색보정")
    graded_clips: list[Path] = []
    ordered_labels = [c["label"] for c in cuts]

    for label in ordered_labels:
        cut = next((c for c in cuts if c["label"] == label), None)
        if cut is None:
            continue
        in_path = cut["out_path"]
        if not in_path.exists():
            print(f"  [SKIP] {label} — 영상 없음")
            continue
        out_path = GRADED_DIR / f"{label}.mp4"
        if out_path.exists():
            print(f"  [SKIP] {label} — 색보정 이미 있음")
        else:
            print(f"  색보정: {label} ({cut['scene_id']}) ...", end=" ", flush=True)
            ok = color_grade(in_path, out_path, cut["scene_id"])
            print("✓" if ok else "실패")
        if out_path.exists():
            graded_clips.append(out_path)

    # ── 최종 편집
    print(f"\n[4/4] 최종 편집 ({len(graded_clips)}클립)")
    final_out = FINAL_DIR / "the_weight_of_honor_v3.mp4"
    ok = stitch_final(graded_clips, final_out)
    if ok:
        sz = final_out.stat().st_size // 1024 // 1024
        dur = len(graded_clips) * (CLIP_DURATION - XFADE_DURATION) + XFADE_DURATION
        print(f"\n✅ 완성: {final_out}")
        print(f"   크기: {sz}MB  |  예상 길이: {dur:.1f}초 ({dur/60:.1f}분)")
    else:
        print("\n[ERR] 최종 편집 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
