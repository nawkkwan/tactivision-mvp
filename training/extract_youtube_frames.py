from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

# ป้องกัน Windows ภาษาไทย error เมื่อชื่อคลิปหรือ yt-dlp มีอีโมจิ
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# เครื่องมือดึงภาพถูกติดตั้งไว้ในโปรเจกต์ เพื่อไม่ต้องลงโปรแกรมทั้งเครื่อง
LOCAL_DEPENDENCIES = Path(__file__).resolve().parent / ".capture_deps"
if LOCAL_DEPENDENCIES.is_dir():
    sys.path.insert(0, str(LOCAL_DEPENDENCIES))

import imageio_ffmpeg
import yt_dlp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ดึงภาพตามช่วงเวลาจาก YouTube โดยไม่เก็บไฟล์วิดีโอเต็ม"
    )
    parser.add_argument("--url", required=True, help="ลิงก์ YouTube")
    parser.add_argument(
        "--output",
        default="training/data/candidates",
        help="โฟลเดอร์เก็บภาพ JPG",
    )
    parser.add_argument(
        "--every-seconds",
        type=float,
        default=120.0,
        help="เก็บหนึ่งภาพทุกกี่วินาที (ค่าเริ่มต้น 120 = 2 นาที)",
    )
    parser.add_argument("--start-seconds", type=float, default=0.0)
    parser.add_argument("--end-seconds", type=float, default=None)
    parser.add_argument(
        "--max-height",
        type=int,
        default=720,
        help="ความละเอียดสตรีมสูงสุด (ค่าเริ่มต้น 720p)",
    )
    parser.add_argument("--max-frames", type=int, default=None)
    parser.add_argument("--workers", type=int, default=1, help="จำนวนภาพที่ดึงพร้อมกัน")
    return parser.parse_args()


def format_timestamp(seconds: float) -> str:
    total_seconds = max(0, int(round(seconds)))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}-{minutes:02d}-{secs:02d}"


def get_video_info(url: str, max_height: int) -> dict:
    ydl_options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 30,
        "retries": 2,
        "extractor_retries": 2,
        "format": (
            f"bestvideo[height<={max_height}][protocol=m3u8_native]/"
            f"bestvideo[height<={max_height}][ext=mp4]/"
            f"bestvideo[height<={max_height}]/"
            f"best[height<={max_height}]/worst"
        ),
    }
    with yt_dlp.YoutubeDL(ydl_options) as ydl:
        info = ydl.extract_info(url, download=False)

    if "entries" in info:
        info = next((entry for entry in info["entries"] if entry), None)
    if not info or not info.get("url"):
        raise RuntimeError("หารูปแบบวิดีโอที่ใช้ดึงภาพไม่ได้")
    if not info.get("duration"):
        raise RuntimeError("อ่านความยาวคลิปไม่ได้ คลิปอาจกำลัง Live อยู่")
    return info


