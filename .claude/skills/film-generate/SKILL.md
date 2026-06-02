---
name: film-generate
description: 씬 이미지로 영상을 생성한다. 씬 번호와 모델을 인자로 받아 img2video 에이전트를 실행한다.
---

# /film-generate

`short-film-project/images/04_scenes/` 의 씬 이미지를 영상으로 변환한다.

## 사용법
```
/film-generate [씬번호|all] [모델]
```

## 예시
```
/film-generate all sora          # 전체 씬을 Sora로 생성
/film-generate 04 higgsfield     # 씬04만 Higgsfield로 생성
/film-generate 01 02 03 sora     # 씬01-03을 Sora로 생성
```

## 실행 순서
1. `short-film-project/images/04_scenes/` 에서 씬 이미지 확인
2. 모델에 따라 Sora 또는 Higgsfield 선택
3. img2video 에이전트로 영상 생성
4. `short-film-project/final/videos/scene{N}_veo3.mp4` 저장
5. GitHub 레포에 커밋 (선택)

## 주요 파일
- 에이전트: `.claude/agents/img2video.md`
- 도구: `pipeline/tools/sora.py`, `pipeline/tools/higgsfield.py`
- 설정: `pipeline/config/color_grades.json`
