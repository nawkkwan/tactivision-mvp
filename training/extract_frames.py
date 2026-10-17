from __future__ import annotations

import argparse
from pathlib import Path

import cv2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ตัดภาพตัวเลือกจากวิดีโอฟุตบอลตามช่วงเวลาที่กำหนด"
    )
    parser.add_argument("--video", required=True, help="ตำแหน่งไฟล์วิดีโอ")
    parser.add_argument(
        "--output",
        default="training/data/candidates",
        help="โฟลเดอร์เก็บภาพที่ตัดออกมา",
    )
    parser.add_argument(
        "--every-seconds",
        type=float,
        default=30.0,
        help="ตัดหนึ่งภาพทุกกี่วินาที (ค่าเริ่มต้น 30)",
    )
    parser.add_argument("--start-seconds", type=float, default=0.0)
    parser.add_argument("--end-seconds", type=float, default=None)
    parser.add_argument("--max-frames", type=int, default=None)
    return parser.parse_args()


def format_timestamp(seconds: float) -> str:
    total_seconds = max(0, int(round(seconds)))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}-{minutes:02d}-{secs:02d}"


def extract_frames(
    video_path: Path,
    output_dir: Path,
    every_seconds: float,
    start_seconds: float = 0.0,
    end_seconds: float | None = None,
    max_frames: int | None = None,
) -> list[Path]:
    if every_seconds <= 0:
        raise ValueError("--every-seconds ต้องมากกว่า 0")
    if start_seconds < 0:
        raise ValueError("--start-seconds ต้องไม่ติดลบ")
    if end_seconds is not None and end_seconds <= start_seconds:
        raise ValueError("--end-seconds ต้องมากกว่า --start-seconds")
    if not video_path.is_file():
        raise FileNotFoundError(f"ไม่พบวิดีโอ: {video_path}")

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"เปิดวิดีโอไม่ได้: {video_path}")

    fps = float(capture.get(cv2.CAP_PROP_FPS))
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0 or frame_count <= 0:
        capture.release()
        raise RuntimeError("อ่าน FPS หรือจำนวนเฟรมจากวิดีโอไม่ได้")

    duration_seconds = frame_count / fps
    stop_seconds = min(end_seconds or duration_seconds, duration_seconds)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved: list[Path] = []
    timestamp = start_seconds
    while timestamp < stop_seconds:
        if max_frames is not None and len(saved) >= max_frames:
            break
        capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        ok, frame = capture.read()
        if not ok:
            break

        filename = f"{video_path.stem}_{format_timestamp(timestamp)}.jpg"
        output_path = output_dir / filename
        if not cv2.imwrite(str(output_path), frame):
            capture.release()
            raise RuntimeError(f"บันทึกภาพไม่ได้: {output_path}")
        saved.append(output_path)
        timestamp += every_seconds

    capture.release()
    return saved


def main() -> None:
    args = parse_args()
    saved = extract_frames(
        video_path=Path(args.video),
        output_dir=Path(args.output),
        every_seconds=args.every_seconds,
        start_seconds=args.start_seconds,
        end_seconds=args.end_seconds,
        max_frames=args.max_frames,
    )
    print(f"ตัดภาพสำเร็จ {len(saved)} ภาพ")
    if saved:
        print(f"โฟลเดอร์: {saved[0].parent.resolve()}")


if __name__ == "__main__":
    main()
