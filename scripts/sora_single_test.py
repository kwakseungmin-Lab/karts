"""기존 큐 전체 취소 후 단건 Sora 테스트."""
import os, requests, time, json
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

key = os.environ["OPENAI_API_KEY"]
URL = "https://api.openai.com/v1/videos"
hdrs = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

# 1. 기존 queued/in_progress 전부 취소
print("기존 작업 취소 중…")
r = requests.get(f"{URL}?limit=100", headers=hdrs, timeout=30)
cancelled = 0
for v in r.json().get("data", []):
    if v["status"] in ("queued", "in_progress"):
        requests.delete(f"{URL}/{v['id']}", headers=hdrs, timeout=10)
        cancelled += 1
print(f"취소: {cancelled}개\n")

# 2. 단건 제출
print("단건 제출…")
payload = {
    "model": "sora-2",
    "prompt": "A lone medieval knight standing on a foggy stone bridge at dawn, slow cinematic push in, desaturated grey tones",
    "seconds": "4",
    "size": "1280x720",
}
r = requests.post(URL, headers=hdrs, json=payload, timeout=30)
print(f"응답: {r.status_code}")
d = r.json()
vid_id = d.get("id")
print(f"video_id: {vid_id}")
print(f"status:   {d.get('status')}\n")

if not vid_id:
    print("제출 실패:", json.dumps(d, indent=2))
    exit(1)

# 3. 폴링 (최대 20분)
out = Path(__file__).parent.parent / "short-film-project" / "output" / "sora_test.mp4"
out.parent.mkdir(parents=True, exist_ok=True)
deadline = time.time() + 1200
prev = ""
while time.time() < deadline:
    time.sleep(10)
    r2 = requests.get(f"{URL}/{vid_id}", headers={"Authorization": f"Bearer {key}"}, timeout=30)
    if r2.status_code != 200:
        print(f"poll error {r2.status_code}"); continue
    d2 = r2.json()
    status = d2.get("status", "")
    prog = d2.get("progress", 0)
    line = f"{status} {prog}%"
    if line != prev:
        print(f"  {line}", flush=True)
        prev = line
    if status == "completed":
        print("\n완료! 다운로드 중…")
        dl = requests.get(f"{URL}/{vid_id}/content/video",
                          headers={"Authorization": f"Bearer {key}"},
                          timeout=120, stream=True)
        with open(out, "wb") as f:
            for chunk in dl.iter_content(8192):
                f.write(chunk)
        size_mb = out.stat().st_size / 1024 / 1024
        print(f"저장 완료: {out}  ({size_mb:.1f} MB)")
        exit(0)
    if status == "failed":
        err = (d2.get("error") or {}).get("message", "")
        print(f"실패: {err}"); exit(1)

print("타임아웃 (20분)")
exit(1)
