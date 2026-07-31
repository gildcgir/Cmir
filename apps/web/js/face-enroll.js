/**
 * Guided multi-pose face enrollment for Cmir consent kiosk.
 * Poses: center → left → right → up → down (MediaPipe Face Landmarker yaw/pitch).
 */
export const ENROLL_POSES = [
  { id: "center", title: "Смотрите прямо в камеру", yaw: [ -12, 12], pitch: [-12, 12] },
  { id: "left", title: "Поверните голову влево", yaw: [ 18, 55], pitch: [-18, 18] },
  { id: "right", title: "Поверните голову вправо", yaw: [-55,-18], pitch: [-18, 18] },
  { id: "up", title: "Поднимите подбородок вверх", yaw: [-18, 18], pitch: [-45,-14] },
  { id: "down", title: "Опустите подбородок вниз", yaw: [-18, 18], pitch: [ 14, 45] },
];

export function poseInRange(yaw, pitch, step) {
  const [y0, y1] = step.yaw;
  const [p0, p1] = step.pitch;
  return yaw >= y0 && yaw <= y1 && pitch >= p0 && pitch <= p1;
}

/** Approximate yaw/pitch (degrees) from Face Landmarker facialTransformationMatrix. */
export function yawPitchFromMatrix(matrixData) {
  if (!matrixData || matrixData.length < 16) return { yaw: 0, pitch: 0, roll: 0 };
  // column-major 4x4
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

export class PoseEnrollment {
  constructor({ onStatus, captureSignature, getPose }) {
    this.onStatus = onStatus || (() => {});
    this.captureSignature = captureSignature;
    this.getPose = getPose;
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
      this.onStatus(`Шаг ${this.stepIndex + 1}/${ENROLL_POSES.length}: ${step.title}`);
      this.stableFrames = 0;
      // wait until pose held ~0.7s
      // eslint-disable-next-line no-await-in-loop
      await this._waitPose(step);
      if (!this.running) break;
      const sig = this.captureSignature();
      if (!sig) {
        this.onStatus("Лицо не видно — повторите позу");
        // eslint-disable-next-line no-await-in-loop
        await sleep(600);
        continue;
      }
      const pose = this.getPose() || { yaw: 0, pitch: 0 };
      this.templates.push({
        pose: step.id,
        embedding: sig,
        yaw: pose.yaw,
        pitch: pose.pitch,
      });
      this.stepIndex += 1;
      this.onStatus(`✓ ${step.title}`);
      // eslint-disable-next-line no-await-in-loop
      await sleep(350);
    }
    this.running = false;
    return this.templates;
  }

  stop() {
    this.running = false;
  }

  async _waitPose(step) {
    const need = 8;
    const started = Date.now();
    const timeoutMs = 9000;
    while (this.running && this.stableFrames < need) {
      const pose = this.getPose();
      const timedOut = Date.now() - started > timeoutMs;
      if ((pose && poseInRange(pose.yaw, pose.pitch, step)) || timedOut) {
        this.stableFrames += 1;
        this.onStatus(
          timedOut
            ? `Шаг ${this.stepIndex + 1}/${ENROLL_POSES.length}: держите лицо в кадре… ${this.stableFrames}/${need}`
            : `Шаг ${this.stepIndex + 1}/${ENROLL_POSES.length}: ${step.title}… ${this.stableFrames}/${need}`,
        );
      } else {
        this.stableFrames = Math.max(0, this.stableFrames - 2);
        this.onStatus(`Шаг ${this.stepIndex + 1}/${ENROLL_POSES.length}: ${step.title}`);
      }
      // eslint-disable-next-line no-await-in-loop
      await sleep(70);
    }
  }
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}
