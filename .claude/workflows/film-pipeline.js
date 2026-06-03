export const meta = {
  name: 'film-pipeline',
  description: '명예의 무게 전체 제작 파이프라인 — 스토리보드부터 최종 검수까지',
  phases: [
    { title: 'Storyboard', detail: '씬별 스토리보드 JSON 및 썸네일 생성' },
    { title: 'Frame Art', detail: '컷별 고해상도 이미지 생성 (GPT Image, 1920×1080)' },
    { title: 'Production', detail: '컷별 영상 생성 (Sora 1792×1024 → 1920×1080)' },
    { title: 'Color Grade', detail: '씬별 색보정 적용' },
    { title: 'Edit', detail: '최종 편집 및 조립' },
    { title: 'QA', detail: '기획안 대비 검수 리포트' },
  ],
}

const SCENES = ['01','02','03','04','05','06','07','08','09','10','11','12']

const STORYBOARD_SCHEMA = {
  type: 'object',
  required: ['scene_id', 'cuts'],
  properties: {
    scene_id: { type: 'string' },
    title: { type: 'string' },
    cuts: {
      type: 'array',
      items: {
        type: 'object',
        required: ['cut_id', 'frame_prompt', 'duration_sec'],
        properties: {
          cut_id: { type: 'string' },
          duration_sec: { type: 'number' },
          camera: { type: 'string' },
          subject: { type: 'string' },
          action: { type: 'string' },
          frame_prompt: { type: 'string' },
        },
      },
    },
  },
}

// ─── Phase 1: Storyboard ───────────────────────────────────────────────────
phase('Storyboard')
log('12개 씬 스토리보드 생성 중...')

const storyboards = await parallel(
  SCENES.map(scene => () =>
    agent(
      `씬 ${scene}의 스토리보드를 생성하라.
      - short-film-project/plan/film_plan.md 에서 씬${scene} 설명 읽기
      - short-film-project/images/04_scenes/ 의 기존 컨셉아트 파일 목록 확인 및 참조
      - short-film-project/plan/color_grades.json 에서 씬${scene} 색감 파라미터 참조
      - 씬을 2~4개 컷으로 분해 (컷 길이 합 = 8초)
      - storyboard-artist 에이전트 지침(.claude/agents/storyboard-artist.md)에 따라 JSON 작성
      - short-film-project/storyboard/scene${scene}_storyboard.json 저장
      - 스키마에 맞는 structured output 반환`,
      {
        label: `storyboard:scene${scene}`,
        phase: 'Storyboard',
        agentType: 'storyboard-artist',
        schema: STORYBOARD_SCHEMA,
      }
    )
  )
)

const allCuts = storyboards
  .filter(Boolean)
  .flatMap(sb => sb.cuts.map(cut => ({ scene_id: sb.scene_id, ...cut })))

log(`스토리보드 완료 — 총 ${allCuts.length}개 컷`)

// ─── Phase 2: Frame Art ────────────────────────────────────────────────────
phase('Frame Art')
log(`${allCuts.length}개 컷 이미지 생성 중... (GPT Image)`)

await parallel(
  allCuts.map(cut => () =>
    agent(
      `씬${cut.scene_id} 컷${cut.cut_id} 이미지를 생성하라.
      프롬프트: "${cut.frame_prompt}"
      - GPT Image (gpt-image-1) 사용, size="1536x1024", quality="high"
      - frame-artist 에이전트 지침(.claude/agents/frame-artist.md)에 따라 1920×1080으로 크롭·스케일
      - short-film-project/final/frames/scene${cut.scene_id}_cut${cut.cut_id}_hd.png 저장`,
      {
        label: `frame:s${cut.scene_id}c${cut.cut_id}`,
        phase: 'Frame Art',
        agentType: 'frame-artist',
      }
    )
  )
)

log('컷 이미지 생성 완료')

// ─── Phase 3: Production ───────────────────────────────────────────────────
phase('Production')
log(`${allCuts.length}개 컷 영상 생성 중... (Sora, 8초)`)

await parallel(
  allCuts.map(cut => () =>
    agent(
      `씬${cut.scene_id} 컷${cut.cut_id} 영상을 생성하라.
      - 입력 이미지: short-film-project/final/frames/scene${cut.scene_id}_cut${cut.cut_id}_hd.png
      - img2video 에이전트 지침(.claude/agents/img2video.md)에 따라 Sora sora-2 사용
      - size="1792x1024", seconds=8, input_reference로 첫프레임 고정
      - 프롬프트: "${cut.frame_prompt}"
      - 생성 후 FFmpeg로 1920×1080 업스케일 (scale=1920:1080:flags=lanczos)
      - short-film-project/final/videos/scene${cut.scene_id}_cut${cut.cut_id}.mp4 저장`,
      {
        label: `video:s${cut.scene_id}c${cut.cut_id}`,
        phase: 'Production',
        agentType: 'img2video',
      }
    )
  )
)

log('영상 생성 완료')

// ─── Phase 4: Color Grade ──────────────────────────────────────────────────
phase('Color Grade')
log('씬별 색보정 적용 중...')

await parallel(
  SCENES.map(scene => () =>
    agent(
      `씬${scene}의 모든 컷 영상에 색보정을 적용하라.
      - 입력: short-film-project/final/videos/scene${scene}_cut*.mp4 (해당하는 모든 컷)
      - color-grader 에이전트 지침(.claude/agents/color-grader.md) 참조
      - short-film-project/plan/color_grades.json 의 씬${scene} 파라미터 사용
      - 출력: short-film-project/final/graded/scene${scene}_cut*.mp4`,
      {
        label: `grade:scene${scene}`,
        phase: 'Color Grade',
        agentType: 'color-grader',
      }
    )
  )
)

log('색보정 완료')

// ─── Phase 5: Edit ─────────────────────────────────────────────────────────
phase('Edit')
log('최종 편집 중...')

await agent(
  `색보정된 모든 컷 영상을 씬·컷 순서대로 이어붙여 최종 완성본을 만들어라.
  - 입력: short-film-project/final/graded/ 의 모든 mp4 (scene01_cut01 → scene12_cutN 순)
  - video-editor 에이전트 지침(.claude/agents/video-editor.md) 참조
  - 씬 경계마다 0.8초 xfade 크로스페이드 트랜지션 적용
  - 출력: short-film-project/final/the_weight_of_honor_v2.mp4
    (1920×1080, H.264, yuv420p, movflags+faststart, QuickTime 호환)`,
  {
    label: 'final-edit',
    phase: 'Edit',
    agentType: 'video-editor',
  }
)

log('편집 완료')

// ─── Phase 6: QA ───────────────────────────────────────────────────────────
phase('QA')
log('기획안 대비 검수 중...')

const report = await agent(
  `완성된 영상을 기획안 대비 검수하고 평가 리포트를 작성하라.
  - 대상: short-film-project/final/the_weight_of_honor_v2.mp4
  - film-critic 에이전트 지침(.claude/agents/film-critic.md) 참조
  - ffprobe로 해상도(1920×1080), 총 길이, 코덱 확인
  - 색감 아크 씬별 검수
  - short-film-project/final/review_report.md 저장 후 요약 반환`,
  {
    label: 'film-critic',
    phase: 'QA',
    agentType: 'film-critic',
  }
)

log('파이프라인 완료!')
return {
  scenes: SCENES.length,
  cuts: allCuts.length,
  output: 'short-film-project/final/the_weight_of_honor_v2.mp4',
  report,
}
