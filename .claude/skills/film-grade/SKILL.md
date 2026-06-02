---
name: film-grade
description: 생성된 씬 영상에 색보정을 적용한다. pipeline/config/color_grades.json의 파라미터를 사용해 씬별 색감 아크를 구현한다.
---

# /film-grade

씬별 영상에 기획서 색감 곡선에 따른 색보정을 적용한다.

## 사용법
```
/film-grade [씬번호|all]
```

## 예시
```
/film-grade all        # 전체 씬 색보정
/film-grade 01 02 03   # 씬01-03만 색보정
```

## 색감 아크
- 씬01-03: 극도 탈색 (채도 15-20%)
- 씬04-08: 블루-그레이 점진 (채도 35-60%)
- 씬09-10: 밝고 따뜻함 (채도 80-85%)
- 씬11-12: 다시 탈색 (채도 20-30%)

## 실행 순서
1. `short-film-project/final/videos/` 에서 씬 영상 확인
2. `pipeline/config/color_grades.json` 에서 파라미터 로드
3. color-grader 에이전트로 FFmpeg 색보정 실행
4. `/tmp/karts_output/graded/` 에 결과 저장

## 주요 파일
- 에이전트: `.claude/agents/color-grader.md`
- 도구: `pipeline/tools/ffmpeg.py`
- 설정: `pipeline/config/color_grades.json`
