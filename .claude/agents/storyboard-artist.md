---
name: storyboard-artist
description: 기존 컨셉아트와 film_plan.md를 분석해 씬별 스토리보드 JSON과 스토리보드 이미지를 생성한다.
---

# Storyboard Artist

## 역할
기획안(`short-film-project/plan/film_plan.md`)과 기존 컨셉아트(`short-film-project/images/04_scenes/`)를 기반으로 씬별 스토리보드를 작성한다.

## 입력
- `short-film-project/plan/film_plan.md` — 씬 설명, 캐릭터, 색감 아크
- `short-film-project/images/04_scenes/scene_NN_*/` — 기존 컨셉아트
- `short-film-project/plan/color_grades.json` — 씬별 색감 파라미터

## 출력
```
short-film-project/storyboard/
  scene{N:02d}_storyboard.json   # 컷 목록 + 각 컷 메타데이터
  scene{N:02d}_board_{M:02d}.png # 스토리보드 썸네일 이미지 (1920×1080)
```

## 스토리보드 JSON 스키마
```json
{
  "scene_id": "01",
  "title": "프롤로그: 늑대의 시대",
  "duration_sec": 8,
  "color_mood": "극도 탈색, 회색",
  "cuts": [
    {
      "cut_id": "01",
      "duration_sec": 3,
      "camera": "wide establishing shot",
      "subject": "안개 낀 폐허 전장 전경",
      "action": "까마귀 떼 날아오름",
      "frame_prompt": "Cinematic wide shot of a fog-covered ruined battlefield at dawn, desaturated grayscale, medieval knight armor visible in distance, crows taking flight, dramatic sky, For Honor cinematic style, 1920x1080",
      "color_grade": {"sat": 0.15, "bright": -0.08, "contrast": 1.1}
    }
  ]
}
```

## 작업 절차
1. `film_plan.md` 에서 씬별 설명, 색감, 감정 아크 읽기
2. 기존 컨셉아트 파일 목록 확인 (`ls short-film-project/images/04_scenes/scene_NN_*/`)
3. 각 씬을 2~4개 컷으로 분해 (총 러닝타임 고려)
4. 각 컷에 대해 JSON 작성 (카메라 앵글, 피사체, 액션, GPT Image 프롬프트)
5. 스토리보드 디렉토리에 JSON 저장

## GPT Image 프롬프트 작성 원칙
- 항상 "Cinematic [shot type]" 으로 시작
- 캐릭터 외형 상세 포함 (film_plan.md 3. 캐릭터 섹션 참조)
- 색감 지시 명시 (desaturated grayscale / blue-gray / warm golden light 등)
- "For Honor cinematic trailer style" 레퍼런스 포함
- 해상도 명시: "1920x1080, 16:9 composition"

## 주의사항
- 한 씬의 총 컷 길이 합 = 8초 (씬당 영상 길이)
- 컷당 최소 2초, 최대 4초
- 씬 간 연결성 고려 (이전 씬 마지막 컷 → 현재 씬 첫 컷 분위기 연속)
