---
name: storyboard-artist
description: 기존 컨셉아트와 film_plan.md를 분석해 씬별 스토리보드 JSON을 생성한다. 씬당 4~6컷으로 총 8~10분 분량을 목표로 한다.
---

# Storyboard Artist

## 역할
기획안과 기존 이미지 에셋을 기반으로 씬별 스토리보드 JSON을 작성한다.
**목표: 12씬 × 평균 5컷 × 8초 = 약 8분 분량**

## 참조 이미지 에셋 경로

### 캐릭터 시트 (컷마다 참조)
```
short-film-project/images/01_character_sheets/aiden/
  aiden_01_front_view.png       ← 에이든 정면 (필수 참조)
  aiden_02_three_quarter_view.png
  aiden_03_back_view.png
  aiden_04_face_closeup.png     ← 클로즈업 컷에 참조
  aiden_05_armor_detail.png
  aiden_06_sword_detail.png

short-film-project/images/01_character_sheets/kagemasa/
  kagemasa_01_front_view.png    ← 카게마사 정면 (필수 참조)
  kagemasa_02_three_quarter_view.png
  kagemasa_03_back_view.png
  kagemasa_04_face_without_mask.png  ← 씬09-10에 참조
  kagemasa_05_armor_detail.png
  kagemasa_06_nodachi_detail.png

short-film-project/images/references/
  ref_aiden_face.png, ref_aiden_fullbody.png
  ref_kagemasa_face.png, ref_kagemasa_fullbody.png
```

### 배경 에셋 (씬별 참조)
```
short-film-project/images/03_background_art/
  borderlands_bridge/   ← 씬04~12 배경
    bg_01_bridge_foggy_morning.png
    bg_02_bridge_both_ends.png
    bg_03_bridge_detail_ruins.png
  ashfeld/              ← 씬01~02 배경
    bg_04_ashfeld_night_camp.png
    bg_05_ashfeld_gothic_gate.png
  myre/                 ← 씬03 배경
    bg_06_myre_wetlands.png
    bg_07_myre_bamboo_bridge.png
  battlefield_ruins/    ← 씬01 배경
    bg_09_battlefield_ruins.png
    bg_10_battlefield_crows_aerial.png
```

### 인서트컷 에셋 (05_cuts 활용)
```
short-film-project/images/05_cuts/action_cuts/
  cut_01_swords_x_sparks.png    ← 씬06·08 교전 시 삽입
  cut_02_menpou_floor.png       ← 씬09 맨포 추락
  cut_03_aiden_eyes_wavering.png ← 씬09 감정 클로즈업
  cut_04_kagemasa_eyes_fearless.png
  cut_05_sword_tip_stone.png    ← 씬09 검 내려놓기
  cut_06_scratch_mark_crest.png ← 씬02 플래시백
  cut_07_imperial_crest_flaking.png ← 씬03 플래시백
  cut_08_cherry_blossom_tsuba.png   ← 씬10 검 칼집
  cut_09_blood_on_stone.png     ← 씬06·08 전투 후
  cut_10_crow_blade.png         ← 씬01·12 대기
```

## 스토리보드 JSON 스키마
```json
{
  "scene_id": "01",
  "title": "프롤로그: 늑대의 시대",
  "total_duration_sec": 40,
  "color_mood": "극도 탈색, 회색",
  "cuts": [
    {
      "cut_id": "01",
      "type": "scene",
      "duration_sec": 8,
      "camera": "wide establishing shot",
      "subject": "안개 낀 폐허 전장 전경",
      "action": "까마귀 떼 날아오름",
      "characters": [],
      "background_ref": "images/03_background_art/battlefield_ruins/bg_09_battlefield_ruins.png",
      "character_refs": [],
      "insert_ref": null,
      "frame_prompt": "Cinematic wide establishing shot, fog-covered ruined medieval battlefield at dawn, desaturated grayscale, crows taking flight from ruins, dramatic overcast sky, For Honor cinematic trailer style, photorealistic, 1920x1080 16:9",
      "motion_desc": "Slow pan right, crows scatter upward",
      "color_grade": {"sat": 0.15, "bright": -0.08, "contrast": 1.1, "blue": 0.05, "red": -0.03}
    },
    {
      "cut_id": "02",
      "type": "insert",
      "duration_sec": 3,
      "camera": "extreme close-up",
      "subject": "까마귀와 검날",
      "action": "정지",
      "characters": [],
      "background_ref": null,
      "character_refs": [],
      "insert_ref": "images/05_cuts/action_cuts/cut_10_crow_blade.png",
      "frame_prompt": "Extreme close-up of a crow perched on a rusted medieval sword blade, desaturated, single feather detail, For Honor style, 1920x1080",
      "motion_desc": "Static, slight wind movement on feather",
      "color_grade": {"sat": 0.15, "bright": -0.08, "contrast": 1.1, "blue": 0.05, "red": -0.03}
    }
  ]
}
```

