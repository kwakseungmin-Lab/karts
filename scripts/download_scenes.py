"""jobs.json의 완료된 Sora 클립을 다운로드.

사용법:
  python3 scripts/download_scenes.py          # 완료된 것만 다운로드
  python3 scripts/download_scenes.py --watch  # 미완료 클립 계속 폴링하며 다운로드
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

JOBS_FILE = Path(__file__).parent.parent / "short-film-project" / "output" / "jobs.json"
SORA_URL = "https://api.openai.com/v1/videos"


def headers() -> dict:
    return {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}


def check_and_download(jobs: dict) -> tuple[int, int, int]:
    """completed/in_progress 상태 확인 후 완료된 것 다운로드. (done, in_progress, failed) 반환."""
    done = in_prog = failed = 0
    key = os.environ.get("OPENAI_API_KEY", "")

    for job_key, job in sorted(jobs.items()):
        video_id = job.get("video_id")
        out_path = Path(job["output"])

        if out_path.exists():
            done += 1
            job["status"] = "downloaded"
            continue

        try:
            r = requests.get(f"{SORA_URL}/{video_id}", headers=headers(), timeout=30)
        except requests.exceptions.RequestException as e:
            print(f"  ⚠ {job_key}: poll error ({e.__class__.__name__})")
            in_prog += 1
            continue
        if r.status_code != 200:
            print(f"  ⚠ {job_key}: poll error {r.status_code}")
            in_prog += 1
            continue

        d = r.json()
        status = d.get("status", "")
        progress = d.get("progress", 0)
        job["status"] = status

        if status == "completed":
            print(f"  ↓ {job_key} 다운로드 중…", end=" ", flush=True)
            content_r = requests.get(
                f"{SORA_URL}/{video_id}/content/video",
                headers={"Authorization": f"Bearer {key}"},
                timeout=120,
                stream=True,
            )
            if content_r.status_code == 200:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "wb") as f:
                    for chunk in content_r.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"완료 → {out_path.name}")
                job["status"] = "downloaded"
                done += 1
            else:
                print(f"다운로드 실패 {content_r.status_code}")
                failed += 1
        elif status == "failed":
            err = (d.get("error") or {}).get("message", "")
            print(f"  ✗ {job_key}: failed — {err}")
            failed += 1
        else:
            print(f"  … {job_key}: {status} {progress}%")
            in_prog += 1

    return done, in_prog, failed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true", help="완료까지 반복 폴링")
    parser.add_argument("--interval", type=int, default=30, help="폴링 간격(초)")
    args = parser.parse_args()

    if not JOBS_FILE.exists():
        print("jobs.json 없음. 먼저 submit_scenes.py를 실행하세요.")
        sys.exit(1)

    while True:
        jobs = json.loads(JOBS_FILE.read_text())
        print(f"\n[{time.strftime('%H:%M:%S')}] 상태 확인 중… ({len(jobs)}개 작업)")
        done, in_prog, failed = check_and_download(jobs)
        JOBS_FILE.write_text(json.dumps(jobs, indent=2))

        total = len(jobs)
        print(f"\n  완료: {done}/{total}  진행중: {in_prog}  실패: {failed}")

        if not args.watch or in_prog == 0:
            break

        print(f"  {args.interval}초 후 재확인…")
        time.sleep(args.interval)

    if done == len(jobs):
        print("\n전체 완료! 이제 stitch_final.py를 실행하세요.")
        print("  python3 scripts/stitch_final.py")


if __name__ == "__main__":
    main()
