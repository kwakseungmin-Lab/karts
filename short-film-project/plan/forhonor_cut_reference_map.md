# For Honor E3 2016 트레일러 AI 재현 — 컷별 레퍼런스 & 프롬프트

> **생성 방식**: YouTube 다운로드 → 영상 분석 → 캐릭터 시트(gpt-image-2) → 씬 이미지(gpt-image-2) → Sora sora-2 영상  
> **레퍼런스 영상**: https://www.youtube.com/watch?v=9oEuaJtnrUs  
> **총 씬**: 8씬 × 8초 = 약 64초

---

## 캐릭터 시트

> 트레일러 프레임 → `gpt-image-2 images.edit` → 전신 정면 캐릭터 시트

### 바이킹 (Viking)
![sheet_viking](../reference/characters/sheet_viking.png)

**특징**: 반나체, 문신, 털망토, 소뿔 투구, 도끼 + 원형 목방패

---

### 사무라이 (Samurai)
![sheet_samurai](../reference/characters/sheet_samurai.png)

**특징**: 횡대 라멜라 갑옷(황토색), 코너 투구, 얼굴 복면, 장창(나기나타)

---

### 기사 (Knight)
![sheet_knight](../reference/characters/sheet_knight.png)

**특징**: 철판 갑옷(다크 스틸), 코니컬 바시넷 투구, 롱소드, 망토, 가죽 폴드론

---

## 씬별 컷 레퍼런스

---

### 씬 01 — 번영하는 땅 (전쟁 이전)
> 시간대: 0:04~0:12 | 등장인물: 없음 | 모드: `images.generate`

**스토리보드 이미지 (gpt-image-2)**

![scene01](../reference/storyboard_v2/scene01_hd.png)

**원본 트레일러 프레임**

![ref01](../reference/analysis_frames/f0004s.jpg)

**프롬프트**
> Cinematic macro close-up of golden wheat stalks in a field at golden hour, warm amber backlight through the wheat creating soft bokeh glow, tiny light dust particles floating in the warm air, the camera is at ground level looking through the wheat, peaceful abundance before the war, deeply warm golden tones, photorealistic, For Honor E3 2016 cinematic style, 16:9

**Sora 모션**: 황금 밀밭을 가로지르는 느린 수평 팬. 역광이 밀 사이로 스며들며 보케 효과

---

### 씬 02 — 왕국의 전성기
> 시간대: 0:12~0:22 | 등장인물: 없음 | 모드: `images.generate`

**스토리보드 이미지 (gpt-image-2)**

![scene02](../reference/storyboard_v2/scene02_hd.png)

**원본 트레일러 프레임**

![ref02](../reference/analysis_frames/f0016s.jpg)

**프롬프트**
> Cinematic aerial wide shot of a lush green medieval landscape at golden hour, a grand stone castle with multiple towers perched dramatically on a rocky hilltop, dense green forested valleys below with a winding river catching the warm sunlight, morning mist clinging to the valleys, majestic and peaceful, the world before destruction, photorealistic, For Honor E3 2016 cinematic style, 16:9

**Sora 모션**: 성채를 중심으로 서서히 항공 크레인 숏. 골짜기와 강줄기가 드러남

---

### 씬 03 — 전쟁의 불길
> 시간대: 0:22~0:38 | 등장인물: 없음 | 모드: `images.generate`

**스토리보드 이미지 (gpt-image-2)**

![scene03](../reference/storyboard_v2/scene03_hd.png)

**원본 트레일러 프레임**

![ref03](../reference/analysis_frames/f0035s.jpg)

**프롬프트**
> Cinematic wide shot of a medieval town completely engulfed in massive fires at night, countless buildings burning simultaneously with intense orange-red flames, thick black smoke rising against the pitch dark sky, collapsed structures and burning timber debris everywhere, extreme contrast between the raging orange fire and total darkness, apocalyptic total destruction of civilization, photorealistic, For Honor E3 2016 cinematic style, 16:9

**Sora 모션**: 불타는 폐허 속을 천천히 전진. 화염이 어둠을 지배

---

### 씬 04 — 폐허 속 혼자 남은 바이킹
> 시간대: 0:38~0:52 | 등장인물: **바이킹** | 모드: `images.edit` (sheet_viking 레퍼런스)

**스토리보드 이미지 (gpt-image-2)**

![scene04](../reference/storyboard_v2/scene04_hd.png)

**원본 트레일러 프레임**

![ref04](../reference/analysis_frames/f0044s.jpg)

**캐릭터 레퍼런스**

![viking](../reference/characters/sheet_viking.png)

**프롬프트**
> Place THIS EXACT viking warrior character into a new scene: seen from BEHIND walking away from the camera through a completely devastated post-war landscape, dead twisted bare trees scattered across rocky barren grey ground extending to the horizon, heavy overcast grey sky, ash and dust in the air, the warrior walks alone carrying his axe — the only living thing in this emptied world, deeply desaturated grey-brown tones, photorealistic, For Honor E3 2016 cinematic rear tracking shot style, 16:9