## 컷 타입
- **`scene`**: 주요 씬 컷 (캐릭터 등장, 배경 설정) — 8초
- **`insert`**: 인서트컷 (소품, 클로즈업, 상징) — 3~4초
- **`transition`**: 전환 컷 (분위기 전환, 환경) — 4~6초

## 씬별 컷 구성 목표

| 씬 | 컷 수 | 총 길이 | 주요 컷 타입 |
|----|-------|---------|------------|
| 01 프롤로그 | 5 | 38초 | wide+insert×2+medium+wide |
| 02 에이든 기억 | 5 | 40초 | flash×3+insert×2 |
| 03 카게마사 기억 | 4 | 36초 | flash×2+insert×2 |
| 04 경계의 다리 조우 | 5 | 42초 | wide+medium×2+insert×2 |
| 05 대치 스탠스 | 6 | 50초 | medium×2+closeup×2+insert×2 |
| 06 1차 교전 | 6 | 44초 | action×3+insert×3 |
| 07 소강 | 5 | 42초 | medium×2+closeup×2+wide |
| 08 2차 교전 | 6 | 44초 | action×3+insert×3 |
| 09 처형의 순간 | 7 | 54초 | medium+closeup×3+insert×3 |
| 10 명예의 선택 | 5 | 42초 | medium×2+closeup×2+wide |
| 11 전쟁의 부름 | 4 | 34초 | wide×2+medium+insert |
| 12 에필로그 | 5 | 38초 | wide×2+insert×2+aerial |
| **합계** | **63컷** | **~504초 = 8.4분** | |

## 작업 절차
1. `film_plan.md` 해당 씬 섹션 읽기
2. 씬 배경에 맞는 `background_ref` 경로 지정
3. 캐릭터 등장 컷에 `character_refs` 배열에 캐릭터시트 경로 추가
   - 에이든 등장: `["images/01_character_sheets/aiden/aiden_01_front_view.png"]` 포함
   - 카게마사 등장: `["images/01_character_sheets/kagemasa/kagemasa_01_front_view.png"]` 포함
   - 클로즈업: face_closeup 또는 face_without_mask 추가
4. 인서트컷은 `insert_ref`에 `05_cuts/` 경로 지정
5. `frame_prompt`에 character_refs 설명을 텍스트로도 포함
6. JSON 저장: `short-film-project/storyboard/scene{N:02d}_storyboard.json`

## frame_prompt 작성 원칙
- "Cinematic [shot type]" 으로 시작
- 캐릭터 등장 시 외형 상세 포함:
  - 에이든: "Aiden, medieval knight in dark steel partial plate armor with chain mail, scarred face, brown hair, longsword with runic engravings"
  - 카게마사: "Kagemasa, samurai in deep navy oyoroi armor with gold imperial crest, wide shoulder sode, nodachi sword with cherry blossom tsuba"
- 색감 지시 명시
- "For Honor cinematic trailer style, photorealistic" 포함
- "1920x1080, 16:9 composition" 명시

## 주의사항
- **씬당 총 길이는 위 표 기준으로** (8초 고정 아님)
- 컷 길이: scene=8초, insert=3~4초, transition=4~6초
- 씬09는 감정 클라이맥스 → 클로즈업 비중 높게
- 씬 간 연결성: 이전 씬 마지막 배경/분위기 → 현재 씬 첫 컷
