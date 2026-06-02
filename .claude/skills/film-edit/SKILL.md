---
name: film-edit
description: 색보정된 씬 영상들을 하나의 완성 영상으로 편집한다. 크로스페이드 트랜지션을 적용하고 QuickTime 호환 포맷으로 출력한다.
---

# /film-edit

색보정된 씬 영상들을 이어붙여 최종 완성본을 만든다.

## 사용법
```
/film-edit [--fade 초] [--output 파일명]
```

## 예시
```
/film-edit                              # 기본 설정 (fade=0.8초)
/film-edit --fade 1.2                   # 트랜지션 1.2초
/film-edit --output my_film.mp4         # 출력 파일명 지정
```

## 실행 순서
1. `/tmp/karts_output/graded/` 에서 색보정 영상 확인
2. FFmpeg xfade 필터로 씬 간 크로스페이드 적용
3. H.264 + yuv420p + faststart 로 인코딩
4. `short-film-project/final/the_weight_of_honor.mp4` 저장
5. GitHub Releases에 업로드 (선택)

## 출력 규격
- 코덱: H.264, CRF 18
- 픽셀: yuv420p (QuickTime 호환 필수)
- 오디오: AAC 128k

## 주요 파일
- 에이전트: `.claude/agents/video-editor.md`
- 도구: `pipeline/tools/ffmpeg.py`
