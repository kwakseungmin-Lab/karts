"""완료된 Sora 영상 상태 확인 및 다운로드."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

import requests

api_key = os.environ["OPENAI_API_KEY"]
video_id = "video_6a1ff35c0da88191a7b1e698bc775cb40c9c70d7264cda86"
headers = {"Authorization": f"Bearer {api_key}"}

r = requests.get(f"https://api.openai.com/v1/videos/{video_id}", headers=headers, timeout=30)
print(f"상태: {r.status_code}")
data = r.json()
print(json.dumps(data, indent=2)[:3000])
