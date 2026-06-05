#!/usr/bin/env python3
"""컷별 레퍼런스 이미지 & 프롬프트 문서 생성."""
import json
import os

SCENES_DIR = "short-film-project/storyboard"
FRAMES_DIR = "short-film-project/final/frames"
VIDEOS_DIR = "short-film-project/final/videos"
OUT_PATH = "short-film-project/plan/cut_reference_map.md"

# cut_reference_map.md 는 short-film-project/plan/ 에 위치
# 이미지는 short-film-project/images/ 에 위치 → 상대 경로 ../images/...
def ref_to_img_tag(ref_path: str) -> str:
    """JSON refs 경로를 plan/ 기준 상대경로 이미지 태그로 변환."""
    # ref_path 예: images/01_character_sheets/aiden/aiden_01_front_view.png
    fname = os.path.basename(ref_path)
    rel = "../" + ref_path
    return f"![{fname}]({rel})"


lines: list[str] = []
lines.append("# 명예의 무게 — 컷별 레퍼런스 이미지 & 프롬프트")
lines.append("")
lines.append("> 생성 방식: GPT Image (frame) → Sora sora-2 (1280×720 → 1920×1080 업스케일)")
lines.append("")

for sc_num in range(1, 13):
    json_path = f"{SCENES_DIR}/scene{sc_num:02d}_storyboard.json"
    if not os.path.exists(json_path):
        continue
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    cuts = data.get("cuts") or data.get("scene", {}).get("cuts", [])
    if not cuts:
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                cuts = v
                break

    scene_title = (
        data.get("scene_title")
        or data.get("title")
        or data.get("scene", {}).get("title", "")
    )

    lines.append("---")
    lines.append(f"## 씬 {sc_num:02d} — {scene_title}")
    lines.append(f"> {len(cuts)}컷")
    lines.append("")

    for i, cut in enumerate(cuts, 1):
        prompt = cut.get("frame_prompt") or cut.get("prompt", "")
        refs: list[str] = [r for r in cut.get("character_refs", []) if r]
        motion = cut.get("motion_desc") or cut.get("camera_motion", "")

        frame_ok = os.path.exists(f"{FRAMES_DIR}/scene{sc_num:02d}_cut{i:02d}_hd.png")
        video_ok = os.path.exists(f"{VIDEOS_DIR}/scene{sc_num:02d}_cut{i:02d}.mp4")

        lines.append(f"### 컷 {i:02d}  |  프레임 {'✓' if frame_ok else '✗'}  영상 {'✓' if video_ok else '✗'}")
        lines.append("")
        lines.append("**프롬프트**")
        lines.append(f"> {prompt}")
        lines.append("")

        if refs:
            lines.append("**레퍼런스 이미지**")
            lines.append("")
            for r in refs:
                lines.append(ref_to_img_tag(r))
                lines.append("")
        else:
            lines.append("**레퍼런스 이미지**: 없음 (환경/사물 씬)")
            lines.append("")

        if motion:
            lines.append(f"**카메라/모션**: {motion}")
            lines.append("")

lines.append("---")
lines.append("")
lines.append("## 비고: 씬06·08 영상 생성 특이사항")
lines.append("")
lines.append("씬06·08은 Sora content moderation 이슈로 스토리보드 프롬프트 대신 **별도 안전 프롬프트**를 사용했습니다.")
lines.append("레퍼런스 이미지도 `scene05_cut01_hd.png` (다리 위 두 전사 투샷)으로 통일했습니다.")
lines.append("")
lines.append("| 전략 | 내용 |")
lines.append("|------|------|")
lines.append("| 1차 시도 | `scene05_cut01_hd.png` 기반 image-to-video |")
lines.append("| moderation_blocked 시 | text-only fallback (이미지 없이 프롬프트만) |")
lines.append("| 레퍼런스 통일 이유 | 캐릭터 일관성 확보 (씬05가 두 캐릭터 동시 등장하는 최초 씬) |")
lines.append("")
lines.append("→ 씬06·08 실제 사용 프롬프트: `scripts/gen_scene06_08_v3.py` 참조 (PROMPTS dict)")

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"완료: {OUT_PATH} ({len(lines)}줄)")
