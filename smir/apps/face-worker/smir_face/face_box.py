"""Face bounding boxes from MediaPipe detections — include hair, stable sizing."""
from __future__ import annotations

from typing import List, Tuple

Box = Tuple[int, int, int, int]


def _clamp(x: int, y: int, bw: int, bh: int, fw: int, fh: int) -> Box:
    bw, bh = max(20, bw), max(20, bh)
    x = max(0, min(x, fw - 1))
    y = max(0, min(y, fh - 1))
    return x, y, min(bw, fw - x), min(bh, fh - y)


def box_from_detection(det, frame_w: int, frame_h: int) -> Box:
    """
    Union of MediaPipe relative bbox + keypoints (eyes/ears/mouth).
    Extra margin on top for hair; wider than chin-only box.
    """
    loc = det.location_data
    rb = loc.relative_bounding_box
    w, h = frame_w, frame_h

    # keypoints in normalized coords
    xs, ys = [], []
    for kp in loc.relative_keypoints:
        xs.append(kp.x * w)
        ys.append(kp.y * h)

    kx1, kx2 = min(xs), max(xs)
    ky1, ky2 = min(ys), max(ys)
    kw, kh = kx2 - kx1, ky2 - ky1

    bx = int(rb.xmin * w)
    by = int(rb.ymin * h)
    bw = int(rb.width * w)
    bh = int(rb.height * h)

    # union
    x1 = min(bx, int(kx1))
    y1 = min(by, int(ky1))
    x2 = max(bx + bw, int(kx2))
    y2 = max(by + bh, int(ky2))
    uw, uh = x2 - x1, y2 - y1

    # prefer keypoint span for width; height extends up for hair
    face_w = max(uw, kw * 1.15)
    face_h = max(uh, kh * 1.35)
    cx = (kx1 + kx2) / 2 if kw > 0 else x1 + uw / 2
    cy = (ky1 + ky2) / 2 if kh > 0 else y1 + uh / 2

    # asym padding: больше сверху (волосы), чуть по бокам
    top_pad = face_h * 0.72
    bottom_pad = face_h * 0.38
    side_pad = face_w * 0.42

    x = int(cx - face_w / 2 - side_pad)
    y = int(cy - face_h / 2 - top_pad)
    bw = int(face_w + 2 * side_pad)
    bh = int(face_h + top_pad + bottom_pad)
    return _clamp(x, y, bw, bh, w, h)


def detections_to_boxes(detections, frame_w: int, frame_h: int) -> List[Box]:
    return [box_from_detection(d, frame_w, frame_h) for d in detections]
