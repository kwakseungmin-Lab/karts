---
name: frame-artist
description: 스토리보드 JSON의 각 컷을 GPT Image로 생성한다. 캐릭터 일관성을 위해 character_refs 이미지를 edit 엔드포인트에 주입한다.
---

# Frame Artist

## 역할
storyboard JSON의 각 컷을 GPT Image(gpt-image-1)로 생성한다.
캐릭터가 등장하는 컷은 반드시 캐릭터 시트를 참조 이미지로 주입해 일관성을 유지한다.

## 입력
- `short-film-project/storyboard/scene{N:02d}_storyboard.json`

## 출력
```
short-film-project/final/frames/
  scene{N:02d}_cut{M:02d}.png      # 생성 원본 (1536×1024)
  scene{N:02d}_cut{M:02d}_hd.png   # FFmpeg 스케일 후 (1920×1080)
```

## 캐릭터 참조 이미지 경로 매핑

```python
CHARACTER_REFS = {
    "aiden": {
        "default": "short-film-project/images/01_character_sheets/aiden/aiden_01_front_view.png",
        "closeup": "short-film-project/images/01_character_sheets/aiden/aiden_04_face_closeup.png",
        "fullbody": "short-film-project/images/references/ref_aiden_fullbody.png",
        "three_quarter": "short-film-project/images/01_character_sheets/aiden/aiden_02_three_quarter_view.png",
    },
    "kagemasa": {
        "default": "short-film-project/images/01_character_sheets/kagemasa/kagemasa_01_front_view.png",
        "closeup": "short-film-project/images/01_character_sheets/kagemasa/kagemasa_04_face_without_mask.png",
        "fullbody": "short-film-project/images/references/ref_kagemasa_fullbody.png",
        "three_quarter": "short-film-project/images/01_character_sheets/kagemasa/kagemasa_02_three_quarter_view.png",
    },
}
```

## GPT Image 호출 방법

### 캐릭터 없는 컷 (배경·인서트)
```python
from openai import OpenAI
import base64

client = OpenAI()

def generate_frame(prompt: str, out_path: str):
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1536x1024",
        quality="high",
        n=1,
    )
    data = base64.b64decode(response.data[0].b64_json)
    with open(out_path, "wb") as f:
        f.write(data)
```

### 캐릭터 등장 컷 (edit 엔드포인트로 참조 이미지 주입)
```python
def generate_frame_with_refs(prompt: str, ref_paths: list[str], out_path: str):
    """
    ref_paths: storyboard의 character_refs + background_ref 경로 목록
    GPT Image edit 엔드포인트는 이미지를 스타일/외형 참조로 활용함
    """
    # 참조 이미지 중 첫 번째를 메인 reference로 사용
    with open(ref_paths[0], "rb") as img_f:
        # 추가 참조는 프롬프트에 텍스트로 명시
        extra_desc = ""
        if len(ref_paths) > 1:
            extra_desc = f" Reference images provided for character consistency."

        response = client.images.edit(
            model="gpt-image-1",
            image=img_f,
            prompt=prompt + extra_desc,
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
    # 1536×1024 → 16:9 크롭(1536×864) → 1920×1080
    subprocess.run([
        "ffmpeg", "-y", "-i", src,
        "-vf", "crop=1536:864:0:80,scale=1920:1080:flags=lanczos",
        dst
    ], check=True)
```

## 작업 절차

1. storyboard JSON 로드
2. 각 컷에 대해:
   a. `character_refs` 가 있으면 → `generate_frame_with_refs()` 사용
   b. `insert_ref` 가 있으면 → 해당 이미지를 edit으로 정제
   c. 없으면 → `generate_frame()` 사용
3. `scale_to_hd()` 로 1920×1080 변환
4. `final/frames/` 에 저장

## 컷 타입별 처리

| 타입 | ref 주입 | 메서드 |
|------|---------|--------|
| scene (캐릭터 있음) | character_refs + background_ref | edit |
| scene (배경만) | background_ref | edit |
| insert (05_cuts 기반) | insert_ref | edit (원본 정제) |
| insert (새 생성) | 없음 | generate |
| transition | background_ref | edit 또는 generate |

## 주의사항
- `OPENAI_API_KEY` 환경변수 필수
- gpt-image-1 응답: `response.data[0].b64_json`
- edit 엔드포인트: 참조 이미지 스타일을 유지하면서 프롬프트 방향으로 생성
- 캐릭터 클로즈업 컷은 `face_closeup` 참조 이미지 우선 사용
- 씬09-10 카게마사 맨포 없는 얼굴: `kagemasa_04_face_without_mask.png` 사용
- 병렬 생성 가능 (동일 씬 내 컷들)
