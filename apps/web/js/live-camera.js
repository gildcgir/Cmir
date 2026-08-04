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
/** Faster detect = fewer bare-face frames between ticks */
const DETECT_INTERVAL_MS = 66;
/** Names need stable frames; masks apply immediately (privacy-first). */
const MIN_NAME_CONFIRM_FRAMES = 2;
const SIG_BLEND = 0.35;
const CONSENT_HOLD_FRAMES = 20;
const FACE_MATCH_INTERVAL_MS = 800;
/** Soft floor for tiny faces; keep modest for mobile perf. */
const MIN_FACE_PX = 18;
const MAX_FACES_PER_FRAME = 8;
/** Upscale pass is expensive — off by default on phone preview. */
const UPSCALE_EVERY_N = 0;
const NMS_IOU = 0.45;
/** Keep drawing last mask while detector briefly loses the face */
const TRACK_HOLD_MISSED = 22;
/** New tracks must confirm before drawing — kills one-frame chest FPs */
const TRACK_CONFIRM_TO_SHOW = 2;
const isMobileUa = /Android|iPhone|iPad|CmirAndroid/i.test(
  typeof navigator !== "undefined" ? navigator.userAgent || "" : "",
);

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

function authHeaders(extra = {}) {
  const h = { ...extra };
  const t = localStorage.getItem("cmir_token") || "";
  if (t) h.Authorization = "Bearer " + t;
  return h;
}

function currentUserId() {
  try {
    const raw = localStorage.getItem("cmir_user");
    if (!raw) return "";
    return JSON.parse(raw)?.id || "";
  } catch (_) {
    return "";
  }
}

/**
 * Strict face gate — reject body false-positives (e.g. chest).
 * Requires two eye-like keypoints in the upper half of the box.
 */
export function isLikelyFaceDetection(d, vw, vh) {
  const bb = d.boundingBox;
  if (!bb || !vw || !vh) return false;
  const norm = bb.originX <= 1 && bb.originY <= 1 && bb.width <= 1;
  const x = norm ? bb.originX * vw : bb.originX;
  const y = norm ? bb.originY * vh : bb.originY;
  const w = norm ? bb.width * vw : bb.width;
  const h = norm ? bb.height * vh : bb.height;
  if (!(w >= MIN_FACE_PX && h >= MIN_FACE_PX)) return false;
  if (w > vw * 0.85 || h > vh * 0.85) return false;
  // Faces are roughly square; chests often make very wide / flat boxes
  const ar = w / h;
  if (ar < 0.55 || ar > 1.55) return false;

  const score = d.categories?.[0]?.score;
  if (typeof score === "number" && score < 0.55) return false;

  const kps = d.keypoints || [];
  if (kps.length < 2) return false;

  const kp = (i) => {
    const p = kps[i];
    if (!p) return null;
    const px = p.x <= 1 ? p.x * vw : p.x;
    const py = p.y <= 1 ? p.y * vh : p.y;
    return { x: px, y: py };
  };
  const right = kp(0);
  const left = kp(1);
  if (!right || !left) return false;

  const eyeDist = Math.hypot(left.x - right.x, left.y - right.y);
  if (eyeDist < 8) return false;
  // Eyes should span a sensible fraction of face width
  if (eyeDist < w * 0.18 || eyeDist > w * 0.92) return false;

  const midY = (left.y + right.y) / 2;
  const midX = (left.x + right.x) / 2;
  // Eyes live in the upper ~58% of a face box — chest FPs sit mid/low
  if (midY < y || midY > y + h * 0.58) return false;
  // Eye midpoint roughly horizontally centered in the box
  if (midX < x + w * 0.15 || midX > x + w * 0.85) return false;

  // Eye line should be nearly horizontal (roll < ~35°)
  const roll = Math.abs(Math.atan2(left.y - right.y, left.x - right.x));
  if (roll > 0.65 && roll < Math.PI - 0.65) return false;

  return true;
}

function bboxAreaNorm(d, vw, vh) {
  const bb = d.boundingBox;
  if (!bb) return 0;
  const norm = bb.originX <= 1;
  if (norm) return Math.max(0, bb.width * bb.height);
  return Math.max(0, (bb.width * bb.height) / (vw * vh));
}

