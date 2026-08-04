/**
 * Guided multi-pose face enrollment for Cmir consent kiosk.
 * Poses: center → left → right → up → down.
 * Each pose: instruction → countdown 3,2,1,0 → capture.
 */
export const ENROLL_POSES = [
  {
    id: "center",
    title: "Смотрите прямо в камеру",
    hint: "Держите голову ровно, лицо полностью в кадре",
    yaw: [-12, 12],
    pitch: [-12, 12],
  },
  {
    id: "left",
    title: "Поверните голову влево",
    hint: "Медленно поверните лицо к левому плечу и задержите",
    yaw: [18, 55],
    pitch: [-18, 18],
  },
  {
    id: "right",
    title: "Поверните голову вправо",
    hint: "Медленно поверните лицо к правому плечу и задержите",
    yaw: [-55, -18],
    pitch: [-18, 18],
  },
  {
    id: "up",
    title: "Поднимите подбородок вверх",
    hint: "Слегка запрокиньте голову, смотря чуть выше камеры",
    yaw: [-18, 18],
    pitch: [-45, -14],
  },
  {
    id: "down",
    title: "Опустите подбородок вниз",
    hint: "Наклоните голову вниз, взгляд чуть ниже камеры",
    yaw: [-18, 18],
    pitch: [14, 45],
  },
];

export function poseInRange(yaw, pitch, step) {
  const [y0, y1] = step.yaw;
  const [p0, p1] = step.pitch;
  return yaw >= y0 && yaw <= y1 && pitch >= p0 && pitch <= p1;
}

/** Approximate yaw/pitch (degrees) from Face Landmarker facialTransformationMatrix. */
export function yawPitchFromMatrix(matrixData) {
  if (!matrixData || matrixData.length < 16) return { yaw: 0, pitch: 0, roll: 0 };
  const r00 = matrixData[0];
  const r10 = matrixData[1];
  const r20 = matrixData[2];
  const r21 = matrixData[6];
  const r22 = matrixData[10];
  const pitch = Math.atan2(-r21, r22) * (180 / Math.PI);
  const yaw = Math.atan2(r20, Math.sqrt(r00 * r00 + r10 * r10)) * (180 / Math.PI);
  const roll = Math.atan2(r10, r00) * (180 / Math.PI);
  return { yaw, pitch, roll };
}

/** Fallback yaw/pitch from face bbox position in frame (no landmarker). */
export function yawPitchFromBbox(bbox, videoW, videoH) {
  if (!bbox || !videoW || !videoH) return { yaw: 0, pitch: 0 };
  const norm = bbox.originX <= 1;
  const cx = (norm ? bbox.originX + bbox.width / 2 : bbox.originX + bbox.width / 2) / (norm ? 1 : videoW);
  const cy = (norm ? bbox.originY + bbox.height / 2 : bbox.originY + bbox.height / 2) / (norm ? 1 : videoH);
  const yaw = (0.5 - cx) * 80;
  const pitch = (cy - 0.5) * 70;
  return { yaw, pitch };
}

/** Yaw/pitch from BlazeFace keypoints (eyes/nose) — works offline in Android WebView. */
export function yawPitchFromKeypoints(kps, videoW, videoH) {
  if (!kps || kps.length < 3 || !videoW || !videoH) return null;
  const pt = (i) => {
    const p = kps[i];
    if (!p) return null;
    return {
      x: p.x <= 1 ? p.x * videoW : p.x,
      y: p.y <= 1 ? p.y * videoH : p.y,
    };
  };
  const right = pt(0);
  const left = pt(1);
  const nose = pt(2);
  if (!right || !left || !nose) return null;
  const midX = (left.x + right.x) / 2;
  const midY = (left.y + right.y) / 2;
  const eyeDist = Math.hypot(left.x - right.x, left.y - right.y) || 1;
  const yaw = ((nose.x - midX) / eyeDist) * 45;
  const pitch = ((nose.y - midY) / eyeDist) * 40;
  return { yaw, pitch };
}

export class PoseEnrollment {
  constructor({
    onStatus,
    onPoseCaptured,
    captureSignature,
    getPose,
    holdNeed = 8,
    timeoutMs = 8000,
    countdownSec = 3,
  } = {}) {
    this.onStatus = onStatus || (() => {});
    this.onPoseCaptured = onPoseCaptured || (() => {});
    this.captureSignature = captureSignature;
    this.getPose = getPose;
    this.holdNeed = holdNeed;
    this.timeoutMs = timeoutMs;
    this.countdownSec = Math.max(0, Number(countdownSec) || 0);
    this.templates = [];
    this.stepIndex = 0;
    this.stableFrames = 0;
    this.running = false;
  }

