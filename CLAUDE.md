# 명예의 무게 (The Weight of Honor) — Film Pipeline

## 프로젝트 개요
단편영화 AI 제작 파이프라인. 씬별 이미지를 영상으로 변환하고, 색보정 후 하나의 완성 영상으로 편집한다.

## 파이프라인 구조
```
이미지 → [img2video agent] → 씬별 영상
        → [color-grader agent] → 색보정 영상
        → [video-editor agent] → 최종 완성 영상
```

## 씬 구성 (12개)
| 씬 | 제목 | 색감 |
|----|------|------|
| 01 | 프롤로그: 늑대의 시대 | 극도 탈색, 회색 |
| 02 | 에이든의 기억 | 탈색, 어두움 |
| 03 | 카게마사의 기억 | 탈색, 차가움 |
| 04 | 경계의 다리: 조우 | 블루-그레이 |
| 05 | 대치: 스탠스의 대화 | 블루-그레이 |
| 06 | 1차 교전 | 블루-그레이, 밝아짐 |
| 07 | 소강: 적의 얼굴 | 점진적 채도 회복 |
| 08 | 2차 교전 | 채도 회복 |
| 09 | 처형의 순간 | 밝은 아침빛 |
| 10 | 명예의 선택 | 가장 밝음, 따뜻함 |
| 11 | 전쟁의 부름 | 다시 탈색 |
| 12 | 에필로그 | 극도 탈색 |

## 디렉토리 구조
```
short-film-project/
├── images/04_scenes/     # 씬별 레퍼런스 이미지
├── final/videos/         # 생성된 씬별 영상
└── final/                # 최종 완성 영상

pipeline/
├── tools/                # API 래퍼 (Sora, Higgsfield, FFmpeg)
└── config/               # 씬별 설정 (색보정 파라미터)
```

## 영상 규격
- 해상도: 1280x720 (720p)
- 씬당 길이: 8초
- 트랜지션: 0.8초 크로스페이드
- 출력 코덱: H.264 (yuv420p, QuickTime 호환)

## 주요 도구
- **Sora (OpenAI)**: 이미지→영상 (sora-2 모델)
- **Higgsfield CLI**: 영상 생성 대안 (veo3_1_lite, seedance1_5)
- **FFmpeg**: 색보정, 편집, 이어붙이기

## 주의사항
- Higgsfield Ultra 플랜: 동시 Job 최대 8개
- Sora 지원 크기: 720x1280, 1280x720, 1024x1792, 1792x1024
- Sora 지원 길이: 4초, 8초, 12초
- Veo 모델은 폭력적 이미지 NSFW 필터 있음
- 최종 영상은 `-pix_fmt yuv420p -movflags +faststart` 필수 (QuickTime 호환)

## 스킬 목록
- `/film-generate` — 씬 이미지 → 영상 생성 (Sora/Higgsfield)
- `/film-grade` — 씬별 색보정 적용
- `/film-edit` — 색보정 영상 → 최종 완성본
- `/film-pipeline` — 전체 파이프라인 한번에 실행
