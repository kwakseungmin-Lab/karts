export const meta = {
  name: 'film-pipeline',
  description: '명예의 무게 전체 제작 파이프라인 — 스토리보드부터 최종 검수까지 (목표: 8~10분)',
  phases: [
    { title: 'Storyboard', detail: '씬별 스토리보드 JSON 생성 (씬당 4~6컷, 총 ~63컷)' },
    { title: 'Frame Art', detail: '컷별 이미지 생성 — 캐릭터시트 참조 주입 (1920×1080)' },
    { title: 'Production', detail: '컷별 영상 생성 (Sora 1792×1024 → 1920×1080)' },
    { title: 'Color Grade', detail: '씬별 색보정 적용' },
    { title: 'Edit', detail: '최종 편집 및 조립' },
    { title: 'QA', detail: '기획안 대비 검수 리포트' },
  ],
}

const SCENES = ['01','02','03','04','05','06','07','08','09','10','11','12']

const STORYBOARD_SCHEMA = {
  type: 'object',
  required: ['scene_id', 'total_duration_sec', 'cuts'],
  properties: {
    scene_id: { type: 'string' },
    title: { type: 'string' },
    total_duration_sec: { type: 'number' },
    color_mood: { type: 'string' },
    cuts: {
      type: 'array',
      minItems: 4,
      maxItems: 7,
      items: {
        type: 'object',
        required: ['cut_id', 'type', 'duration_sec', 'frame_prompt'],
        properties: {
          cut_id: { type: 'string' },
          type: { type: 'string', enum: ['scene', 'insert', 'transition'] },
          duration_sec: { type: 'number' },
          camera: { type: 'string' },
          subject: { type: 'string' },
          action: { type: 'string' },
          characters: { type: 'array', items: { type: 'string' } },
          background_ref: { type: 'string' },
          character_refs: { type: 'array', items: { type: 'string' } },
          insert_ref: { type: 'string' },
          frame_prompt: { type: 'string' },
          motion_desc: { type: 'string' },
        },
      },
    },
  },
}

// ─── Phase 1: Storyboard ───────────────────────────────────────────────────
phase('Storyboard')
log('12개 씬 스토리보드 생성 중... (씬당 4~6컷, 총 ~63컷 목표)')

const storyboards = await parallel(
  SCENES.map(scene => () =>
    agent(
      `씬 ${scene}의 스토리보드를 생성하라.

      필수 참조 파일:
      - short-film-project/plan/film_plan.md (씬${scene} 섹션)
      - short-film-project/plan/color_grades.json (씬${scene} 색감)
      - short-film-project/images/01_character_sheets/ (캐릭터 시트)
      - short-film-project/images/03_background_art/ (배경 에셋)
      - short-film-project/images/05_cuts/action_cuts/ (인서트컷 에셋)

      규칙:
      - 씬당 4~6개 컷 생성 (scene/insert/transition 타입 혼합)
      - scene 컷: 8초, insert 컷: 3~4초, transition 컷: 4~6초
      - 캐릭터 등장 컷의 character_refs에 반드시 캐릭터 시트 경로 포함
      - storyboard-artist 에이전트 지침(.claude/agents/storyboard-artist.md) 준수
      - short-film-project/storyboard/scene${scene}_storyboard.json 저장
      - structured output 반환`,
      {
        label: `storyboard:scene${scene}`,
        phase: 'Storyboard',
        agentType: 'storyboard-artist',
        schema: STORYBOARD_SCHEMA,
      }
    )
  )
)

const validBoards = storyboards.filter(Boolean)
const allCuts = validBoards.flatMap(sb =>
  sb.cuts.map(cut => ({ scene_id: sb.scene_id, ...cut }))
)
const totalDuration = validBoards.reduce((sum, sb) => sum + (sb.total_duration_sec || 0), 0)

log(`스토리보드 완료 — ${validBoards.length}씬, 총 ${allCuts.length}컷, 예상 ${Math.round(totalDuration / 60)}분 ${totalDuration % 60}초`)

// ─── Phase 2: Frame Art ────────────────────────────────────────────────────
phase('Frame Art')
log(`${allCuts.length}개 컷 이미지 생성 중... (캐릭터 참조 이미지 주입)`)

await parallel(
  allCuts.map(cut => () =>
    agent(
      `씬${cut.scene_id} 컷${cut.cut_id} 이미지를 생성하라.

      컷 정보:
      - 타입: ${cut.type}
      - 프롬프트: "${cut.frame_prompt}"
      - 캐릭터 참조: ${JSON.stringify(cut.character_refs || [])}
      - 배경 참조: ${cut.background_ref || '없음'}
      - 인서트 참조: ${cut.insert_ref || '없음'}

      규칙:
      - frame-artist 에이전트 지침(.claude/agents/frame-artist.md) 준수
      - character_refs 있으면 GPT Image edit 엔드포인트로 캐릭터 참조 주입
      - insert_ref 있으면 해당 이미지를 기반으로 정제 생성
      - 생성 크기: 1536×1024 → FFmpeg로 1920×1080 변환
      - 저장: short-film-project/final/frames/scene${cut.scene_id}_cut${cut.cut_id}_hd.png`,
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
log(`${allCuts.length}개 컷 영상 생성 중... (Sora)`)

await parallel(
  allCuts.map(cut => () =>
    agent(
      `씬${cut.scene_id} 컷${cut.cut_id} 영상을 생성하라.

      - 입력 이미지: short-film-project/final/frames/scene${cut.scene_id}_cut${cut.cut_id}_hd.png
      - img2video 에이전트 지침(.claude/agents/img2video.md) 준수
      - Sora sora-2, size="1792x1024", seconds=${cut.duration_sec <= 4 ? 4 : cut.duration_sec <= 8 ? 8 : 12}
      - 모션: "${cut.motion_desc || cut.action || ''}"
      - 프롬프트: "${cut.frame_prompt}"
      - FFmpeg 1920×1080 업스케일 후 저장
      - 저장: short-film-project/final/videos/scene${cut.scene_id}_cut${cut.cut_id}.mp4`,
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
      - 입력: short-film-project/final/videos/scene${scene}_cut*.mp4
      - color-grader 에이전트 지침(.claude/agents/color-grader.md) 준수
      - short-film-project/plan/color_grades.json 씬${scene} 파라미터 적용
      - 저장: short-film-project/final/graded/scene${scene}_cut*.mp4`,
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
  `색보정된 모든 컷을 씬·컷 순서대로 이어붙여 최종 완성본을 만들어라.
  - 입력: short-film-project/final/graded/ 의 모든 mp4 (scene01_cut01 → scene12_cutN 순)
  - video-editor 에이전트 지침(.claude/agents/video-editor.md) 준수
  - 씬 경계마다 0.8초 xfade 크로스페이드 적용
  - 컷 내부는 직접 연결 (cut 변화는 빠른 컷)
  - 저장: short-film-project/final/the_weight_of_honor_v2.mp4
    (1920×1080, H.264, yuv420p, movflags+faststart)`,
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
  - film-critic 에이전트 지침(.claude/agents/film-critic.md) 준수
  - 총 길이 5분 이상 여부 확인 (목표: 8~10분)
  - 저장: short-film-project/final/review_report.md`,
  {
    label: 'film-critic',
    phase: 'QA',
    agentType: 'film-critic',
  }
)

log('파이프라인 완료!')
return {
  scenes: validBoards.length,
  cuts: allCuts.length,
  estimated_duration: `${Math.round(totalDuration / 60)}분 ${totalDuration % 60}초`,
  output: 'short-film-project/final/the_weight_of_honor_v2.mp4',
  report,
}