function bboxIoU(a, b, vw, vh) {
  const toPx = (bb) => {
    const norm = bb.originX <= 1;
    return {
      x: norm ? bb.originX * vw : bb.originX,
      y: norm ? bb.originY * vh : bb.originY,
      w: norm ? bb.width * vw : bb.width,
      h: norm ? bb.height * vh : bb.height,
    };
  };
  const A = toPx(a.boundingBox);
  const B = toPx(b.boundingBox);
  const x1 = Math.max(A.x, B.x);
  const y1 = Math.max(A.y, B.y);
  const x2 = Math.min(A.x + A.w, B.x + B.w);
  const y2 = Math.min(A.y + A.h, B.y + B.h);
  const inter = Math.max(0, x2 - x1) * Math.max(0, y2 - y1);
  const uni = A.w * A.h + B.w * B.h - inter;
  return uni > 0 ? inter / uni : 0;
}

function nmsMerge(dets, vw, vh, iouThr = NMS_IOU) {
  const sorted = [...dets].sort(
    (a, b) => bboxAreaNorm(b, vw, vh) - bboxAreaNorm(a, vw, vh),
  );
  const kept = [];
  for (const d of sorted) {
    if (!d?.boundingBox) continue;
    if (kept.some((k) => bboxIoU(k, d, vw, vh) >= iouThr)) continue;
    kept.push(d);
  }
  return kept;
}

