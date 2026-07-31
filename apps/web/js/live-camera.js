/**
 * Мгновенный локальный поток USB + маски/подписи как в админ-превью.
 */
import {
  coverTransform,
  drawNameUnderChin,
  drawOrientedOverlay,
  poseFromDetection,
  smoothPose,
} from "./mask-preview.js";

const PATCH = 32;
const MATCH_THRESHOLD = 0.72;
const MATCH_HOLD_THRESHOLD = 0.62; // hysteresis while already matched
const DETECT_INTERVAL_MS = 33;
const MIN_MASK_CONFIRM_FRAMES = 2;
const SIG_BLEND = 0.35;
const CONSENT_HOLD_FRAMES = 20;

function deviceIdFromCamera(cam) {
  if (cam?.device_id) return cam.device_id;
  const url = cam?.stream_url || "";
  if (url.startsWith("local://")) return url.slice(8);
  return "";
}

function cosine(a, b) {
  if (!a || !b || a.length !== b.length) return 0;
  let s = 0;
  for (let i = 0; i < a.length; i++) s += a[i] * b[i];
  return s;
}

function faceTemplateVectors(face) {
  const out = [];
  if (Array.isArray(face?.embeddings)) {
    for (const e of face.embeddings) if (e?.length === PATCH * PATCH) out.push(e);
  }
  if (Array.isArray(face?.templates)) {
    for (const t of face.templates) {
      const e = t?.embedding || t;
      if (e?.length === PATCH * PATCH) out.push(e);
    }
  }
  if (!out.length && face?.embedding?.length === PATCH * PATCH) out.push(face.embedding);
  return out;
}

function bestFaceScore(sig, face) {
  let best = 0;
  for (const emb of faceTemplateVectors(face)) {
    best = Math.max(best, cosine(sig, emb));
  }
  return best;
}

function matchFace(sig, faces, { priorUserId = "" } = {}) {
  if (!sig) return null;
  let best = null;
  let bestScore = priorUserId ? MATCH_HOLD_THRESHOLD : MATCH_THRESHOLD;
  for (const f of faces) {
    const thr = priorUserId && f.user_id === priorUserId ? MATCH_HOLD_THRESHOLD : MATCH_THRESHOLD;
    const score = bestFaceScore(sig, f);
    if (score >= thr && score >= bestScore) {
      bestScore = score;
      best = f;
    }
  }
  return best;
}

/** Фильтр ложных срабатываний (руки и т.п.) — только похожие на лицо bbox. */
export function isLikelyFaceDetection(d, vw, vh) {
  const bb = d.boundingBox;
  if (!bb || !vw || !vh) return false;
  const norm = bb.originX <= 1 && bb.originY <= 1 && bb.width <= 1;
  const x = norm ? bb.originX * vw : bb.originX;
  const y = norm ? bb.originY * vh : bb.originY;
  const w = norm ? bb.width * vw : bb.width;
  const h = norm ? bb.height * vh : bb.height;
  if (w < 56 || h < 56) return false;
  if (w > vw * 0.42 || h > vh * 0.48) return false;
  const ar = w / h;
  if (ar < 0.68 || ar > 1.32) return false;
  const area = (w * h) / (vw * vh);
  if (area < 0.005 || area > 0.28) return false;

  const kps = d.keypoints;
  if (!kps || kps.length < 3) return false;
  const rx = kps[0].x <= 1 ? kps[0].x * vw : kps[0].x;
  const ry = kps[0].y <= 1 ? kps[0].y * vh : kps[0].y;
  const lx = kps[1].x <= 1 ? kps[1].x * vw : kps[1].x;
  const ly = kps[1].y <= 1 ? kps[1].y * vh : kps[1].y;
  const ny = kps[2].y <= 1 ? kps[2].y * vh : kps[2].y;
  const eyeDist = Math.hypot(lx - rx, ly - ry);
  if (eyeDist < 30 || eyeDist > Math.min(vw, vh) * 0.34) return false;
  const eyeMidY = (ry + ly) / 2;
  if (ny < eyeMidY - 6) return false;
  if (ny > eyeMidY + h * 0.55) return false;
  const cx = (rx + lx) / 2;
  const bbCx = x + w / 2;
  if (Math.abs(cx - bbCx) > w * 0.28) return false;
  if (eyeMidY < y + h * 0.12 || eyeMidY > y + h * 0.58) return false;
  return true;
}

