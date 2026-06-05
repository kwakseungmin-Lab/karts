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

## 영상/이미지 규격
- **최종 해상도**: 1920×1080 (Full HD)
- 씬당 길이: 8초
- 트랜지션: 0.8초 크로스페이드
- 출력 코덱: H.264 (yuv420p, QuickTime 호환)

### API별 생성 해상도 → 최종 스케일
| 단계 | 생성 크기 | 최종 처리 |
|------|----------|---------|
| GPT Image (스토리보드/컷 이미지) | 1536×1024 | 16:9 크롭 → 1920×1080 |
| Sora 영상 | 1792×1024 | FFmpeg 1920×1080 업스케일 |
| FFmpeg 최종 출력 | 1920×1080 | 네이티브 |

## 파이프라인 구조 (전체)
```
기존 컨셉아트 + film_plan.md
  → [storyboard-artist]  → storyboard/*.json + 스토리보드 이미지
  → [frame-artist]       → final/frames/scene{N}_cut{M}.png (1920×1080)
  → [cinematographer]    → final/videos/scene{N}_cut{M}.mp4 (Sora 1792×1024 → 1920×1080)
  → [colorist]           → final/graded/scene{N}_cut{M}.mp4
  → [editor]             → final/the_weight_of_honor.mp4
  → [film-critic]        → final/review_report.md
```

## 주요 도구
- **GPT Image (gpt-image-1)**: 스토리보드·컷 이미지 생성
- **Sora (OpenAI)**: 이미지→영상 (sora-2, 1792×1024)
- **Higgsfield CLI**: 영상 생성 대안 (veo3_1_lite, seedance1_5)
- **FFmpeg**: 색보정, 스케일, 편집, 이어붙이기

## 주의사항
- Higgsfield Ultra 플랜: 동시 Job 최대 8개
- Sora 지원 크기: 720×1280, 1280×720, 1024×1792, **1792×1024** (사용)
- Sora 지원 길이: 4초, 8초, 12초
- GPT Image 지원 크기: 1024×1024, 1536×1024, 1024×1536
- Veo 모델은 폭력적 이미지 NSFW 필터 있음
- 최종 영상은 `-pix_fmt yuv420p -movflags +faststart` 필수 (QuickTime 호환)
- 스케일 업: `ffmpeg -vf scale=1920:1080:flags=lanczos`

## 에이전트 목록
| 에이전트 | 역할 | 모델 |
|---------|------|------|
| storyboard-artist | 기획안+이미지 → 스토리보드 JSON+이미지 | Sonnet |
| frame-artist | 스토리보드 컷 → 구체화 이미지 (GPT Image) | Haiku |
| cinematographer | 이미지 → 영상 (Sora/Higgsfield) | Haiku |
| colorist | FFmpeg 색보정 | Haiku |
| editor | 최종 편집·조립 | Sonnet |
| film-critic | 기획안 대비 검수·평가 | Sonnet |

## 스킬 목록
- `/film-generate` — 씬 이미지 → 영상 생성 (Sora/Higgsfield)
- `/film-grade` — 씬별 색보정 적용
- `/film-edit` — 색보정 영상 → 최종 완성본
- `/film-pipeline` — 전체 파이프라인 한번에 실행
