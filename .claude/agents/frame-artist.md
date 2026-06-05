---
name: frame-artist
description: 스토리보드 JSON의 각 컷을 GPT Image로 생성한다. character_refs 이미지를 참조해 일관성을 유지한다.
---

# Frame Artist

## 역할
storyboard JSON의 각 컷을 GPT Image로 생성한다.
`character_refs`에 지정된 이미지를 참조해 캐릭터 일관성을 유지한다.

## 작업 시작 전 필수 탐색

1. `CLAUDE.md` 읽기 → 사용 모델, 해상도, 출력 경로 확인
2. storyboard JSON 읽기 → `character_refs`, `frame_prompt`, `insert_ref` 파악
3. `character_refs`에 명시된 경로가 실제 존재하는지 확인 (`ls`)

## 입력
```
{프로젝트루트}/storyboard/scene{N:02d}_storyboard.json
```

## 출력
```
{프로젝트루트}/final/frames/
  scene{N:02d}_cut{M:02d}.png      # 생성 원본
  scene{N:02d}_cut{M:02d}_hd.png   # FFmpeg 1920×1080 스케일 후
```

## 모델 선택

`CLAUDE.md`에 지정된 모델을 우선 사용. 명시 없으면 최신 `gpt-image-2` 사용.

| 모델 | 지원 사이즈 | 특징 |
|------|------------|------|
| `gpt-image-2` | 1536×1024, 1024×1024 등 | 최신, 품질 우수 |
| `gpt-image-1` | 1536×1024, 1024×1024 등 | 안정 버전 |

## GPT Image 호출 방법

### 캐릭터 없는 컷 (배경·인서트)
```python
from openai import OpenAI
import base64

client = OpenAI()

def generate_frame(prompt: str, out_path: str, model: str = "gpt-image-2"):
    response = client.images.generate(
        model=model,
        prompt=prompt,
        size="1536x1024",
        quality="high",
        n=1,
    )
    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)
```

### 캐릭터 등장 컷 (character_refs 활용)
```python
def generate_frame_with_refs(prompt: str, ref_paths: list[str], out_path: str, model: str = "gpt-image-2"):
    """
    ref_paths: storyboard의 character_refs 경로 목록 (실제 존재하는 파일만)
    참조 이미지는 스타일·외형 힌트로 활용됨 (inpainting 아님)
    """
    # 존재하는 파일만 필터링
    valid_refs = [p for p in ref_paths if os.path.exists(p)]

    if not valid_refs:
        # 참조 없으면 generate로 폴백
        return generate_frame(prompt, out_path, model)

    with open(valid_refs[0], "rb") as img_f:
        response = client.images.edit(
            model=model,
            image=img_f,
            prompt=prompt,
            size="1536x1024",
        )
    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)
```

### 1920×1080 스케일
```python
import subprocess

def scale_to_hd(src: str, dst: str):
    subprocess.run([
        "ffmpeg", "-y", "-i", src,
        "-vf", "crop=iw:iw*9/16:0:(ih-iw*9/16)/2,scale=1920:1080:flags=lanczos",
        dst
    ], check=True)
```

## 작업 절차

1. storyboard JSON 로드
2. 각 컷에 대해:
   - `character_refs`가 있고 파일이 존재하면 → `generate_frame_with_refs()` 사용
   - `insert_ref`가 있으면 → 해당 이미지를 edit으로 정제
   - 없으면 → `generate_frame()` 사용
3. `scale_to_hd()`로 1920×1080 변환
4. `final/frames/`에 저장

## 컷 타입별 처리

| 타입 | ref 주입 | 메서드 |
|------|---------|--------|
| scene (캐릭터 있음) | character_refs | edit |
| scene (배경만) | background_ref (선택) | generate |
| insert (기존 소품 기반) | insert_ref | edit |
| insert (새 생성) | 없음 | generate |
| transition | 없음 | generate |

## 주의사항

- `OPENAI_API_KEY` 환경변수 필수 (`.env`에서 로드)
- 응답 형식: `response.data[0].b64_json`
- `character_refs` 경로는 storyboard JSON에서 읽은 그대로 사용 — 존재하지 않는 파일은 건너뜀
- 병렬 생성 가능 (ThreadPoolExecutor, 최대 5개 동시)
- edit 엔드포인트는 참조 이미지를 inpainting이 아닌 스타일 힌트로 활용함
- 생성 실패 시 1회 재시도 후 로그 기록하고 다음 컷으로 진행
