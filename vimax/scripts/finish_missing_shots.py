"""누락된 9개 샷의 first_frame + video를 ViMax 내부 도구로 직접 생성."""
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ViMax 내부 도구 사용 — API 키는 이미 환경변수나 yaml로 관리됨
from tools.image_generator_gptimage_openai_api import ImageGeneratorGptImageOpenAIAPI
from tools.video_generator_sora_openai_api import VideoGeneratorSoraOpenAIAPI

WORKING = Path(".working_dir/script2video_sora/shots")
MISSING = [17, 18, 19, 20, 21, 23, 24, 25, 26]


def load_prompt(shot_idx: int) -> str:
    p = WORKING / str(shot_idx) / "shot_description.json"
    d = json.loads(p.read_text())
    return d.get("ff_desc") or d.get("visual_desc") or "Medieval cinematic warrior scene, photorealistic"


async def main() -> None:
    img_gen = ImageGeneratorGptImageOpenAIAPI()
    vid_gen = VideoGeneratorSoraOpenAIAPI()

    # 1단계: 누락된 프레임 이미지 생성
    for idx in MISSING:
        frame_path = WORKING / str(idx) / "first_frame.png"
        if frame_path.exists():
            print(f"샷{idx}: 프레임 있음, 건너뜀")
            continue
        print(f"샷{idx}: GPT Image 프레임 생성 중...")
        prompt = load_prompt(idx)
        out = await img_gen.generate_single_image(
            prompt=prompt,
            reference_image_paths=[],
            aspect_ratio="16:9",
        )
        raw = WORKING / str(idx) / "first_frame_raw.png"
        out.save(str(raw))
        subprocess.run([
            "ffmpeg", "-y", "-i", str(raw),
            "-vf", "scale=1920:1080:flags=lanczos,setsar=1",
            "-pix_fmt", "yuv420p", str(frame_path),
        ], check=True, capture_output=True)
        print(f"  ✅ 프레임 저장: 샷{idx}")

    # 2단계: Sora 영상 생성 (순차 — 모더레이션 차단 시 정지 fallback)
    for idx in MISSING:
        video_path = WORKING / str(idx) / "video.mp4"
        if video_path.exists():
            print(f"샷{idx}: 영상 있음, 건너뜀")
            continue
        frame_path = WORKING / str(idx) / "first_frame.png"
        prompt = load_prompt(idx)
        print(f"샷{idx}: Sora 영상 생성 중...")
        try:
            out = await vid_gen.generate_single_video(
                prompt=prompt,
                reference_image_paths=[str(frame_path)],
                duration=8,
                aspect_ratio="16:9",
            )
            out.save(str(video_path))
            print(f"  ✅ 영상 저장: 샷{idx}")
        except Exception as e:
            print(f"  ⚠️ 샷{idx} 실패 ({e}) — 정지 이미지 fallback")
            subprocess.run([
                "ffmpeg", "-y", "-loop", "1", "-i", str(frame_path), "-t", "8",
                "-vf", "scale=1280:720:flags=lanczos,format=yuv420p",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-movflags", "+faststart", str(video_path),
            ], check=True, capture_output=True)
            print(f"  ✅ fallback 저장: 샷{idx}")

    print("\n✅ 누락 샷 처리 완료! ViMax 파이프라인 마무리 실행 중...")

    # 3단계: ViMax 파이프라인 최종 편집 (final_video.mp4)
    from scripts.honor_script import script, user_requirement, style
    from pipelines.script2video_pipeline import Script2VideoPipeline
    pipeline = Script2VideoPipeline.init_from_config("configs/script2video_sora.yaml")
    await pipeline(script=script, user_requirement=user_requirement, style=style)


if __name__ == "__main__":
    asyncio.run(main())