/** Scale detections from an upscaled canvas back to video pixel space. */
function scaleDetectionsDown(dets, factor) {
  if (!factor || factor === 1) return dets;
  return dets.map((d) => {
    const bb = d.boundingBox;
    if (!bb) return d;
    const norm = bb.originX <= 1;
    // Normalized coords stay the same across scales; pixel coords need /factor
    if (norm) return d;
    return {
      ...d,
      boundingBox: {
        ...bb,
        originX: bb.originX / factor,
        originY: bb.originY / factor,
        width: bb.width / factor,
        height: bb.height / factor,
      },
      keypoints: (d.keypoints || []).map((kp) => ({
        ...kp,
        x: kp.x / factor,
        y: kp.y / factor,
      })),
    };
  });
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
    this.detector = null; // full-range (distant)
    this.detectorNear = null; // short-range (close)
    this.upscaleCanvas = null;
    this.upscaleCtx = null;
    this.detectTick = 0;
    this.maskImg = null;
    this.stream = null;
    this.running = false;
    this.raf = 0;
    this.lastTs = 0;
    this.faceSmooth = new Map();
    this.matchCache = new Map();
    this.apiBase = "";
    this.ready = false;
    this.compositeMode = true;
    this.onRecognized = null;
    this.cameraId = "";
    this.presenceAcc = new Map();
    this.presenceTimer = null;
    this.lastFaceBbox = null;
    this.lastKeypoints = null;
    this.privacyReady = false;
    this.firstDetectDone = false;
    /** Bumped on every stop() — invalidates in-flight start() so getUserMedia can't leak. */
    this._session = 0;
  }

  async init() {
    if (this.ready) return;
    const localBase = new URL("../vendor/mediapipe/", import.meta.url);
    const localBundle = new URL("vision_bundle.mjs", localBase).href;
    const localWasm = new URL("wasm", localBase).href;
    const modelNear = new URL("models/blaze_face_short_range.tflite", localBase).href;

    const loadFaceDetector = async (bundleUrl, wasmPath, modelPath, minConf) => {
      const { FaceDetector, FilesetResolver } = await import(bundleUrl);
      const vision = await FilesetResolver.forVisionTasks(wasmPath);
      return FaceDetector.createFromOptions(vision, {
        baseOptions: { modelAssetPath: modelPath },
        runningMode: "VIDEO",
        minDetectionConfidence: minConf,
      });
    };

    const tryLocal = async () => {
      // short_range only — full_range.tflite mismatches tasks-vision 0.10 graph
      // (2304 vs 896 boxes) and crashes detectForVideo in WebView.
      const near = await loadFaceDetector(localBundle, localWasm, modelNear, 0.55);
      return { far: null, near };
    };

    const tryCdn = async () => {
      const near = await loadFaceDetector(
        "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/+esm",
        "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm",
        "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite",
        0.55,
      );
      return { far: null, near };
    };

    try {
      const pair = await tryLocal();
      this.detector = pair.near;
      this.detectorNear = null;
    } catch (e) {
      console.warn("local MediaPipe failed, trying CDN", e);
      const pair = await tryCdn();
      this.detector = pair.near;
      this.detectorNear = null;
    }
    if (!this.detector) throw new Error("Face detector failed to load");
    this.ready = true;
  }

  async waitForVideoDims(timeoutMs = 4000) {
    const v = this.video;
    if (v.videoWidth > 0) return;
    await new Promise((resolve, reject) => {
      const t0 = Date.now();
      const onReady = () => {
        if (v.videoWidth > 0) {
          cleanup();
          resolve();
        } else if (Date.now() - t0 > timeoutMs) {
          cleanup();
          reject(new Error("Камера не отдала кадр"));
        }
      };
      const cleanup = () => {
        v.removeEventListener("loadeddata", onReady);
        v.removeEventListener("loadedmetadata", onReady);
        clearInterval(id);
      };
      v.addEventListener("loadeddata", onReady);
      v.addEventListener("loadedmetadata", onReady);
      const id = setInterval(onReady, 50);
      onReady();
    });
  }

  _releaseMediaStream(stream) {
    if (!stream) return;
    try {
      stream.getTracks().forEach((t) => t.stop());
    } catch (_) {}
  }

  async start({
    deviceId,
    facingMode = "",
    maskImageUrl = "",
    apiBase = "",
    cameraId = "",
    compositeMode = true,
  } = {}) {
    this.stop({ keepReady: true });
    const session = this._session;
    this.apiBase = apiBase;
    this.cameraId = cameraId;
    this.compositeMode = compositeMode !== false;
    this.privacyReady = false;
    this.firstDetectDone = false;
    this.setMaskImageUrl(maskImageUrl);
    this.video.classList.add("live-source-hidden");
    this.canvas.style.display = "";
    this.canvas.parentElement?.classList.add("privacy-composite");
    this.canvas.style.opacity = "1";
    this.resizeCanvas();
    if (this.ctx) {
      this.ctx.fillStyle = "#000";
      this.ctx.fillRect(0, 0, this.canvas.width || 2, this.canvas.height || 2);
    }

    // Privacy: detector must be ready before any camera pixels are painted
    await this.init();
    if (session !== this._session) return;

    const idealW = isMobileUa ? 640 : 1280;
    const idealH = isMobileUa ? 480 : 720;
    let stream;
    if (deviceId) {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { deviceId: { exact: deviceId }, width: { ideal: idealW }, height: { ideal: idealH } },
        });
      } catch (_) {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: facingMode || "user" }, width: { ideal: idealW }, height: { ideal: idealH } },
          audio: false,
        });
      }
    } else if (facingMode) {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: { ideal: facingMode },
            width: { ideal: idealW },
            height: { ideal: idealH },
          },
          audio: false,
        });
      } catch (_) {
        try {
          stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: { exact: facingMode } },
            audio: false,
          });
        } catch (_) {
          stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        }
      }
    } else {
      await ensureCameraPermission();
      if (session !== this._session) return;
      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: idealW }, height: { ideal: idealH } },
        audio: false,
      });
    }
    if (session !== this._session) {
      this._releaseMediaStream(stream);
      return;
    }
    this.stream = stream;
    this.video.srcObject = stream;
    this.video.muted = true;
    this.video.setAttribute("playsinline", "true");
    this.video.setAttribute("autoplay", "true");
    try {
      await this.video.play();
    } catch (e) {
      console.warn("video.play failed", e);
    }
    if (session !== this._session) {
      this._releaseMediaStream(stream);
      if (this.stream === stream) this.stream = null;
      if (this.video.srcObject === stream) this.video.srcObject = null;
      return;
    }
    try {
      await this.waitForVideoDims();
    } catch (e) {
      console.warn(e);
    }
    if (session !== this._session) {
      this._releaseMediaStream(stream);
      if (this.stream === stream) this.stream = null;
      if (this.video.srcObject === stream) this.video.srcObject = null;
      return;
    }

    this.running = true;
    this.lastTs = 0;
    const tick = (ts) => {
      if (!this.running || session !== this._session) return;
      this.raf = requestAnimationFrame(tick);
      this.drawFrame(ts);
    };
    this.raf = requestAnimationFrame(tick);
    this.presenceTimer = setInterval(() => this.flushPresence(), 5000);
  }

  collectDetections(video, vw, vh, ts) {
    const stamp = performance.now();
    let dets = [];
    try {
      dets = dets.concat(this.detector?.detectForVideo(video, stamp)?.detections || []);
    } catch (_) {}
    try {
      dets = dets.concat(this.detectorNear?.detectForVideo(video, stamp + 1)?.detections || []);
    } catch (_) {}

    // 2× upscale pass — makes distant faces look larger to the model
    this.detectTick = (this.detectTick || 0) + 1;
    if (this.detectTick % UPSCALE_EVERY_N === 0 && this.detector && vw > 0) {
      const factor = 2;
      if (!this.upscaleCanvas) {
        this.upscaleCanvas = document.createElement("canvas");
        this.upscaleCtx = this.upscaleCanvas.getContext("2d", { willReadFrequently: true });
      }
      const uw = Math.min(1920, Math.round(vw * factor));
      const uh = Math.min(1920, Math.round(vh * factor));
      const fx = uw / vw;
      const fy = uh / vh;
      if (this.upscaleCanvas.width !== uw || this.upscaleCanvas.height !== uh) {
        this.upscaleCanvas.width = uw;
        this.upscaleCanvas.height = uh;
      }
      this.upscaleCtx.drawImage(video, 0, 0, uw, uh);
      try {
        const up = this.detector.detectForVideo(this.upscaleCanvas, stamp + 2)?.detections || [];
        // MediaPipe returns normalized boxes relative to the input frame
        dets = dets.concat(scaleDetectionsDown(up, fx));
      } catch (_) {}
    }

    return nmsMerge(
      dets.filter((d) => isLikelyFaceDetection(d, vw, vh)),
      vw,
      vh,
    );
  }

  /** Server-side match — gallery never downloaded to the browser. */
  requestFaceMatch(trackKey, sig, priorUserId) {
    if (!this.apiBase || !sig) return;
    const cached = this.matchCache.get(trackKey);
    const now = performance.now();
    if (cached?.pending) return;
    if (cached && now - cached.at < FACE_MATCH_INTERVAL_MS) return;
    this.matchCache.set(trackKey, {
      ...(cached || {}),
      pending: true,
      at: now,
    });
    fetch(`${this.apiBase}/api/v1/face-match`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        embedding: sig,
        prior_user_id: priorUserId || "",
      }),
    })
      .then((r) => r.json())
      .then((json) => {
        const data = json.data || {};
        this.matchCache.set(trackKey, {
          user_id: data.matched ? data.user_id : null,
          display_name: data.matched ? data.display_name || "" : null,
          at: performance.now(),
          pending: false,
        });
      })
      .catch(() => {
        const prev = this.matchCache.get(trackKey) || {};
        this.matchCache.set(trackKey, { ...prev, pending: false, at: performance.now() });
      });
  }

  cachedMatch(trackKey) {
    const c = this.matchCache.get(trackKey);
    if (!c?.user_id) return null;
    return { user_id: c.user_id, display_name: c.display_name || "" };
  }

  setMaskImageUrl(url) {
    this.maskImg = null;
    if (!url) return;
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => { this.maskImg = img; };
    img.src = url;
  }

  getLastFaceSignature() {
    if (!this.lastFaceBbox) return null;
    return signatureFromVideo(this.video, this.lastFaceBbox);
  }

  flushPresence() {
    // Browser may only report self (JWT); worker reports all matched faces.
    if (!this.apiBase || !this.cameraId || !this.presenceAcc.size) return Promise.resolve();
    const token = localStorage.getItem("cmir_token") || "";
    const selfId = currentUserId();
    if (!token || !selfId) {
      this.presenceAcc.clear();
      return Promise.resolve();
    }
    const seconds = this.presenceAcc.get(selfId) || 0;
    this.presenceAcc.clear();
    if (seconds <= 0) return Promise.resolve();
    return fetch(`${this.apiBase}/api/v1/face-presence`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        camera_id: this.cameraId,
        presence: [{ user_id: selfId, camera_id: this.cameraId, seconds: Math.round(seconds * 1000) / 1000 }],
      }),
      keepalive: true,
    }).catch(() => {});
  }

  stop({ keepReady = false } = {}) {
    this._session = (this._session || 0) + 1;
    this.flushPresence();
    this.running = false;
    if (this.raf) cancelAnimationFrame(this.raf);
    this.raf = 0;
    if (this.presenceTimer) {
      clearInterval(this.presenceTimer);
      this.presenceTimer = null;
    }
    const orphan = this.stream || this.video?.srcObject;
    this.stream = null;
    if (this.video) this.video.srcObject = null;
    this._releaseMediaStream(orphan);
    this.video?.classList.remove("live-source-hidden");
    this.canvas?.parentElement?.classList.remove("privacy-composite");
    this.faceSmooth.clear();
    this.matchCache.clear();
    this.presenceAcc.clear();
    this.lastFaceBbox = null;
    this.lastKeypoints = null;
    this.privacyReady = false;
    this.firstDetectDone = false;
    this.ctx?.clearRect(0, 0, this.canvas.width, this.canvas.height);
    if (!keepReady) {
      this.ready = false;
      for (const det of [this.detector, this.detectorNear]) {
        if (!det) continue;
        try { det.close(); } catch (_) {}
      }
      this.detector = null;
      this.detectorNear = null;
    }
  }

  resizeCanvas() {
    const wrap = this.canvas.parentElement;
    let w = wrap?.clientWidth || 0;
    let h = wrap?.clientHeight || 0;
    // Sheet can briefly report 0×0 before layout — fall back to stream size
    if (w < 2 || h < 2) {
      w = Math.max(2, this.video?.videoWidth || 640);
      h = Math.max(2, this.video?.videoHeight || 360);
    }
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

    // Detector not ready: stay black (never paint raw faces)
    if (!this.detector) {
      this.ctx.fillStyle = "#000";
      this.ctx.fillRect(0, 0, cw, ch);
      return;
    }

    if (ts - this.lastTs >= DETECT_INTERVAL_MS) {
      const elapsedSec = this.lastTs
        ? Math.min(0.25, Math.max(DETECT_INTERVAL_MS / 1000, (ts - this.lastTs) / 1000))
        : DETECT_INTERVAL_MS / 1000;
      this.lastTs = ts;
      let dets = this.collectDetections(video, vw, vh, ts);
      // Prefer larger faces first when capping for performance in huge crowds
      if (dets.length > MAX_FACES_PER_FRAME) {
        dets = dets
          .map((d) => ({ d, area: bboxAreaNorm(d, vw, vh) }))
          .sort((a, b) => b.area - a.area)
          .slice(0, MAX_FACES_PER_FRAME)
          .map((x) => x.d);
      }
      const usedKeys = new Set();
      let primaryBbox = null;
      let primaryKps = null;

      for (const d of dets) {
        // Eyes-only privacy bar / mask (not full face)
        const raw = poseFromDetection(d.keypoints, vw, vh, d.boundingBox, false);
        if (!raw) continue;
        const key = matchFaceTrack(this.faceSmooth, raw);
        const prev = this.faceSmooth.get(key);
        const smooth = smoothPose(prev?.smooth, raw);
        // Signature is expensive (getImageData) — reuse until match interval
        let sig = prev?.sig || null;
        const priorId = prev?.userId || "";
        const cachedMatch = this.matchCache.get(key);
        if (!sig || !cachedMatch || performance.now() - (cachedMatch.at || 0) >= FACE_MATCH_INTERVAL_MS) {
          const sigRaw = signatureFromVideo(video, d.boundingBox);
          sig = blendSignature(prev?.sig, sigRaw);
          this.requestFaceMatch(key, sig, priorId);
        }
        let face = this.cachedMatch(key);
        let hold = prev?.hold || 0;
        if (face?.user_id) {
          hold = CONSENT_HOLD_FRAMES;
        } else if (hold > 0 && priorId) {
          face = { user_id: priorId, display_name: prev?.name || "" };
          hold -= 1;
        } else {
          hold = 0;
        }
        const name = face?.display_name || null;
        const userId = face?.user_id || null;
        const hadName = prev?.name;
        const confirm = (prev?.confirm || 0) + 1;
        this.faceSmooth.set(key, {
          smooth: { ...smooth, _inflate: 1 },
          name,
          userId,
          sig,
          confirm,
          shown: (prev?.shown || 0) + 1,
          missed: 0,
          hold,
          vx: prev?.smooth ? (smooth.cx - prev.smooth.cx) * 0.5 + (prev.vx || 0) * 0.5 : 0,
          vy: prev?.smooth ? (smooth.cy - prev.smooth.cy) * 0.5 + (prev.vy || 0) * 0.5 : 0,
        });
        usedKeys.add(key);
        if (!primaryBbox) {
          primaryBbox = d.boundingBox;
          primaryKps = d.keypoints || null;
        }
        if (userId) {
          this.presenceAcc.set(userId, (this.presenceAcc.get(userId) || 0) + elapsedSec);
        }
        if (name && !hadName && this.onRecognized) {
          this.onRecognized({ name, userId, key });
        }
      }

      if (primaryBbox) this.lastFaceBbox = primaryBbox;
      if (primaryKps) this.lastKeypoints = primaryKps;

      for (const [key, state] of this.faceSmooth) {
        if (usedKeys.has(key)) continue;
        state.missed = (state.missed || 0) + 1;
        state.confirm = 0;
        // Coast last pose with velocity + inflate while briefly lost
        if (state.smooth) {
          const grow = 1 + Math.min(0.45, state.missed * 0.04);
          const vx = (state.vx || 0) * 0.85;
          const vy = (state.vy || 0) * 0.85;
          state.vx = vx;
          state.vy = vy;
          state.smooth = {
            ...state.smooth,
            cx: state.smooth.cx + vx,
            cy: state.smooth.cy + vy,
            w: state.smooth.w * 1.015,
            h: state.smooth.h * 1.015,
            _inflate: grow,
          };
        }
        if (state.missed > TRACK_HOLD_MISSED) this.faceSmooth.delete(key);
      }
      this.firstDetectDone = true;
    }

    // Privacy-first: black until first detection pass (masks applied in same frame)
    if (this.compositeMode && !this.firstDetectDone) {
      this.ctx.fillStyle = "#000";
      this.ctx.fillRect(0, 0, cw, ch);
      return;
    }

    // Draw video THEN immediately overlay eye masks / names
    this.ctx.fillStyle = "#000";
    this.ctx.fillRect(0, 0, cw, ch);
    this.ctx.drawImage(video, ox, oy, vw * scale, vh * scale);

    for (const state of this.faceSmooth.values()) {
      if (!state.smooth) continue;
      // Don't paint unconfirmed tracks (flicker / body FPs)
      if ((state.shown || 0) < TRACK_CONFIRM_TO_SHOW && !(state.missed > 0)) continue;
      // If never confirmed, don't keep drawing while coasting
      if ((state.shown || 0) < TRACK_CONFIRM_TO_SHOW) continue;
      const named = state.name && (state.confirm || 0) >= MIN_NAME_CONFIRM_FRAMES && !(state.missed > 0);
      if (named) {
        drawNameUnderChin(this.ctx, state.smooth, state.name, scale, ox, oy);
      } else {
        const pose = state.smooth;
        const inflate = pose._inflate || (state.missed ? 1 + Math.min(0.4, state.missed * 0.035) : 1);
        const drawPose = inflate === 1 ? pose : { ...pose, w: pose.w * inflate, h: pose.h * inflate };
        drawOrientedOverlay(this.ctx, drawPose, this.maskImg, scale, ox, oy);
      }
    }

    if (!this.privacyReady) {
      this.privacyReady = true;
      this.canvas.style.opacity = "1";
    }
  }
}

function matchFaceTrack(faceSmooth, raw) {
  let bestKey = null;
  // Tighter association — reduces track hopping / duplicate masks
  let bestDist = Math.max(18, (raw.w || 40) * 0.75);
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
          await fetch(`${apiBase}/api/v1/pois/${poi.id}/stream/acquire`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              client_id: clientId || "browser",
              browser_usb: true,
              wait_hls: false,
            }),
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
