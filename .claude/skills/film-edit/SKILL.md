---
name: film-edit
description: 색보정된 씬 영상들을 하나의 완성 영상으로 편집한다. FFmpeg xfade 크로스페이드 트랜지션 적용 후 QuickTime 호환 포맷으로 출력한다.
---

# /film-edit

색보정 영상들을 이어붙여 최종 완성본을 만든다.

## 사용법
```
/film-edit [--fade 초]
```

## 출력
`short-film-project/final/the_weight_of_honor.mp4`
- H.264, yuv420p, faststart (QuickTime 호환)
- 씬 간 0.8초 크로스페이드

## 에이전트 및 도구
- 에이전트: `.claude/agents/video-editor.md`
- 기존 도구: `tools/video/video_stitch.py`
