from __future__ import annotations

from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

AVATAR_URL = "https://yt3.googleusercontent.com/A9yiwDUN7Rn5NWfF7nNXYz-fBybpf5V94KPSg_FqCWZ8tAcArP9nrxlLcBnJrF2_T-EyBNBy-g=s900-c-k-c0x00ffffff-no-rj"
SHORT_IDS = [
    "JN94JmHmfg0",
    "ZwFYqyY18FY",
    "aaJVpiTJzho",
    "J-9OxOWfh3U",
    "6vc000i2q7E",
    "tkswTMz9y6w",
]
HEADERS = {"User-Agent": "Mozilla/5.0 YunaSiteAssetFetcher/1.0"}


def fetch_image(url: str) -> tuple[bytes, tuple[int, int], str]:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if not content_type.startswith("image/"):
        raise ValueError(f"not an image: {url} ({content_type})")
    image = Image.open(BytesIO(response.content))
    image.verify()
    return response.content, image.size, content_type


avatar, size, content_type = fetch_image(AVATAR_URL)
(ASSETS / "yuna-channel-avatar.jpg").write_bytes(avatar)
print(f"avatar {size[0]}x{size[1]} {content_type}")

for short_id in SHORT_IDS:
    candidates = [
        f"https://i.ytimg.com/vi/{short_id}/oar2.jpg",
        f"https://i.ytimg.com/vi/{short_id}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{short_id}/hqdefault.jpg",
    ]
    last_error: Exception | None = None
    for candidate in candidates:
        try:
            data, dims, content_type = fetch_image(candidate)
            if dims[0] < 320 or dims[1] < 320:
                raise ValueError(f"image too small: {dims}")
            target = ASSETS / f"short-{short_id}.jpg"
            target.write_bytes(data)
            print(f"{short_id} {dims[0]}x{dims[1]} {candidate}")
            break
        except Exception as exc:  # bounded fallback across public thumbnail variants
            last_error = exc
    else:
        raise RuntimeError(f"No usable thumbnail for {short_id}: {last_error}")
