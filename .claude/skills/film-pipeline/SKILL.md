---
name: film-pipeline
description: 이미지→영상 생성, 색보정, 편집을 순서대로 실행해 명예의 무게 완성 영상을 만드는 전체 파이프라인.
---

# /film-pipeline

명예의 무게 전체 파이프라인을 한번에 실행한다.

```
short-film-project/images/04_scenes/
  → [img2video] →  short-film-project/final/videos/
  → [color-grader] → /tmp/karts_output/graded/
  → [video-editor] → short-film-project/final/the_weight_of_honor.mp4
```

## 사용법
```
/film-pipeline [--model sora|higgsfield] [--scenes all|01-12]
```

## 실행 단계
1. **img2video 에이전트** — 씬 이미지 → 영상 (Sora 또는 Higgsfield CLI)
2. **color-grader 에이전트** — `short-film-project/plan/color_grades.json` 파라미터 적용
3. **video-editor 에이전트** — xfade 크로스페이드(0.8초) + 최종 출력

## 산출물
- `short-film-project/final/videos/scene{N}_veo3.mp4` × 12
- `short-film-project/final/the_weight_of_honor.mp4`

## 관련 에이전트
- `.claude/agents/img2video.md`
- `.claude/agents/color-grader.md`
- `.claude/agents/video-editor.md`

## 관련 도구 (기존)
- `tools/video/sora_video.py` — Sora BaseTool 래퍼
- `tools/video/video_stitch.py` — FFmpeg 이어붙이기
- `tools/enhancement/color_grade.py` — LUT 기반 색보정

## cinematic 스킬과의 관계
`/cinematic` 은 9단계 전체 프로덕션 파이프라인.
`/film-pipeline` 은 이미 기획/이미지가 완성된 상태에서 영상만 생성·편집하는 단축 파이프라인.
