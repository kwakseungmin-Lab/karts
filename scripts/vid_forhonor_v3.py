"""For Honor 재현 v3 — storyboard_v2 이미지 → Sora 영상 생성 + 조립."""
from __future__ import annotations
import base64, io, os, subprocess, sys, time
from pathlib import Path
import requests
from PIL import Image, ImageOps

for _env in [Path.home()/"karts"/".env", Path(__file__).parent.parent/".env"]:
    if _env.exists():
        for line in _env.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())
        break

BASE_DIR  = Path(__file__).parent.parent
BOARD_DIR = BASE_DIR / "short-film-project" / "reference" / "storyboard_v2"
VIDEO_DIR = BASE_DIR / "short-film-project" / "final" / "forhonor_v3"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

SORA_URL  = "https://api.openai.com/v1/videos"
SORA_SIZE = "1280x720"
FORCE     = "--force" in sys.argv

CUTS = [
    {
        "id": "01", "seconds": "8",
        "prompt": (
            "Cinematic macro close-up of golden wheat field at sunset, warm amber backlight "
            "filtering through wheat stalks creating beautiful bokeh glow, light dust particles "
            "floating in warm air, peaceful abundance, slow gentle horizontal camera pan "
            "through the golden grass, For Honor cinematic style, photorealistic."
        ),
    },
    {
        "id": "02", "seconds": "8",
        "prompt": (
            "Cinematic sweeping aerial crane shot of a grand medieval castle on a rocky hilltop "
            "surrounded by lush green forests, golden morning light through mist, winding river "
            "valley below, peaceful majestic kingdom before war, slow aerial sweep revealing "
            "the full landscape, For Honor cinematic style, photorealistic."
        ),
    },
    {
        "id": "03", "seconds": "8",
        "prompt": (
            "Cinematic wide shot of a medieval town burning with massive fires at night, "
            "intense orange flames consuming buildings, thick black smoke filling the dark sky, "
            "apocalyptic destruction of civilization, slow push through the burning ruins, "
            "For Honor cinematic style, photorealistic."
        ),
    },
    {
        "id": "04", "seconds": "8",
        "prompt": (
            "Cinematic rear tracking shot of a lone massive viking warrior walking slowly "
            "through a completely devastated post-war landscape, dead twisted trees, "
            "rocky barren grey ground, overcast grey sky, completely alone, "
            "slow follow shot capturing isolation and desolation, "
            "For Honor cinematic style, photorealistic."
        ),
    },
    {
        "id": "05", "seconds": "8",
        "prompt": (
            "Cinematic medium wide shot of a viking warrior and a samurai warrior "
            "facing each other across a vast rocky wasteland, both have just spotted each other "
            "and stopped, tense unexpected encounter between two lone survivors, "
            "dead trees and cliffs in background, grey sky, "
            "slow circular orbit around the two warriors, For Honor cinematic style, photorealistic."
        ),
    },
    {
        "id": "06", "seconds": "8",
        "prompt": (
            "Cinematic wide shot of three warriors — viking with axe, samurai with polearm, "
            "knight with sword — in a three-way standoff on a rocky desolate landscape, "
            "all three facing each other in equal triangular formation, none has advantage, "
            "grey misty mountains in background, slow pullback revealing all three warriors, "
            "For Honor cinematic style, photorealistic."
        ),
    },
    {
        "id": "07a", "seconds": "8",
        "prompt": (
            "Cinematic medium shot, a viking warrior swinging his battle axe at a samurai "
            "who deflects with his naginata polearm, the two are ENEMIES fighting each other, "
            "dust kicked up from their feet, dead trees and grey sky, dramatic side lighting, "
            "slow motion impact moment then normal speed, For Honor combat cinematic style, photorealistic."
        ),
    },
    {
        "id": "07b", "seconds": "8",
        "prompt": (
            "Cinematic low angle shot, an armored knight driving his longsword downward at a "
            "massive viking who blocks with his round shield while counter-swinging his axe, "
            "the two are ENEMIES in brutal close combat, ruins in background, grey sky, "
            "dramatic impact freeze frame, For Honor combat cinematic style, photorealistic."
        ),
    },
    {
        "id": "07c", "seconds": "8",
        "prompt": (
            "Cinematic dynamic shot, a viking warrior in the center being attacked simultaneously "
            "from the left by an armored knight with sword and from the right by a samurai with weapon, "
            "the viking fights back against both enemies at once, hundreds of warriors from all "
            "three factions fighting each other in the chaotic background, "
            "360 degree orbit around the central combat, For Honor cinematic style, photorealistic."
        ),
    },
    {
        "id": "07d", "seconds": "8",
        "prompt": (
            "Cinematic sweeping wide pan across a massive three-way medieval battle, "
            "three factions fighting each other simultaneously — knights vs samurai on left, "
            "vikings vs knights on right, cross banners and chrysanthemum banners and skull banners "
            "on opposing sides clashing together, total chaotic three-way war, "
            "dust and fire across the battlefield, For Honor large battle cinematic style, photorealistic."
        ),
    },
    {
        "id": "08", "seconds": "8",
        "prompt": (
            "Cinematic slow aerial pullback from high above an ancient scarred battlefield, "
            "three faction banners — cross, chrysanthemum, skull — standing in ruins, "
            "new tiny figures beginning to gather at the edges, the cycle repeating endlessly, "
            "cold grey-green desaturated tones, god's eye view rising ever higher, "
            "For Honor cinematic aerial style, photorealistic."
        ),
    },
]