function blendSignature(prev, next) {
  if (!next) return prev;
  if (!prev) return next;
  return prev.map((v, i) => v * (1 - SIG_BLEND) + next[i] * SIG_BLEND);
}

export function signatureFromVideo(video, bbox) {
  const vw = video.videoWidth;
  const vh = video.videoHeight;
  if (!vw || !vh || !bbox) return null;
  const norm = bbox.originX <= 1 && bbox.originY <= 1;
  let x = norm ? bbox.originX * vw : bbox.originX;
  let y = norm ? bbox.originY * vh : bbox.originY;
  let w = norm ? bbox.width * vw : bbox.width;
  let h = norm ? bbox.height * vh : bbox.height;
  x = Math.max(0, x);
  y = Math.max(0, y);
  w = Math.min(w, vw - x);
  h = Math.min(h, vh - y);
  if (w < 8 || h < 8) return null;
  const canvas = document.createElement("canvas");
  canvas.width = PATCH;
  canvas.height = PATCH;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, x, y, w, h, 0, 0, PATCH, PATCH);
  const img = ctx.getImageData(0, 0, PATCH, PATCH);
  const gray = new Float32Array(PATCH * PATCH);
  let minV = 1;
  let maxV = 0;
  for (let i = 0; i < PATCH * PATCH; i++) {
    const o = i * 4;
    const v = (img.data[o] + img.data[o + 1] + img.data[o + 2]) / (3 * 255);
    gray[i] = v;
    if (v < minV) minV = v;
    if (v > maxV) maxV = v;
  }
  const span = Math.max(1e-6, maxV - minV);
  for (let i = 0; i < gray.length; i++) gray[i] = (gray[i] - minV) / span;
  let normV = 0;
  for (let i = 0; i < gray.length; i++) normV += gray[i] * gray[i];
  normV = Math.sqrt(normV) || 1;
  return Array.from(gray, (v) => v / normV);
}

let devicesCache = null;
let devicesCacheAt = 0;

export async function ensureCameraPermission() {
  if (!navigator.mediaDevices?.getUserMedia) return false;
  try {
    const s = await navigator.mediaDevices.getUserMedia({ video: true });
    s.getTracks().forEach((t) => t.stop());
    return true;
  } catch (_) {
    return false;
  }
}

async function enumerateVideoDevices() {
  const now = Date.now();
  if (devicesCache && now - devicesCacheAt < 5000) return devicesCache;
  await ensureCameraPermission();
  if (!navigator.mediaDevices?.enumerateDevices) return [];
  const all = await navigator.mediaDevices.enumerateDevices();
  devicesCache = all.filter((d) => d.kind === "videoinput");
  devicesCacheAt = now;
  return devicesCache;
}

function matchDeviceId(savedId, devices) {
  if (!savedId) return "";
  if (devices.some((d) => d.deviceId === savedId)) return savedId;
  return savedId;
}

/** Синхронный fallback (без enumerateDevices). */
export function resolveUsbDeviceId(cam) {
  return deviceIdFromCamera(cam);
}

function deviceScore(label) {
  const l = (label || "").toLowerCase();
  if (/gopro/.test(l)) return 100;
  if (/obs|virtual|continuity|iphone|blackhole|capture screen/.test(l)) return -1;
  if (/facetime|built-in|встроенн/.test(l)) return 50;
  if (/webcam|usb|camera|камер/.test(l)) return 40;
  return 10;
}

/** GoPro если есть, иначе обычная веб-камера (не virtual/Continuity). */
export function pickPreferredVideoDevice(devices) {
  if (!devices?.length) return null;
  const ranked = devices
    .map((d) => ({ d, s: deviceScore(d.label) }))
    .filter((x) => x.s >= 0)
    .sort((a, b) => b.s - a.s || 0);
  return ranked[0]?.d || devices[0] || null;
}

/**
 * Разрешает USB deviceId: запрашивает доступ к камере, сверяет с сохранённым id,
 * при необходимости берёт другую активную камеру того же POI или единственную USB.
 * Если GoPro нет — заглушка: встроенная / USB веб-камера.
 */
