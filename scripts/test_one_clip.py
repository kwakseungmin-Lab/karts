"""씬1 클립1 단건 테스트 — text-to-video."""
import os, requests, time
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

key = os.environ["OPENAI_API_KEY"]
hdrs_json = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
hdrs_auth = {"Authorization": f"Bearer {key}"}
URL = "https://api.openai.com/v1/videos"

payload = {
    "model": "sora-2",
    "prompt": (
        "Desolate medieval battlefield at dawn, grey sky, crows circling overhead, "
        "slow cinematic pan across broken armor and weapons on the ground, "
        "desaturated color palette, dramatic fog, cinematic 2.39:1 aspect ratio"
    ),
    "seconds": "4",
    "size": "1280x720",
}

print("제출 중…")
r = requests.post(URL, headers=hdrs_json, json=payload, timeout=30)
print(f"응답: {r.status_code}")
d = r.json()
vid_id = d.get("id")
print(f"video_id: {vid_id}  status: {d.get('status')}")

if not vid_id:
    print("실패:", d); exit(1)

out = Path(__file__).parent.parent / "short-film-project" / "output" / "scene_01" / "clip_01_test.mp4"
out.parent.mkdir(parents=True, exist_ok=True)

print("폴링 시작…")
deadline = time.time() + 1800  # 최대 30분
while time.time() < deadline:
    time.sleep(15)
    r2 = requests.get(f"{URL}/{vid_id}", headers=hdrs_auth, timeout=30)
    if r2.status_code != 200:
        print(f"  poll error {r2.status_code}"); continue
    d2 = r2.json()
    status = d2.get("status", "")
    prog = d2.get("progress", 0)
    print(f"  {status} {prog}%", flush=True)
    if status == "completed":
        print("완료! 다운로드 중…")
        dl = requests.get(f"{URL}/{vid_id}/content/video", headers=hdrs_auth, timeout=120, stream=True)
        with open(out, "wb") as f:
            for chunk in dl.iter_content(8192):
                f.write(chunk)
        print(f"저장: {out}")
        break
    if status == "failed":
        err = (d2.get("error") or {}).get("message", "")
        print(f"실패: {err}"); break
else:
    print("타임아웃 (30분)")
