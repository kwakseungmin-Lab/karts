---
name: film-pipeline
description: 명예의 무게 전체 제작 파이프라인을 처음부터 끝까지 실행한다. 스토리보드 생성 → 컷 이미지 → 영상 생성 → 색보정 → 최종 편집 → 검수까지 자동 오케스트레이션.
---

# /film-pipeline

이 스킬을 호출하면 아래 Workflow 스크립트를 실행한다.

```
Workflow({ scriptPath: "/tmp/karts/.claude/workflows/film-pipeline.js" })
```

## 파이프라인 단계

| Phase | 에이전트 | 입력 | 출력 |
|-------|---------|------|------|
| Storyboard | storyboard-artist × 12 | film_plan.md + 컨셉아트 | storyboard/*.json |
| Frame Art | frame-artist × N컷 | storyboard JSON | final/frames/*_hd.png (1920×1080) |
| Production | img2video × N컷 | frames/*.png | final/videos/*.mp4 (1920×1080) |
| Color Grade | color-grader × 12 | final/videos/ | final/graded/*.mp4 |
| Edit | video-editor | final/graded/ | final/the_weight_of_honor_v2.mp4 |
| QA | film-critic | 최종본 + 기획안 | final/review_report.md |

## 최종 산출물
- `short-film-project/final/the_weight_of_honor_v2.mp4` — 1920×1080 Full HD
- `short-film-project/final/review_report.md` — 검수 리포트

## 관련 파일
- 워크플로우: `.claude/workflows/film-pipeline.js`
- 에이전트: `.claude/agents/storyboard-artist.md`, `frame-artist.md`, `img2video.md`, `color-grader.md`, `video-editor.md`, `film-critic.md`
- 기획안: `short-film-project/plan/film_plan.md`
- 색감 파라미터: `short-film-project/plan/color_grades.json`