CUT_ORDER = ["01","02","03","04","05","06","07a","07b","07c","07d","08"]


def to_data_url(p: Path) -> str:
    w, h = map(int, SORA_SIZE.split("x"))
    img = Image.open(p).convert("RGB")
    img = ImageOps.fit(img, (w, h), Image.LANCZOS)
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"


def submit(api_key: str, cut: dict) -> tuple[str, dict]:
    cid   = cut["id"]
    frame = BOARD_DIR / f"scene{cid}_hd.png"
    if not frame.exists():
        print(f"[{cid}] 프레임 없음: {frame}", file=sys.stderr); sys.exit(1)

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "sora-2",
        "prompt": cut["prompt"],
        "seconds": cut["seconds"],
        "size": SORA_SIZE,
        "input_reference": {"image_url": to_data_url(frame)},
    }
    print(f"[{cid}] Sora 제출...")
    r = requests.post(SORA_URL, headers=headers, json=payload, timeout=60)
    if r.status_code not in (200, 201, 202):
        print(f"  실패 {r.status_code}: {r.text[:200]}", file=sys.stderr); sys.exit(1)
    data = r.json()
    print(f"  Job: {data['id']}")
    return data["id"], headers


def poll(job_id: str, headers: dict, cid: str) -> None:
    deadline = time.time() + 900
    prev = ""
    while time.time() < deadline:
        time.sleep(15)
        d = requests.get(f"{SORA_URL}/{job_id}", headers=headers, timeout=30).json()
        status = d.get("status", "")
        line = f"  {status} {d.get('progress',0)}%"
        if line != prev: print(line, flush=True); prev = line
        if status == "completed": print(f"  [{cid}] 완료!"); return
        if status in ("failed", "cancelled"):
            print(f"  [{cid}] 실패: {(d.get('error') or {}).get('message','')}", file=sys.stderr)
            sys.exit(1)


def save(job_id: str, api_key: str, cid: str) -> None:
    raw   = Path(f"/tmp/fhv3_{cid}_raw.mp4")
    final = VIDEO_DIR / f"scene{cid}.mp4"
    resp  = requests.get(f"{SORA_URL}/{job_id}/content",
                         headers={"Authorization": f"Bearer {api_key}"},
                         timeout=300, stream=True)
    with open(raw, "wb") as f:
        for chunk in resp.iter_content(8192): f.write(chunk)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw),
         "-vf", "scale=1920:1080:flags=lanczos",
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
         "-an", "-movflags", "+faststart", str(final)],
        check=True, capture_output=True)
    print(f"  [{cid}] 저장: {final.name} ({final.stat().st_size/1024/1024:.1f}MB)\n")


def assemble() -> None:
    concat = Path("/tmp/fhv3_concat.txt")
    with open(concat, "w") as f:
        for cid in CUT_ORDER:
            p = VIDEO_DIR / f"scene{cid}.mp4"
            if p.exists(): f.write(f"file '{p}'\n")

    final = VIDEO_DIR / "forhonor_v3.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
         "-an", "-movflags", "+faststart", str(final)],
        check=True, capture_output=True)
    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(final)]).decode())
    print(f"\n{'='*50}")
    print(f"완성: {final}")
    print(f"길이: {int(dur//60)}분 {int(dur%60)}초 | {final.stat().st_size/1024/1024:.0f}MB")
    subprocess.run(["open", str(final)])


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key: sys.exit("API KEY 없음")

    print(f"For Honor v3 — {len(CUTS)}컷 Sora 생성\n")
    for cut in CUTS:
        cid = cut["id"]
        out = VIDEO_DIR / f"scene{cid}.mp4"
        if out.exists() and not FORCE:
            print(f"[{cid}] 이미 존재, 스킵"); continue
        job_id, headers = submit(api_key, cut)
        poll(job_id, headers, cid)
        save(job_id, api_key, cid)

    print("─── 조립 중... ───")
    assemble()


if __name__ == "__main__":
    main()
