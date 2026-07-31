"""
Phase 0–1: video → face detect → eye black bars (or emoji) unless consented.

Usage:
  python -m smir_face.worker --input demo.mp4 --output out.mp4
  python -m smir_face.worker --input demo.mp4 --output out.mp4 \\
    --api-url http://localhost:8090 --poi-id <uuid>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from smir_face.avatar_sprite import DEFAULT_OVERLAY_SCALE, EMOJI_IDS, get_sprite, overlay_sprite
from smir_face.embeddings import (
    fetch_consented_faces_from_api,
    fetch_embeddings_from_api,
    load_embeddings_json,
    match_consented_face,
    patch_from_bbox,
    post_face_presence,
)
from smir_face.eye_mask import (
    FaceBarTracker,
    bbox_from_detection,
    draw_eye_rects,
    draw_face_bar,
    draw_mask_image,
    eye_rects_from_detections,
    face_bars_from_detections,
)
from smir_face.face_box import detections_to_boxes
from smir_face.privacy_gate import PrivacyGate
from smir_face.rtmp_writer import FfmpegRtmpWriter
from smir_face.rtsp_capture import FfmpegRtspCapture
from smir_face.tracker import FaceTracker


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Smir face worker POC")
    p.add_argument("--input", required=True, help="Input video path")
    p.add_argument(
        "--output",
        required=True,
        help="Output MP4 path or RTMP URL (rtmp://127.0.0.1:1935/gopro_avatar)",
    )
    p.add_argument("--consent-embeddings", default="", help="JSON file with embeddings")
    p.add_argument("--api-url", default="", help="Smir API base URL")
    p.add_argument("--poi-id", default="", help="POI UUID for consent lookup")
    p.add_argument("--camera-id", default="", help="Camera UUID for face presence / airtime")
    p.add_argument(
        "--demo-fallback",
        action="store_true",
        help="If MediaPipe finds no face, use moving demo bbox (Phase 0 synthetic video)",
    )
    p.add_argument("--max-frames", type=int, default=0, help="Stop after N frames (0=all)")
    p.add_argument("--consent-threshold", type=float, default=0.0, help="Match threshold override")
    p.add_argument(
        "--mask",
        default="eye-rect",
        choices=("eye-rect", "face-bar", "emoji"),
        help="Privacy mask: eye rectangles (default), face bar, or emoji sprite",
    )
    p.add_argument(
        "--emoji",
        default="stylized",
        choices=list(EMOJI_IDS),
        help="Emoji style when --mask emoji",
    )
    p.add_argument(
        "--track-smooth",
        type=float,
        default=0.55,
        help="Smoothing for eye bars / face box (higher = stickier)",
    )
    p.add_argument(
        "--overlay-scale",
        type=float,
        default=DEFAULT_OVERLAY_SCALE,
        help="Emoji size when --mask emoji",
    )
    p.add_argument("--mask-image", default="", help="PNG/JPG overlay instead of black mask")
    p.add_argument(
        "--output-delay-ms",
        type=int,
        default=300,
        help="Задержка выходного буфера (мс): кадр анализируется до публикации",
    )
    return p.parse_args()


def demo_bbox(frame_idx: int, total: int, w: int, h: int) -> tuple[int, int, int, int]:
    t = frame_idx / max(total - 1, 1)
    cx = int(w * (0.25 + 0.5 * t))
    cy = h // 2
    return cx - 55, cy - 70, 110, 140


def run(
    input_path: str,
    output_path: str,
    consent_path: str,
    api_url: str,
    poi_id: str,
    camera_id: str = "",
    demo_fallback: bool = False,
    max_frames: int = 0,
    consent_threshold: float = 0.0,
    mask_mode: str = "face-bar",
    emoji_id: str = "stylized",
    track_smooth: float = 0.55,
    overlay_scale: float = DEFAULT_OVERLAY_SCALE,
    mask_image_path: str = "",
    output_delay_ms: int = 900,
) -> int:
    try:
        import cv2
        import mediapipe as mp
    except ImportError:
        print("Install: pip install -r requirements.txt", file=sys.stderr)
        return 1

    consented_faces: list[dict] = []
    if consent_path:
        consented_faces = [{"embedding": e, "display_name": ""} for e in load_embeddings_json(consent_path)]
    elif api_url:
        consented_faces = fetch_consented_faces_from_api(api_url)

    def reload_consented() -> None:
        nonlocal consented_faces
        if api_url:
            fresh = fetch_consented_faces_from_api(api_url)
            if fresh:
                consented_faces = fresh

    is_rtsp = input_path.lower().startswith(("rtsp://", "rtsps://", "http://", "https://"))
    src = Path(input_path)
    if not is_rtsp and not src.is_file():
        print(f"Input not found: {src}", file=sys.stderr)
        return 1

    cap = None
    rtsp_cap: FfmpegRtspCapture | None = None
    if is_rtsp:
        print(f"Live input: {input_path} (max_frames={max_frames or 'unlimited'})")
        try:
            rtsp_cap = FfmpegRtspCapture(input_path)
            w, h, fps = rtsp_cap.width, rtsp_cap.height, rtsp_cap.fps
            print(f"RTSP via ffmpeg: {w}x{h} @ {fps:.1f} fps")
        except Exception as e:
            print(f"ffmpeg RTSP failed ({e}), trying OpenCV…", file=sys.stderr)
            rtsp_cap = None

    if rtsp_cap is None:
        if is_rtsp:
            import os

            os.environ.setdefault(
                "OPENCV_FFMPEG_CAPTURE_OPTIONS",
                "rtsp_transport;tcp|stimeout;5000000",
            )
            cap = cv2.VideoCapture(input_path, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                cap = cv2.VideoCapture(input_path)
        else:
            cap = cv2.VideoCapture(str(src))
        if not cap.isOpened():
            print(f"Cannot open: {input_path}", file=sys.stderr)
            return 1
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    else:
        cap = None

    match_threshold = consent_threshold if consent_threshold > 0 else 0.85

    mp_face = mp.solutions.face_detection
    # model 1 = full range (лучше для GoPro / средних дистанций)
    min_conf = 0.35
    detector = mp_face.FaceDetection(model_selection=1, min_detection_confidence=min_conf)

    use_emoji = mask_mode == "emoji"
    use_eye_rect = mask_mode == "eye-rect"
    face_tracker = FaceTracker(pos_smooth=track_smooth, size_smooth=max(0.22, track_smooth - 0.12))
    bar_tracker = FaceBarTracker(pos_smooth=track_smooth, size_smooth=max(0.25, track_smooth - 0.15))
    sprite = get_sprite(emoji_id, size=384) if use_emoji else None
    mask_img = None
    if mask_image_path:
        mask_img = cv2.imread(mask_image_path, cv2.IMREAD_UNCHANGED)
        if mask_img is not None:
            print(f"Custom mask image: {mask_image_path}")
    print(
        f"Mask: {mask_mode} | pos_smooth={track_smooth} | output_delay={output_delay_ms}ms"
        + (f" | emoji={emoji_id}" if use_emoji else "")
    )

    delay_frames = max(1, int(fps * output_delay_ms / 1000.0))
    privacy_gate = PrivacyGate(delay_frames=delay_frames, face_ttl=12, expand=1.2)
    fast_bar_tracker = FaceBarTracker(pos_smooth=0.35, size_smooth=0.3)
    presence_acc: dict[str, float] = {}
    frame_dt = 1.0 / max(fps, 1.0)

    def flush_presence() -> None:
        nonlocal presence_acc
        if not api_url or not camera_id or not presence_acc:
            presence_acc = {}
            return
        items = [
            {"user_id": uid, "camera_id": camera_id, "seconds": round(sec, 3)}
            for uid, sec in presence_acc.items()
            if sec > 0
        ]
        presence_acc = {}
        import os

        post_face_presence(api_url, camera_id, items, os.environ.get("SMIR_WORKER_TOKEN", ""))

    def draw_name_under_chin(out, fx: int, fy: int, fbw: int, fbh: int, name: str) -> None:
        import cv2

        if not name:
            return
        chin_y = fy + int(fbh * 0.92)
        cx = fx + fbw // 2
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = max(0.5, fbw / 240.0)
        thickness = max(1, int(scale * 2))
        (tw, th), baseline = cv2.getTextSize(name, font, scale, thickness)
        tx = max(0, min(cx - tw // 2, out.shape[1] - tw - 1))
        ty = min(out.shape[0] - 4, chin_y + th + 6)
        pad = 4
        cv2.rectangle(
            out,
            (tx - pad, ty - th - pad),
            (tx + tw + pad, ty + baseline + pad),
            (0, 0, 0),
            -1,
        )
        cv2.putText(out, name, (tx, ty), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

    def _draw_privacy_at_detection(out, det, fw: int, fh: int) -> None:
        fx, fy, fbw, fbh = bbox_from_detection(det, fw, fh)
        expanded = privacy_gate.expand_box(fx, fy, fbw, fbh, fw, fh)
        sig = patch_from_bbox(out, fx, fy, fbw, fbh)
        hit = match_consented_face(sig, consented_faces, threshold=match_threshold)
        matched_name = (hit or {}).get("display_name") or ""
        if hit and hit.get("user_id"):
            presence_acc[hit["user_id"]] = presence_acc.get(hit["user_id"], 0.0) + frame_dt
        if matched_name:
            nonlocal real_count
            real_count += 1
            draw_name_under_chin(out, fx, fy, fbw, fbh, matched_name)
            return
        nonlocal avatar_count
        avatar_count += 1
        if mask_img is not None:
            draw_mask_image(out, expanded, mask_img)
        elif use_eye_rect:
            draw_eye_rects(out, eye_rects_from_detections([det], fw, fh))
        elif use_emoji and sprite is not None:
            overlay_sprite(out, sprite, expanded, overlay_scale)
        else:
            draw_face_bar(out, expanded)

    def _draw_privacy_at_box(out, box: tuple[int, int, int, int]) -> None:
        nonlocal avatar_count
        avatar_count += 1
        if mask_img is not None:
            draw_mask_image(out, box, mask_img)
        elif use_eye_rect:
            draw_face_bar(out, box)
        elif use_emoji and sprite is not None:
            overlay_sprite(out, sprite, box, overlay_scale)
        else:
            draw_face_bar(out, box)

    def _center_near(cx: float, cy: float, centers: list[tuple[float, float]], fw: int) -> bool:
        thresh = fw * 0.12
        return any((cx - mx) ** 2 + (cy - my) ** 2 < thresh ** 2 for mx, my in centers)

    def apply_privacy_mask(frame: np.ndarray) -> np.ndarray:
        nonlocal avatar_count, real_count
        import cv2

        out = frame.copy()
        fh, fw = out.shape[:2]
        rgb = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
        results = detector.process(rgb)
        dets = results.detections or []

        det_boxes = []
        for det in dets:
            fx, fy, fbw, fbh = bbox_from_detection(det, fw, fh)
            det_boxes.append(privacy_gate.expand_box(fx, fy, fbw, fbh, fw, fh))

        tracked_boxes = privacy_gate.update_tracks(det_boxes)
        masked_centers: list[tuple[float, float]] = []

        for det in dets:
            fx, fy, fbw, fbh = bbox_from_detection(det, fw, fh)
            _draw_privacy_at_detection(out, det, fw, fh)
            masked_centers.append((fx + fbw / 2, fy + fbh / 2))

        for box in tracked_boxes:
            bx, by, bw, bh = box
            cx, cy = bx + bw / 2, by + bh / 2
            if _center_near(cx, cy, masked_centers, fw):
                continue
            _draw_privacy_at_box(out, box)
            masked_centers.append((cx, cy))

        return out

    def write_frame(frame: np.ndarray) -> bool:
        if rtmp_writer is not None:
            return rtmp_writer.write(frame)
        if writer is not None:
            writer.append_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            return True
        return False

    frame_idx = 0
    avatar_count = 0
    real_count = 0
    if cap is not None:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    else:
        total_frames = max(max_frames, 1) if max_frames > 0 else 1

    is_rtmp_out = output_path.lower().startswith("rtmp://")
    writer = None
    rtmp_writer: FfmpegRtmpWriter | None = None
    if is_rtmp_out:
        rtmp_writer = FfmpegRtmpWriter(output_path, w, h, fps=fps)
        print(f"RTMP publish: {output_path}")
    else:
        try:
            import imageio

            writer = imageio.get_writer(output_path, fps=fps, codec="libx264")
        except Exception as e:
            print(f"Warning: streaming writer failed ({e})", file=sys.stderr)
            writer = None

    while True:
        if rtsp_cap is not None:
            ok, frame = rtsp_cap.read()
        else:
            ok, frame = cap.read()
        if not ok or frame is None:
            break

        for ready in privacy_gate.ingest(frame):
            masked = apply_privacy_mask(ready)
            if not write_frame(masked):
                print("RTMP writer stopped", file=sys.stderr)
                ok = False
                break

        if not ok:
            break

        frame_idx += 1
        if frame_idx % 150 == 0:
            reload_consented()
        if frame_idx % 30 == 0 and frame_idx > 0:
            flush_presence()
        if frame_idx % 90 == 0 and frame_idx > 0:
            print(f"  … {frame_idx} frames", flush=True)
        if max_frames > 0 and frame_idx >= max_frames:
            break

    flush_presence()
    for tail in privacy_gate.flush():
        masked = apply_privacy_mask(tail)
        write_frame(masked)

    if rtsp_cap is not None:
        rtsp_cap.release()
    elif cap is not None:
        cap.release()
    if rtmp_writer is not None:
        rtmp_writer.close()
    elif writer is not None:
        writer.close()
        if not Path(output_path).is_file():
            print(f"Failed to write video: {output_path}", file=sys.stderr)
            return 1
    else:
        print("No output writer", file=sys.stderr)
        return 1
    print(f"Processed {frame_idx} frames -> {output_path}")
    label = "masked" if not use_emoji else "avatars"
    print(f"Consented templates: {len(consented_faces)} | {label}: {avatar_count} | real: {real_count}")
    return 0


def main() -> None:
    args = parse_args()
    raise SystemExit(
        run(
            args.input,
            args.output,
            args.consent_embeddings,
            args.api_url,
            args.poi_id,
            camera_id=getattr(args, "camera_id", "") or "",
            demo_fallback=args.demo_fallback,
            max_frames=args.max_frames,
            consent_threshold=args.consent_threshold,
            mask_mode=args.mask,
            emoji_id=args.emoji,
            track_smooth=args.track_smooth,
            overlay_scale=args.overlay_scale,
            mask_image_path=args.mask_image,
            output_delay_ms=args.output_delay_ms,
        )
    )


if __name__ == "__main__":
    main()