**Sora 모션**: 바이킹 뒤를 따라가는 느린 트래킹 숏. 황폐한 대지가 지평선까지 펼쳐짐

---

### 씬 05 — 첫 만남 (바이킹 ↔ 사무라이)
> 시간대: 0:52~1:08 | 등장인물: **바이킹, 사무라이** | 모드: `images.edit` (sheet_viking 레퍼런스)

**스토리보드 이미지 (gpt-image-2)**

![scene05](../reference/storyboard_v2/scene05_hd.png)

**원본 트레일러 프레임**

![ref05](../reference/analysis_frames/f0067s.jpg)

**캐릭터 레퍼런스**

![viking](../reference/characters/sheet_viking.png)

**프롬프트**
> Place THIS EXACT viking warrior character into a new scene, standing on the LEFT side of frame on rocky debris-covered ground facing right, on the RIGHT side at distance stands a samurai warrior in horizontal-banded lamellar armor with a long naginata, both warriors have just noticed each other and stopped walking, wide shot showing both warriors and the vast rocky wasteland between them, dead trees and cliff faces in background, grey overcast sky, tense moment of unexpected encounter between two lone survivors, desaturated warm-grey tones, photorealistic, For Honor E3 2016 cinematic style, 16:9

**Sora 모션**: 두 전사를 원거리에서 천천히 선회. 둘 사이의 광활한 거리를 강조

---

### 씬 06 — 세 번째 전사 (기사 등장 / 삼각 대치)
> 시간대: 1:08~1:22 | 등장인물: **바이킹, 사무라이, 기사** | 모드: `images.edit` (sheet_knight 레퍼런스)

**스토리보드 이미지 (gpt-image-2)**

![scene06](../reference/storyboard_v2/scene06_hd.png)

**원본 트레일러 프레임**

![ref06](../reference/analysis_frames/f0093s.jpg)

**캐릭터 레퍼런스**

![knight](../reference/characters/sheet_knight.png)

**프롬프트**
> Place THIS EXACT knight warrior character into a new scene, standing on the RIGHT side of frame on a rocky ridge, on the LEFT stands a massive viking warrior with axe and shield, in the CENTER BACKGROUND stands a samurai warrior with a long polearm, all three warriors are facing each other in a wide triangular standoff, dramatic aerial perspective looking slightly down at the three figures, rocky mountainous desolate landscape, heavy grey sky with mist, none of the three has an advantage — equal triangular formation, desaturated grey tones, photorealistic, For Honor E3 2016 cinematic style, 16:9

**Sora 모션**: 고지대에서 내려다보며 서서히 풀백. 삼각 대형이 드러남

---

### 씬 07a — 바이킹 vs 사무라이 (첫 교전)
> 시간대: 1:22~1:30 | 등장인물: **바이킹, 사무라이** | 모드: `images.edit` (sheet_viking 레퍼런스)

**스토리보드 이미지 (gpt-image-2)**

![scene07a](../reference/storyboard_v2/scene07a_hd.png)

**캐릭터 레퍼런스**

![viking](../reference/characters/sheet_viking.png)

**프롬프트**
> Place THIS EXACT viking warrior character in an intense one-on-one duel, the viking is on the LEFT swinging his axe TOWARD the opponent on the RIGHT, the opponent on the RIGHT is a samurai in horizontal-banded lamellar armor deflecting with his naginata polearm, the two warriors are FIGHTING EACH OTHER — they are ENEMIES, not allies, rocky wasteland ground, dead trees, grey overcast sky, dramatic side lighting, dust kicked up from their feet, cinematic medium shot capturing the clash, desaturated tones with motion blur on the weapons, photorealistic, For Honor E3 2016 combat cinematic style, 16:9

**Sora 모션**: 두 전사 충돌 순간 슬로우모션 → 정상 속도. 카메라가 충돌 지점 주위를 선회

---

### 씬 07b — 기사 vs 바이킹 (근접 충돌)
> 시간대: 1:30~1:38 | 등장인물: **기사, 바이킹** | 모드: `images.edit` (sheet_knight 레퍼런스)

**스토리보드 이미지 (gpt-image-2)**

![scene07b](../reference/storyboard_v2/scene07b_hd.png)

**캐릭터 레퍼런스**

![knight](../reference/characters/sheet_knight.png)

**프롬프트**
> Place THIS EXACT knight warrior character in an intense one-on-one combat, the knight is on the RIGHT raising his longsword to strike DOWNWARD at the opponent, the opponent on the LEFT is a massive shirtless tattooed viking warrior blocking with his round wooden shield while counter-attacking with his axe, the two warriors are FIGHTING EACH OTHER as mortal enemies, rocky battlefield ground with ruins in background, dramatic low angle shot, the knight's dark steel armor vs the viking's raw fur and muscle, desaturated grey tones, cinematic impact moment, photorealistic, For Honor E3 2016 combat cinematic style, 16:9

**Sora 모션**: 로우앵글에서 기사의 검이 내려치는 임팩트 순간. 방패 충격 효과