export async function resolveUsbDeviceIdAsync(cam, fallbackCams = []) {
  const candidates = [cam, ...fallbackCams].filter(Boolean);
  const devices = await enumerateVideoDevices();

  for (const c of candidates) {
    const id = deviceIdFromCamera(c);
    if (!id) continue;
    const matched = matchDeviceId(id, devices);
    if (matched && devices.some((d) => d.deviceId === matched)) return matched;
  }

  for (const c of candidates) {
    const label = (c.device_label || c.name || "").trim().toLowerCase();
    if (!label) continue;
    const byLabel = devices.find((d) => (d.label || "").toLowerCase().includes(label));
    if (byLabel?.deviceId) return byLabel.deviceId;
  }

  // Явный GoPro в конфиге, но устройства нет → stub webcam
  const wantsGopro = candidates.some((c) =>
    /gopro/i.test(`${c.device_label || ""} ${c.name || ""}`),
  );
  if (wantsGopro) {
    const stub = pickPreferredVideoDevice(devices.filter((d) => !/gopro/i.test(d.label || "")));
    if (stub?.deviceId) return stub.deviceId;
  }

  const saved = deviceIdFromCamera(cam);
  if (saved && devices.some((d) => d.deviceId === saved)) return saved;

  const wantsUsb = candidates.some((c) => c.is_active && (c.source_type === "local_usb" || deviceIdFromCamera(c)));
  if (wantsUsb && devices.length) {
    const pref = pickPreferredVideoDevice(devices);
    return pref?.deviceId || "";
  }

  return "";
}

export class LiveCameraView {
  constructor(videoEl, canvasEl) {
    this.video = videoEl;
    this.canvas = canvasEl;
    if (!canvasEl) throw new Error("Canvas для маски не найден");
    this.ctx = canvasEl.getContext("2d");
    this.detector = null;
    this.maskImg = null;
    this.stream = null;
    this.running = false;
    this.raf = 0;
    this.lastTs = 0;
    this.faceSmooth = new Map();
    this.consentedFaces = [];
    this.apiBase = "";
    this.reloadTimer = null;
    this.ready = false;
    this.compositeMode = true;
    this.onRecognized = null;
    this.cameraId = "";
    this.presenceAcc = new Map();
    this.presenceTimer = null;
    this.lastFaceBbox = null;
    this.privacyReady = false;
    this.firstDetectDone = false;
  }

