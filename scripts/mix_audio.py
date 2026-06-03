"""BGM + 씬별 효과음 + 영상 최종 합성."""
import subprocess
import sys

VIDEO = "short-film-project/final/the_weight_of_honor_v4_video.mp4"
BGM   = "short-film-project/final/bgm_ai.mp3"
SFX   = "short-film-project/final/sfx"
OUT   = "short-film-project/final/the_weight_of_honor_v4.mp4"

# 씬 시작 타임스탬프 (xfade 0.8초 반영, 단위: ms)
# 씬01:0 씬02:24900 씬03:37500 씬04:54100 씬05:70700
# 씬06:83300 씬07:99600 씬08:120500 씬09:136500
# 씬10:165100 씬11:198300 씬12:210900
SFX_EVENTS = [
    # (파일명, delay_ms, volume)
    ("wind_ambient",      0,      0.6),   # 씬01 프롤로그 시작
    ("armor_footsteps",   54100,  0.8),   # 씬04 다리 조우
    ("sword_draw",        68000,  0.9),   # 씬04 끝 / 씬05 전환
    ("sword_clash_heavy", 85000,  1.0),   # 씬06 1차 교전
    ("battle_impact",     92000,  1.0),   # 씬06 중반
    ("sword_clash_heavy", 122000, 1.0),   # 씬08 2차 교전
    ("battle_impact",     130000, 1.0),   # 씬08 중반
    ("sword_draw",        139000, 0.8),   # 씬09 처형 직전
    ("war_horn",          198300, 0.9),   # 씬11 전쟁의 부름
    ("wind_ambient",      210900, 0.5),   # 씬12 에필로그
]

# FFmpeg 입력 구성
inputs = ["-i", VIDEO, "-i", BGM]
for name, _, _ in SFX_EVENTS:
    inputs += ["-i", f"{SFX}/{name}.mp3"]

# filter_complex 구성
filters = []

# BGM: 219초로 트림, 볼륨 0.45, 마지막 5초 페이드아웃
filters.append(f"[1:a]atrim=0:219,asetpts=PTS-STARTPTS,volume=0.45,afade=t=out:st=214:d=5[bgm]")

# 효과음: 각각 adelay + volume
sfx_labels = []
for i, (name, delay_ms, vol) in enumerate(SFX_EVENTS):
    idx = i + 2  # 0=video, 1=bgm, 2+= sfx
    label = f"sfx{i}"
    filters.append(f"[{idx}:a]adelay={delay_ms}|{delay_ms},volume={vol}[{label}]")
    sfx_labels.append(f"[{label}]")

# 전체 믹스 (BGM + 모든 효과음)
all_audio = "[bgm]" + "".join(sfx_labels)
n_inputs = 1 + len(SFX_EVENTS)
filters.append(f"{all_audio}amix=inputs={n_inputs}:duration=first:dropout_transition=2[aout]")

filter_str = ";".join(filters)

cmd = [
    "ffmpeg", "-y",
    *inputs,
    "-filter_complex", filter_str,
    "-map", "0:v",
    "-map", "[aout]",
    "-c:v", "copy",
    "-c:a", "aac", "-b:a", "192k",
    "-movflags", "+faststart",
    OUT
]

print("FFmpeg 합성 시작...")
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print("오류:", result.stderr[-2000:])
    sys.exit(1)

# 결과 확인
probe = subprocess.run(
    ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", OUT],
    capture_output=True, text=True
)
import json, os
d = json.loads(probe.stdout)
size_mb = os.path.getsize(OUT) / 1024 / 1024
dur = float(d["format"]["duration"])
print(f"완료: {OUT}")
print(f"길이: {int(dur//60)}분 {int(dur%60)}초 | 크기: {size_mb:.1f}MB")
