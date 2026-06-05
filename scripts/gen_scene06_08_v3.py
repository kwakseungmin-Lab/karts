#!/usr/bin/env python3
"""Generate videos for scenes 06 and 08 using Sora API — v3.

Strategy:
  1. Try image-to-video with safe prompt.
  2. If moderation_blocked → retry text-only (no input_reference).
  3. Skips cuts whose output file was produced in this session.
"""

import os
import base64
import io
import time
import subprocess
import json
import logging
from typing import Optional

import requests
from PIL import Image, ImageOps

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------
ENV_PATH = "/Users/ksm2761/karts/.env"
for line in open(ENV_PATH):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip()

API_KEY = os.environ["OPENAI_API_KEY"]
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

FRAMES_DIR = "/Users/ksm2761/karts/short-film-project/final/frames"
VIDEOS_DIR = "/Users/ksm2761/karts/short-film-project/final/videos"
os.makedirs(VIDEOS_DIR, exist_ok=True)

SESSION_START = time.time()

# ---------------------------------------------------------------------------
# Cut definitions  (scene, cut, seconds)
# ---------------------------------------------------------------------------
CUTS = [
    ("06", "01", 8),
    ("06", "02", 4),
    ("06", "03", 8),
    ("06", "04", 8),
    ("06", "05", 8),
    ("06", "06", 4),
    ("06", "07", 8),
    ("08", "01", 8),
    ("08", "02", 4),
    ("08", "03", 8),
    ("08", "04", 8),
    ("08", "05", 4),
    ("08", "06", 8),
    ("08", "07", 8),
]

