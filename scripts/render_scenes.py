"""씬별 이미지 → Sora image-to-video 일괄 렌더링.

사용법:
  python3 scripts/render_scenes.py           # 전체 12씬
  python3 scripts/render_scenes.py --scene 4  # 특정 씬만
  python3 scripts/render_scenes.py --dry-run  # 실행 목록만 출력

출력: short-film-project/output/scene_XX/clip_YY.mp4
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# .env 로드
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.video.sora_video import SoraVideo

# ── 씬별 설정 ─────────────────────────────────────────────────────────────────
# 각 이미지에 대해 (이미지 경로, Sora 프롬프트, 클립 길이(초)) 정의
BASE = Path(__file__).parent.parent / "short-film-project" / "images" / "04_scenes"

SCENES: dict[int, list[dict]] = {
    1: [
        {"image": "scene_01_prologue/scene01_01_prologue_wide.png",
         "prompt": "Desolate medieval battlefield at dawn, grey sky, crows circling overhead, slow cinematic pan across broken armor and weapons on the ground, desaturated color palette, dramatic fog",
         "duration": 5},
        {"image": "scene_01_prologue/scene01_02_prologue_crows.png",
         "prompt": "Flock of crows taking flight from a ruined medieval battlefield at dawn, slow motion, grey desaturated tones, cinematic wide angle",
         "duration": 4},
    ],
    2: [
        {"image": "scene_02_aiden_memory/scene02_01_commander_silhouette.png",
         "prompt": "Dark medieval commander silhouette in firelight at night camp, dramatic shadows, torchlight flicker, cinematic close composition",
         "duration": 4},
        {"image": "scene_02_aiden_memory/scene02_02_aiden_refusal.png",
         "prompt": "Armored knight refusing orders, turning away from a superior, tense body language, torchlit night camp, handheld camera feel, desaturated",
         "duration": 5},
        {"image": "scene_02_aiden_memory/scene02_03_gothic_gate_desertion.png",
         "prompt": "Lone armored knight walking away through a gothic stone gate into darkness, slow moving away shot, dim moonlight, fog, cinematic 2.39:1",
         "duration": 5},
    ],
    3: [
        {"image": "scene_03_kagemasa_memory/scene03_01_ambush_wide.png",
         "prompt": "Wide shot of a mountain valley ambush in a snowstorm, samurai soldiers falling, chaos and snow swirling, desaturated cold tones, cinematic",
         "duration": 5},
        {"image": "scene_03_kagemasa_memory/scene03_02_kagemasa_lone_survivor.png",
         "prompt": "Lone samurai warrior standing alone in a snowy valley, all allies defeated around him, slow push in on his back, grey cold desaturated palette, wind blowing snow",
         "duration": 5},
    ],
    4: [
        {"image": "scene_04_bridge_encounter/scene04_01_bridge_fog_silhouettes.png",
         "prompt": "Two warrior silhouettes approaching each other on a fog-covered ruined stone bridge at dawn, slow approach, heavy mist, cinematic 2.39:1",
         "duration": 5},
        {"image": "scene_04_bridge_encounter/scene04_02_swords_drawn.png",
         "prompt": "A medieval knight and a samurai drawing their swords simultaneously on a misty bridge, dramatic freeze-like slow motion, fog swirling",
         "duration": 4},
    ],
    5: [
        {"image": "scene_05_stance_dialogue/scene05_01_stance_confrontation.png",
         "prompt": "A medieval knight and a samurai in fighting stances facing each other on a foggy bridge, circling slowly, intense eye contact, cinematic",
         "duration": 5},
        {"image": "scene_05_stance_dialogue/scene05_02_eyes_closeup_diptych.png",
         "prompt": "Extreme close-up alternating between a knight's and samurai's eyes over a sword guard, tense standoff, fog in background, desaturated",
         "duration": 4},
    ],
    6: [
        {"image": "scene_06_first_clash/scene06_01_first_clash_sparks.png",
         "prompt": "Epic sword clash between a medieval knight and samurai on a bridge, metal sparks flying in slow motion, dynamic camera angle, cinematic action",
         "duration": 5},
        {"image": "scene_06_first_clash/scene06_02_first_blood.png",
         "prompt": "Medieval knight and samurai after first sword exchange, both breathing hard, one bleeding slightly, dramatic pause, cinematic medium shot",
         "duration": 4},
    ],
    7: [
        {"image": "scene_07_lull/scene07_01_mutual_recognition.png",
         "prompt": "A knight and samurai pausing in combat, both noticing each other's military crests, moment of recognition and understanding, slow zoom in",
         "duration": 5},
        {"image": "scene_07_lull/scene07_02_acknowledgment_nod.png",
         "prompt": "Subtle nod of acknowledgment between a knight and samurai on a foggy bridge, respectful pause in battle, cinematic close shot",
         "duration": 4},
    ],
    8: [
        {"image": "scene_08_second_clash/scene08_01_second_clash_intense.png",
         "prompt": "Intense second sword duel between medieval knight and samurai on bridge, fast aggressive exchanges, emotional combat, dynamic action cinematography",
         "duration": 6},
        {"image": "scene_08_second_clash/scene08_02_kagemasa_forced_to_kneel.png",
         "prompt": "Samurai warrior forced to one knee on a bridge by a knight's blade, dramatic defeat pose, morning light, cinematic low angle",
         "duration": 5},
    ],
    9: [
        {"image": "scene_09_execution_moment/scene09_01_execution_position.png",
         "prompt": "Knight raising sword for execution over a kneeling samurai, dramatic backlit morning light, time seems to slow, cinematic 2.39:1",
         "duration": 4},
        {"image": "scene_09_execution_moment/scene09_02_menpou_falling.png",
         "prompt": "Samurai demon mask (menpou) falling in slow motion from a warrior's face, tumbling through the air, bridge stone below, cinematic slow motion",
         "duration": 4},
        {"image": "scene_09_execution_moment/scene09_03_bare_face_revealed.png",
         "prompt": "Samurai warrior's bare face revealed as his mask falls, showing exhaustion and deep humanity, knight hesitating, emotional close-up",
         "duration": 4},
        {"image": "scene_09_execution_moment/scene09_04_sword_lowered.png",
         "prompt": "Knight slowly lowering his sword, choosing mercy, trembling hand releasing tension, morning sunlight, emotional cinematic moment",
         "duration": 4},
        {"image": "scene_09_execution_moment/scene09_05_sword_tip_on_stone.png",
         "prompt": "Knight's sword tip touching the stone ground of the bridge, the blade resting, not killing, quiet resolution, slow push out",
         "duration": 4},
    ],
    10: [
        {"image": "scene_10_honor_choice/scene10_01_sheathing_swords.png",
         "prompt": "Both knight and samurai sheathing their swords simultaneously on a bridge, synchronized motion, mutual respect, morning light warming",
         "duration": 5},
        {"image": "scene_10_honor_choice/scene10_02_mutual_salute.png",
         "prompt": "Medieval knight giving a knight's bow and samurai giving a deep samurai bow simultaneously, mutual honor salute on bridge, warm morning light",
         "duration": 5},
    ],
    11: [
        {"image": "scene_11_war_call/scene11_01_parting_ways.png",
         "prompt": "Knight and samurai walking away from each other to opposite ends of bridge, slow zoom out, war horns audible, bittersweet departure",
         "duration": 5},
        {"image": "scene_11_war_call/scene11_02_last_look.png",
         "prompt": "Knight and samurai each pausing and looking back over their shoulder one last time before disappearing into fog on opposite sides, cinematic",
         "duration": 5},
    ],
    12: [
        {"image": "scene_12_epilogue/scene12_01_empty_bridge.png",
         "prompt": "Empty ruined stone bridge with only battle marks remaining, fog slowly rolling in, no warriors, quiet melancholy, slow pan, desaturating back",
         "duration": 5},
        {"image": "scene_12_epilogue/scene12_02_crane_shot_armies.png",
         "prompt": "Aerial crane shot pulling back to reveal vast armies on both sides of the bridge still facing each other, two tiny warriors disappearing into them, epic scale",
         "duration": 6},
    ],
}


def render_clip(tool: SoraVideo, scene_num: int, clip_idx: int, cfg: dict, dry_run: bool) -> bool:
    img_rel = cfg["image"]
    image_path = BASE / img_rel
    out_dir = Path(__file__).parent.parent / "short-film-project" / "output" / f"scene_{scene_num:02d}"
    out_path = out_dir / f"clip_{clip_idx:02d}.mp4"

    if not image_path.exists():
        print(f"  ⚠ 이미지 없음: {image_path}")
        return False

    if out_path.exists():
        print(f"  ✓ 이미 생성됨: {out_path.name} (skip)")
        return True

    if dry_run:
        print(f"  [dry] 씬{scene_num} 클립{clip_idx}: {image_path.name} → {out_path.name} ({cfg['duration']}초)")
        return True

    print(f"  → {image_path.name} … ", end="", flush=True)
    t0 = time.time()
    result = tool.execute({
        "image_path": str(image_path),
        "prompt": cfg["prompt"],
        "duration": cfg["duration"],
        "resolution": "1080p",
        "quality": "medium",
        "output_path": str(out_path),
    })
    elapsed = time.time() - t0
    if result.success:
        print(f"완료 ({elapsed:.0f}s) → {out_path}")
        return True
    else:
        print(f"실패: {result.error}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", type=int, default=0, help="특정 씬 번호 (0=전체)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--test", action="store_true", help="씬1 클립1만 테스트")
    args = parser.parse_args()

    tool = SoraVideo()
    if not args.dry_run:
        ok, msg = tool.check_dependencies()
        if not ok:
            print(f"[오류] {msg}")
            sys.exit(1)

    scenes_to_run = {args.scene: SCENES[args.scene]} if args.scene else SCENES
    if args.test:
        scenes_to_run = {1: [SCENES[1][0]]}

    total = sum(len(v) for v in scenes_to_run.values())
    done = 0
    print(f"총 {len(scenes_to_run)}개 씬, {total}개 클립 렌더링 시작\n")

    for scene_num, clips in sorted(scenes_to_run.items()):
        print(f"▶ 씬 {scene_num} ({len(clips)}개 클립)")
        for i, cfg in enumerate(clips, 1):
            ok = render_clip(tool, scene_num, i, cfg, args.dry_run)
            if ok:
                done += 1

    print(f"\n완료: {done}/{total}")


if __name__ == "__main__":
    main()
