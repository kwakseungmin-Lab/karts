---
name: film-pipeline
description: 이미지→영상 생성, 색보정, 편집을 순서대로 실행해 완성 영상을 만드는 전체 파이프라인. 모델과 씬 범위를 지정할 수 있다.
---

# /film-pipeline

전체 파이프라인을 한번에 실행한다.

```
이미지 → [img2video] → [color-grader] → [video-editor] → 완성 영상
```

## 사용법
```
/film-pipeline [--model sora|higgsfield] [--scenes all|01-12]
```

## 예시
```
/film-pipeline                              # 기본 (전체 씬, Higgsfield)
/film-pipeline --model sora                 # Sora로 전체 생성
/film-pipeline --model sora --scenes 01-03  # 씬01-03만 Sora로
```

## 실행 단계
1. **img2video** — `short-film-project/images/04_scenes/` → 씬별 영상
2. **color-grader** — 씬별 색감 아크 적용
3. **video-editor** — 크로스페이드 트랜지션 + 최종 출력
4. **GitHub** — `short-film-project/final/` 커밋 + Release 업로드

## 산출물
- `short-film-project/final/videos/scene{N}_veo3.mp4` (씬별 영상 12개)
- `short-film-project/final/the_weight_of_honor.mp4` (최종 완성본)

## 관련 스킬
- `/film-generate` — 1단계만 실행
- `/film-grade` — 2단계만 실행
- `/film-edit` — 3단계만 실행

## 주요 파일
- 에이전트: `.claude/agents/img2video.md`, `color-grader.md`, `video-editor.md`
- 도구: `pipeline/tools/`
- 설정: `pipeline/config/color_grades.json`