# ---------------------------------------------------------------------------
# Prompts — moderation-safe, no combat verbs
# ---------------------------------------------------------------------------
PROMPTS: dict[str, str] = {
    "06_01": (
        "Epic cinematic medium wide orbiting shot, two armored warriors on a "
        "fog-covered ruined stone bridge at dawn. Left figure: samurai in deep navy "
        "layered oyoroi plate armor with gold mon crest, wide shoulder sode guards, "
        "holding a long nodachi with ornate cherry blossom tsuba — arms raised overhead "
        "in a formal opening kata stance. Right figure: medieval knight in dark steel "
        "partial plate with chain mail links, gripping a longsword engraved with runic "
        "symbols — arm raised to meet the incoming blade. Camera arcs dynamically "
        "around both figures, morning mist swirling at knee level. Desaturated cool "
        "blue-grey cinematic palette. For Honor video game cinematic style, "
        "photorealistic CGI, dramatic lighting, 1280x720."
    ),
    "06_02": (
        "Extreme close-up macro slow-motion insert, two ornate sword blades meeting — "
        "a nodachi with cherry blossom tsuba and a longsword with runic engravings "
        "crossing at the forte. Brilliant orange and white light sparks scatter outward "
        "in slow motion from the contact point against a cool blue-grey blurred "
        "background. Ultra-sharp blade edge detail, micro scratches on polished steel. "
        "For Honor cinematic style, photorealistic, dramatic key light, 1280x720."
    ),
    "06_03": (
        "Cinematic medium handheld dynamic shot on a ruined stone bridge, morning fog "
        "partially cleared. Medieval knight in dark steel partial plate armor, scarred "
        "face, brown hair — body low and forward, shoulder pressing against the torso "
        "of an armored samurai in deep navy oyoroi, who leans back regaining footing. "
        "Motion blur on limbs conveys momentum. Camera is loose and reactive. Side "
        "light catches reflections on stone floor. Cool desaturated blue-grey tone. "
        "For Honor cinematic trailer style, photorealistic, 1280x720."
    ),
    "06_04": (
        "Cinematic medium 360-degree tracking orbit on a ruined stone bridge, morning "
        "light from the side. Samurai in deep navy oyoroi armor, wide shoulder sode, "
        "advances steadily with nodachi extended in sweeping horizontal kata form. "
        "Medieval knight in dark steel partial plate moves back toward the stone "
        "railing, longsword raised to deflect each arc. Camera completes a full "
        "revolution. Rim light glints off blades and armor. Residual mist wisps on "
        "bridge floor. For Honor cinematic trailer style, photorealistic, 1280x720."
    ),
    "06_05": (
        "Cinematic medium close-up on a ruined stone bridge, morning side-light. "
        "Medieval knight in dark steel partial plate armor raises longsword high then "
        "redirects the tip low in a flowing kata transition. Samurai in deep navy oyoroi "
        "armor steps back in surprise, recomposing fighting stance. A single vivid red "
        "mark on the navy thigh armor plate stands out against the desaturated cool "
        "blue-grey palette as the only saturated color. Both warriors pause momentarily. "
        "For Honor cinematic trailer style, photorealistic, 1280x720."
    ),
    "06_06": (
        "Extreme macro close-up insert, a single vivid crimson pigment droplet landing "
        "on weathered grey stone surface and spreading slowly into the rough texture. "
        "Cool early morning raking light across stone grain. The crimson is the only "
        "saturated color in the desaturated grey frame. Minimal motion — only the slow "
        "capillary spread across ancient porous stone. Cinematic macro photography "
        "style, photorealistic, 1280x720."
    ),
    "06_07": (
        "Cinematic low angle dramatic push-in shot on a fog-hazed stone bridge. Two "
        "armored warriors charge toward each other — medieval knight in dark steel "
        "partial plate with runic longsword and samurai in deep navy oyoroi with cherry "
        "blossom nodachi — blades crossing and locking in a held bind at center frame. "
        "Camera rushes from ground level and holds as both faces come inches apart, "
        "intense eye contact, chests heaving. Dramatic rim lighting along both blade "
        "edges. Cool blue-grey desaturated tone, slight warm glow behind both figures. "
        "For Honor cinematic epic climax, photorealistic, 1280x720."
    ),
    "08_01": (
        "Cinematic dynamic orbiting medium shot, 180-degree arc around two warriors on "
        "a ruined stone bridge, fog fully cleared, bright morning side-light. Medieval "
        "knight in dark steel partial plate armor, scarred face, brown hair, longsword "
        "with runic engravings — arm extended overhead in a vertical descending kata "
        "form. Samurai in deep navy oyoroi armor with gold imperial crest, wide shoulder "
        "sode, nodachi with cherry blossom tsuba — pivoting to redirect the incoming "
        "blade. Second round of formal duel, elevated intensity. Morning light glinting "
        "off steel, dust rising from stone. For Honor cinematic trailer style, "
        "photorealistic, 1280x720."
    ),
    "08_02": (
        "Extreme close-up slow-motion insert, two blade edges scraping laterally, "
        "light sparks and small metal fragments drifting in a slow arc through morning "
        "light. One chain mail ring separates and spins away from frame. Ancient rough "
        "stone bridge surface beneath, blurred. For Honor cinematic trailer style, "
        "photorealistic, 1280x720."
    ),
    "08_03": (
        "Cinematic scene on a ruined stone bridge, fog cleared, morning light. Medieval "
        "knight in dark steel partial plate armor executes a powerful guard-break "
        "technique, shoulder forward, then in a fluid continuation swings the longsword "
        "crossguard into the samurai's demon-face menpou mask. Samurai in deep navy "
        "oyoroi armor — gold imperial crest, wide sode — staggers back; close-up of "
        "a jagged crack running across the lacquered menpou mask. Camera pulls back to "
        "low-angle medium. For Honor cinematic style, photorealistic, 1280x720."
    ),
    "08_04": (
        "Cinematic POV handheld shaky shot on a ruined stone bridge, morning light. "
        "Samurai in deep navy oyoroi armor, cracked menpou mask, wide shoulder sode — "
        "advancing with wide sweeping nodachi kata arcs that carry raw emotional power. "
        "Medieval knight in dark steel partial plate moves back step by step, longsword "
        "raised in repeated deflections, until back presses against the crumbling stone "
        "bridge parapet. Dynamic, kinetic choreography. For Honor cinematic trailer "
        "style, photorealistic, 1280x720."
    ),
    "08_05": (
        "Extreme macro close-up insert, vivid crimson pigment droplets falling in slow "
        "motion onto ancient rough-textured stone surface. Each drop spreads into the "
        "stone grain, rich crimson contrasting with cool grey stone texture. Morning "
        "side-light rakes across every pore and surface detail. Minimal motion. "
        "Cinematic macro photography style, photorealistic, 1280x720."
    ),
    "08_06": (
        "Cinematic low angle shot looking upward at a medieval knight in dark steel "
        "partial plate armor — scarred face, brown hair, longsword raised overhead — "
        "standing over a kneeling samurai on a stone bridge. Samurai in deep navy oyoroi "
        "armor, cracked menpou mask beginning to tilt, one knee on stone, head lifted "
        "in dignified composure. Knight silhouetted against bright morning sky, rim "
        "light tracing the raised sword edge. Emotional stillness. For Honor cinematic "
        "trailer style, photorealistic, 1280x720."
    ),
    "08_07": (
        "For Honor cinematic trailer style whip-pan tracking shot, two armored warriors "
        "in a breathtaking rapid formal sword-dance on a ruined stone bridge. Medieval "
        "knight in battered dark steel partial plate, scarred face, runic longsword — "
        "and samurai in deep navy oyoroi with cracked gold-crested menpou, wide sode, "
        "cherry blossom nodachi — execute an intricate choreographed kata exchange at "
        "peak speed. Both figures show wear but stand unyielding, gazes locked. Each "
        "blade crossing sends arcs of light-sparks through warm morning sunlight. "
        "Camera whips between tight angles capturing motion blur. Photorealistic, "
        "1280x720."
    ),
}


