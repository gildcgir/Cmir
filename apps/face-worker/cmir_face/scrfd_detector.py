"""
SCRFD (InsightFace) face detector with optional SAHI-style tiling for small faces.

Falls back gracefully if insightface/onnxruntime is not installed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np

Box = Tuple[int, int, int, int]


@dataclass
class FaceHit:
    """Unified detection used by the privacy pipeline."""

    bbox: Box  # x, y, w, h in pixels
    score: float = 1.0
    kps: Optional[np.ndarray] = None  # (5, 2) left_eye, right_eye, nose, left_mouth, right_mouth
    embedding: Optional[np.ndarray] = None


def _clamp_box(x: int, y: int, bw: int, bh: int, fw: int, fh: int) -> Box:
    bw, bh = max(8, bw), max(8, bh)
    x = max(0, min(int(x), fw - 1))
    y = max(0, min(int(y), fh - 1))
    return x, y, min(bw, fw - x), min(bh, fh - y)


def pad_box(box: Box, pad: float, fw: int, fh: int) -> Box:
    """Expand bbox by `pad` fraction on each side (e.g. 0.2 = +20%)."""
    x, y, bw, bh = box
    px, py = int(bw * pad), int(bh * pad)
    return _clamp_box(x - px, y - py, bw + 2 * px, bh + 2 * py, fw, fh)


def nms_hits(hits: Sequence[FaceHit], iou_thr: float = 0.45) -> List[FaceHit]:
    if not hits:
        return []
    order = sorted(range(len(hits)), key=lambda i: hits[i].score, reverse=True)
    keep: List[int] = []
    suppressed = [False] * len(hits)

    def iou(a: Box, b: Box) -> float:
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        x1, y1 = max(ax, bx), max(ay, by)
        x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        if inter <= 0:
            return 0.0
        return inter / float(aw * ah + bw * bh - inter)

    for i in order:
        if suppressed[i]:
            continue
        keep.append(i)
        for j in order:
            if suppressed[j] or j == i:
                continue
            if iou(hits[i].bbox, hits[j].bbox) >= iou_thr:
                suppressed[j] = True
    return [hits[i] for i in keep]


def _tiles(fw: int, fh: int, grid: Tuple[int, int], overlap: float) -> List[Tuple[int, int, int, int]]:
    cols, rows = grid
    cols = max(1, cols)
    rows = max(1, rows)
    if cols == 1 and rows == 1:
        return [(0, 0, fw, fh)]
    tw = int(fw / cols * (1 + overlap))
    th = int(fh / rows * (1 + overlap))
    tw = min(fw, max(tw, fw // cols + 1))
    th = min(fh, max(th, fh // rows + 1))
    out: List[Tuple[int, int, int, int]] = []
    for r in range(rows):
        for c in range(cols):
            x0 = int(c * (fw - tw) / max(cols - 1, 1)) if cols > 1 else 0
            y0 = int(r * (fh - th) / max(rows - 1, 1)) if rows > 1 else 0
            out.append((x0, y0, min(tw, fw - x0), min(th, fh - y0)))
    # Always include full frame for large faces
    out.append((0, 0, fw, fh))
    return out


class ScrfdDetector:
    """InsightFace FaceAnalysis (SCRFD + optional recognition)."""

    def __init__(
        self,
        det_size: Tuple[int, int] = (640, 640),
        providers: Optional[List[str]] = None,
        model_name: str = "buffalo_l",
        ctx_id: int = -1,
        tile: bool = True,
        tile_grid: Tuple[int, int] = (2, 2),
        tile_overlap: float = 0.25,
        tile_min_side: int = 900,
        det_thresh: float = 0.35,
    ) -> None:
        from insightface.app import FaceAnalysis

        if providers is None:
            providers = ["CUDAExecutionProvider", "CoreMLExecutionProvider", "CPUExecutionProvider"]
        self.app = FaceAnalysis(name=model_name, providers=providers, allowed_modules=["detection"])
        # ctx_id=-1 → CPU; 0 → first GPU when available
        self.app.prepare(ctx_id=ctx_id, det_size=det_size)
        self.tile = tile
        self.tile_grid = tile_grid
        self.tile_overlap = tile_overlap
        self.tile_min_side = tile_min_side
        self.det_thresh = det_thresh
        self.det_size = det_size

    @staticmethod
    def available() -> bool:
        try:
            import insightface  # noqa: F401
            import onnxruntime  # noqa: F401

            return True
        except Exception:
            return False

    def _face_to_hit(self, face, ox: int = 0, oy: int = 0, fw: int = 0, fh: int = 0) -> Optional[FaceHit]:
        score = float(getattr(face, "det_score", 1.0) or 1.0)
        if score < self.det_thresh:
            return None
        bbox = np.asarray(face.bbox, dtype=np.float32).reshape(-1)
        if bbox.size < 4:
            return None
        x1, y1, x2, y2 = bbox[:4]
        x1, y1, x2, y2 = x1 + ox, y1 + oy, x2 + ox, y2 + oy
        box = _clamp_box(int(x1), int(y1), int(x2 - x1), int(y2 - y1), fw, fh)
        kps = None
        if getattr(face, "kps", None) is not None:
            kps = np.asarray(face.kps, dtype=np.float32).reshape(-1, 2).copy()
            kps[:, 0] += ox
            kps[:, 1] += oy
        emb = None
        if getattr(face, "embedding", None) is not None:
            emb = np.asarray(face.embedding, dtype=np.float32)
        return FaceHit(bbox=box, score=score, kps=kps, embedding=emb)

    def _detect_roi(self, frame_bgr: np.ndarray, ox: int, oy: int, fw: int, fh: int) -> List[FaceHit]:
        faces = self.app.get(frame_bgr)
        hits: List[FaceHit] = []
        for face in faces or []:
            hit = self._face_to_hit(face, ox=ox, oy=oy, fw=fw, fh=fh)
            if hit is not None:
                hits.append(hit)
        return hits

    def detect(self, frame_bgr: np.ndarray) -> List[FaceHit]:
        fh, fw = frame_bgr.shape[:2]
        use_tiles = self.tile and max(fw, fh) >= self.tile_min_side
        if not use_tiles:
            return nms_hits(self._detect_roi(frame_bgr, 0, 0, fw, fh))

        hits: List[FaceHit] = []
        for x0, y0, tw, th in _tiles(fw, fh, self.tile_grid, self.tile_overlap):
            roi = frame_bgr[y0 : y0 + th, x0 : x0 + tw]
            if roi.size == 0:
                continue
            hits.extend(self._detect_roi(roi, x0, y0, fw, fh))
        return nms_hits(hits)


class MediaPipeDetector:
    """Legacy MediaPipe full-range detector (selfie / close-up fallback)."""

    def __init__(self, min_conf: float = 0.35, model_selection: int = 1) -> None:
        import mediapipe as mp

        self._det = mp.solutions.face_detection.FaceDetection(
            model_selection=model_selection,
            min_detection_confidence=min_conf,
        )

    def detect(self, frame_bgr: np.ndarray) -> List[FaceHit]:
        import cv2

        fh, fw = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self._det.process(rgb)
        hits: List[FaceHit] = []
        for det in results.detections or []:
            rb = det.location_data.relative_bounding_box
            x = int(rb.xmin * fw)
            y = int(rb.ymin * fh)
            bw = int(rb.width * fw)
            bh = int(rb.height * fh)
            box = _clamp_box(x, y, bw, bh, fw, fh)
            score = float(det.score[0]) if det.score else 0.5
            kps = None
            rk = det.location_data.relative_keypoints
            if rk and len(rk) >= 2:
                pts = []
                for i in range(min(5, len(rk))):
                    pts.append([rk[i].x * fw, rk[i].y * fh])
                while len(pts) < 5:
                    pts.append(pts[-1])
                kps = np.asarray(pts, dtype=np.float32)
            hits.append(FaceHit(bbox=box, score=score, kps=kps))
        return hits


class HybridDetector:
    """SCRFD primary + MediaPipe secondary, NMS-merged (best of both worlds)."""

    def __init__(self, scrfd: ScrfdDetector, mp: MediaPipeDetector) -> None:
        self.scrfd = scrfd
        self.mp = mp

    def detect(self, frame_bgr: np.ndarray) -> List[FaceHit]:
        hits = list(self.scrfd.detect(frame_bgr))
        hits.extend(self.mp.detect(frame_bgr))
        return nms_hits(hits, iou_thr=0.4)


def create_detector(
    kind: str = "auto",
    tile: bool = True,
    det_size: int = 640,
    tile_grid: str = "2x2",
) -> Tuple[object, str]:
    """
    Returns (detector, name).
    kind: auto | scrfd | mediapipe
    """
    grid = (2, 2)
    if "x" in tile_grid:
        try:
            a, b = tile_grid.lower().split("x", 1)
            grid = (max(1, int(a)), max(1, int(b)))
        except Exception:
            grid = (2, 2)

    if kind == "mediapipe":
        return MediaPipeDetector(), "mediapipe"

    scrfd = None
    if ScrfdDetector.available():
        try:
            scrfd = ScrfdDetector(
                det_size=(det_size, det_size),
                tile=tile,
                tile_grid=grid,
            )
        except Exception as e:
            print(f"SCRFD init failed ({e})", flush=True)
            if kind == "scrfd":
                raise

    if kind == "scrfd":
        if scrfd is None:
            raise RuntimeError(
                "SCRFD requested but insightface/onnxruntime unavailable. "
                "pip install insightface onnxruntime"
            )
        return scrfd, "scrfd"

    # auto: hybrid when SCRFD works, else MediaPipe alone
    mp = MediaPipeDetector()
    if scrfd is not None:
        return HybridDetector(scrfd, mp), "scrfd+mediapipe"
    return mp, "mediapipe"
