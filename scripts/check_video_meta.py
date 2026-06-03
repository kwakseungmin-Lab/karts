"""Check video metadata and download URL structure."""
from __future__ import annotations

import json
import logging
import os

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

VIDEO_ID = "video_6a1ff42247b88190906421cc3b7a1cfc0fbe9ee4bd51b6aa"
SORA_URL = "https://api.openai.com/v1/videos"


def main() -> None:
    headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}
    r = requests.get(f"{SORA_URL}/{VIDEO_ID}", headers=headers, timeout=30)
    log.info("Status: %s", r.status_code)
    log.info("Response:\n%s", json.dumps(r.json(), indent=2))


if __name__ == "__main__":
    main()