  async init() {
    if (this.ready) return;
    const { FaceDetector, FilesetResolver } = await import(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14"
    );
    const vision = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm",
    );
    this.detector = await FaceDetector.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath:
          "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite",
      },
      runningMode: "VIDEO",
      minDetectionConfidence: 0.58,
    });
    this.ready = true;
  }

  async loadConsentedFaces() {
    if (!this.apiBase) return;
    try {
      const res = await fetch(`${this.apiBase}/api/v1/consented-faces`);
      const json = await res.json();
      this.consentedFaces = json.data?.faces || [];
    } catch (_) {
      this.consentedFaces = [];
    }
  }

  setMaskImageUrl(url) {
    this.maskImg = null;
    if (!url) return;
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => { this.maskImg = img; };
    img.src = url;
  }

  async start({
    deviceId,
    maskImageUrl = "",
    apiBase = "",
    cameraId = "",
    compositeMode = true,
  } = {}) {
    this.stop({ keepReady: true });
    this.apiBase = apiBase;
    this.cameraId = cameraId;
    this.compositeMode = compositeMode !== false;
    this.privacyReady = false;
    this.firstDetectDone = false;
    this.setMaskImageUrl(maskImageUrl);
    this.video.classList.toggle("live-source-hidden", this.compositeMode);
    this.canvas.parentElement?.classList.add("privacy-composite");
    if (this.compositeMode) this.canvas.style.opacity = "0";

    await this.init();
    await this.loadConsentedFaces();

    let stream;
    if (deviceId) {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { deviceId: { exact: deviceId } },
        });
      } catch (_) {
        stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId } });
      }
    } else {
      await ensureCameraPermission();
      stream = await navigator.mediaDevices.getUserMedia({ video: true });
    }
    this.stream = stream;
    this.video.srcObject = stream;
    await this.video.play();
    this.running = true;
    this.lastTs = 0;
    const tick = (ts) => {
      if (!this.running) return;
      this.raf = requestAnimationFrame(tick);
      this.drawFrame(ts);
    };
    this.raf = requestAnimationFrame(tick);

    if (this.reloadTimer) clearInterval(this.reloadTimer);
    this.reloadTimer = setInterval(() => this.loadConsentedFaces(), 5000);
    this.presenceTimer = setInterval(() => this.flushPresence(), 1000);
  }

  getLastFaceSignature() {
    if (!this.lastFaceBbox) return null;
    return signatureFromVideo(this.video, this.lastFaceBbox);
  }

  flushPresence() {
    if (!this.apiBase || !this.cameraId || !this.presenceAcc.size) return Promise.resolve();
    const presence = [...this.presenceAcc.entries()].map(([userId, seconds]) => ({
      user_id: userId,
      camera_id: this.cameraId,
      seconds: Math.round(seconds * 1000) / 1000,
    }));
    this.presenceAcc.clear();
    return fetch(`${this.apiBase}/api/v1/face-presence`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ camera_id: this.cameraId, presence }),
      keepalive: true,
    }).catch(() => {});
  }

  stop({ keepReady = false } = {}) {
    this.flushPresence();
    this.running = false;
    if (this.raf) cancelAnimationFrame(this.raf);
    this.raf = 0;
    if (this.reloadTimer) {
      clearInterval(this.reloadTimer);
      this.reloadTimer = null;
    }
    if (this.presenceTimer) {
      clearInterval(this.presenceTimer);
      this.presenceTimer = null;
    }
    if (this.stream) {
      this.stream.getTracks().forEach((t) => t.stop());
      this.stream = null;
    }
    this.video.srcObject = null;
    this.video.classList.remove("live-source-hidden");
    this.canvas.parentElement?.classList.remove("privacy-composite");
    this.faceSmooth.clear();
    this.presenceAcc.clear();
    this.lastFaceBbox = null;
    this.privacyReady = false;
    this.firstDetectDone = false;
    this.ctx?.clearRect(0, 0, this.canvas.width, this.canvas.height);
    if (!keepReady) this.ready = false;
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

  drawFrame(ts) {
    const video = this.video;
    if (!video.videoWidth) return;
    this.resizeCanvas();
    const cw = this.canvas.width;
    const ch = this.canvas.height;
    const vw = video.videoWidth;
    const vh = video.videoHeight;
    const { scale, ox, oy } = coverTransform(vw, vh, cw, ch);

    this.ctx.fillStyle = "#000";
    this.ctx.fillRect(0, 0, cw, ch);

    if (!this.detector) return;

    if (ts - this.lastTs >= DETECT_INTERVAL_MS) {
      const elapsedSec = this.lastTs
        ? Math.min(0.25, Math.max(DETECT_INTERVAL_MS / 1000, (ts - this.lastTs) / 1000))
        : DETECT_INTERVAL_MS / 1000;
      this.lastTs = ts;
      const dets = (this.detector.detectForVideo(video, performance.now()).detections || [])
        .filter((d) => isLikelyFaceDetection(d, vw, vh));
      const usedKeys = new Set();
      let primaryBbox = null;

      for (const d of dets) {
        const coverHead = !!this.maskImg;
        const raw = poseFromDetection(d.keypoints, vw, vh, d.boundingBox, coverHead);
        if (!raw) continue;
        const key = matchFaceTrack(this.faceSmooth, raw);
        const prev = this.faceSmooth.get(key);
        const smooth = smoothPose(prev?.smooth, raw);
        const sigRaw = signatureFromVideo(video, d.boundingBox);
        const sig = blendSignature(prev?.sig, sigRaw);
        const priorId = prev?.userId || "";
        let face = matchFace(sig, this.consentedFaces, { priorUserId: priorId });
        let hold = prev?.hold || 0;
        if (face?.user_id) {
          hold = CONSENT_HOLD_FRAMES;
        } else if (hold > 0 && priorId) {
          // hysteresis: keep registered identity briefly on angled frames
          face = this.consentedFaces.find((f) => f.user_id === priorId) || null;
          hold -= 1;
        } else {
          hold = 0;
        }
        const name = face?.display_name || null;
        const userId = face?.user_id || null;
        const hadName = prev?.name;
        const confirm = (prev?.confirm || 0) + 1;
        this.faceSmooth.set(key, { smooth, name, userId, sig, confirm, missed: 0, hold });
        usedKeys.add(key);
        if (!primaryBbox) primaryBbox = d.boundingBox;
        if (userId) {
          this.presenceAcc.set(userId, (this.presenceAcc.get(userId) || 0) + elapsedSec);
        }
        if (name && !hadName && this.onRecognized) {
          this.onRecognized({ name, userId, key });
        }
      }

      if (primaryBbox) this.lastFaceBbox = primaryBbox;

      for (const [key, state] of this.faceSmooth) {
        if (usedKeys.has(key)) continue;
        state.missed = (state.missed || 0) + 1;
        state.confirm = 0;
        if (state.missed > 8) this.faceSmooth.delete(key);
      }
      this.firstDetectDone = true;
    }

    if (this.compositeMode && !this.firstDetectDone) return;

    if (this.compositeMode) {
      this.ctx.drawImage(video, ox, oy, vw * scale, vh * scale);
    }

    for (const state of this.faceSmooth.values()) {
      if (!state.smooth) continue;
      if (state.name) {
        drawNameUnderChin(this.ctx, state.smooth, state.name, scale, ox, oy);
      } else if ((state.confirm || 0) >= MIN_MASK_CONFIRM_FRAMES) {
        drawOrientedOverlay(this.ctx, state.smooth, this.maskImg, scale, ox, oy);
      }
    }

    if (this.compositeMode && !this.privacyReady) {
      this.privacyReady = true;
      this.canvas.style.opacity = "1";
    }
  }
}