---

### 씬 07c — 바이킹 혼전 (양면 협공)
> 시간대: 1:38~1:45 | 등장인물: **바이킹, 기사, 사무라이** | 모드: `images.edit` (sheet_viking 레퍼런스)

**스토리보드 이미지 (gpt-image-2)**

![scene07c](../reference/storyboard_v2/scene07c_hd.png)

**캐릭터 레퍼런스**

![viking](../reference/characters/sheet_viking.png)

**프롬프트**
> Place THIS EXACT viking warrior character in the CENTER of a chaotic three-way battle, the viking is fighting SIMULTANEOUSLY against enemies on BOTH SIDES — a knight in dark plate armor attacks him from the LEFT, a samurai in lamellar armor attacks him from the RIGHT, in the BACKGROUND hundreds of warriors from all three factions are fighting EACH OTHER in total chaotic melee — knights vs samurai, vikings vs knights, samurai vs vikings, faction banners of all three sides visible among the chaos, smoke and dust, fire in distant background, ALL THREE FACTIONS ARE ENEMIES fighting each other, photorealistic, For Honor E3 2016 large battle cinematic style, 16:9

**Sora 모션**: 바이킹 중심으로 360도 회전하며 양쪽 적이 모두 보임. 배경 전투 카오스

---

### 씬 07d — 전장 와이드 (세 진영 난전)
> 시간대: 1:45~1:52 | 등장인물: 전군 | 모드: `images.generate`

**스토리보드 이미지 (gpt-image-2)**

![scene07d](../reference/storyboard_v2/scene07d_hd.png)

**프롬프트**
> Cinematic wide battle shot, a chaotic three-way medieval battle where THREE FACTIONS ARE FIGHTING EACH OTHER simultaneously — LEFT side: dark steel armored knights clashing AGAINST samurai warriors, RIGHT side: fur-clad viking warriors fighting AGAINST knights, CENTER: samurai warriors battling AGAINST vikings, each faction fights the other two — total three-way war, faction banners visible: cross banner (knights), chrysanthemum banner (samurai), skull banner (vikings) — all on OPPOSING sides, dramatic battlefield chaos, dust and fire, rocky hillside terrain, cinematic wide shot showing the full scale of mutual combat, photorealistic, For Honor E3 2016 battle cinematic style, 16:9

**Sora 모션**: 스위핑 와이드 팬으로 전장 전체를 훑음. 세 진영 깃발이 각각 반대편에서 보임

---

### 씬 08 — 순환 (전쟁은 끝나지 않는다)
> 시간대: 1:52~2:30 | 등장인물: 없음 (항공뷰) | 모드: `images.generate`

**스토리보드 이미지 (gpt-image-2)**

![scene08](../reference/storyboard_v2/scene08_hd.png)

**원본 트레일러 프레임**

![ref08](../reference/analysis_frames/f0160s.jpg)

**프롬프트**
> Cinematic very high altitude bird's eye aerial view looking straight down at an ancient deeply scarred battlefield landscape, the ground shows centuries of battle scars and partially recovered vegetation, THREE faction banners standing upright in the ruined earth — a white flag with black cross (knights), a dark flag with chrysanthemum (samurai), a black flag with skull (vikings), tiny warrior figures barely visible beginning to gather at the edges again, cold grey-green atmospheric aerial perspective, hopeless sense of eternal cyclical war, photorealistic, For Honor E3 2016 god's eye cinematic style, 16:9

**Sora 모션**: 신의 시점에서 점점 더 높이 올라가는 항공 풀백. 전장이 점점 작아짐

---

## 파이프라인 요약

```
1. YouTube 다운로드    forhonor_e3_2016.mp4
       ↓
2. 프레임 추출        reference/analysis_frames/ (20장)
       ↓
3. 영상 분석         reference/forhonor_analysis.md
       ↓
4. 캐릭터 시트       reference/characters/sheet_viking/samurai/knight.png
   (gpt-image-2 images.edit — 트레일러 프레임 레퍼런스)
       ↓
5. 씬 이미지         reference/storyboard_v2/scene01~08_hd.png
   (gpt-image-2 images.edit/generate — 캐릭터 시트 레퍼런스)
       ↓
6. Sora 영상         final/forhonor_remake_v2/scene01~08.mp4
   (sora-2, 1280×720 → 1920×1080 업스케일)
       ↓
7. 최종 조립         final/forhonor_remake_v2/forhonor_remake_v2.mp4
```

## 생성 모델 정보

| 단계 | 모델 | 입력 |
|------|------|------|
| 캐릭터 시트 | `gpt-image-2` (images.edit) | 트레일러 실제 프레임 |
| 배경 씬 이미지 | `gpt-image-2` (images.generate) | 프롬프트만 |
| 캐릭터 씬 이미지 | `gpt-image-2` (images.edit) | 캐릭터 시트 |
| 영상 생성 | `sora-2` | 씬 이미지 |
| 업스케일 | `FFmpeg lanczos` | 1280×720 → 1920×1080 |
