"""Sora (OpenAI) image-to-video wrapper."""

import os
import subprocess
from pathlib import Path

import openai
from PIL import Image


REPO_ROOT = Path(__file__).parent.parent.parent
IMAGES_DIR = REPO_ROOT / "short-film-project/images/04_scenes"
VIDEOS_DIR = REPO_ROOT / "short-film-project/final/videos"

SCENE_PROMPTS = {
    "01": "Wide shot of a desolate war-torn battlefield at dawn, crows circling, ruins and smoke, cinematic, desaturated grey-brown tones",
    "02": "A lone armored commander standing before troops at a gothic campsite at night, torchlight, tension and defiance, cinematic",
    "03": "A lone armored warrior standing in a vast snowy mountain pass at dawn, mist rising from valleys, cinematic wide shot",
    "04": "Two armored warriors slowly approach each other on a ruined stone bridge shrouded in dense fog, cinematic wide shot, blue-grey desaturated",
    "05": "Two warriors in combat stances facing each other on a misty bridge, psychological standoff, intense eye contact, cinematic",
    "06": "Two armored warriors clash swords on a stone bridge, metal sparks fly, intense medieval combat, cinematic",
    "07": "Two armored knights on a stone bridge in fog, a quiet moment of stillness, facing each other, cinematic",
    "08": "Two warriors engage in an intense second duel on a stone bridge, emotional and powerful swordfight, cinematic slow motion",
    "09": "An armored warrior standing alone on a misty stone bridge at sunrise, sword held downward, cinematic and solemn",
    "10": "Two warriors sheathe their swords and bow in mutual respect on a misty bridge, dawn light, solemn and cinematic",
    "11": "Two warriors part ways on a bridge as distant war horns sound, walking in opposite directions, fog and grey skies, cinematic",
    "12": "Aerial crane shot of an empty stone bridge with footprints in the mud, vast armies visible in the distance, cinematic wide",
}

SCENE_IMAGE_FILES = {
    "01": "scene_01_prologue/scene01_01_prologue_wide.png",
    "02": "scene_02_aiden_memory/scene02_01_commander_silhouette.png",
    "03": "scene_03_kagemasa_memory/scene03_02_kagemasa_lone_survivor.png",
    "04": "scene_04_bridge_encounter/scene04_01_bridge_fog_silhouettes.png",
    "05": "scene_05_stance_dialogue/scene05_01_stance_confrontation.png",
    "06": "scene_06_first_clash/scene06_01_first_clash_sparks.png",
    "07": "scene_07_lull/scene07_01_mutual_recognition.png",
    "08": "scene_08_second_clash/scene08_01_second_clash_intense.png",
    "09": "scene_09_execution_moment/scene09_05_sword_tip_on_stone.png",
    "10": "scene_10_honor_choice/scene10_01_sheathing_swords.png",
    "11": "scene_11_war_call/scene11_01_parting_ways.png",
    "12": "scene_12_epilogue/scene12_01_empty_bridge.png",
}


def _get_client() -> openai.OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    return openai.OpenAI(api_key=api_key)


def _prepare_image(scene_num: str, target_size: tuple[int, int] = (1280, 720)) -> Path:
    """씬 이미지를 Sora 입력 크기에 맞게 리사이즈."""
    img_path = IMAGES_DIR / SCENE_IMAGE_FILES[scene_num]
    if not img_path.exists():
        raise FileNotFoundError(f"이미지 없음: {img_path}")

    tmp_path = Path(f"/tmp/sora_scene{scene_num}_resized.png")
    img = Image.open(img_path)
    img_resized = img.resize(target_size, Image.LANCZOS)
    img_resized.save(tmp_path)
    return tmp_path


def generate_video(
    scene_num: str,
    seconds: int = 8,
    size: str = "1280x720",
    model: str = "sora-2",
) -> Path:
    """씬 이미지로 Sora 영상을 생성하고 저장 경로를 반환."""
    client = _get_client()
    prompt = SCENE_PROMPTS[scene_num]
    img_path = _prepare_image(scene_num)
    out_path = VIDEOS_DIR / f"scene{scene_num}_sora.mp4"
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"씬{scene_num} 생성 중 ({model}, {seconds}초, {size})...")
    with open(img_path, "rb") as img_f:
        job = client.videos.create(
            model=model,
            prompt=prompt,
            input_reference=img_f,
            seconds=seconds,
            size=size,
        )

    print(f"  Job: {job.id} — 대기 중...")
    video = client.videos.poll(job.id, poll_interval_ms=10000)

    tmp_out = Path(f"/tmp/sora_scene{scene_num}.mp4")
    client.videos.download_content(video.id).write_to_file(str(tmp_out))

    # QuickTime 호환 재인코딩
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(tmp_out),
         "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", "-c:a", "aac",
         str(out_path)],
        check=True, capture_output=True,
    )
    print(f"  ✓ 저장: {out_path} ({out_path.stat().st_size // 1024}KB)")
    return out_path


def generate_all(scenes: list[str] | None = None, **kwargs) -> dict[str, Path]:
    """전체 또는 지정 씬 영상 생성."""
    targets = scenes or sorted(SCENE_PROMPTS.keys())
    results = {}
    for n in targets:
        try:
            results[n] = generate_video(n, **kwargs)
        except Exception as e:
            print(f"  ✗ 씬{n} 실패: {e}")
    return results
