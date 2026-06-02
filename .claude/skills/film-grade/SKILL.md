---
name: film-grade
description: 생성된 씬 영상에 색보정을 적용한다. short-film-project/plan/color_grades.json의 파라미터로 씬별 색감 아크를 구현한다.
---

# /film-grade

씬별 영상에 색보정을 적용한다.

## 사용법
```
/film-grade [씬번호|all]
```

## 색감 아크
- 씬01-03: 극도 탈색 (채도 15-20%)
- 씬04-08: 블루-그레이 점진 (채도 35-60%)
- 씬09-10: 밝고 따뜻함 (채도 80-85%)
- 씬11-12: 다시 탈색 (채도 20-30%)

## 에이전트 및 도구
- 에이전트: `.claude/agents/color-grader.md`
- 파라미터: `short-film-project/plan/color_grades.json`
- 기존 도구: `tools/enhancement/color_grade.py`