  get current() {
    return ENROLL_POSES[this.stepIndex] || null;
  }

  get done() {
    return this.templates.length >= ENROLL_POSES.length;
  }

  reset() {
    this.templates = [];
    this.stepIndex = 0;
    this.stableFrames = 0;
    this.running = false;
  }

  async run() {
    this.reset();
    this.running = true;
    while (this.running && this.stepIndex < ENROLL_POSES.length) {
      const step = this.current;
      this.onStatus({
        step: this.stepIndex + 1,
        total: ENROLL_POSES.length,
        poseId: step.id,
        title: step.title,
        hint: step.hint,
        progress: 0,
        phase: "guide",
        countdown: null,
      });
      await sleep(600);
      if (!this.running) break;

      await this._countdown(step);
      if (!this.running) break;

      // Short hold after 0 — then capture (countdown already prepared the user)
      this.stableFrames = 0;
      await this._waitPose(step);
      if (!this.running) break;

      const sig = this.captureSignature();
      if (!sig) {
        this.onStatus({
          step: this.stepIndex + 1,
          total: ENROLL_POSES.length,
          poseId: step.id,
          title: step.title,
          hint: "Лицо не видно — вернитесь в кадр, повторим отсчёт",
          progress: 0,
          phase: "retry",
          countdown: null,
        });
        await sleep(900);
        continue;
      }
      const pose = this.getPose() || { yaw: 0, pitch: 0 };
      const tpl = {
        pose: step.id,
        embedding: sig,
        yaw: pose.yaw,
        pitch: pose.pitch,
      };
      this.templates.push(tpl);
      this.onPoseCaptured(tpl, [...this.templates]);
      this.stepIndex += 1;
      this.onStatus({
        step: this.stepIndex,
        total: ENROLL_POSES.length,
        poseId: step.id,
        title: `✓ ${step.title}`,
        hint: this.stepIndex < ENROLL_POSES.length ? "Отлично, следующий ракурс…" : "Все ракурсы сохранены",
        progress: 1,
        phase: "captured",
        countdown: null,
      });
      await sleep(500);
    }
    this.running = false;
    this.onStatus({
      step: this.templates.length,
      total: ENROLL_POSES.length,
      phase: "done",
      countdown: null,
      title: "Готово",
      hint: "",
      progress: 1,
    });
    return this.templates;
  }

  stop() {
    this.running = false;
  }

  async _countdown(step) {
    const from = this.countdownSec;
    for (let n = from; n >= 0; n--) {
      if (!this.running) return;
      this.onStatus({
        step: this.stepIndex + 1,
        total: ENROLL_POSES.length,
        poseId: step.id,
        title: step.title,
        hint: n === 0 ? "Фиксация ракурса!" : `Примите позу — съёмка через ${n}…`,
        progress: from <= 0 ? 1 : (from - n) / from,
        phase: "countdown",
        countdown: n,
      });
      await sleep(1000);
    }
  }

  async _waitPose(step) {
    const need = this.holdNeed;
    const started = Date.now();
    const timeoutMs = this.timeoutMs;
    while (this.running && this.stableFrames < need) {
      const pose = this.getPose();
      const timedOut = Date.now() - started > timeoutMs;
      if ((pose && poseInRange(pose.yaw, pose.pitch, step)) || timedOut) {
        this.stableFrames += 1;
        this.onStatus({
          step: this.stepIndex + 1,
          total: ENROLL_POSES.length,
          poseId: step.id,
          title: timedOut ? "Держите лицо в кадре" : step.title,
          hint: timedOut ? "Фиксация…" : "Отлично, держите…",
          progress: this.stableFrames / need,
          phase: "hold",
          countdown: null,
        });
      } else {
        this.stableFrames = Math.max(0, this.stableFrames - 2);
        this.onStatus({
          step: this.stepIndex + 1,
          total: ENROLL_POSES.length,
          poseId: step.id,
          title: step.title,
          hint: step.hint,
          progress: this.stableFrames / need,
          phase: "guide",
          countdown: null,
        });
      }
      await sleep(70);
    }
  }
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}
