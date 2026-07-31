/** Превью маски: поворот по голове, плашка 2× шире, картинка — на всю голову */

const BAR_WIDTH_FACTOR = 1.28 * 2;
const POS_SMOOTH = 0.28;
const SIZE_SMOOTH = 0.22;
const ANGLE_SMOOTH = 0.35;

function kpCoord(v, dim) {
  return v <= 1 ? v * dim : v;
}

function bboxPixels(bbox, vw, vh) {
  if (!bbox) return null;
  const norm = bbox.originX <= 1 && bbox.originY <= 1 && bbox.width <= 1;
  return {
    x: norm ? bbox.originX * vw : bbox.originX,
    y: norm ? bbox.originY * vh : bbox.originY,
    w: norm ? bbox.width * vw : bbox.width,
    h: norm ? bbox.height * vh : bbox.height,
  };
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function lerpAngle(a, b, t) {
  let d = b - a;
  while (d > Math.PI) d -= 2 * Math.PI;
  while (d < -Math.PI) d += 2 * Math.PI;
  return a + d * t;
}

export function drawNameUnderChin(ctx, pose, name, scale, ox, oy) {
  const cx = ox + pose.cx * scale;
  const chinY = oy + (pose.cy + pose.h * 0.62) * scale;
  const fontSize = Math.max(12, pose.w * scale * 0.16);
  ctx.save();
  ctx.font = `600 ${fontSize}px system-ui, sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  const tw = ctx.measureText(name).width;
  const th = fontSize * 1.15;
  ctx.fillStyle = "rgba(0,0,0,0.85)";
  ctx.fillRect(cx - tw / 2 - 6, chinY, tw + 12, th + 8);
  ctx.fillStyle = "#fff";
  ctx.fillText(name, cx, chinY + 4);
  ctx.restore();
}

export function smoothPose(oldP, newP) {
  if (!oldP) return { ...newP };
  return {
    cx: lerp(oldP.cx, newP.cx, POS_SMOOTH),
    cy: lerp(oldP.cy, newP.cy, POS_SMOOTH),
    w: lerp(oldP.w, newP.w, SIZE_SMOOTH),
    h: lerp(oldP.h, newP.h, SIZE_SMOOTH),
    roll: lerpAngle(oldP.roll, newP.roll, ANGLE_SMOOTH),
    pitch: lerpAngle(oldP.pitch, newP.pitch, ANGLE_SMOOTH),
    yaw: lerpAngle(oldP.yaw, newP.yaw, ANGLE_SMOOTH),
    mode: newP.mode,
  };
}

export function poseFromDetection(kps, vw, vh, bbox, coverHead) {
  if (!kps || kps.length < 2) {
    const box = bboxPixels(bbox, vw, vh);
    if (!box) return null;
    const cx = box.x + box.w / 2;
    const cy = box.y + box.h * 0.42;
    const w = coverHead ? box.w * 1.35 : box.w * 1.1;
    const h = coverHead ? box.h * 1.4 : box.h * 0.45;
    return { cx, cy, w, h, roll: 0, pitch: 0, yaw: 0, mode: coverHead ? "head" : "bar" };
  }

  const rx = kpCoord(kps[0].x, vw);
  const ry = kpCoord(kps[0].y, vh);
  const lx = kpCoord(kps[1].x, vw);
  const ly = kpCoord(kps[1].y, vh);
  const nx = kps[2] ? kpCoord(kps[2].x, vw) : (rx + lx) / 2;
  const ny = kps[2] ? kpCoord(kps[2].y, vh) : (ry + ly) / 2;
  const mx = kps[3] ? kpCoord(kps[3].x, vw) : nx;
  const my = kps[3] ? kpCoord(kps[3].y, vh) : ny + 20;
  const rex = kps[4] ? kpCoord(kps[4].x, vw) : rx - 30;
  const rey = kps[4] ? kpCoord(kps[4].y, vh) : ry;
  const lex = kps[5] ? kpCoord(kps[5].x, vw) : lx + 30;
  const ley = kps[5] ? kpCoord(kps[5].y, vh) : ly;

  const eyeDist = Math.max(12, Math.hypot(lx - rx, ly - ry));
  const cx = (rx + lx) / 2;
  const cy = (ry + ly) / 2;

  const roll = Math.atan2(ly - ry, lx - rx);

  const ex = lx - rx;
  const ey = ly - ry;
  const elen = Math.hypot(ex, ey) || 1;
  const perpX = -ey / elen;
  const perpY = ex / elen;
  const noseOff = (nx - cx) * perpX + (ny - cy) * perpY;
  const yaw = Math.atan2(noseOff, eyeDist * 0.85);

  const earMidX = (rex + lex) / 2;
  const earMidY = (rey + ley) / 2;
  const earSpan = Math.hypot(lex - rex, ley - rey) || eyeDist * 1.6;
  const chinY = Math.max(my, ny + eyeDist * 0.35);
  const pitch = Math.atan2(chinY - cy - eyeDist * 0.55, earSpan * 0.5);

  if (coverHead) {
    const xs = [rx, lx, nx, mx, rex, lex];
    const ys = [ry, ly, ny, my, rey, ley];
    const box = bboxPixels(bbox, vw, vh);
    let minX = Math.min(...xs);
    let maxX = Math.max(...xs);
    let minY = Math.min(...ys);
    let maxY = Math.max(...ys);
    if (box) {
      minX = Math.min(minX, box.x);
      maxX = Math.max(maxX, box.x + box.w);
      minY = Math.min(minY, box.y);
      maxY = Math.max(maxY, box.y + box.h);
    }
    const padX = eyeDist * 0.55;
    const padTop = eyeDist * 0.75;
    const padBottom = eyeDist * 0.45;
    const w = (maxX - minX) + padX * 2;
    const h = (maxY - minY) + padTop + padBottom;
    return {
      cx: (minX + maxX) / 2,
      cy: (minY + maxY) / 2 + padBottom * 0.15,
      w: Math.max(w, eyeDist * 2.4),
      h: Math.max(h, eyeDist * 2.8),
      roll,
      pitch,
      yaw,
      mode: "head",
    };
  }

  const barW = Math.max(72, eyeDist * BAR_WIDTH_FACTOR);
  const barH = Math.max(22, barW * 0.52);
  return {
    cx,
    cy: cy - barH * 0.08,
    w: barW,
    h: barH,
    roll,
    pitch,
    yaw,
    mode: "bar",
  };
}

export function coverTransform(vw, vh, cw, ch) {
  const scale = Math.max(cw / vw, ch / vh);
  const dw = vw * scale;
  const dh = vh * scale;
  return { scale, ox: (cw - dw) / 2, oy: (ch - dh) / 2 };
}

export function drawDefaultPrivacyBar(ctx, pose, scale, ox, oy) {
  const cx = ox + pose.cx * scale;
  const cy = oy + pose.cy * scale;
  const w = pose.w * scale;
  const h = pose.h * scale;
  const skewX = Math.tan(pose.yaw) * 0.42;
  const skewY = Math.tan(pose.pitch) * 0.38;
  const scaleX = 1 + Math.sin(pose.yaw) * 0.22;
  const scaleY = 1 + Math.sin(pose.pitch) * 0.18;

  ctx.save();
  ctx.globalAlpha = 1;
  ctx.translate(cx, cy);
  ctx.rotate(pose.roll);
  ctx.transform(scaleX, skewY, skewX, scaleY, 0, 0);
  ctx.fillStyle = "#000";
  ctx.fillRect(-w / 2, -h / 2, w, h);
  ctx.strokeStyle = "rgba(255,255,255,0.35)";
  ctx.lineWidth = Math.max(1, w * 0.02);
  ctx.strokeRect(-w / 2, -h / 2, w, h);
  ctx.restore();
}

export function drawOrientedOverlay(ctx, pose, maskImg, scale, ox, oy) {
  if (!maskImg || pose.mode === "bar") {
    drawDefaultPrivacyBar(ctx, pose, scale, ox, oy);
    return;
  }

  const cx = ox + pose.cx * scale;
  const cy = oy + pose.cy * scale;
  const w = pose.w * scale;
  const h = pose.h * scale;

  const skewX = Math.tan(pose.yaw) * 0.42;
  const skewY = Math.tan(pose.pitch) * 0.38;
  const scaleX = 1 + Math.sin(pose.yaw) * 0.22;
  const scaleY = 1 + Math.sin(pose.pitch) * 0.18;

  ctx.save();
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = "source-over";
  ctx.translate(cx, cy);
  ctx.rotate(pose.roll);
  ctx.transform(scaleX, skewY, skewX, scaleY, 0, 0);

  ctx.fillStyle = "#000";
  ctx.fillRect(-w / 2, -h / 2, w, h);
  ctx.drawImage(maskImg, -w / 2, -h / 2, w, h);
  ctx.restore();
}

export class AdminMaskPreview {
  constructor(videoEl, canvasEl) {
    this.video = videoEl;
    this.canvas = canvasEl;
    this.ctx = canvasEl.getContext("2d");
    this.detector = null;
    this.maskImg = null;
    this.maskUrl = "";
    this.running = false;
    this.raf = 0;
    this.smooth = null;
    this.lastTs = 0;
    this.ready = false;
  }

  async init() {
    if (this.ready) return;
    const { FaceDetector, FilesetResolver } = await import(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14"
    );
    const vision = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"
    );
    this.detector = await FaceDetector.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath:
          "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite",
      },
      runningMode: "VIDEO",
    });
    this.ready = true;
  }

  setMaskUrl(url) {
    this.maskUrl = url || "";
    this.maskImg = null;
    this.smooth = null;
    if (!url) return;
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      this.maskImg = img;
      this.smooth = null;
    };
    img.onerror = () => { this.maskImg = null; };
    img.src = url;
  }

  resizeCanvas() {
    const wrap = this.canvas.parentElement;
    if (!wrap) return;
    const w = wrap.clientWidth;
    const h = wrap.clientHeight;
    if (this.canvas.width !== w || this.canvas.height !== h) {
      this.canvas.width = w;
      this.canvas.height = h;
    }
  }

  start() {
    if (this.running) return;
    this.running = true;
    this.lastTs = 0;
    const tick = (ts) => {
      if (!this.running) return;
      this.raf = requestAnimationFrame(tick);
      this.drawFrame(ts);
    };
    this.raf = requestAnimationFrame(tick);
  }

  stop() {
    this.running = false;
    if (this.raf) cancelAnimationFrame(this.raf);
    this.raf = 0;
    this.smooth = null;
    this.ctx?.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  drawFrame(ts) {
    const video = this.video;
    if (!video.videoWidth || !this.detector) return;
    this.resizeCanvas();
    const cw = this.canvas.width;
    const ch = this.canvas.height;
    const vw = video.videoWidth;
    const vh = video.videoHeight;
    const { scale, ox, oy } = coverTransform(vw, vh, cw, ch);

    this.ctx.clearRect(0, 0, cw, ch);

    if (ts - this.lastTs >= 33) {
      this.lastTs = ts;
      const dets = this.detector.detectForVideo(video, performance.now()).detections;
      if (dets.length) {
        const d = dets[0];
        const raw = poseFromDetection(d.keypoints, vw, vh, d.boundingBox, !!this.maskImg);
        if (raw) this.smooth = smoothPose(this.smooth, raw);
      }
    }

    if (!this.smooth) return;
    drawOrientedOverlay(this.ctx, this.smooth, this.maskImg, scale, ox, oy);
  }
}