function matchFaceTrack(faceSmooth, raw) {
  let bestKey = null;
  let bestDist = 96;
  for (const [key, state] of faceSmooth) {
    const p = state.smooth;
    if (!p) continue;
    const d = Math.hypot(p.cx - raw.cx, p.cy - raw.cy);
    if (d < bestDist) {
      bestDist = d;
      bestKey = key;
    }
  }
  if (bestKey) return bestKey;
  return `f_${Math.round(raw.cx)}_${Math.round(raw.cy)}_${Date.now() % 100000}`;
}

export async function startUsbCameraView(video, canvas, cam, poi, apiBase, fallbackCams = []) {
  const deviceId = await resolveUsbDeviceIdAsync(cam, fallbackCams);
  if (!deviceId) throw new Error("USB-камера не настроена");
  const view = new LiveCameraView(video, canvas);
  const maskUrl = poi?.mask_image_url ? `${apiBase}${poi.mask_image_url}` : "";
  await view.start({ deviceId, maskImageUrl: maskUrl, apiBase, cameraId: cam?.id || "" });
  return view;
}

function wantsLocalUsb(cam) {
  return !!(
    cam?.source_type === "local_usb"
    || cam?.device_id
    || (cam?.stream_url || "").startsWith("local://")
  );
}

/**
 * USB (getUserMedia) с маской, при ошибке — защищённый HLS.
 * Возвращает { mode: 'usb'|'hls', view, hls }.
 */
export async function startMaskedPageCamera({
  video,
  canvas,
  cam,
  poi,
  fallbackCams = [],
  apiBase,
  clientId,
  onStatus,
  usbOnly = false,
}) {
  if (!cam) throw new Error("Камера не настроена");
  const deviceId = await resolveUsbDeviceIdAsync(cam, fallbackCams);
  const tryUsb = wantsLocalUsb(cam) || !!deviceId;

  if (tryUsb && video && canvas) {
    let lastErr = null;
    for (let i = 0; i < 3; i++) {
      try {
        onStatus?.(i ? `Камера занята, повтор ${i + 1}/3…` : "Подключение USB-камеры…");
        // снять ffmpeg с этого POI, чтобы освободить FaceTime
        if (poi?.id) {
          await fetch(`${apiBase}/api/v1/pois/${poi.id}/stream/release`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ client_id: clientId || "browser", force: true }),
          }).catch(() => {});
        }
        const view = new LiveCameraView(video, canvas);
        const maskUrl = poi?.mask_image_url ? `${apiBase}${poi.mask_image_url}` : "";
        await view.start({ deviceId, maskImageUrl: maskUrl, apiBase, cameraId: cam?.id || "" });
        return { mode: "usb", view, hls: null };
      } catch (e) {
        lastErr = e;
        await new Promise((r) => setTimeout(r, 500));
      }
    }
    if (usbOnly || wantsLocalUsb(cam)) {
      throw lastErr || new Error("USB-камера недоступна");
    }
    onStatus?.(`USB: ${lastErr?.message || "ошибка"}. Пробуем сетевой поток…`);
  }

  if (poi?.id) {
    await fetch(`${apiBase}/api/v1/pois/${poi.id}/stream/acquire`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_id: clientId || "browser", wait_hls: false }),
    }).catch(() => {});
  }
  onStatus?.("Подключение защищённого потока…");
  const { waitMaskedPlayback, playHlsOnVideo } = await import("./stream-player.js");
  const { url } = await waitMaskedPlayback(cam.id, clientId, { maxWaitMs: 20000, pollMs: 800 });
  const hls = await playHlsOnVideo(video, url, {});
  return { mode: "hls", view: null, hls };
}
