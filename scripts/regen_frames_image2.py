#!/usr/bin/env python3
"""전체 컷 프레임을 gpt-image-2로 재생성.

- storyboard JSON의 character_refs / background_ref를 실제로 주입
- character_refs 있음 → edit 엔드포인트 (첫 번째 이미지 주입)
- background_ref만 있음 → edit 엔드포인트
- 둘 다 없음 → generate 엔드포인트
- ThreadPoolExecutor로 최대 4개 병렬
- 실패 시 재시도 1회
"""

import base64
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# .env 로드
for line in open("/Users/ksm2761/karts/.env"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip()

from openai import OpenAI  # noqa: E402

client = OpenAI()

PROJECT_ROOT = Path("/Users/ksm2761/karts/short-film-project")
STORYBOARD_DIR = PROJECT_ROOT / "storyboard"
FRAMES_DIR = PROJECT_ROOT / "final/frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "gpt-image-2"
SIZE = "1536x1024"
QUALITY = "high"
MAX_WORKERS = 4


def resolve_ref(ref_path: str) -> Optional[Path]:
    """storyboard JSON의 상대 경로를 절대 경로로 변환 후 존재 여부 확인."""
    p = PROJECT_ROOT / ref_path
    return p if p.exists() else None


def load_cuts() -> list[dict]:
    cuts = []
    for sc_num in range(1, 13):
        json_path = STORYBOARD_DIR / f"scene{sc_num:02d}_storyboard.json"
        if not json_path.exists():
            continue
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        scene_cuts = data.get("cuts") or data.get("scene", {}).get("cuts", [])
        if not scene_cuts:
            for v in data.values():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    scene_cuts = v
                    break

        for i, cut in enumerate(scene_cuts, 1):
            prompt = cut.get("frame_prompt") or cut.get("prompt", "")
            char_refs = [r for r in cut.get("character_refs", []) if r]
            bg_ref = cut.get("background_ref", "")

            # 실제 존재하는 참조 이미지 확인
            valid_char_refs = [resolve_ref(r) for r in char_refs]
            valid_char_refs = [p for p in valid_char_refs if p]
            valid_bg_ref = resolve_ref(bg_ref) if bg_ref else None

            cuts.append({
                "scene": sc_num,
                "cut": i,
                "prompt": prompt,
                "char_refs": valid_char_refs,
                "bg_ref": valid_bg_ref,
                "out_path": FRAMES_DIR / f"scene{sc_num:02d}_cut{i:02d}_hd.png",
            })
    return cuts


def generate_with_ref(prompt: str, ref_path: Path, out_path: Path) -> bytes:
    """edit 엔드포인트로 참조 이미지 주입."""
    with open(ref_path, "rb") as f:
        resp = client.images.edit(
            model=MODEL,
            image=f,
            prompt=prompt,
            size=SIZE,
        )
    return base64.b64decode(resp.data[0].b64_json)


def generate_without_ref(prompt: str, out_path: Path) -> bytes:
    """generate 엔드포인트."""
    resp = client.images.generate(
        model=MODEL,
        prompt=prompt,
        size=SIZE,
        quality=QUALITY,
        n=1,
    )
    return base64.b64decode(resp.data[0].b64_json)


def process_cut(cut: dict, retry: int = 1) -> Optional[str]:
    sc, ct = cut["scene"], cut["cut"]
    label = f"scene{sc:02d}_cut{ct:02d}"
    out_path: Path = cut["out_path"]
    prompt = cut["prompt"]
    char_refs: list[Path] = cut["char_refs"]
    bg_ref: Optional[Path] = cut["bg_ref"]

    # 주입할 참조 이미지 결정: character_refs 우선, 없으면 background_ref
    ref_to_use = char_refs[0] if char_refs else bg_ref
    mode = "edit" if ref_to_use else "generate"

    log.info("%-22s [%s] char_refs=%d bg=%s",
             label, mode, len(char_refs), "✓" if bg_ref else "✗")

    for attempt in range(retry + 1):
        try:
            if ref_to_use:
                data = generate_with_ref(prompt, ref_to_use, out_path)
            else:
                data = generate_without_ref(prompt, out_path)

            out_path.write_bytes(data)
            log.info("OK  %s  (%d bytes)", label, len(data))
            return str(out_path)

        except Exception as e:
            err = str(e)
            if attempt < retry:
                log.warning("RETRY %s (%d/%d): %s", label, attempt + 1, retry, err[:100])
                time.sleep(5)
            else:
                # edit 실패 시 generate로 폴백
                if ref_to_use and "edit" in mode:
                    log.warning("%s edit 실패 → generate 폴백", label)
                    try:
                        data = generate_without_ref(prompt, out_path)
                        out_path.write_bytes(data)
                        log.info("OK  %s  (generate fallback, %d bytes)", label, len(data))
                        return str(out_path)
                    except Exception as e2:
                        log.error("FAIL %s: %s", label, e2)
                else:
                    log.error("FAIL %s: %s", label, err[:100])

    return None


def main() -> None:
    cuts = load_cuts()

    edit_count = sum(1 for c in cuts if c["char_refs"] or c["bg_ref"])
    gen_count = len(cuts) - edit_count
    log.info("총 %d컷 — edit: %d, generate: %d (병렬: %d)",
             len(cuts), edit_count, gen_count, MAX_WORKERS)

    results: dict[str, Optional[str]] = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_cut = {executor.submit(process_cut, cut): cut for cut in cuts}
        for future in as_completed(future_to_cut):
            cut = future_to_cut[future]
            label = f"scene{cut['scene']:02d}_cut{cut['cut']:02d}"
            results[label] = future.result()

    ok = [k for k, v in results.items() if v]
    fail = [k for k, v in results.items() if not v]

    log.info("=== 완료: %d/%d ===", len(ok), len(cuts))
    if fail:
        log.warning("실패: %s", fail)

    import json as _json
    print(_json.dumps(
        [{"cut": k, "status": "ok" if results[k] else "failed"} for k in sorted(results)],
        ensure_ascii=False, indent=2
    ))


if __name__ == "__main__":
    main()