def load_hls_segments(
    playlist_url: str, http_headers: dict[str, str]
) -> tuple[str | None, list[tuple[float, float, str]]]:
    request = urllib.request.Request(playlist_url, headers=http_headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        playlist = response.read().decode("utf-8")

    init_url: str | None = None
    segments: list[tuple[float, float, str]] = []
    elapsed = 0.0
    pending_duration: float | None = None

    for raw_line in playlist.splitlines():
        line = raw_line.strip()
        if line.startswith("#EXT-X-MAP:"):
            match = re.search(r'URI="([^"]+)"', line)
            if match:
                init_url = urljoin(playlist_url, match.group(1))
        elif line.startswith("#EXTINF:"):
            pending_duration = float(line.split(":", 1)[1].split(",", 1)[0])
        elif line and not line.startswith("#") and pending_duration is not None:
            segment_url = urljoin(playlist_url, line)
            segments.append((elapsed, pending_duration, segment_url))
            elapsed += pending_duration
            pending_duration = None

    if not segments:
        raise RuntimeError("ไม่พบช่วงย่อยในสตรีม HLS")
    return init_url, segments


def find_hls_segment(
    segments: list[tuple[float, float, str]], timestamp: float
) -> tuple[float, float, str]:
    for start, duration, url in segments:
        if start <= timestamp < start + duration:
            return start, duration, url
    return segments[-1]


def build_timestamps(
    duration: float,
    start: float,
    end: float | None,
    every: float,
    max_frames: int | None,
) -> list[float]:
    if every <= 0:
        raise ValueError("--every-seconds ต้องมากกว่า 0")
    if start < 0:
        raise ValueError("--start-seconds ต้องไม่ติดลบ")

    stop = min(end if end is not None else duration, duration)
    if stop <= start:
        raise ValueError("--end-seconds ต้องมากกว่า --start-seconds")

    timestamps: list[float] = []
    current = start
    while current < stop:
        if max_frames is not None and len(timestamps) >= max_frames:
            break
        timestamps.append(current)
        current += every
    return timestamps


def extract_one_frame(
    ffmpeg: str,
    stream_url: str,
    timestamp: float,
    output_path: Path,
    http_headers: dict[str, str],
) -> None:
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
    if http_headers:
        header_text = "".join(f"{key}: {value}\r\n" for key, value in http_headers.items())
        command.extend(["-headers", header_text])
    command.extend(
        [
            "-ss",
            str(timestamp),
            "-i",
            stream_url,
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(output_path),
        ]
    )
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        message = result.stderr.strip().splitlines()
        detail = message[-1] if message else "ไม่ทราบสาเหตุ"
        raise RuntimeError(f"FFmpeg ดึงภาพไม่สำเร็จ: {detail}")


def extract_one_hls_frame(
    ffmpeg: str,
    init_url: str | None,
    segment: tuple[float, float, str],
    timestamp: float,
    output_path: Path,
    http_headers: dict[str, str],
) -> None:
    segment_start, segment_duration, segment_url = segment
    offset = max(0.0, timestamp - segment_start)

    playlist_lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:6",
        f"#EXT-X-TARGETDURATION:{max(1, int(segment_duration + 1))}",
        "#EXT-X-PLAYLIST-TYPE:VOD",
    ]
    if init_url:
        playlist_lines.append(f'#EXT-X-MAP:URI="{init_url}"')
    playlist_lines.extend(
        [
            f"#EXTINF:{segment_duration:.3f},",
            segment_url,
            "#EXT-X-ENDLIST",
        ]
    )

    with tempfile.TemporaryDirectory(prefix="tactivision-hls-") as temp_dir:
        playlist_path = Path(temp_dir) / "selected-segment.m3u8"
        playlist_path.write_text("\n".join(playlist_lines) + "\n", encoding="utf-8")

        command = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-protocol_whitelist",
            "file,http,https,tcp,tls,crypto",
        ]
        command.extend(
            [
                "-i",
                str(playlist_path),
                "-ss",
                str(offset),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(output_path),
            ]
        )
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            message = result.stderr.strip().splitlines()
            detail = "\n".join(message[-8:]) if message else "ไม่ทราบสาเหตุ"
            raise RuntimeError(f"FFmpeg ดึงช่วง HLS ไม่สำเร็จ: {detail}")


def main() -> None:
    args = parse_args()
    if args.workers < 1:
        raise ValueError("--workers ต้องมากกว่า 0")
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("กำลังอ่านข้อมูลคลิป YouTube...")
    info = get_video_info(args.url, args.max_height)
    timestamps = build_timestamps(
        duration=float(info["duration"]),
        start=args.start_seconds,
        end=args.end_seconds,
        every=args.every_seconds,
        max_frames=args.max_frames,
    )

    video_id = info.get("id", "youtube")
    print(f"คลิป: {info.get('title', video_id)}")
    print(f"จะดึงทั้งหมด {len(timestamps)} ภาพ (ไม่เก็บไฟล์วิดีโอ)")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    headers = info.get("http_headers") or {}
    saved: list[Path] = []
    hls_init: str | None = None
    hls_segments: list[tuple[float, float, str]] | None = None
    if info.get("protocol") == "m3u8_native" or ".m3u8" in info["url"]:
        hls_init, hls_segments = load_hls_segments(info["url"], headers)

    def capture(timestamp: float) -> Path:
        output_path = output_dir / f"{video_id}_{format_timestamp(timestamp)}.jpg"
        if output_path.exists() and output_path.stat().st_size > 0:
            return output_path

        if hls_segments is not None:
            extract_one_hls_frame(
                ffmpeg=ffmpeg,
                init_url=hls_init,
                segment=find_hls_segment(hls_segments, timestamp),
                timestamp=timestamp,
                output_path=output_path,
                http_headers=headers,
            )
        else:
            extract_one_frame(
                ffmpeg=ffmpeg,
                stream_url=info["url"],
                timestamp=timestamp,
                output_path=output_path,
                http_headers=headers,
            )
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(f"ไม่ได้ภาพ: {output_path.name}")
        return output_path

    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        pending = {executor.submit(capture, timestamp): timestamp for timestamp in timestamps}
        for index, future in enumerate(as_completed(pending), start=1):
            try:
                output_path = future.result()
                saved.append(output_path)
                print(f"[{index}/{len(timestamps)}] สำเร็จ {output_path.name}")
            except Exception as exc:
                failures.append(format_timestamp(pending[future]))
                print(f"[{index}/{len(timestamps)}] พลาด {failures[-1]}: {exc}")

    print(f"เสร็จแล้ว: {len(saved)} ภาพ")
    print(f"โฟลเดอร์: {output_dir.resolve()}")
    if failures:
        raise RuntimeError(f"ดึงไม่สำเร็จ {len(failures)} ภาพ: {', '.join(failures)}; รันคำสั่งเดิมเพื่อลองใหม่")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"เกิดข้อผิดพลาด: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
