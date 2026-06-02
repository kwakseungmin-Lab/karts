"""Higgsfield CLI wrapper for image-to-video generation."""

import json
import subprocess
from pathlib import Path


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
    "08": "Two warriors engage in an intense second duel on a stone bridge, emotional and powerful, cinematic slow motion",
    "09": "An armored warrior standing alone on a misty stone bridge at sunrise, sword held downward, cinematic and solemn",
    "10": "Two warriors sheathe their swords and bow in mutual respect on a misty bridge, dawn light, cinematic",
    "11": "Two warriors part ways on a bridge as distant war horns sound, fog and grey skies, cinematic",
    "12": "Aerial crane shot of an empty stone bridge, vast armies in the distance, cinematic wide",
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


def _run(cmd: list[str]) -> dict:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


def upload_image(image_path: Path) -> str:
    """이미지를 Higgsfield에 업로드하고 UUID 반환."""
    data = _run(["higgsfield", "upload", "create", str(image_path), "--json"])
    return data["id"]


def create_job(upload_id: str, scene_num: str, model: str = "veo3_1_lite") -> str:
    """영상 생성 Job을 제출하고 Job ID 반환."""
    data = _run([
        "higgsfield", "generate", "create", model,
        "--prompt", SCENE_PROMPTS[scene_num],
        "--image", upload_id,
        "--json",
    ])
    return data[0]


def wait_job(job_id: str, timeout: str = "15m") -> dict:
    """Job 완료를 기다리고 결과 반환."""
    return _run([
        "higgsfield", "generate", "wait", job_id,
        "--timeout", timeout, "--json", "--quiet",
    ])


def generate_video(
    scene_num: str,
    model: str = "veo3_1_lite",
    output_suffix: str = "veo3",
) -> Path:
    """씬 이미지로 Higgsfield 영상을 생성하고 저장 경로를 반환."""
    img_path = IMAGES_DIR / SCENE_IMAGE_FILES[scene_num]
    out_path = VIDEOS_DIR / f"scene{scene_num}_{output_suffix}.mp4"
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"씬{scene_num} 업로드 중...")
    upload_id = upload_image(img_path)

    print(f"씬{scene_num} Job 생성 ({model})...")
    job_id = create_job(upload_id, scene_num, model)
    print(f"  Job: {job_id}")

    print(f"씬{scene_num} 완료 대기 중...")
    result = wait_job(job_id)
    url = result.get("result_url", "")

    if not url:
        status = result.get("status", "unknown")
        raise RuntimeError(f"영상 URL 없음 (status: {status})")

    subprocess.run(
        ["curl", "-sL", url, "-o", str(out_path)],
        check=True,
    )
    print(f"  ✓ 저장: {out_path} ({out_path.stat().st_size // 1024}KB)")
    return out_path


def generate_all(
    scenes: list[str] | None = None,
    model: str = "veo3_1_lite",
    max_concurrent: int = 8,
) -> dict[str, Path]:
    """전체 또는 지정 씬 영상 생성 (배치 처리, 최대 8개 동시)."""
    targets = scenes or sorted(SCENE_PROMPTS.keys())
    results = {}

    for i in range(0, len(targets), max_concurrent):
        batch = targets[i:i + max_concurrent]
        job_ids: dict[str, str] = {}

        for n in batch:
            try:
                img_path = IMAGES_DIR / SCENE_IMAGE_FILES[n]
                upload_id = upload_image(img_path)
                job_ids[n] = create_job(upload_id, n, model)
                print(f"씬{n}: Job {job_ids[n][:8]}...")
            except Exception as e:
                print(f"씬{n}: Job 생성 실패 — {e}")

        for n, job_id in job_ids.items():
            try:
                result = wait_job(job_id)
                url = result.get("result_url", "")
                out_path = VIDEOS_DIR / f"scene{n}_veo3.mp4"
                subprocess.run(["curl", "-sL", url, "-o", str(out_path)], check=True)
                results[n] = out_path
                print(f"씬{n}: ✓")
            except Exception as e:
                print(f"씬{n}: ✗ {e}")

    return results
