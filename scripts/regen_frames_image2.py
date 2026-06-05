#!/usr/bin/env python3
"""전체 컷 프레임을 gpt-image-2로 재생성.

수정사항:
1. 씬04~12 다리 배경은 kv_bridge.png를 우선 참조 이미지로 고정
2. 모든 프롬프트에 "단일 프레임" 강제 문구 추가
3. 타이틀카드(scene12_cut06) 한국어 제거
4. 1792×1024(16:9) 생성 → FFmpeg 1920×1080 업스케일
"""

import base64
import json
import logging
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

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
SIZE = "1792x1024"  # 16:9 네이티브
QUALITY = "high"
MAX_WORKERS = 4

# 다리 키비주얼 — 씬04~12 모든 컷에 고정 참조
BRIDGE_KV = PROJECT_ROOT / "images/key_visuals/kv_bridge.png"
BRIDGE_SCENES = set(range(4, 13))

# 단일 프레임 강제 문구
SINGLE_FRAME_SUFFIX = (
    " Single cinematic frame only — no comic panels, no split screens, "
    "no diptych, no multi-panel layout, no borders between images."
)

# 타이틀카드 전용 프롬프트 (한국어 없음)
TITLE_CARD_PROMPT = (
    "Cinematic title card for a medieval fantasy short film. Deep black background. "
    "Center composition: two crossed swords forming an X — a Western longsword with runic engravings "
    "on the left blade, and a Japanese nodachi with cherry blossom handguard on the right blade. "
    "Where the blades cross, a faint golden light glows. "
    "Below the crossed swords: elegant serif text 'The Weight of Honor' in small-cap typography. "
    "Extremely desaturated near-black palette with only subtle warm gold glow at the blade crossing. "
    "For Honor cinematic title card style, photorealistic, dramatic chiaroscuro lighting, "
    "single frame, 1920x1080 16:9."
)


def resolve_ref(ref_path: str) -> Optional[Path]:
    p = PROJECT_ROOT / ref_path
    return p if p.exists() else None


def load_cuts() -> list[dict]:
    cuts = []
    for sc_num in range(0, 13):
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

            valid_char_refs = [p for p in (resolve_ref(r) for r in char_refs) if p]
            valid_bg_ref = resolve_ref(bg_ref) if bg_ref else None

            # 타이틀카드 프롬프트 교체
            is_title_card = (sc_num == 12 and i == 6)
            if is_title_card:
                prompt = TITLE_CARD_PROMPT
            else:
                prompt = prompt + SINGLE_FRAME_SUFFIX

            # 다리 씬: kv_bridge.png를 우선 참조로 고정
            bridge_ref = BRIDGE_KV if (sc_num in BRIDGE_SCENES and BRIDGE_KV.exists()) else None

            cuts.append({
                "scene": sc_num,
                "cut": i,
                "prompt": prompt,
                "char_refs": valid_char_refs,
                "bg_ref": valid_bg_ref,
                "bridge_ref": bridge_ref,
                "out_path": FRAMES_DIR / f"scene{sc_num:02d}_cut{i:02d}_hd.png",
            })
    return cuts


def upscale_to_1080(src: Path, dst: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src),
         "-vf", "scale=1920:1080:flags=lanczos",
         "-q:v", "2", str(dst)],
        check=True, capture_output=True,
    )


def generate_with_ref(prompt: str, ref_path: Path) -> bytes:
    with open(ref_path, "rb") as f:
        resp = client.images.edit(
            model=MODEL, image=f, prompt=prompt, size=SIZE,
        )
    return base64.b64decode(resp.data[0].b64_json)


def generate_without_ref(prompt: str) -> bytes:
    resp = client.images.generate(
        model=MODEL, prompt=prompt, size=SIZE, quality=QUALITY, n=1,
    )
    return base64.b64decode(resp.data[0].b64_json)


def process_cut(cut: dict, retry: int = 1) -> Optional[str]:
    sc, ct = cut["scene"], cut["cut"]
    label = f"scene{sc:02d}_cut{ct:02d}"
    out_path: Path = cut["out_path"]
    prompt = cut["prompt"]
    char_refs: list[Path] = cut["char_refs"]
    bridge_ref: Optional[Path] = cut["bridge_ref"]

    # 참조 이미지 우선순위: 다리 키비주얼 > 캐릭터 시트 > 배경
    ref_to_use = bridge_ref or (char_refs[0] if char_refs else cut["bg_ref"])
    mode = "edit" if ref_to_use else "generate"

    log.info("%-22s [%s] bridge=%s char=%d",
             label, mode, "✓" if bridge_ref else "✗", len(char_refs))

    for attempt in range(retry + 1):
        try:
            data = generate_with_ref(prompt, ref_to_use) if ref_to_use else generate_without_ref(prompt)

            tmp = out_path.with_suffix(".tmp.png")
            tmp.write_bytes(data)
            upscale_to_1080(tmp, out_path)
            tmp.unlink(missing_ok=True)
            log.info("OK  %s  1920×1080", label)
            return str(out_path)

        except Exception as e:
            if attempt < retry:
                log.warning("RETRY %s (%d/%d): %s", label, attempt + 1, retry, str(e)[:80])
                time.sleep(5)
            else:
                if ref_to_use:
                    log.warning("%s edit 실패 → generate 폴백", label)
                    try:
                        data = generate_without_ref(prompt)
                        tmp = out_path.with_suffix(".tmp.png")
                        tmp.write_bytes(data)
                        upscale_to_1080(tmp, out_path)
                        tmp.unlink(missing_ok=True)
                        log.info("OK  %s  (fallback)", label)
                        return str(out_path)
                    except Exception as e2:
                        log.error("FAIL %s: %s", label, e2)
                else:
                    log.error("FAIL %s: %s", label, str(e)[:80])
    return None


def main() -> None:
    cuts = load_cuts()
    bridge_count = sum(1 for c in cuts if c["bridge_ref"])
    log.info("총 %d컷 — 다리 고정: %d, 병렬: %d", len(cuts), bridge_count, MAX_WORKERS)

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
        ensure_ascii=False, indent=2,
    ))


if __name__ == "__main__":
    main()
