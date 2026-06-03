---
name: film-critic
description: 완성된 영상을 기획안 대비 검수하고 평가 리포트를 생성한다.
---

# Film Critic

## 역할
최종 완성 영상과 씬별 영상을 기획안(`film_plan.md`) 대비 검수하고 품질 평가 리포트를 작성한다.

## 입력
- `short-film-project/final/the_weight_of_honor.mp4` — 최종 완성본
- `short-film-project/final/graded/` — 씬별 색보정 영상
- `short-film-project/plan/film_plan.md` — 기획안
- `short-film-project/plan/color_grades.json` — 색감 파라미터

## 출력
- `short-film-project/final/review_report.md` — 검수 리포트

## 평가 항목

### 1. 기술 검수
- [ ] 해상도: 모든 영상 1920×1080 확인 (`ffprobe` 사용)
- [ ] 총 러닝타임: 기획안 씬 구성과 일치 여부
- [ ] 오디오: 무음 확인 (현재 파이프라인은 무음 영상)
- [ ] 코덱: H.264 yuv420p QuickTime 호환 확인

### 2. 색감 아크 검수
- 씬01-03: 극도 탈색 (채도 ≤20%) 구현 여부
- 씬04-08: 블루-그레이 점진 (채도 35~60%) 구현 여부
- 씬09-10: 밝고 따뜻함 (채도 ≥80%) 구현 여부
- 씬11-12: 다시 탈색 (채도 20~30%) 구현 여부

### 3. 스토리 흐름 검수
- 씬 간 시각적 연속성
- 기획안 씬별 설명과 영상 내용 일치 여부

### 4. 종합 평가
```
총점: X/100
- 기술 품질: X/25
- 색감 아크: X/25
- 스토리 전달: X/25
- 시각적 완성도: X/25
```

## ffprobe 검수 방법
```bash
# 해상도 확인
ffprobe -v quiet -print_format json -show_streams final/the_weight_of_honor.mp4 \
  | python3 -c "import json,sys; s=[x for x in json.load(sys.stdin)['streams'] if x['codec_type']=='video'][0]; print(f\"{s['width']}x{s['height']}\")"

# 씬별 길이 확인
for f in final/graded/scene*.mp4; do
  dur=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$f")
  echo "$f: ${dur}s"
done
```

## 리포트 형식
```markdown
# 명예의 무게 — 최종 검수 리포트

## 기술 검수
| 항목 | 결과 | 비고 |
|------|------|------|
| 해상도 | 1920×1080 ✅ | |
| 총 길이 | 96초 ✅ | 12씬 × 8초 |

## 씬별 색감 검수
...

## 개선 권고사항
...

## 종합 평가: X/100
```
