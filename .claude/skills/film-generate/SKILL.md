---
name: film-generate
description: 씬 이미지로 영상을 생성한다. img2video 에이전트를 사용해 Sora 또는 Higgsfield CLI로 short-film-project/final/videos/에 저장한다.
---

# /film-generate

`short-film-project/images/04_scenes/` 의 씬 이미지를 영상으로 변환한다.

## 사용법
```
/film-generate [씬번호|all] [sora|higgsfield]
```

## 예시
```
/film-generate all sora          # 전체 씬을 Sora로
/film-generate 04 higgsfield     # 씬04만 Higgsfield로
/film-generate 01 02 03 sora     # 씬01-03을 Sora로
```

## 에이전트 및 도구
- 에이전트: `.claude/agents/img2video.md`
- 기존 도구: `tools/video/sora_video.py`, `tools/video/higgsfield_video.py`
- 씬 프롬프트: `short-film-project/plan/film_plan.md`
