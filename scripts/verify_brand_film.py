from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "assets" / "yuna-kbeauty-brand-film.mp4"
POSTER = ROOT / "assets" / "yuna-kbeauty-brand-film-poster.jpg"
MAX_GITHUB_BYTES = 95 * 1024 * 1024


def probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(result.stdout)


assert VIDEO.is_file(), VIDEO
assert POSTER.is_file(), POSTER
video = probe(VIDEO)
poster = probe(POSTER)
video_stream = next(s for s in video["streams"] if s["codec_type"] == "video")
audio_stream = next(s for s in video["streams"] if s["codec_type"] == "audio")
poster_stream = next(s for s in poster["streams"] if s["codec_type"] == "video")
duration = float(video["format"]["duration"])
size = VIDEO.stat().st_size

assert 179.8 <= duration <= 180.2, duration
assert (video_stream["width"], video_stream["height"]) == (1920, 1080), video_stream
assert video_stream["codec_name"] == "h264", video_stream
assert video_stream.get("pix_fmt") in {"yuv420p", "yuvj420p"}, video_stream
assert audio_stream["codec_name"] == "aac", audio_stream
assert int(audio_stream["sample_rate"]) == 48000, audio_stream
assert size <= MAX_GITHUB_BYTES, size
assert (poster_stream["width"], poster_stream["height"]) == (1920, 1080), poster_stream

print(
    json.dumps(
        {
            "status": "PASS",
            "duration_seconds": duration,
            "video": f"{video_stream['codec_name']} {video_stream['width']}x{video_stream['height']} {video_stream.get('pix_fmt')}",
            "audio": f"{audio_stream['codec_name']} {audio_stream['sample_rate']}Hz {audio_stream.get('channels')}ch",
            "bytes": size,
            "github_limit_margin_bytes": MAX_GITHUB_BYTES - size,
            "poster": f"{poster_stream['width']}x{poster_stream['height']}",
        },
        indent=2,
    )
)