def image_to_data_url(path: str) -> str:
    img = Image.open(path).convert("RGB")
    img = ImageOps.fit(img, (1280, 720), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def submit_video(prompt: str, seconds: int, hd_path: Optional[str] = None) -> str:
    """Submit a Sora job. If hd_path given, uses image-to-video; otherwise text-to-video."""
    payload: dict = {
        "model": "sora-2",
        "prompt": prompt,
        "seconds": str(seconds),
        "size": "1280x720",
    }
    if hd_path:
        payload["input_reference"] = {"image_url": image_to_data_url(hd_path)}

    resp = requests.post(
        "https://api.openai.com/v1/videos",
        headers=HEADERS,
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    video_id = resp.json()["id"]
    mode = "img2vid" if hd_path else "txt2vid"
    log.info("Submitted %s job: %s", mode, video_id)
    return video_id


def poll_video(video_id: str, max_minutes: int = 15) -> tuple[bool, bool]:
    """Poll until done. Returns (success, was_moderation_blocked)."""
    deadline = time.time() + max_minutes * 60
    consecutive_errors = 0
    while time.time() < deadline:
        time.sleep(15)
        try:
            r = requests.get(
                f"https://api.openai.com/v1/videos/{video_id}",
                headers=HEADERS,
                timeout=45,
            )
            r.raise_for_status()
            consecutive_errors = 0
        except requests.exceptions.RequestException as exc:
            consecutive_errors += 1
            log.warning("Poll network error (%d/5): %s", consecutive_errors, exc)
            if consecutive_errors >= 5:
                log.error("Too many consecutive poll errors for %s", video_id)
                return False, False
            continue
        data = r.json()
        status = data.get("status")
        progress = data.get("progress", 0)
        log.info("  Job %s status: %s (%s%%)", video_id, status, progress)
        if status == "completed":
            return True, False
        if status in ("failed", "cancelled"):
            err_obj = data.get("error") or {}
            code = err_obj.get("code", "")
            msg = err_obj.get("message", status)
            log.error("Job %s ended with status %s: %s", video_id, status, msg)
            return False, code == "moderation_blocked"
    log.error("Timeout waiting for job %s", video_id)
    return False, False


def download_and_upscale(video_id: str, out_path: str) -> None:
    resp = requests.get(
        f"https://api.openai.com/v1/videos/{video_id}/content",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=120,
        stream=True,
    )
    resp.raise_for_status()
    tmp_path = f"/tmp/raw_{video_id}.mp4"
    with open(tmp_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    size = os.path.getsize(tmp_path)
    log.info("Downloaded raw video (%d bytes) → %s", size, tmp_path)

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", tmp_path,
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            out_path,
        ],
        check=True,
        capture_output=True,
    )
    log.info("Upscaled → %s", out_path)
    os.remove(tmp_path)


def process_cut(scene: str, cut: str, seconds: int) -> Optional[str]:
    key = f"{scene}_{cut}"
    hd_path = os.path.join(FRAMES_DIR, f"scene{scene}_cut{cut}_hd.png")
    out_path = os.path.join(VIDEOS_DIR, f"scene{scene}_cut{cut}.mp4")

    # Skip only files produced in THIS session
    if os.path.exists(out_path) and os.path.getsize(out_path) > 100_000:
        mtime = os.path.getmtime(out_path)
        if mtime >= SESSION_START:
            log.info("SKIP scene%s cut%s — produced this session (%d bytes)",
                     scene, cut, os.path.getsize(out_path))
            return out_path

    prompt = PROMPTS[key]
    frame = hd_path if os.path.exists(hd_path) else None

    log.info("=== Processing scene%s cut%s (%ds) ===", scene, cut, seconds)

    # Attempt 1: image-to-video (if frame exists)
    try:
        video_id = submit_video(prompt, seconds, hd_path=frame)
        success, moderated = poll_video(video_id)
        if success:
            download_and_upscale(video_id, out_path)
            return out_path
        if moderated and frame:
            log.warning("Moderation blocked img2vid for %s — retrying text-only", key)
            # Attempt 2: text-to-video (no image reference)
            video_id2 = submit_video(prompt, seconds, hd_path=None)
            success2, moderated2 = poll_video(video_id2)
            if success2:
                download_and_upscale(video_id2, out_path)
                return out_path
            log.error("Text-only also failed for %s (moderated=%s)", key, moderated2)
        else:
            log.error("Generation failed for %s (non-moderation)", key)
    except Exception as e:
        log.error("Error processing %s: %s", key, e, exc_info=True)

    return None


def main() -> None:
    results = []
    for scene, cut, seconds in CUTS:
        out = process_cut(scene, cut, seconds)
        results.append((scene, cut, out))

    log.info("\n=== RESULTS ===")
    for scene, cut, path in results:
        if path and os.path.exists(path):
            size = os.path.getsize(path)
            log.info("scene%s_cut%s.mp4  %d bytes  (%.1f MB)", scene, cut, size, size / 1_048_576)
        else:
            log.warning("scene%s_cut%s  FAILED", scene, cut)

    summary = []
    for scene, cut, path in results:
        entry: dict = {"scene": scene, "cut": cut}
        if path and os.path.exists(path):
            entry["path"] = path
            entry["size_bytes"] = os.path.getsize(path)
            entry["size_mb"] = round(os.path.getsize(path) / 1_048_576, 1)
            entry["status"] = "ok"
        else:
            entry["status"] = "failed"
        summary.append(entry)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
