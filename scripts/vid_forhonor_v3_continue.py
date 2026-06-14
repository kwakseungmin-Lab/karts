"""For Honor v3 — 07b~08 이어서 생성 + 조립."""
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

CUTS = [
    {
        "id": "07b", "seconds": "8",
        "prompt": (
            "Cinematic dramatic low angle wide shot, two medieval warriors in an intense standoff "
            "on a rocky battlefield, on the LEFT a large bare-chested tattooed warrior holding "
            "a shield and axe in defensive stance, on the RIGHT an armored knight in dark steel "
            "plate bracing his sword, both warriors tensed and ready in opposition to each other, "
            "destroyed stone fortress walls in the background, grey overcast sky, "
            "cinematic tension before the clash, For Honor combat cinematic style, photorealistic."
        ),
    },
    {
        "id": "07c", "seconds": "8",
        "prompt": (
            "Cinematic dynamic orbiting shot, a massive viking warrior stands in the center "
            "of a chaotic three-way battlefield surrounded by warriors from two other factions, "
            "hundreds of armored figures from three different medieval factions engaged in "
            "battle throughout the background, faction banners visible from all sides, "
            "dust clouds and fire in the distance, epic cinematic scale, "
            "360 degree rotating camera revealing the full chaos, "
            "For Honor large battle cinematic style, photorealistic."
        ),
    },
    {
        "id": "07d", "seconds": "8",
        "prompt": (
            "Cinematic sweeping wide pan across a massive medieval battlefield, "
            "three distinct armies with different armor styles and banners clashing in chaos — "
            "dark steel plate armored knights on the left, lamellar armored samurai in the center, "
            "fur-clad viking warriors on the right — all three armies converging against each other, "
            "cross banners, chrysanthemum banners, and skull banners on opposing sides, "
            "dust and smoke, For Honor large battle cinematic style, photorealistic."
        ),
    },
    {
        "id": "08", "seconds": "8",
        "prompt": (
            "Cinematic slow aerial pullback from high above an ancient scarred battlefield, "
            "three faction banners standing in ruins — a cross banner, a chrysanthemum banner, "
            "a skull banner — new tiny figures beginning to gather at the edges again, "
            "cold grey-green desaturated atmospheric tones, god's eye view rising ever higher, "
            "hopeless eternal cycle, For Honor cinematic aerial style, photorealistic."
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


def run(api_key: str, cut: dict) -> None:
    cid   = cut["id"]
    out   = VIDEO_DIR / f"scene{cid}.mp4"
    if out.exists():
        print(f"[{cid}] 존재, 스킵"); return

    frame = BOARD_DIR / f"scene{cid}_hd.png"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "sora-2", "prompt": cut["prompt"],
        "seconds": cut["seconds"], "size": SORA_SIZE,
        "input_reference": {"image_url": to_data_url(frame)},
    }
    print(f"[{cid}] 제출...")
    r = requests.post(SORA_URL, headers=headers, json=payload, timeout=60)
    if r.status_code not in (200, 201, 202):
        print(f"실패: {r.text[:200]}", file=sys.stderr); sys.exit(1)
    job_id = r.json()["id"]
    print(f"  Job: {job_id}")

    deadline = time.time() + 900
    prev = ""
    while time.time() < deadline:
        time.sleep(15)
        d = requests.get(f"{SORA_URL}/{job_id}", headers=headers, timeout=30).json()
        status = d.get("status", "")
        line = f"  {status} {d.get('progress',0)}%"
        if line != prev: print(line, flush=True); prev = line
        if status == "completed": print(f"  [{cid}] 완료!"); break
        if status in ("failed", "cancelled"):
            print(f"  [{cid}] 실패: {(d.get('error') or {}).get('message','')}", file=sys.stderr)
            sys.exit(1)

    raw = Path(f"/tmp/fhv3_{cid}_raw.mp4")
    resp = requests.get(f"{SORA_URL}/{job_id}/content",
                        headers={"Authorization": f"Bearer {api_key}"},
                        timeout=300, stream=True)
    with open(raw, "wb") as f:
        for chunk in resp.iter_content(8192): f.write(chunk)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw),
         "-vf", "scale=1920:1080:flags=lanczos",
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
         "-an", "-movflags", "+faststart", str(out)],
        check=True, capture_output=True)
    print(f"  [{cid}] 저장: {out.name} ({out.stat().st_size/1024/1024:.1f}MB)\n")


def assemble() -> None:
    concat = Path("/tmp/fhv3_concat.txt")
    with open(concat, "w") as f:
        for cid in CUT_ORDER:
            p = VIDEO_DIR / f"scene{cid}.mp4"
            if p.exists(): f.write(f"file '{p}'\n")
            else: print(f"  경고: {cid} 없음, 스킵")

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


if __name__ == "__main__":
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key: sys.exit("API KEY 없음")
    for cut in CUTS:
        run(api_key, cut)
    assemble()
